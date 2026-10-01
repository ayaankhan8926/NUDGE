"""
NUDGE Replanner v2

The replanner consumes OBSERVE results and chooses the next controlled
step. It never executes an action itself.

Recovery policy:
- Failed consequential actions never get silently retried.
- A failed action may be proposed again once, with a human gate.
- After one failed retry, NUDGE stops safely.
- Successful invoice email -> approval-required sheet update.
- Successful sheet update -> complete.
"""

CONSEQUENTIAL = {
    "send_email",
    "delete_email",
    "create_calendar_event",
    "modify_calendar_event",
    "update_sheet",
}

def _failed_replan(action, observation, context):
    attempts = int((context or {}).get("recovery_attempts", 0))
    message = observation.get(
        "observation",
        "The previous action failed."
    )

    # Never loop forever.
    if attempts >= 1:
        return {
            "status": "replanned",
            "decision": "stop",
            "reason": (
                f"{message} NUDGE already attempted recovery once, "
                "so it stopped safely instead of looping."
            ),
            "next_action": None,
            "requires_human": True,
            "source": "deterministic_recovery",
            "recovery": {
                "attempted": True,
                "attempts": attempts,
                "outcome": "stopped_after_retry"
            }
        }

    # Consequential actions must not be retried silently.
    if action in CONSEQUENTIAL:
        return {
            "status": "replanned",
            "decision": "retry",
            "reason": (
                f"{message} NUDGE can retry the same action once, "
                "but a fresh human approval is required."
            ),
            "next_action": action,
            "requires_human": True,
            "source": "deterministic_recovery",
            "recovery": {
                "attempted": True,
                "attempts": attempts + 1,
                "outcome": "awaiting_human_retry"
            }
        }

    # Safe read/analysis actions can be retried without crossing the
    # external-action boundary.
    return {
        "status": "replanned",
        "decision": "retry",
        "reason": (
            f"{message} NUDGE will retry the safe workspace operation."
        ),
        "next_action": action,
        "requires_human": False,
        "source": "deterministic_recovery",
        "recovery": {
            "attempted": True,
            "attempts": attempts + 1,
            "outcome": "safe_retry"
        }
    }


def replan_after_observation(
    goal,
    observation,
    previous_action,
    intent=None,
    workflow_context=None
):
    observation = observation or {}
    context = dict(workflow_context or {})

    if observation.get("status") == "failed":
        recovery = observation.get("recovery") or {}
        if recovery.get("attempts"):
            context["recovery_attempts"] = recovery["attempts"]
        return _failed_replan(
            previous_action,
            observation,
            context
        )

    if previous_action == "send_email":
        changes = observation.get("changes") or {}
        return {
            "status": "replanned",
            "decision": "continue",
            "reason": (
                "The follow-up email was verified successfully. "
                "The invoice sheet should now be updated."
            ),
            "next_action": "update_sheet",
            "requires_human": True,
            "source": "deterministic",
            "context": {
                "intent": intent,
                "client": changes.get("client"),
                "invoice_id": changes.get("invoice_id"),
                "email_id": changes.get("email_id"),
                "amount": changes.get("amount"),
            }
        }

    if previous_action == "update_sheet":
        changes = observation.get("changes") or {}
        return {
            "status": "replanned",
            "decision": "complete",
            "reason": (
                "The invoice sheet was successfully updated "
                "and no additional action is currently required."
            ),
            "next_action": None,
            "requires_human": False,
            "source": "deterministic",
            "context": {
                "intent": intent,
                "client": changes.get("client"),
                "invoice_id": changes.get("invoice_id"),
                "email_id": changes.get("email_id"),
            }
        }

    if previous_action == "create_draft":
        return {
            "status": "replanned",
            "decision": "complete",
            "reason": "The draft was created successfully.",
            "next_action": None,
            "requires_human": False,
            "source": "deterministic",
        }

    return {
        "status": "replanned",
        "decision": "complete",
        "reason": "The observed action completed successfully.",
        "next_action": None,
        "requires_human": False,
        "source": "deterministic",
    }
