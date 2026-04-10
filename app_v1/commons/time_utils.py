from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Timezone-aware current UTC time."""
    return datetime.now(timezone.utc)


def get_as_utc(dt: datetime | None) -> datetime:
    """
    Normalize a datetime to timezone-aware UTC.

    - If dt is None: returns None
    - If dt is naive: assumes it's already UTC and attaches tzinfo=UTC
    - If dt has tzinfo: converts to UTC
    """
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

