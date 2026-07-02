from faststream.kafka import KafkaBroker

from core.config import settings

broker = KafkaBroker(settings.kafka.bootstrap_servers)

publisher = broker.publisher(settings.kafka.notifications_topic)
