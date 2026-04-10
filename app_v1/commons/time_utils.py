from datetime import datetime, timezone


def current_time_in_utc() -> datetime:
    return datetime.now(timezone.utc)