"""Application configuration"""
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # MinIO
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET_VIDEOS: str = "roadsense-videos"
    MINIO_BUCKET_FRAMES: str = "roadsense-frames"
    
    # Video Processing
    FRAME_EXTRACTION_FPS: int = 2
    MAX_VIDEO_SIZE_MB: int = 500
    SUPPORTED_VIDEO_FORMATS: str = "mp4,avi,mov,mkv"
    
    # Detection Service
    DETECTION_SERVICE_URL: str = "http://detection-service:8001"
    
    # Application
    LOG_LEVEL: str = "INFO"
    
    @property
    def supported_formats_list(self) -> List[str]:
        return [fmt.strip() for fmt in self.SUPPORTED_VIDEO_FORMATS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
