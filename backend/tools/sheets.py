import json
import os
from datetime import datetime


RUNTIME_DIR = os.path.join(
    os.environ.get("TMPDIR", "/tmp"),
    "nudge_runtime"
)

os.makedirs(RUNTIME_DIR, exist_ok=True)

SHEET_UPDATES_FILE = os.path.join(
    RUNTIME_DIR,
    "sheet_updates.json"
)


def _load_updates():
    if not os.path.exists(SHEET_UPDATES_FILE):
        return []

    try:
        with open(
            SHEET_UPDATES_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return []


def _save_updates(updates):
    os.makedirs(RUNTIME_DIR, exist_ok=True)

    with open(
        SHEET_UPDATES_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            updates,
            file,
            indent=2,
            ensure_ascii=False
        )


def update_invoice_sheet(payload):
    invoice_id = payload.get("invoice_id")

    if not invoice_id:
        return {
            "status": "failed",
            "tool": "invoice_sheet",
            "message": "invoice_id is required",
        }

    updates = _load_updates()

    update = {
        "invoice_id": invoice_id,
        "client": payload.get("client"),
        "email_id": payload.get("email_id"),
        "status": "follow_up_sent",
        "note": payload.get(
            "note",
            "Follow-up email sent and invoice record updated."
        ),
        "updated_at": datetime.utcnow().isoformat(),
    }

    updates.append(update)
    _save_updates(updates)

    return {
        "status": "executed",
        "tool": "invoice_sheet",
        "message": (
            f"Invoice {invoice_id} updated successfully"
        ),
        "update": update,
    }


def get_invoice_sheet_updates():
    return _load_updates()