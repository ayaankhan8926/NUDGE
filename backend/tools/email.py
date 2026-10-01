import json
import os
from datetime import datetime


RUNTIME_DIR = os.path.join(
    os.environ.get("TMPDIR", "/tmp"),
    "nudge_runtime"
)

os.makedirs(RUNTIME_DIR, exist_ok=True)

SENT_EMAILS_FILE = os.path.join(
    RUNTIME_DIR,
    "sent_emails.json"
)


def _load_sent_emails():
    if not os.path.exists(SENT_EMAILS_FILE):
        return []

    try:
        with open(
            SENT_EMAILS_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return []


def _save_sent_emails(emails):
    os.makedirs(RUNTIME_DIR, exist_ok=True)

    with open(
        SENT_EMAILS_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            emails,
            file,
            indent=2,
            ensure_ascii=False
        )


def send_email(payload):
    emails = _load_sent_emails()

    email_number = len(emails) + 1

    email = {
        "email_id": f"SENT-{email_number:04d}",
        "client": payload.get("client"),
        "invoice_id": payload.get("invoice_id"),
        "amount": payload.get("amount"),
        "message": payload.get("message", ""),
        "sent_at": datetime.utcnow().isoformat(),
        "status": "sent",
    }

    emails.append(email)
    _save_sent_emails(emails)

    return {
        "status": "sent",
        "tool": "gmail",
        "message": "Email sent successfully.",
        "email": email,
    }


def get_sent_emails():
    return _load_sent_emails()