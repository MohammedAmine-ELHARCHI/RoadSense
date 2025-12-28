from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Service Configuration
    SERVICE_NAME: str = "export-sig-service"
    SERVICE_VERSION: str = "1.0.0"
    
    # Database Configuration
    DATABASE_URL: str
    
    # Redis Configuration
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 4
    
    # External Services
    GEOREF_SERVICE_URL: str = "http://georef-service:8004"
    SEVERITY_SERVICE_URL: str = "http://severity-service:8002"
    
    # Export Configuration
    EXPORT_DIR: str = "/app/exports"
    MAX_EXPORT_SIZE_MB: int = 100
    DEFAULT_COORDINATE_SYSTEM: str = "EPSG:4326"
    GEOJSON_PRECISION: int = 6
    
    class Config:
        env_file = ".env"


settings = Settings()
