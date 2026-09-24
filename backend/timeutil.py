"""The SERVER decides what 'today' is (in the team's timezone).
The phone's clock is never trusted, so nobody can cheat the date lock."""
from datetime import date, datetime
from zoneinfo import ZoneInfo

import config

TZ = ZoneInfo(config.TIMEZONE)


def now() -> datetime:
    return datetime.now(TZ)


def today() -> date:
    return now().date()


def hhmm() -> str:
    return now().strftime("%H:%M")
