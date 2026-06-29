from functools import cache

from redis.asyncio import Redis

from core.config import settings


@cache
def get_redis() -> Redis:
    return Redis(
        host=settings.redis.host, port=settings.redis.port, db=settings.redis.db
    )
