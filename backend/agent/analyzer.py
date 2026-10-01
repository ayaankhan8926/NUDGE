from tools.workspace import (
    read_invoices,
    search_emails,
    read_calendar
)


def _safe_text(value):
    return str(value or "").strip().lower()


def _is_replied(email):
    return bool(email.get("replied"))


def _client_key(record_or_client):
    """
    Normalize either a client string or a record containing a client.
    """
    if isinstance(record_or_client, dict):
        return _safe_text(record_or_client.get("client"))

    return _safe_text(record_or_client)


def _build_invoice_candidates(invoice_data, email_data, handled_invoice_ids=None):
    """
    Identify pending invoices whose clients have not replied.
    """

    handled_invoice_ids = set(handled_invoice_ids or [])

    replied_clients = {
        _client_key(email)
        for email in email_data
        if _is_replied(email) and _client_key(email)
    }

    candidates = []

    for invoice in invoice_data:
        client = invoice.get("client")
        client_key = _client_key(client)

        if _safe_text(invoice.get("status")) != "pending":
            continue

        if str(invoice.get("invoice_id") or "") in handled_invoice_ids:
            continue

        if client_key in replied_clients:
            continue

        candidates.append({
            "client": client,
            "invoice_id": invoice.get("invoice_id"),
            "amount": invoice.get("amount"),
            "due_date": invoice.get("due_date"),
            "reason": "Pending invoice with no email reply"
        })

    return candidates


def _build_email_candidates(email_data):
    """
    Identify email records that can be considered follow-up candidates.
    """

    candidates = []

    for email in email_data:
        if _is_replied(email):
            continue

        candidates.append({
            "client": email.get("client"),
            "email_id": email.get("email_id"),
            "subject": email.get("subject"),
            "reason": "Email thread has no recorded reply"
        })

    return candidates


def _build_meeting_candidates(calendar_data, email_data):
    """
    Return calendar events as review candidates.

    The current synthetic workspace does not guarantee a one-to-one
    meeting/email identifier, so this does not invent relationships.
    """

    unreplied_clients = [
        email.get("client")
        for email in email_data
        if not _is_replied(email)
    ]

    candidates = []

    for event in calendar_data:
        candidates.append({
            "event": event,
            "unreplied_clients": unreplied_clients,
            "reason": "Calendar event available for follow-up review"
        })

    return candidates


def analyze_workspace(intent=None, workspace_state=None):
    """
    Inspect the synthetic workspace and produce intent-aware findings.

    Backward compatible with:
        analyze_workspace()
    """

    invoices = read_invoices()
    emails = search_emails()
    calendar = read_calendar()

    invoice_data = [dict(item) for item in (invoices.get("data") or [])]
    email_data = [dict(item) for item in (emails.get("data") or [])]
    calendar_data = [dict(item) for item in (calendar.get("data") or [])]

    # The browser carries the synthetic demo workspace between runs.
    # Apply those user-visible changes before analyzing so a new run sees
    # the same state the user just approved. This is still demo data only.
    state = workspace_state if isinstance(workspace_state, dict) else {}
    state_invoices = state.get("invoices") or []
    state_sent_emails = state.get("sentEmails") or []
    state_sheet_updates = state.get("sheetUpdates") or []

    invoice_overrides = {
        item.get("invoice"): item
        for item in state_invoices
        if isinstance(item, dict) and item.get("invoice")
    }

    for invoice in invoice_data:
        override = invoice_overrides.get(invoice.get("invoice_id"))
        if not override:
            continue
        state_value = _safe_text(override.get("state"))
        if state_value in {"follow-up sent", "replied"}:
            invoice["status"] = "follow_up_sent"

    # A sent demo follow-up means the corresponding thread has already been
    # handled, so do not surface it again as an unanswered email candidate.
    handled_email_ids = {
        str(item.get("email_id") or "").strip()
        for item in state_sent_emails
        if isinstance(item, dict) and item.get("email_id")
    }

    handled_invoice_ids = {
        str(item.get("invoice_id") or "").strip()
        for item in state_sent_emails + state_sheet_updates
        if isinstance(item, dict) and item.get("invoice_id")
    }

    email_data = [
        email for email in email_data
        if email.get("email_id") not in handled_email_ids
    ]

    invoice_candidates = _build_invoice_candidates(
        invoice_data,
        email_data,
        handled_invoice_ids=handled_invoice_ids
    )

    email_candidates = _build_email_candidates(
        email_data
    )

    meeting_candidates = _build_meeting_candidates(
        calendar_data,
        email_data
    )

    normalized_intent = _safe_text(intent)

    if normalized_intent == "invoice_follow_up" or not normalized_intent:
        follow_up_candidates = invoice_candidates
    elif normalized_intent == "email_follow_up":
        follow_up_candidates = email_candidates
    elif normalized_intent == "meeting_follow_up":
        follow_up_candidates = meeting_candidates
    else:
        follow_up_candidates = invoice_candidates

    return {
        "status": "success",
        "intent": normalized_intent or "invoice_follow_up",
        "sources_checked": [
            "sheets",
            "gmail",
            "calendar"
        ],
        "follow_up_candidates": follow_up_candidates,
        "invoice_follow_up_candidates": invoice_candidates,
        "email_follow_up_candidates": email_candidates,
        "meeting_follow_up_candidates": meeting_candidates,
        "calendar_events": calendar_data,
        "summary": {
            "pending_invoice_candidates": len(invoice_candidates),
            "email_follow_up_candidates": len(email_candidates),
            "calendar_events": len(calendar_data)
        }
    }
