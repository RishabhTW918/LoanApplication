import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from services.common.kafka_consumer import BaseKafkaConsumer
from services.common.config import settings
from .decision_engine import DecisionEngine


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DecisionService:
    """
    Decision Service consumes credit reports and makes loan decisions.
    """

    def __init__(self):
        # Create database connection
        self.engine = create_engine(
            settings.database_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True
        )
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info("Decision service initialized")

    def process_credit_report(self, message: dict):
        """
        Process a credit report and make a decision.

        Args:
            message: Credit report data from Kafka
        """
        db: Session = self.SessionLocal()

        try:
            application_id = message["application_id"]
            cibil_score = message["cibil_score"]
            monthly_income = message["monthly_income_inr"]
            loan_amount = message["loan_amount_inr"]

            logger.info(f"Processing credit report for application {application_id}")

            # Make decision using business rules
            status, reason = DecisionEngine.make_decision(
                cibil_score=cibil_score,
                monthly_income_inr=monthly_income,
                loan_amount_inr=loan_amount
            )

            logger.info(
                f"Decision for {application_id}: {status} - {reason}"
            )

            # Update application in database
            from services.common.models import LoanApplication  # Import here to avoid circular imports

            application = db.query(LoanApplication).filter(
                LoanApplication.id == application_id
            ).first()

            if not application:
                logger.error(f"Application {application_id} not found in database")
                return

            # Update status and score
            application.status = status
            application.cibil_score = cibil_score


            #  update to database
            db.commit()

            logger.info(
                f"Updated application {application_id} to status {status} "
                f"with CIBIL score {cibil_score}"
            )

        except Exception as e:
            logger.error(f"Error processing credit report: {e}", exc_info=True)
            db.rollback()
            raise
        finally:
            db.close()

    def start(self):
        """Start consuming credit reports."""
        consumer = BaseKafkaConsumer(
            topic=settings.kafka_topic_credit_reports_generated,
            group_id="decision-service-group",
            message_handler=self.process_credit_report
        )
        consumer.start()
        pass

def main():
    """Entry point for decision service."""
    logger.info("Starting Decision Service...")
    service = DecisionService()

    try:
        service.start()
    except KeyboardInterrupt:
        logger.info("Decision service interrupted")

if __name__ == "__main__":
    main()