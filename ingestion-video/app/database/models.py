"""Database models for video ingestion"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

Base = declarative_base()

class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Video(Base):
    """Video upload and processing tracking"""
    __tablename__ = "videos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    duration = Column(Float, nullable=True)  # seconds
    fps = Column(Float, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    codec = Column(String(50), nullable=True)
    
    # Storage
    storage_path = Column(String(500), nullable=False)
    
    # Processing status
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    frames_extracted = Column(Integer, default=0)
    frames_total = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    
    # Metadata (renamed to avoid SQLAlchemy reserved word)
    upload_user_id = Column(String(100), nullable=True)
    video_metadata = Column(Text, nullable=True)  # JSON string


class Frame(Base):
    """Extracted frames from videos"""
    __tablename__ = "frames"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), nullable=False)  # References videos.id
    
    # Frame info
    frame_number = Column(Integer, nullable=False)
    timestamp = Column(Float, nullable=False)  # seconds from video start
    
    # Storage
    storage_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    
    # Detection status
    detection_completed = Column(Boolean, default=False)
    detection_id = Column(UUID(as_uuid=True), nullable=True)  # References detection results
    
    # Timestamps
    extracted_at = Column(DateTime, default=datetime.utcnow)
    
    # GPS metadata (if available from video)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)
