from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()


class PriorityScore(Base):
    __tablename__ = "priority_scores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id = Column(Integer, index=True, nullable=False)
    
    # Priority components (0-100 scale)
    severity_score = Column(Float, nullable=False)
    traffic_score = Column(Float, default=50.0)
    density_score = Column(Float, default=50.0)
    age_score = Column(Float, default=50.0)
    accessibility_score = Column(Float, default=50.0)
    
    # Final priority score (0-100 scale)
    total_priority_score = Column(Float, nullable=False, index=True)
    priority_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Metadata
    defect_count = Column(Integer, default=0)
    avg_severity = Column(Float)
    max_severity = Column(Float)
    road_name = Column(String(255))
    road_type = Column(String(50))
    
    # Maintenance info
    estimated_cost = Column(Float)
    estimated_duration_days = Column(Integer)
    maintenance_urgency = Column(String(50))
    last_inspection_date = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    calculated_at = Column(DateTime, default=datetime.utcnow)


class MaintenanceTask(Base):
    __tablename__ = "maintenance_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id = Column(Integer, ForeignKey('priority_scores.segment_id'), index=True)
    
    # Task details
    task_type = Column(String(50), nullable=False)  # INSPECTION, REPAIR, REPLACEMENT
    status = Column(String(20), default="PENDING")  # PENDING, SCHEDULED, IN_PROGRESS, COMPLETED
    priority_score = Column(Float, nullable=False)
    
    # Scheduling
    scheduled_date = Column(DateTime)
    completion_date = Column(DateTime)
    assigned_team = Column(String(100))
    
    # Cost
    estimated_cost = Column(Float)
    actual_cost = Column(Float)
    
    # Notes
    description = Column(Text)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
