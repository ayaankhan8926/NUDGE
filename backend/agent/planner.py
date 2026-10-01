from agent.gemini import create_gemini_plan


# NUDGE keeps intent detection deterministic so the model cannot
# silently change the workflow category or bypass the safety policy.
INTENT_RULES = {
    "invoice_follow_up": (
        ("invoice", "invoices", "bill", "billing"),
        ("follow", "reply", "replied", "overdue", "pending"),
    ),
    "email_follow_up": (
        ("email", "emails", "mail", "message"),
        ("follow", "reply", "replied", "respond", "remind"),
    ),
    "meeting_follow_up": (
        ("meeting", "meetings", "calendar", "appointment", "event"),
        ("follow", "after", "remind", "prepare", "schedule"),
    ),
    "draft_email": (
        ("draft", "compose", "write", "prepare"),
        ("email", "mail", "message"),
    ),
}


def detect_goal_intent(goal):
    """
    Classify a goal into a small, controlled NUDGE workflow category.

    This is deliberately deterministic. Gemini may still create the
    execution plan, but it does not get to invent the workflow category.
    """

    text = " ".join(str(goal or "").lower().split())

    if not text:
        return {
            "intent": "ambiguous",
            "confidence": 0.0,
            "reason": "No goal was provided."
        }

    # Invoice-specific goals take priority because they can also contain
    # generic email/follow-up language.
    for intent, (primary_terms, secondary_terms) in INTENT_RULES.items():
        has_primary = any(term in text for term in primary_terms)
        has_secondary = any(term in text for term in secondary_terms)

        if has_primary and has_secondary:
            return {
                "intent": intent,
                "confidence": 0.95,
                "reason": f"Goal contains signals for {intent.replace('_', ' ')}."
            }

    # Explicit follow-up without a clear domain is intentionally ambiguous.
    if any(term in text for term in ("follow up", "follow-up", "followup")):
        return {
            "intent": "ambiguous",
            "confidence": 0.55,
            "reason": (
                "The goal asks for a follow-up but does not clearly identify "
                "the workspace context."
            )
        }

    # A broad workspace request can still be handled by the planner.
    if any(
        term in text
        for term in (
            "workspace",
            "gmail",
            "calendar",
            "sheets",
            "spreadsheet",
            "check everything",
            "review everything",
        )
    ):
        return {
            "intent": "general_workspace",
            "confidence": 0.80,
            "reason": "The goal explicitly references workspace data."
        }

    return {
        "intent": "ambiguous",
        "confidence": 0.40,
        "reason": (
            "The goal does not contain enough domain information to select "
            "a specialized workflow."
        )
    }


def _fallback_steps(intent):
    """
    Safe deterministic plans used when Gemini is unavailable.

    These are planning descriptions only. Actual execution still passes
    through the interpreter, execution layer, and Python risk gate.
    """

    common = [
        {
            "step": 1,
            "action": "understand_goal",
            "description": "Understand the user's objective."
        }
    ]

    if intent == "invoice_follow_up":
        return common + [
            {
                "step": 2,
                "action": "read_sheet",
                "tool": "sheets",
                "description": "Check pending invoices in the invoice sheet."
            },
            {
                "step": 3,
                "action": "read_email",
                "tool": "gmail",
                "description": "Check which invoice clients have replied."
            },
            {
                "step": 4,
                "action": "analyze_data",
                "tool": "workspace",
                "description": (
                    "Identify pending invoice clients who have not replied."
                )
            },
            {
                "step": 5,
                "action": "send_email",
                "tool": "gmail",
                "description": (
                    "Prepare a follow-up email for a client with no reply; "
                    "human approval is required before sending."
                )
            },
        ]

    if intent == "email_follow_up":
        return common + [
            {
                "step": 2,
                "action": "read_email",
                "tool": "gmail",
                "description": "Find relevant email threads and reply status."
            },
            {
                "step": 3,
                "action": "analyze_data",
                "tool": "workspace",
                "description": "Identify threads that need a follow-up."
            },
            {
                "step": 4,
                "action": "send_email",
                "tool": "gmail",
                "description": (
                    "Prepare a follow-up message; human approval is required "
                    "before sending."
                )
            },
        ]

    if intent == "meeting_follow_up":
        return common + [
            {
                "step": 2,
                "action": "read_calendar",
                "tool": "calendar",
                "description": "Review relevant calendar meetings and events."
            },
            {
                "step": 3,
                "action": "read_email",
                "tool": "gmail",
                "description": "Check related email threads and replies."
            },
            {
                "step": 4,
                "action": "analyze_data",
                "tool": "workspace",
                "description": (
                    "Identify meeting follow-ups that need attention."
                )
            },
            {
                "step": 5,
                "action": "create_draft",
                "tool": "gmail",
                "description": (
                    "Prepare a follow-up draft without sending it."
                )
            },
        ]

    if intent == "draft_email":
        return common + [
            {
                "step": 2,
                "action": "read_email",
                "tool": "gmail",
                "description": "Inspect relevant email context before drafting."
            },
            {
                "step": 3,
                "action": "create_draft",
                "tool": "gmail",
                "description": "Create an email draft for human review."
            },
        ]

    return common + [
        {
            "step": 2,
            "action": "read_email",
            "tool": "gmail",
            "description": "Inspect relevant Gmail information."
        },
        {
            "step": 3,
            "action": "read_calendar",
            "tool": "calendar",
            "description": "Inspect relevant Calendar information."
        },
        {
            "step": 4,
            "action": "read_sheet",
            "tool": "sheets",
            "description": "Inspect relevant Sheets information."
        },
        {
            "step": 5,
            "action": "analyze_data",
            "tool": "workspace",
            "description": "Analyze the collected workspace information."
        },
    ]


