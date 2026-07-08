from __future__ import annotations

from functools import cache
from typing import Annotated

from fastapi import Depends
from faststream.kafka import KafkaBroker
from faststream.kafka.publisher import BatchPublisher, DefaultPublisher
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import db_helper
from core.publisher import get_kafka_broker
from core.redis import get_redis


@cache
def get_kafka_publisher(
    broker: Annotated[KafkaBroker, Depends(get_kafka_broker)],
) -> BatchPublisher | DefaultPublisher:
    return broker.publisher(settings.kafka.notifications_topic, batch=True)


SessionDep = Annotated[AsyncSession, Depends(db_helper.get_session)]
RedisDep = Annotated[Redis, Depends(get_redis)]

KafkaPublisherDep = Annotated[BatchPublisher, Depends(get_kafka_publisher)]
