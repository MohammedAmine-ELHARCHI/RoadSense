from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from geoalchemy2 import Geometry
import uuid

Base = declarative_base()


class RoadSegment(Base):
    """Road segment from OpenStreetMap"""
    __tablename__ = "road_segments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    osm_id = Column(String(100), unique=True, index=True)
    name = Column(String(255), nullable=True)
    road_type = Column(String(50), nullable=True)  # highway, primary, secondary, etc.
    surface = Column(String(50), nullable=True)
    max_speed = Column(Integer, nullable=True)
    lanes = Column(Integer, nullable=True)
    one_way = Column(Boolean, default=False)
    
    # Geometry (LineString in WGS84)
    geometry = Column(Geometry(geometry_type='LINESTRING', srid=4326), nullable=False)
    length_meters = Column(Float, nullable=True)
    
    # Traffic importance (1-10 scale)
    traffic_importance = Column(Integer, default=5)
    
    # Maintenance info
    last_maintenance_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    georeferenced_defects = relationship("GeoreferencedDefect", back_populates="road_segment")


class GeoreferencedDefect(Base):
    """Defect mapped to road segment"""
    __tablename__ = "georeferenced_defects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Link to detection
    detection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    frame_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Road segment mapping
    segment_id = Column(Integer, ForeignKey("road_segments.id"), nullable=True, index=True)
    
    # Original GPS location (from video/frame metadata)
    gps_location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=True)
    
    # Matched location on road network
    matched_location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=True)
    
    # Map-matching metrics
    distance_to_road = Column(Float, nullable=True)  # meters
    confidence = Column(Float, nullable=True)  # 0-1 score
    heading = Column(Float, nullable=True)  # degrees
    
    # Defect info (denormalized for faster queries)
    defect_type = Column(String(50), nullable=True)
    severity_score = Column(Float, nullable=True)
    
    # Status
    is_matched = Column(Boolean, default=False)
    needs_review = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    road_segment = relationship("RoadSegment", back_populates="georeferenced_defects")


class SpatialIndex(Base):
    """Spatial index metadata"""
    __tablename__ = "spatial_indexes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(100), nullable=False)
    column_name = Column(String(100), nullable=False)
    index_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
