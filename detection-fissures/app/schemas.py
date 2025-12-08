from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class BoundingBox(BaseModel):
    """Bounding box coordinates"""
    x_min: float = Field(..., description="Minimum X coordinate")
    y_min: float = Field(..., description="Minimum Y coordinate")
    x_max: float = Field(..., description="Maximum X coordinate")
    y_max: float = Field(..., description="Maximum Y coordinate")

class DetectionResult(BaseModel):
    """Single defect detection result"""
    class_name: str = Field(..., description="Defect class: crack, pothole, alligator_crack, patch")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    bounding_box: BoundingBox = Field(..., description="Bounding box coordinates")
    mask: Optional[List[List[int]]] = Field(None, description="Segmentation mask (optional)")
    area_pixels: int = Field(..., description="Area of defect in pixels")

class DetectionResponse(BaseModel):
    """Response from detection endpoint"""
    image_id: str = Field(..., description="Unique image identifier")
    detections: List[DetectionResult] = Field(..., description="List of detected defects")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    model_version: str = Field(..., description="Model version used")
    annotated_image_url: Optional[str] = Field(None, description="URL to annotated image")

class DetectionRequest(BaseModel):
    """Request for detection"""
    confidence_threshold: float = Field(0.5, ge=0.0, le=1.0, description="Confidence threshold")
    return_masks: bool = Field(True, description="Whether to return segmentation masks")
    save_annotated: bool = Field(True, description="Whether to save annotated image")

class ModelInfo(BaseModel):
    """Model information"""
    model_type: str
    version: str
    classes: List[str]
    input_size: tuple
    performance_metrics: dict

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    models_loaded: bool
