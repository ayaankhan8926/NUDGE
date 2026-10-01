from risk.gate import evaluate_action
from tools.email import send_email
from tools.sheets import update_invoice_sheet


def execute_action(action, payload=None, approved=False):
    payload = payload or {}

    risk_result = evaluate_action(action)

    # Blocked actions can never execute.
    if risk_result["decision"] == "blocked":
        return {
            "status": "blocked",
            "action": action,
            "reason": risk_result["reason"],
            "payload": payload
        }

    # Risky actions require explicit human approval.
    if (
        risk_result["decision"] == "approval_required"
        and not approved
    ):
        return {
            "status": "approval_required",
            "action": action,
            "reason": risk_result["reason"],
            "payload": payload
        }

    # ---------------------------------------------------------
    # SEND EMAIL
    # ---------------------------------------------------------
    if action == "send_email":
        email_result = send_email(payload)

        return {
            "status": "executed",
            "action": action,
            "message": email_result["message"],
            "tool": email_result["tool"],
            "payload": payload,
            "execution": email_result
        }

    # ---------------------------------------------------------
    # UPDATE INVOICE SHEET
    # ---------------------------------------------------------
    if action == "update_sheet":
        sheet_result = update_invoice_sheet(payload)

        if sheet_result["status"] == "failed":
            return {
                "status": "failed",
                "action": action,
                "message": sheet_result["message"],
                "tool": sheet_result["tool"],
                "payload": payload,
                "execution": sheet_result
            }

        return {
            "status": "executed",
            "action": action,
            "message": sheet_result["message"],
            "tool": sheet_result["tool"],
            "payload": payload,
            "execution": sheet_result
        }

    # ---------------------------------------------------------
    # OTHER SAFE ACTIONS
    # ---------------------------------------------------------
    return {
        "status": "executed",
        "action": action,
        "message": f"{action} executed successfully.",
        "payload": payload
    }