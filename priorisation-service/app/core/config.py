# Import BaseSettings from pydantic for configuration management
from pydantic_settings import BaseSettings


# Define Settings class that extends BaseSettings for type-safe configuration
class Settings(BaseSettings):
    # Service Configuration section
    # Define the name of this microservice
    SERVICE_NAME: str = "priorisation-service"
    # Define the version number of this service
    SERVICE_VERSION: str = "1.0.0"
    
    # Database Configuration section
    # PostgreSQL database connection URL (loaded from environment)
    DATABASE_URL: str
    
    # Redis Configuration section for caching
    # Redis server hostname
    REDIS_HOST: str = "redis"
    # Redis server port number
    REDIS_PORT: int = 6379
    # Redis database number to use (0-15)
    REDIS_DB: int = 3
    
    # External Services URLs
    # URL for the severity scoring service
    SEVERITY_SERVICE_URL: str = "http://severity-service:8002"
    # URL for the georeferencing service
    GEOREF_SERVICE_URL: str = "http://georef-service:8004"
    
    # Priority Algorithm Weights (must sum to 1.0)
    # Weight for severity component in priority calculation (35%)
    WEIGHT_SEVERITY: float = 0.35
    # Weight for traffic importance component (25%)
    WEIGHT_TRAFFIC: float = 0.25
    # Weight for defect density component (20%)
    WEIGHT_DENSITY: float = 0.20
    # Weight for age/time component (15%)
    WEIGHT_AGE: float = 0.15
    # Weight for accessibility component (5%)
    WEIGHT_ACCESSIBILITY: float = 0.05
    
    # Thresholds for priority classification
    # Minimum possible priority score value
    MIN_PRIORITY_SCORE: float = 0.0
    # Threshold above which priority is considered HIGH
    HIGH_PRIORITY_THRESHOLD: float = 70.0
    # Threshold above which priority is considered CRITICAL
    CRITICAL_PRIORITY_THRESHOLD: float = 85.0
    
    # Inner Config class for pydantic settings
    class Config:
        # Specify the .env file to load environment variables from
        env_file = ".env"


# Instantiate the settings object to be imported by other modules
settings = Settings()
