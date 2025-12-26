from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = "development"
    
    # PostgreSQL
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "roadsense"
    POSTGRES_USER: str = "roadsense_user"
    POSTGRES_PASSWORD: str = "roadsense_password_2025"
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # MinIO
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "roadsense_access"
    MINIO_SECRET_KEY: str = "roadsense_secret_key_2025"
    MINIO_SECURE: bool = False
    
    # Model Configuration
    TF_MODEL_PATH: str = "models/frozen_inference_graph_mobilenet.pb"
    CONFIDENCE_THRESHOLD: float = 0.5
    
    # Service Configuration
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    TEMP_DIR: str = "temp"
    
    # Model Classes (TensorFlow model - 8 damage types)
    MODEL_CLASSES: list = [
        "D00 - Longitudinal Crack",
        "D01 - Transverse Crack", 
        "D10 - Alligator Crack",
        "D11 - Pothole",
        "D20 - Bleeding",
        "D40 - Rutting",
        "D43 - Cross Walk Blur",
        "D44 - White Line Blur"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
