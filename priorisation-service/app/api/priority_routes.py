from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database.connection import get_db
from app.services.priority_service import PriorityService
from app.core.config import settings

router = APIRouter()


# Request/Response models
class DefectInput(BaseModel):
    """Single defect information for priority calculation"""
    severity_score: float = Field(..., ge=0, le=10, description="Severity score 0-10")
    age_days: int = Field(0, ge=0, description="Days since defect detected")
    road_name: Optional[str] = Field(None, description="Road name")
    road_type: str = Field("residential", description="Road type")
    segment_length_meters: float = Field(100.0, gt=0, description="Segment length in meters")


class ComputePriorityRequest(BaseModel):
    """Request to compute priority for a segment"""
    segment_id: int = Field(..., description="Road segment ID")
    defects: List[DefectInput] = Field(..., min_items=1, description="List of defects on segment")


class PriorityScoreResponse(BaseModel):
    """Priority score response"""
    id: str
    segment_id: int
    severity_score: float
    traffic_score: float
    density_score: float
    age_score: float
    accessibility_score: float
    total_priority_score: float
    priority_level: str
    defect_count: int
    avg_severity: float
    max_severity: float
    road_name: Optional[str]
    road_type: Optional[str]
    estimated_cost: Optional[float]
    estimated_duration_days: Optional[int]
    calculated_at: str


@router.post("/compute", summary="Compute priority for a road segment")
async def compute_priority(
    request: ComputePriorityRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate priority score for a road segment based on its defects.
    
    The priority algorithm considers:
    - Severity of defects (35%)
    - Traffic importance (25%)
    - Defect density (20%)
    - Age of defects (15%)
    - Accessibility (5%)
    """
    defects_data = [defect.dict() for defect in request.defects]
    
    priority_score = await PriorityService.compute_segment_priority(
        db=db,
        segment_id=request.segment_id,
        defects=defects_data
    )
    
    return {
        "id": str(priority_score.id),
        "segment_id": priority_score.segment_id,
        "severity_score": priority_score.severity_score,
        "traffic_score": priority_score.traffic_score,
        "density_score": priority_score.density_score,
        "age_score": priority_score.age_score,
        "accessibility_score": priority_score.accessibility_score,
        "total_priority_score": priority_score.total_priority_score,
        "priority_level": priority_score.priority_level,
        "defect_count": priority_score.defect_count,
        "avg_severity": priority_score.avg_severity,
        "max_severity": priority_score.max_severity,
        "road_name": priority_score.road_name,
        "road_type": priority_score.road_type,
        "estimated_cost": priority_score.estimated_cost,
        "estimated_duration_days": priority_score.estimated_duration_days,
        "calculated_at": priority_score.calculated_at.isoformat()
    }


@router.get("/list", summary="Get prioritized segments list")
async def get_priority_list(
    min_priority: Optional[float] = Query(None, ge=0, le=100, description="Minimum priority score"),
    priority_level: Optional[str] = Query(None, regex="^(LOW|MEDIUM|HIGH|CRITICAL)$"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get prioritized list of road segments ordered by priority score.
    
    Filter by minimum priority score or priority level.
    """
    segments = await PriorityService.get_priority_list(
        db=db,
        min_priority=min_priority,
        priority_level=priority_level,
        limit=limit
    )
    
    return {
        "count": len(segments),
        "filters": {
            "min_priority": min_priority,
            "priority_level": priority_level,
            "limit": limit
        },
        "segments": [
            {
                "id": str(seg.id),
                "segment_id": seg.segment_id,
                "priority_score": seg.total_priority_score,
                "priority_level": seg.priority_level,
                "defect_count": seg.defect_count,
                "avg_severity": seg.avg_severity,
                "road_name": seg.road_name,
                "road_type": seg.road_type,
                "estimated_cost": seg.estimated_cost,
                "estimated_duration_days": seg.estimated_duration_days
            }
            for seg in segments
        ]
    }


@router.get("/segment/{segment_id}", summary="Get priority details for segment")
async def get_segment_priority(
    segment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed priority information for a specific road segment."""
    from sqlalchemy import select
    from app.database.models import PriorityScore
    
    result = await db.execute(
        select(PriorityScore).where(PriorityScore.segment_id == segment_id)
    )
    priority = result.scalar_one_or_none()
    
    if not priority:
        raise HTTPException(status_code=404, detail=f"No priority data for segment {segment_id}")
    
    return {
        "id": str(priority.id),
        "segment_id": priority.segment_id,
        "severity_score": priority.severity_score,
        "traffic_score": priority.traffic_score,
        "density_score": priority.density_score,
        "age_score": priority.age_score,
        "accessibility_score": priority.accessibility_score,
        "total_priority_score": priority.total_priority_score,
        "priority_level": priority.priority_level,
        "defect_count": priority.defect_count,
        "avg_severity": priority.avg_severity,
        "max_severity": priority.max_severity,
        "road_name": priority.road_name,
        "road_type": priority.road_type,
        "estimated_cost": priority.estimated_cost,
        "estimated_duration_days": priority.estimated_duration_days,
        "maintenance_urgency": priority.maintenance_urgency,
        "created_at": priority.created_at.isoformat(),
        "updated_at": priority.updated_at.isoformat(),
        "calculated_at": priority.calculated_at.isoformat()
    }


@router.get("/stats", summary="Get priority statistics")
async def get_statistics(db: AsyncSession = Depends(get_db)):
    """
    Get overall priority statistics including:
    - Total segments analyzed
    - Distribution by priority level
    - Total defects
    - Total estimated cost
    """
    stats = await PriorityService.get_statistics(db)
    
    return {
        **stats,
        "algorithm_weights": {
            "severity": settings.WEIGHT_SEVERITY,
            "traffic": settings.WEIGHT_TRAFFIC,
            "density": settings.WEIGHT_DENSITY,
            "age": settings.WEIGHT_AGE,
            "accessibility": settings.WEIGHT_ACCESSIBILITY
        },
        "thresholds": {
            "high_priority": settings.HIGH_PRIORITY_THRESHOLD,
            "critical_priority": settings.CRITICAL_PRIORITY_THRESHOLD
        }
    }


@router.post("/recompute", summary="Recompute all priorities")
async def recompute_all_priorities(db: AsyncSession = Depends(get_db)):
    """
    Recompute priority scores for all segments.
    
    Useful when algorithm weights or thresholds change.
    """
    # This would typically fetch all segments and recompute
    # For now, return a message
    return {
        "message": "Priority recomputation triggered",
        "status": "In development - will recompute all segment priorities"
    }
