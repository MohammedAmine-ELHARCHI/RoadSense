from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # Service URLs
    DETECTION_SERVICE_URL: str = "http://detection-service:8001"
    SEVERITY_SERVICE_URL: str = "http://severity-service:8002"
    INGESTION_SERVICE_URL: str = "http://ingestion-service:8003"
    
    # GeoRef Configuration
    DEFAULT_DISTANCE_THRESHOLD: float = 50.0  # meters
    MAP_MATCHING_TOLERANCE: float = 30.0  # meters
    ENABLE_OSM_INTEGRATION: bool = True
    
    class Config:
        env_file = ".env"


settings = Settings()
