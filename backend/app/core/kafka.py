import json
import logging
from aiokafka import AIOKafkaProducer
from app.core.config import settings

logger = logging.getLogger(__name__)

producer: AIOKafkaProducer = None


async def get_kafka_producer() -> AIOKafkaProducer:
    global producer
    if producer is None:
        try:
            producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
            )
            await producer.start()
        except Exception as e:
            logger.warning(f"Kafka connection failed (running in fallback mode): {e}")
            producer = None
    return producer


async def produce_event(topic: str, value: dict, key: str = None):
    p = await get_kafka_producer()
    if p:
        try:
            await p.send_and_wait(topic, value=value, key=key)
        except Exception as e:
            logger.error(f"Failed to produce Kafka message to topic {topic}: {e}")
    else:
        logger.info(f"[Kafka Fallback Log] Topic: {topic} | Key: {key} | Value: {value}")


async def stop_kafka_producer():
    global producer
    if producer:
        await producer.stop()
        producer = None
