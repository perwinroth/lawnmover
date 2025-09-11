from typing import Optional

BOOKING_HINTS = [
    "bokun.io",
    "fareharbor.com",
    "checkfront.com",
    "trekksoft.com",
    "getyourguide.com",
    "timecenter.se",
    "boka.se",
    "bokadirekt.se",
    "enkelbokning.se",
    "billetto",
    "tickster",
    "eventbrite",
    "/boka",
    "/booking",
]


def detect_booking_type(url: Optional[str]) -> Optional[str]:
    if not url or not isinstance(url, str):
        return None
    u = url.lower()
    for hint in BOOKING_HINTS:
        if hint in u:
            return "external"
    # Swedish verbs often use "boka" for booking
    if "boka" in u or "booking" in u:
        return "external"
    return None

