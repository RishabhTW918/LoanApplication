from kafka import KafkaProducer
import json
import logging
from typing import Dict, Any
from LoanApplication.services.common.config import settings

logger = logging.getLogger(__name__)


class ApplicationKafkaProducer:

    def __init__(self):
        self.producer = None
        self._connect()

    def _connect(self):
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",
                retries=3,
                max_in_flight_requests_per_connection=1,
                compression_type="gzip",
            )
            logger.info("Connected to Kafka")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise

    def publish_application_submitted(self, application_data: Dict[str, Any]) -> bool:
        try:
            message = {
                "application_id": str(application_data["application_id"]),
                "pan_number": application_data["pan_number"],
                "applicant_name": application_data.get("applicant_name"),
                "monthly_income_inr": float(application_data["monthly_income_inr"]),
                "loan_amount_inr": float(application_data["loan_amount_inr"]),
                "loan_type": application_data["loan_type"],
            }

            future = self.producer.send(
                settings.kafka_topic_applications_submitted,
                value=message,
                key=message["application_id"].encode("utf-8"),  # Partition by app ID
            )

            record_metadata = future.get(timeout=10)
            logger.info(
                f"Published application {message['application_id']} to "
                f"topic {record_metadata.topic} partition {record_metadata.partition} "
                f"offset {record_metadata.offset}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to publish application: {e}")
            return False

    def close(self):
        """Close Kafka producer connection."""
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer closed")


# Singleton instance
kafka_producer = ApplicationKafkaProducer()
