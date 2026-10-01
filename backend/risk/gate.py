SAFE_ACTIONS = {
    "read_email",
    "read_calendar",
    "read_sheet",
    "analyze_data",
    "create_draft"
}

RISKY_ACTIONS = {
    "send_email",
    "delete_email",
    "create_calendar_event",
    "modify_calendar_event",
    "update_sheet"
}

BLOCKED_ACTIONS = {
    "delete_account",
    "change_password",
    "transfer_money"
}


def evaluate_action(action):
    """
    Evaluate whether an agent action can execute automatically.
    """

    if action in SAFE_ACTIONS:
        return {
            "decision": "allow",
            "action": action,
            "reason": "Action is considered safe."
        }

    if action in RISKY_ACTIONS:
        return {
            "decision": "approval_required",
            "action": action,
            "reason": "Human approval is required before this action."
        }

    if action in BLOCKED_ACTIONS:
        return {
            "decision": "blocked",
            "action": action,
            "reason": "This action is not permitted."
        }

    return {
        "decision": "approval_required",
        "action": action,
        "reason": "Unknown actions require human approval."
    }