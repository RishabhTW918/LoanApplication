from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    app_name: str = "Loan Prequalification API"
    debug: bool = False

    database_url: str = "postgresql://postgres:postgres@localhost:5432/loan_prequal"

    kafka_bootstrap_servers: List[str] = ["localhost:9092"]
    kafka_topic_applications_submitted: str = "loan_applications_submitted"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Validation
    pan_regex: str = r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()