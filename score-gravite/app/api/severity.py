from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
import numpy as np

from app.database.connection import get_db
from app.config import settings
from app.models import predictor

router = APIRouter(tags=["Severity Scoring"])

# Pydantic models
class SeverityFeatures(BaseModel):
    """Features for severity prediction"""
    defect_type: str = Field(..., description="Type of defect (crack, pothole, etc.)")
    area: float = Field(..., description="Defect area in pixels")
    width: float = Field(..., description="Defect width in pixels")
    height: float = Field(..., description="Defect height in pixels")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    image_quality: Optional[float] = Field(0.8, ge=0.0, le=1.0, description="Image quality score")
    
class SeverityPrediction(BaseModel):
    """Severity prediction result"""
    defect_id: UUID
    severity_score: float = Field(..., ge=0.0, le=10.0, description="Severity score (0-10)")
    severity_level: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence")
    features_used: dict

class BatchSeverityRequest(BaseModel):
    """Batch severity scoring request"""
    defects: List[dict] = Field(..., description="List of defects with features")

@router.post("/compute", response_model=SeverityPrediction)
async def predict_severity(
    features: SeverityFeatures,
    db: AsyncSession = Depends(get_db)
):
    """
    Predict severity score for a single defect using trained XGBoost model.
    Falls back to heuristic method if model is not loaded.
    """
    try:
        # Use trained model predictor
        result = predictor.predict(
            defect_type=features.defect_type,
            area=features.area,
            width=features.width,
            height=features.height,
            confidence=features.confidence,
            lighting_quality=features.image_quality
        )
        
        return SeverityPrediction(
            defect_id=UUID("00000000-0000-0000-0000-000000000000"),  # Placeholder
            severity_score=result['severity_score'],
            severity_level=result['severity_level'],
            confidence=result['confidence'],
            features_used={
                **features.dict(),
                'prediction_method': result['method']
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Severity prediction failed: {str(e)}")

@router.post("/batch", response_model=List[SeverityPrediction])
async def batch_predict_severity(
    request: BatchSeverityRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Predict severity scores for multiple defects in batch.
    """
    try:
        results = []
        for defect_data in request.defects:
            features = SeverityFeatures(**defect_data)
            prediction = await predict_severity(features, db)
            results.append(prediction)
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch severity prediction failed: {str(e)}")

@router.get("/model/info")
async def get_model_info():
    """Get information about the severity scoring model"""
    model_info = predictor.get_model_info()
    
    return {
        **model_info,
        "features": [
            "defect_type",
            "area",
            "width",
            "height",
            "confidence",
            "image_quality"
        ],
        "severity_levels": {
            "LOW": "0.0 - 3.0",
            "MEDIUM": "3.0 - 6.0",
            "HIGH": "6.0 - 8.5",
            "CRITICAL": "8.5 - 10.0"
        }
    }
