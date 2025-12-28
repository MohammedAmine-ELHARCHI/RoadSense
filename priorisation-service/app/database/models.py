# Import datetime for timestamp fields
from datetime import datetime
# Import SQLAlchemy column types and constraints
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text, Boolean
# Import PostgreSQL-specific UUID type
from sqlalchemy.dialects.postgresql import UUID
# Import declarative base for model definition
from sqlalchemy.ext.declarative import declarative_base
# Import uuid for generating unique identifiers
import uuid

# Create base class for all ORM models
Base = declarative_base()


# Define PriorityScore model for storing road segment priority calculations
class PriorityScore(Base):
    # Specify the database table name
    __tablename__ = "priority_scores"
    
    # Primary key: unique identifier as UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Road segment identifier with index for fast lookups
    # Road segment identifier with index for fast lookups
    segment_id = Column(Integer, index=True, nullable=False)
    
    # Priority components (0-100 scale) - individual scoring factors
    # Severity score component based on defect severity (required field)
    severity_score = Column(Float, nullable=False)
    # Traffic importance score based on road type and usage
    traffic_score = Column(Float, default=50.0)
    # Density score based on defects per kilometer
    density_score = Column(Float, default=50.0)
    # Age score based on how long defects have existed
    age_score = Column(Float, default=50.0)
    # Accessibility score for maintenance crew access
    accessibility_score = Column(Float, default=50.0)
    
    # Final priority score (0-100 scale) - weighted sum of components
    # Total priority score with index for efficient sorting and filtering
    total_priority_score = Column(Float, nullable=False, index=True)
    # Priority level classification: LOW, MEDIUM, HIGH, or CRITICAL
    priority_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Metadata section - aggregate statistics about segment defects
    # Number of defects detected on this segment
    defect_count = Column(Integer, default=0)
    # Average severity across all defects on segment
    avg_severity = Column(Float)
    # Maximum severity of any single defect on segment
    max_severity = Column(Float)
    # Name of the road (from OSM data)
    road_name = Column(String(255))
    # Type of road (motorway, primary, residential, etc.)
    road_type = Column(String(50))
    
    # Maintenance info section - cost and time estimates
    # Estimated cost for repairing this segment in currency units
    estimated_cost = Column(Float)
    # Estimated duration for maintenance work in days
    estimated_duration_days = Column(Integer)
    # Urgency classification for maintenance scheduling
    maintenance_urgency = Column(String(50))
    # Date of last physical inspection of this segment
    last_inspection_date = Column(DateTime)
    
    # Timestamps section - tracking record lifecycle
    # Record creation timestamp (set once on insert)
    created_at = Column(DateTime, default=datetime.utcnow)
    # Record last update timestamp (auto-updated on changes)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # When this specific priority score was calculated
    calculated_at = Column(DateTime, default=datetime.utcnow)


# Define MaintenanceTask model for managing maintenance work orders
class MaintenanceTask(Base):
    # Specify the database table name
    __tablename__ = "maintenance_tasks"
    
    # Primary key: unique identifier as UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Foreign key linking to priority_scores table, indexed for joins
    segment_id = Column(Integer, ForeignKey('priority_scores.segment_id'), index=True)
    
    # Task details section - work order information
    # Type of task: INSPECTION, REPAIR, or REPLACEMENT
    task_type = Column(String(50), nullable=False)  # INSPECTION, REPAIR, REPLACEMENT
    # Current status: PENDING, SCHEDULED, IN_PROGRESS, or COMPLETED
    status = Column(String(20), default="PENDING")  # PENDING, SCHEDULED, IN_PROGRESS, COMPLETED
    # Priority score at time of task creation
    priority_score = Column(Float, nullable=False)
    
    # Scheduling section - time management fields
    # Planned date for performing the maintenance
    scheduled_date = Column(DateTime)
    # Actual date when maintenance was completed
    completion_date = Column(DateTime)
    # Name or ID of maintenance team assigned to task
    assigned_team = Column(String(100))
    
    # Cost section - budget and actual spending
    # Estimated cost before work begins
    estimated_cost = Column(Float)
    # Actual cost after work is completed
    actual_cost = Column(Float)
    
    # Notes section - free text documentation
    # Brief description of the maintenance task
    description = Column(Text)
    # Additional notes, observations, or comments
    notes = Column(Text)
    
    # Timestamps - tracking task lifecycle
    # When the task was created
    created_at = Column(DateTime, default=datetime.utcnow)
    # When the task was last updated
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
