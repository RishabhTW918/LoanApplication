from kafka import KafkaConsumer
import json
import logging
from typing import Callable
from .config import settings

logger = logging.getLogger(__name__)

class BaseKafkaConsumer:
    """
    Base Kafka consumer with common configuration and error handling.
    """

    def __init__(self, topic: str, group_id: str, message_handler: Callable):
        self.topic = topic
        self.group_id = group_id
        self.message_handler = message_handler
        self.consumer = None
        self._connect()

    def _connect(self):
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=settings.kafka_bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',  # Start from beginning if no offset
                enable_auto_commit=False,  # Manual commit for reliability
                max_poll_records=10,  # Process in small batches
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
            )
            logger.info(f"Consumer connected to topic: {self.topic}")
        except Exception as e:
            logger.error(f"Failed to connect consumer: {e}")
            raise


    def start(self):
        logger.info(f"Starting consumer for topic: {self.topic}")

        try:
            for message in self.consumer:
                try:
                    logger.info(
                        f"Received message from partition {message.partition} "
                        f"offset {message.offset}"
                    )

                    # Process the message
                    self.message_handler(message.value)

                    # Commit offset after successful processing
                    self.consumer.commit()
                    logger.info(f"Successfully processed and committed offset {message.offset}")

                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        finally:
            self.close()

    def close(self):
        if self.consumer:
            self.consumer.close()
            logger.info("Consumer closed")