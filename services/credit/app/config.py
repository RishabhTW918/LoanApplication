from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    kafka_bootstrap_servers: List[str] = ["localhost:9092"]
    kafka_topic_credit_reports_generated :  str = "credit_reports_generated"
    kafka_topic_applications_submitted : str = "loan_applications_submitted"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()