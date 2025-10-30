import logging
import json
from kafka import KafkaProducer
from cibil_simulator import CIBILSimulator
from config import settings
from kafka_consumer import BaseKafkaConsumer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CreditService:

    def __init__(self):
        # Create Kafka producer for publishing credit reports
        self.producer = KafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',
            retries=3
        )
        logger.info("Credit service initialized")

    def process_application(self, message: dict):
        """
        Process a loan application and generate CIBIL score.

        Args:
            message: Application data from Kafka
        """
        try:
            application_id = message["application_id"]
            pan_number = message["pan_number"]
            monthly_income = float(message["monthly_income_inr"])
            loan_type = message["loan_type"]

            logger.info(f"Processing application {application_id}")

            # Simulate CIBIL score generation
            cibil_score = CIBILSimulator.generate_score(
                pan_number=pan_number,
                monthly_income_inr=monthly_income,
                loan_type=loan_type
            )

            score_category = CIBILSimulator.get_score_category(cibil_score)
            logger.info(
                f"Generated score {cibil_score} ({score_category}) "
                f"for application {application_id}"
            )

            # Prepare credit report message
            credit_report = {
                "application_id": application_id,
                "pan_number": pan_number,
                "applicant_name": message.get("applicant_name"),
                "monthly_income_inr": monthly_income,
                "loan_amount_inr": float(message["loan_amount_inr"]),
                "loan_type": loan_type,
                "cibil_score": cibil_score,
                "score_category": score_category
            }

            # Publish to credit_reports_generated topic
            future = self.producer.send(
                settings.kafka_topic_credit_reports_generated,
                value=credit_report,
                key=application_id.encode('utf-8')
            )

            # Wait for confirmation
            record_metadata = future.get(timeout=10)
            logger.info(
                f"Published credit report for {application_id} to "
                f"partition {record_metadata.partition} "
                f"offset {record_metadata.offset}"
            )

        except Exception as e:
            logger.error(f"Error processing application: {e}", exc_info=True)
            raise

    def start(self):
        """Start consuming applications."""
        consumer = BaseKafkaConsumer(
            topic=settings.kafka_topic_applications_submitted,
            group_id="credit-service-group",
            message_handler=self.process_application
        )
        consumer.start()

    def close(self):
        """Clean up resources."""
        if self.producer:
            self.producer.close()
            logger.info("Producer closed")



def main():
    """Entry point for credit service."""
    logger.info("Starting Credit Service...")
    service = CreditService()

    try:
        service.start()
    except KeyboardInterrupt:
        logger.info("Credit service interrupted")
    finally:
        service.close()

if __name__ == "__main__":
    main()