from datetime import UTC, datetime, timedelta, timezone

from fastapi import Request


def get_current_naive_dt() -> datetime:
    dt = datetime.now(tz=UTC)
    return dt.replace(microsecond=0, tzinfo=None)


def get_msc_dt(dt: datetime) -> datetime:
    moscow_tz = timezone(timedelta(hours=3))
    return dt.astimezone(moscow_tz)


def get_user_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host

    return client_ip
