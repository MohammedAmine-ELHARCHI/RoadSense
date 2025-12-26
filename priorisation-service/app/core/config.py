from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Service Configuration
    SERVICE_NAME: str = "priorisation-service"
    SERVICE_VERSION: str = "1.0.0"
    
    # Database Configuration
    DATABASE_URL: str
    
    # Redis Configuration
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 3
    
    # External Services
    SEVERITY_SERVICE_URL: str = "http://severity-service:8002"
    GEOREF_SERVICE_URL: str = "http://georef-service:8004"
    
    # Priority Algorithm Weights (must sum to 1.0)
    WEIGHT_SEVERITY: float = 0.35
    WEIGHT_TRAFFIC: float = 0.25
    WEIGHT_DENSITY: float = 0.20
    WEIGHT_AGE: float = 0.15
    WEIGHT_ACCESSIBILITY: float = 0.05
    
    # Thresholds
    MIN_PRIORITY_SCORE: float = 0.0
    HIGH_PRIORITY_THRESHOLD: float = 70.0
    CRITICAL_PRIORITY_THRESHOLD: float = 85.0
    
    class Config:
        env_file = ".env"


settings = Settings()
