from functools import cache

from faststream.kafka import KafkaBroker

from core.config import settings


@cache
def get_kafka_broker() -> KafkaBroker:
    return KafkaBroker(settings.kafka.bootstrap_servers)
