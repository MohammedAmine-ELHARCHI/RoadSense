"""MinIO storage client for video and frame storage"""
from minio import Minio
from minio.error import S3Error
from app.core.config import settings
import logging
from io import BytesIO
from datetime import timedelta

logger = logging.getLogger(__name__)

class MinIOStorage:
    def __init__(self):
        self.client = None
        self.video_bucket = settings.MINIO_BUCKET_VIDEOS
        self.frame_bucket = settings.MINIO_BUCKET_FRAMES
    
    async def connect(self):
        """Initialize MinIO client"""
        logger.info(f"Connecting to MinIO at {settings.MINIO_ENDPOINT}")
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )
        
        # Create buckets if they don't exist
        await self._ensure_bucket(self.video_bucket)
        await self._ensure_bucket(self.frame_bucket)
        logger.info("✅ MinIO connected")
    
    async def disconnect(self):
        """Cleanup MinIO client"""
        self.client = None
        logger.info("MinIO disconnected")
    
    async def _ensure_bucket(self, bucket_name: str):
        """Create bucket if it doesn't exist"""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"Created MinIO bucket: {bucket_name}")
            else:
                logger.info(f"MinIO bucket exists: {bucket_name}")
        except S3Error as e:
            logger.error(f"Error creating bucket {bucket_name}: {e}")
            raise
    
    async def upload_video(self, file_data: bytes, object_name: str) -> str:
        """Upload video to MinIO"""
        try:
            self.client.put_object(
                self.video_bucket,
                object_name,
                BytesIO(file_data),
                length=len(file_data),
                content_type="video/mp4"
            )
            return f"{self.video_bucket}/{object_name}"
        except S3Error as e:
            logger.error(f"Error uploading video {object_name}: {e}")
            raise
    
    async def upload_frame(self, file_data: bytes, object_name: str) -> str:
        """Upload frame image to MinIO"""
        try:
            self.client.put_object(
                self.frame_bucket,
                object_name,
                BytesIO(file_data),
                length=len(file_data),
                content_type="image/jpeg"
            )
            return f"{self.frame_bucket}/{object_name}"
        except S3Error as e:
            logger.error(f"Error uploading frame {object_name}: {e}")
            raise
    
    async def download_video(self, object_name: str) -> bytes:
        """Download video from MinIO"""
        try:
            response = self.client.get_object(self.video_bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error(f"Error downloading video {object_name}: {e}")
            raise
    
    async def get_presigned_url(self, bucket: str, object_name: str, expires_seconds: int = 3600) -> str:
        """Get presigned URL for object"""
        try:
            url = self.client.presigned_get_object(
                bucket,
                object_name,
                expires=timedelta(seconds=expires_seconds)
            )
            return url
        except S3Error as e:
            logger.error(f"Error getting presigned URL for {object_name}: {e}")
            raise

storage = MinIOStorage()
