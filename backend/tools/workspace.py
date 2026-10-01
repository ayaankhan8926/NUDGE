from tools.fixtures import (
    get_invoices,
    get_emails,
    get_calendar_events
)


def read_invoices():
    """
    Read invoice records from the Sheets fixture.
    """
    return {
        "tool": "sheets",
        "status": "success",
        "data": get_invoices()
    }


def search_emails():
    """
    Search email records from the Gmail fixture.
    """
    return {
        "tool": "gmail",
        "status": "success",
        "data": get_emails()
    }


def read_calendar():
    """
    Read calendar events from the Calendar fixture.
    """
    return {
        "tool": "calendar",
        "status": "success",
        "data": get_calendar_events()
    }