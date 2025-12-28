# Import BaseSettings from pydantic for configuration management
from pydantic_settings import BaseSettings
# Import Optional type for nullable fields
from typing import Optional
# Import os module for environment variables
import os

# Define Settings class extending BaseSettings for type-safe configuration
class Settings(BaseSettings):
    # Environment section
    # Current environment: development, staging, or production
    ENVIRONMENT: str = "development"
    
    # PostgreSQL database configuration section
    # Database server hostname
    POSTGRES_HOST: str = "postgres"
    # Database server port number
    POSTGRES_PORT: int = 5432
    # Database name
    POSTGRES_DB: str = "roadsense"
    # Database username
    POSTGRES_USER: str = "roadsense_user"
    # Database password
    POSTGRES_PASSWORD: str = "roadsense_password_2025"
    
    # Property decorator for dynamic database URL generation
    @property
    # Method to construct PostgreSQL connection URL
    def DATABASE_URL(self) -> str:
        # Build and return connection string with all parameters
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # MinIO object storage configuration section
    # MinIO server endpoint (host:port)
    MINIO_ENDPOINT: str = "minio:9000"
    # MinIO access key for authentication
    MINIO_ACCESS_KEY: str = "roadsense_access"
    # MinIO secret key for authentication
    MINIO_SECRET_KEY: str = "roadsense_secret_key_2025"
    # Whether to use HTTPS for MinIO connection
    MINIO_SECURE: bool = False
    
    # Model Configuration section
    # Path to TensorFlow frozen model file
    TF_MODEL_PATH: str = "models/frozen_inference_graph_mobilenet.pb"
    # Minimum confidence threshold for valid detections (0.0-1.0)
    CONFIDENCE_THRESHOLD: float = 0.5
    
    # Service Configuration section
    # Maximum file upload size in bytes (10MB)
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    # Temporary directory for file processing
    TEMP_DIR: str = "temp"
    
    # Model Classes (TensorFlow model - 8 damage types)
    # List of defect types the model can detect
    MODEL_CLASSES: list = [
        # Type 1: Longitudinal cracks (parallel to road direction)
        "D00 - Longitudinal Crack",
        # Type 2: Transverse cracks (perpendicular to road direction)
        "D01 - Transverse Crack", 
        # Type 3: Alligator/crocodile cracking pattern
        "D10 - Alligator Crack",
        # Type 4: Potholes (bowl-shaped depressions)
        "D11 - Pothole",
        # Type 5: Bleeding (excess asphalt on surface)
        "D20 - Bleeding",
        # Type 6: Rutting (wheel path depressions)
        "D40 - Rutting",
        # Type 7: Faded crosswalk markings
        "D43 - Cross Walk Blur",
        # Type 8: Faded white line markings
        "D44 - White Line Blur"
    ]
    
    # Inner Config class for pydantic settings
    class Config:
        # Specify .env file to load environment variables from
        env_file = ".env"
        # Enable case-sensitive environment variable names
        case_sensitive = True

# Instantiate settings object to be imported by other modules
settings = Settings()
