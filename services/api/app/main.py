from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict
import logging
from uuid import UUID
from database import get_db,engine,Base
from models import LoanApplication
from schemas import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationStatusResponse,
    ErrorResponse
)
from kafka_producer import kafka_producer
from config import settings


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="Loan Prequalification Service API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up API service...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources."""
    logger.info("Shutting down API service...")
    kafka_producer.close()

@app.get("/", tags=["Health"])
async def root():
    return {
        "service": settings.app_name,
        "status": "healthy",
        "version": "1.0.0"
    }

@app.post(
    "/application",
    response_model=ApplicationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"description": "Application accepted and queued for processing"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    tags=["Applications"]
)
async def submit_application(
    application: ApplicationCreate,
    db: Session = Depends(get_db)
):
    """
    Submit a new loan prequalification application.

    This endpoint:
    1. Validates the application data
    2. Saves it to the database with PENDING status
    3. Publishes an event to Kafka for async processing
    4. Returns immediately with 202 Accepted

    Args:
        application: The application data
        db: Database session (injected)

    Returns:
        ApplicationResponse with application_id and status

    Raises:
        HTTPException: If validation fails or system error occurs
    """
    try:
        # Create database record
        db_application = LoanApplication(
            pan_number=application.pan_number,
            applicant_name=application.applicant_name,
            monthly_income_inr=application.monthly_income_inr,
            loan_amount_inr=application.loan_amount_inr,
            loan_type=application.loan_type.value,
            status="PENDING"
        )

        db.add(db_application)
        db.commit()
        db.refresh(db_application)

        logger.info(f"Created application {db_application.id} in database")

        # Prepare Kafka message
        application_data = {
            "application_id": db_application.id,
            "pan_number": db_application.pan_number,
            "applicant_name": db_application.applicant_name,
            "monthly_income_inr": db_application.monthly_income_inr,
            "loan_amount_inr": db_application.loan_amount_inr,
            "loan_type": db_application.loan_type
        }

        # Publish to Kafka
        published = kafka_producer.publish_application_submitted(application_data)

        if not published:
            logger.error(f"Failed to publish application {db_application.id} to Kafka")
            # Note: We don't rollback the DB transaction
            # The application is still in PENDING state and can be retried

        return ApplicationResponse(
            application_id=db_application.id,
            status = db_application.status
        )

    except Exception as e:
        logger.error(f"Error submitting application: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process application. Please try again later."
        )
#
@app.get(
    "/applications/{application_id}/status",
    response_model=ApplicationStatusResponse,
    responses={
        200: {"description": "Application status retrieved successfully"},
        404: {"model": ErrorResponse, "description": "Application not found"}
    },
    tags=["Applications"]
)
async def get_application_status(
    application_id: UUID,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get the current status of a loan application.
    Args:
        application_id: UUID of the application
        db: Database session (injected)
    Returns:
        ApplicationStatusResponse with current status and details
    """
    try:
        application = db.query(LoanApplication).filter(
            LoanApplication.id == application_id
        ).first()

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {application_id} not found"
            )

        return ApplicationStatusResponse(
            application_id=application.id,
            status=application.status,
            cibil_score=application.cibil_score,
            created_at=application.created_at,
            updated_at=application.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving application status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve application status"
        )

# # Additional utility endpoints for testing/debugging
#
# @app.get("/applications", tags=["Applications"])
# async def list_applications(
#     limit: int = 10,
#     offset: int = 0,
#     db: Session = Depends(get_db)
# ):
#     """
#     List recent applications (for testing/debugging).
#
#     Args:
#         limit: Number of applications to return (default 10)
#         offset: Number of applications to skip (default 0)
#         db: Database session
#
#     Returns:
#         List of applications
#     """
#     applications = db.query(LoanApplication).order_by(
#         LoanApplication.created_at.desc()
#     ).limit(limit).offset(offset).all()
#
#     return {
#         "total": db.query(LoanApplication).count(),
#         "applications": applications
#     }