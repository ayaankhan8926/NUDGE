from flask import Flask, jsonify, request
from flask_cors import CORS
import uuid

from agent.planner import create_plan
from agent.analyzer import analyze_workspace
from agent.interpreter import get_next_action

from execution.runner import execute_action
from execution.store import create_run

from routes.approval import approval_bp


app = Flask(__name__)

CORS(app)

app.register_blueprint(approval_bp)


@app.get("/")
def home():
    return jsonify({
        "name": "NUDGE",
        "status": "online",
        "message": "NUDGE agent backend is running"
    })


@app.get("/api/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "nudge-backend"
    })


def _build_follow_up_message(candidate):
    """
    Build a safe demo message without assuming every workflow has
    invoice-specific fields.
    """

    client = candidate.get("client") or "there"
    invoice_id = candidate.get("invoice_id")
    amount = candidate.get("amount")

    if invoice_id:
        amount_text = (
            f" for ₹{amount}"
            if amount is not None
            else ""
        )

        return (
            f"Hello {client},\\n\\n"
            f"This is a follow-up regarding invoice "
            f"{invoice_id}{amount_text}. "
            f"Please let us know the payment status.\\n\\n"
            "Thank you."
        )

    subject = candidate.get("subject")

    if subject:
        return (
            f"Hello {client},\\n\\n"
            f"This is a follow-up regarding: {subject}.\\n\\n"
            "Please let us know when you have an update.\\n\\n"
            "Thank you."
        )

    return (
        f"Hello {client},\\n\\n"
        "Just following up on our previous communication. "
        "Please let us know when you have an update.\\n\\n"
        "Thank you."
    )


@app.post("/api/agent/run")
def run_agent():

    data = request.get_json(
        silent=True
    ) or {}

    goal = str(
        data.get("goal", "")
    ).strip()

    if not goal:
        return jsonify({
            "error": "Goal is required"
        }), 400

    # ==================================================
    # 1. PLAN
    # ==================================================

    plan = create_plan(goal)

    if plan.get("status") == "error":
        return jsonify(plan), 400

    intent = plan.get(
        "intent",
        "ambiguous"
    )

    # ==================================================
    # 2. OBSERVE WORKSPACE
    # ==================================================
    #
    # The analyzer is now intent-aware. This is the key
    # connection between the new planner and analyzer.
    #

    analysis = analyze_workspace(
        intent=intent,
        workspace_state=data.get("workspace_state")
    )

    # ==================================================
    # 3. INTERPRET PLAN
    # ==================================================

    try:
        next_action = get_next_action(
            plan
        )

    except Exception as error:

        print(
            f"[NUDGE] Action interpreter unavailable: {error}"
        )

        next_action = None

    # ==================================================
    # 4. CREATE RUN
    # ==================================================

    run_id = str(
        uuid.uuid4()
    )

    candidates = analysis.get(
        "follow_up_candidates",
        []
    )

    # ==================================================
    # 5. DETERMINE WHETHER FOLLOW-UP IS REQUIRED
    # ==================================================
    #
    # The current execution/demo path is deliberately kept
    # deterministic. The workspace analyzer supplies the
    # candidate and the execution runner enforces the risk
    # gate before anything external can happen.
    #

    follow_up_required = len(
        candidates
    ) > 0

    # ==================================================
    # 6. PREPARE RISKY EMAIL ACTION
    # ==================================================

    if follow_up_required:

        candidate = candidates[0]

        email_payload = {
            "client": candidate.get(
                "client"
            ),
            "invoice_id": candidate.get(
                "invoice_id"
            ),
            "amount": candidate.get(
                "amount"
            ),
            "email_id": candidate.get(
                "email_id"
            ),
            "subject": candidate.get(
                "subject"
            ),
            "message": _build_follow_up_message(
                candidate
            )
        }

        # IMPORTANT:
        # Never pass approved=True here.
        # send_email must pass through the Python risk gate.

        action_result = execute_action(
            "send_email",
            email_payload
        )

        run_data = {
            "run_id": run_id,
            "goal": goal,
            "intent": intent,
            "intent_confidence": plan.get(
                "intent_confidence"
            ),
            "intent_reason": plan.get(
                "intent_reason"
            ),
            "plan": plan,
            "interpreted_action": next_action,
            "analysis": analysis,
            "action": action_result,
            "status": action_result["status"],
            "decision": None,
            "workflow_context": {
                "intent": intent,
                "candidate": candidate
            }
        }

        create_run(
            run_id,
            run_data
        )

        print(
            "[NUDGE] Follow-up candidate found:"
            f" {candidate.get('client')} |"
            f" {candidate.get('invoice_id') or candidate.get('email_id')}"
        )

        print(
            "[NUDGE] Intent:"
            f" {intent}"
        )

        print(
            "[NUDGE] Risk gate result:"
            f" {action_result.get('status')}"
        )

        return jsonify({
            "status": action_result["status"],
            "run_id": run_id,
            "goal": goal,
            "intent": intent,
            "intent_confidence": plan.get(
                "intent_confidence"
            ),
            "plan": plan,
            "interpreted_action": next_action,
            "analysis": analysis,
            "action": action_result
        })

    # ==================================================
    # 7. NO FOLLOW-UP REQUIRED
    # ==================================================

    run_data = {
        "run_id": run_id,
        "goal": goal,
        "intent": intent,
        "intent_confidence": plan.get(
            "intent_confidence"
        ),
        "intent_reason": plan.get(
            "intent_reason"
        ),
        "plan": plan,
        "interpreted_action": next_action,
        "analysis": analysis,
        "action": None,
        "status": "completed",
        "decision": None,
        "workflow_context": {
            "intent": intent
        }
    }

    create_run(
        run_id,
        run_data
    )

    print(
        "[NUDGE] No follow-up candidates found."
    )

    return jsonify({
        "status": "completed",
        "run_id": run_id,
        "goal": goal,
        "intent": intent,
        "intent_confidence": plan.get(
            "intent_confidence"
        ),
        "plan": plan,
        "interpreted_action": next_action,
        "analysis": analysis,
        "action": None
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
