"""
NUDGE Action Interpreter

Gemini plans.
The interpreter normalizes Gemini's language.
The Python risk gate decides whether an action is allowed.

Gemini NEVER executes actions directly.
"""

RISKY_ACTIONS = {
    "send_email",
    "delete_email",
    "create_calendar_event",
    "modify_calendar_event",
    "update_sheet",
}


def normalize_action(action):
    """
    Convert Gemini's natural-language action into
    a controlled internal NUDGE action.
    """

    if not action:
        return None

    text = str(action).strip().lower()

    # Already normalized
    known_actions = {
        "read_email",
        "read_calendar",
        "read_sheet",
        "analyze_data",
        "create_draft",
        "send_email",
        "delete_email",
        "create_calendar_event",
        "modify_calendar_event",
        "update_sheet",
    }

    if text in known_actions:
        return text

    # --------------------------------------------------
    # SHEETS
    # --------------------------------------------------

    if (
        "invoice" in text
        and (
            "read" in text
            or "retrieve" in text
            or "check" in text
        )
    ):
        return "read_sheet"

    if (
        "spreadsheet" in text
        and (
            "read" in text
            or "analy" in text
            or "check" in text
        )
    ):
        if "analy" in text:
            return "analyze_data"

        return "read_sheet"

    if "analy" in text and (
        "data" in text
        or "record" in text
        or "spreadsheet" in text
        or "invoice" in text
    ):
        return "analyze_data"

    if "sheet" in text and "update" in text:
        return "update_sheet"

    # --------------------------------------------------
    # GMAIL - READ
    # --------------------------------------------------

    if (
        "search" in text
        and "email" in text
    ):
        return "read_email"

    if (
        "search" in text
        and "mail" in text
    ):
        return "read_email"

    if (
        "check" in text
        and (
            "email" in text
            or "mail" in text
            or "reply" in text
            or "repl" in text
        )
    ):
        return "read_email"

    if (
        "read" in text
        and (
            "email" in text
            or "mail" in text
        )
    ):
        return "read_email"

    # --------------------------------------------------
    # GMAIL - DRAFT
    # --------------------------------------------------

    if (
        "draft" in text
        or "prepare" in text
    ) and (
        "email" in text
        or "mail" in text
        or "follow-up" in text
        or "follow up" in text
    ):
        return "create_draft"

    # --------------------------------------------------
    # GMAIL - SEND
    # --------------------------------------------------

    # Any explicit email sending language is risky.
    if (
        "send" in text
        and (
            "email" in text
            or "emails" in text
            or "mail" in text
            or "message" in text
        )
    ):
        return "send_email"

    if (
        "follow-up" in text
        or "follow up" in text
    ) and (
        "send" in text
        or "sending" in text
    ):
        return "send_email"

    # --------------------------------------------------
    # CALENDAR
    # --------------------------------------------------

    if (
        "calendar" in text
        and (
            "read" in text
            or "check" in text
            or "inspect" in text
        )
    ):
        return "read_calendar"

    if (
        "calendar" in text
        and "create" in text
    ):
        return "create_calendar_event"

    if (
        "calendar" in text
        and (
            "modify" in text
            or "update" in text
            or "change" in text
        )
    ):
        return "modify_calendar_event"

    # --------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------

    return None


def interpret_plan(plan):
    """
    Safely interpret Gemini's plan.

    Only recognized actions are allowed to reach
    the execution layer.
    """

    if not plan:
        return {
            "status": "invalid",
            "actions": [],
            "risk_actions": [],
            "requires_human_approval": True,
            "reason": "No plan was provided."
        }

    steps = plan.get(
        "steps",
        []
    )

    interpreted_actions = []

    for step in steps:

        raw_action = step.get(
            "action",
            ""
        )

        internal_action = normalize_action(
            raw_action
        )

        if not internal_action:
            continue

        interpreted_actions.append({
            "step": step.get("step"),
            "tool": step.get("tool"),
            "source_action": raw_action,
            "action": internal_action,
            "description": step.get(
                "description",
                ""
            )
        })

    risk_actions = [
        action["action"]
        for action in interpreted_actions
        if action["action"] in RISKY_ACTIONS
    ]

    return {
        "status": "interpreted",
        "actions": interpreted_actions,
        "risk_actions": risk_actions,
        "requires_human_approval": (
            len(risk_actions) > 0
        )
    }


def get_next_action(plan):
    """
    Select the next meaningful action.

    Risky actions are prioritized so NUDGE can reach
    the Python risk gate when the plan contains one.
    """

    interpreted = interpret_plan(plan)

    actions = interpreted["actions"]

    if not actions:
        return None

    # Always prioritize risky actions.
    for action in actions:

        if action["action"] in RISKY_ACTIONS:
            return action

    # Otherwise use the first safe action.
    return actions[0]