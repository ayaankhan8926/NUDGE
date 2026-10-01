INVOICE_DATA = [
    {
        "invoice_id": "INV-1042",
        "client": "ABC Technologies",
        "amount": 45000,
        "status": "pending",
        "due_date": "2026-09-28"
    },
    {
        "invoice_id": "INV-1043",
        "client": "XYZ Solutions",
        "amount": 32000,
        "status": "pending",
        "due_date": "2026-09-25"
    },
    {
        "invoice_id": "INV-1044",
        "client": "Nova Systems",
        "amount": 58000,
        "status": "pending",
        "due_date": "2026-09-20"
    }
]


EMAIL_DATA = [
    {
        "email_id": "EMAIL-001",
        "client": "ABC Technologies",
        "subject": "Re: Invoice INV-1042",
        "message": "We have received the invoice. Payment is being processed.",
        "replied": True
    },
    {
        "email_id": "EMAIL-002",
        "client": "Nova Systems",
        "subject": "Re: Invoice INV-1044",
        "message": "Thanks for sending this. We will process it shortly.",
        "replied": True
    },
    {
        "email_id": "EMAIL-003",
        "client": "XYZ Solutions",
        "subject": "Invoice INV-1043",
        "message": "",
        "replied": False
    }
]


CALENDAR_DATA = [
    {
        "event_id": "EVENT-001",
        "title": "ABC Technologies Review",
        "client": "ABC Technologies",
        "date": "2026-10-01",
        "time": "11:00"
    },
    {
        "event_id": "EVENT-002",
        "title": "Nova Systems Follow-up",
        "client": "Nova Systems",
        "date": "2026-10-02",
        "time": "15:30"
    }
]


def get_invoices():
    return INVOICE_DATA


def get_emails():
    return EMAIL_DATA


def get_calendar_events():
    return CALENDAR_DATA