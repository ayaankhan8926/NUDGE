from flask import Blueprint, jsonify, request

from agent.observe import observe_execution
from agent.replanner import replan_after_observation
from execution.runner import execute_action

approval_bp = Blueprint("approval", __name__)


def get_run_from_request(run_id):
    body = request.get_json(silent=True) or {}
    run = body.get("run")
    if isinstance(run, dict) and run.get("run_id") == run_id:
        return run
    return None


def create_sheet_action(run, email_record):
    old_action = run.get("action") or {}
    payload = old_action.get("payload") or {}

    email_id = (
        email_record.get("email_id")
        if isinstance(email_record, dict)
        else None
    )

    client = payload.get("client", "client")
    invoice_id = payload.get("invoice_id", "invoice")

    return {
        "status": "approval_required",
        "action": "update_sheet",
        "reason": (
            "The email was sent successfully. "
            "NUDGE now wants to update the invoice sheet."
        ),
        "payload": {
            "invoice_id": payload.get("invoice_id"),
            "client": payload.get("client"),
            "email_id": email_id or payload.get("email_id"),
            "amount": payload.get("amount"),
            "status": "follow_up_sent",
            "note": f"Follow-up email sent to {client} for {invoice_id}.",
            "message": (
                f"Record the approved follow-up for {invoice_id} "
                "in the invoice sheet."
            ),
        },
    }


def safe_replan(run, action_name, observation, execution_result):
    try:
        return replan_after_observation(
            goal=run.get("goal", ""),
            observation=observation,
            previous_action=action_name,
            intent=run.get("intent"),
            workflow_context=run.get("workflow_context"),
        )
    except Exception:
        if observation.get("status") == "failed":
            return {
                "status": "replanned",
                "decision": "stop",
                "reason": observation.get(
                    "observation",
                    "The previous action failed. NUDGE stopped safely."
                ),
                "next_action": None,
                "requires_human": True,
                "source": "deterministic_fallback",
            }

        if action_name == "send_email":
            return {
                "status": "replanned",
                "decision": "continue",
                "reason": (
                    "The follow-up email was sent successfully. "
                    "The invoice sheet should now be updated."
                ),
                "next_action": "update_sheet",
                "requires_human": True,
                "source": "deterministic_fallback",
            }

        if action_name == "update_sheet":
            return {
                "status": "replanned",
                "decision": "complete",
                "reason": (
                    "The invoice sheet was successfully updated "
                    "and no additional action is currently required."
                ),
                "next_action": None,
                "requires_human": False,
                "source": "deterministic_fallback",
            }

        return {
            "status": "replanned",
            "decision": "complete",
            "reason": "The approved action completed successfully.",
            "next_action": None,
            "requires_human": False,
            "source": "deterministic_fallback",
        }


def build_observation(action_name, execution_result):
    """
    Always normalize the execution result before replanning.

    Some tool implementations return the execution record under
    `execution`, while older observe implementations expect a particular
    nested shape. This wrapper keeps the approval flow resilient.
    """
    try:
        observation = observe_execution(action_name, execution_result)
    except Exception as exc:
        observation = {
            "status": "failed",
            "observation": f"Observation failed: {exc}",
            "requires_replan": True,
        }

    # Defensive fallback for the exact case we just encountered:
    # execution succeeded but the observer returned no object.
    if not isinstance(observation, dict):
        observation = None

    if observation is None:
        execution = execution_result.get("execution") or {}

        if action_name == "send_email":
            email = execution.get("email") or {}
            if execution_result.get("status") == "executed" and email:
                observation = {
                    "status": "success",
                    "observation": (
                        "The follow-up email was successfully recorded as sent."
                    ),
                    "changes": {
                        "email_sent": True,
                        "client": email.get("client"),
                        "invoice_id": email.get("invoice_id"),
                        "email_id": email.get("email_id"),
                    },
                    "latest_email": email,
                    "requires_replan": True,
                }

        elif action_name == "update_sheet":
            update = execution.get("sheet_update") or execution.get("update") or {}
            if execution_result.get("status") == "executed":
                observation = {
                    "status": "success",
                    "observation": (
                        "The invoice sheet was successfully updated."
                    ),
                    "changes": {
                        "sheet_updated": True,
                        "invoice_id": update.get("invoice_id"),
                        "client": update.get("client"),
                    },
                    "latest_sheet_update": update,
                    "requires_replan": True,
                }

    return observation or {
        "status": "failed",
        "observation": "No observation was available after the previous action.",
        "requires_replan": True,
    }


@approval_bp.post("/api/agent/<run_id>/approve")
def approve_run(run_id):
    run = get_run_from_request(run_id)

    if not run:
        return jsonify({
            "error": "Run state missing. Please start a new run."
        }), 404

    action = run.get("action") or {}
    action_name = action.get("action")
    payload = action.get("payload") or {}

    if not action_name:
        return jsonify({
            "error": "No action is waiting for approval."
        }), 400

    execution_result = execute_action(
        action_name,
        payload,
        approved=True
    )

    run["decision"] = "approve"
    run["execution_result"] = execution_result

    observation = build_observation(
        action_name,
        execution_result
    )
    run["observation"] = observation

    replanning = safe_replan(
        run,
        action_name,
        observation,
        execution_result
    )
    run["replanning"] = replanning

    if execution_result.get("status") != "executed":
        run["status"] = "replanning"
        return jsonify({
            "status": "replanning",
            "run": run
        })

    if (
        action_name == "send_email"
        and replanning.get("decision") == "continue"
    ):
        email_record = (
            execution_result.get("execution", {}).get("email")
            or observation.get("latest_email")
            or {}
        )

        run["action"] = create_sheet_action(
            run,
            email_record
        )
        run["status"] = "approval_required"

        return jsonify({
            "status": "approval_required",
            "run": run
        })

    if replanning.get("decision") == "complete":
        run["action"] = None
        run["status"] = "completed"

        return jsonify({
            "status": "completed",
            "run": run
        })

    run["status"] = "replanning"

    return jsonify({
        "status": "replanning",
        "run": run
    })


@approval_bp.post("/api/agent/<run_id>/reject")
def reject_run(run_id):
    run = get_run_from_request(run_id)

    if not run:
        return jsonify({
            "error": "Run state missing. Please start a new run."
        }), 404

    run["decision"] = "reject"
    run["status"] = "rejected"
    run["replanning"] = {
        "status": "replanned",
        "decision": "stop",
        "reason": (
            "Human rejected the proposed action. "
            "NUDGE will not bypass the decision."
        ),
        "next_action": None,
        "requires_human": False,
        "source": "human",
    }

    return jsonify({
        "status": "rejected",
        "run": run
    })


@approval_bp.post("/api/agent/<run_id>/edit")
def edit_run(run_id):
    run = get_run_from_request(run_id)

    if not run:
        return jsonify({
            "error": "Run state missing. Please start a new run."
        }), 404

    body = request.get_json(silent=True) or {}
    message = str(body.get("message", "")).strip()

    if not message:
        return jsonify({
            "error": "Edited message cannot be empty."
        }), 400

    action = run.get("action") or {}
    payload = action.get("payload") or {}

    payload["message"] = message

    if action.get("action") == "update_sheet":
        payload["note"] = message

    action["payload"] = payload
    action["status"] = "approval_required"

    run["action"] = action
    run["decision"] = "edit"
    run["status"] = "approval_required"

    return jsonify({
        "status": "approval_required",
        "run": run
    })
