from datetime import UTC, datetime


def get_current_naive_dt() -> datetime:
    dt = datetime.now(tz=UTC)
    return dt.replace(microsecond=0, tzinfo=None)