def _risk_actions_for_steps(steps):
    risky = {
        "send_email",
        "delete_email",
        "create_calendar_event",
        "modify_calendar_event",
        "update_sheet",
    }

    return [
        step.get("action")
        for step in steps
        if step.get("action") in risky
    ]


def create_plan(goal):
    """
    Create an execution plan using Gemini with a deterministic intent layer.

    Gemini can propose the detailed plan, but NUDGE always attaches a
    deterministic intent classification and preserves the existing
    human-approval requirement for risky actions.

    If Gemini is unavailable or returns an unusable plan, NUDGE falls back
    to a deterministic plan so development/demo execution can continue.
    """

    goal = str(goal or "").strip()

    if not goal:
        return {
            "status": "error",
            "message": "Goal is required"
        }

    intent_info = detect_goal_intent(goal)
    intent = intent_info["intent"]

    try:
        gemini_plan = create_gemini_plan(goal)

        if not isinstance(gemini_plan, dict):
            raise ValueError("Gemini returned an invalid plan.")

        steps = gemini_plan.get("steps") or []

        if not isinstance(steps, list) or not steps:
            raise ValueError("Gemini returned no executable planning steps.")

        risk_actions = _risk_actions_for_steps(steps)

        # Preserve any Gemini risk actions that are valid strings, while
        # making sure risky actions visible in the actual steps are included.
        gemini_risks = gemini_plan.get("risk_actions") or []
        if isinstance(gemini_risks, list):
            for action in gemini_risks:
                if action not in risk_actions:
                    risk_actions.append(action)

        return {
            "status": "planned",
            "source": "gemini",
            "goal": goal,
            "intent": intent,
            "intent_confidence": intent_info["confidence"],
            "intent_reason": intent_info["reason"],
            "goal_understanding": gemini_plan.get(
                "goal_understanding",
                ""
            ),
            "steps": steps,
            "risk_actions": risk_actions,
            "requires_human_approval": (
                len(risk_actions) > 0
                or bool(gemini_plan.get("requires_human_approval", False))
            )
        }

    except Exception as error:
        print(
            f"[NUDGE] Gemini planner unavailable: {error}"
        )

        steps = _fallback_steps(intent)
        risk_actions = _risk_actions_for_steps(steps)

        return {
            "status": "planned",
            "source": "fallback",
            "goal": goal,
            "intent": intent,
            "intent_confidence": intent_info["confidence"],
            "intent_reason": intent_info["reason"],
            "goal_understanding": (
                f"NUDGE classified this as a {intent.replace('_', ' ')} "
                "workflow and is using the local deterministic planner."
            ),
            "steps": steps,
            "risk_actions": risk_actions,
            "requires_human_approval": len(risk_actions) > 0
        }
