from minio import Minio
from minio.error import S3Error
import io
from typing import Optional
import os

from app.config import settings

class MinIOStorage:
    """MinIO storage handler"""
    
    def __init__(self):
        self.client = None
        self.connected = False
        
    async def connect(self):
        """Initialize MinIO client"""
        try:
            self.client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            
            # Ensure buckets exist
            buckets = [
                "raw-videos",
                "extracted-frames",
                "annotated-images",
                "segmentation-masks",
                "metadata"
            ]
            
            for bucket in buckets:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    print(f"✅ Created bucket: {bucket}")
            
            self.connected = True
            print("✅ MinIO storage connected")
            
        except Exception as e:
            print(f"❌ MinIO connection failed: {e}")
            raise
    
    async def upload_image(
        self,
        bucket_name: str,
        object_name: str,
        image_bytes: bytes,
        content_type: str = "image/jpeg"
    ) -> str:
        """
        Upload image to MinIO
        
        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object
            image_bytes: Image data as bytes
            content_type: MIME type
            
        Returns:
            Object path
        """
        try:
            self.client.put_object(
                bucket_name,
                object_name,
                io.BytesIO(image_bytes),
                length=len(image_bytes),
                content_type=content_type
            )
            
            return f"{bucket_name}/{object_name}"
            
        except S3Error as e:
            print(f"❌ Error uploading to MinIO: {e}")
            raise
    
    async def download_image(
        self,
        bucket_name: str,
        object_name: str
    ) -> bytes:
        """
        Download image from MinIO
        
        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object
            
        Returns:
            Image data as bytes
        """
        try:
            response = self.client.get_object(bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            
            return data
            
        except S3Error as e:
            print(f"❌ Error downloading from MinIO: {e}")
            raise
    
    async def get_presigned_url(
        self,
        bucket_name: str,
        object_name: str,
        expires_seconds: int = 3600
    ) -> str:
        """
        Get presigned URL for an object
        
        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object
            expires_seconds: URL expiration time
            
        Returns:
            Presigned URL
        """
        from datetime import timedelta
        try:
            url = self.client.presigned_get_object(
                bucket_name,
                object_name,
                expires=timedelta(seconds=expires_seconds)
            )
            return url
            
        except S3Error as e:
            print(f"❌ Error generating presigned URL: {e}")
            raise

# Global storage instance
storage = MinIOStorage()
