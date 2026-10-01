"""
NUDGE Observation Layer

OBSERVE verifies what actually happened after execution.
It does not trust the planner or executor blindly and it never
performs actions itself.

The returned evidence is consumed by the replanner.
"""

from tools.email import get_sent_emails
from tools.sheets import get_invoice_sheet_updates


def _failed(message, action, evidence=None):
    return {
        "status": "failed",
        "action": action,
        "observation": message,
        "changes": {},
        "evidence": evidence or {},
        "requires_replan": False
    }


def _success(action, message, changes, evidence=None):
    return {
        "status": "success",
        "action": action,
        "observation": message,
        "changes": changes or {},
        "evidence": evidence or {},
        "requires_replan": True
    }


def _matches_execution(record, execution_result):
    """
    Prevent an old runtime record from being mistaken for the latest
    successful action when the execution layer provides an identifier.
    """
    if not execution_result:
        return True

    expected_id = (
        execution_result.get("email_id")
        or execution_result.get("update_id")
        or execution_result.get("execution_id")
    )

    if not expected_id:
        return True

    actual_id = (
        record.get("email_id")
        or record.get("update_id")
        or record.get("execution_id")
    )

    return not actual_id or actual_id == expected_id


def observe_execution(
    action,
    execution_result=None,
    intent=None,
    context=None
):
    """
    Verify the result of an executed action.

    Backward compatible with:
        observe_execution(action, execution_result)

    Additional optional metadata:
        intent
        context
    """

    execution_result = execution_result or {}
    context = context or {}

    if execution_result.get("status") == "failed":
        return _failed(
            execution_result.get(
                "message",
                "The previous action failed."
            ),
            action,
            {
                "execution_result": execution_result,
                "intent": intent,
                "context": context
            }
        )
