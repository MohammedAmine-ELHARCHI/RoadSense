from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database.connection import Base

class DetectionResult(Base):
    __tablename__ = "detection_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_id = Column(String(255), unique=True, nullable=False, index=True)
    frame_id = Column(UUID(as_uuid=True), nullable=True)  # Will link to frames table when video service is built
    frame_path = Column(Text)
    annotated_image_path = Column(Text)
    total_defects = Column(Integer, default=0)
    detection_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    model_version = Column(String(50))
    processing_time_ms = Column(Float)
    
    # Relationships
    defects = relationship("Defect", back_populates="detection_result", cascade="all, delete-orphan")

class Defect(Base):
    __tablename__ = "defects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    detection_result_id = Column(UUID(as_uuid=True), ForeignKey("detection_results.id", ondelete="CASCADE"), nullable=False)
    class_name = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    bbox_x_min = Column(Float, nullable=False)
    bbox_y_min = Column(Float, nullable=False)
    bbox_x_max = Column(Float, nullable=False)
    bbox_y_max = Column(Float, nullable=False)
    area_pixels = Column(Integer)
    mask_path = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    detection_result = relationship("DetectionResult", back_populates="defects")
    severity_score = relationship("SeverityScore", back_populates="defect", uselist=False, cascade="all, delete-orphan")

class SeverityScore(Base):
    __tablename__ = "severity_scores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    defect_id = Column(UUID(as_uuid=True), ForeignKey("defects.id", ondelete="CASCADE"), nullable=False)
    severity_score = Column(Float)
    risk_category = Column(String(20), index=True)
    risk_score = Column(Float)
    computed_at = Column(DateTime(timezone=True), server_default=func.now())
    model_version = Column(String(50))
    
    # Relationships
    defect = relationship("Defect", back_populates="severity_score")
