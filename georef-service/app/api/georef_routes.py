from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database.connection import get_db
from app.services.georef_service import GeoRefService
from app.core.config import settings

router = APIRouter()


# Request/Response models
class GeoRefRequest(BaseModel):
    """Single defect georeferencing request"""
    detection_id: str = Field(..., description="Detection UUID")
    latitude: float = Field(..., ge=-90, le=90, description="GPS latitude")
    longitude: float = Field(..., ge=-180, le=180, description="GPS longitude")
    defect_type: Optional[str] = Field(None, description="Defect type (D00, D10, etc.)")
    severity_score: Optional[float] = Field(None, ge=0, le=10, description="Severity score")
    heading: Optional[float] = Field(None, ge=0, lt=360, description="Vehicle heading in degrees")


class BatchGeoRefRequest(BaseModel):
    """Batch georeferencing request"""
    defects: List[GeoRefRequest] = Field(..., description="List of defects to georeference")


class NearbySearchRequest(BaseModel):
    """Nearby defects search request"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_meters: float = Field(100.0, gt=0, le=5000, description="Search radius in meters")


@router.post("/", summary="Georeference a single defect")
async def georeference_defect(
    request: GeoRefRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Map a defect detection to the road network using GPS coordinates.
    
    Returns the matched road segment and confidence metrics.
    """
    service = GeoRefService(distance_threshold=settings.DEFAULT_DISTANCE_THRESHOLD)
    
    result = await service.georeference_defect(
        db=db,
        detection_id=request.detection_id,
        latitude=request.latitude,
        longitude=request.longitude,
        defect_type=request.defect_type,
        severity_score=request.severity_score,
        heading=request.heading
    )
    
    return result


@router.post("/batch", summary="Batch georeference multiple defects")
async def batch_georeference(
    request: BatchGeoRefRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Georeference multiple defects at once.
    
    Useful for processing extracted frames from a video.
    """
    service = GeoRefService(distance_threshold=settings.DEFAULT_DISTANCE_THRESHOLD)
    
    defects_data = [defect.dict() for defect in request.defects]
    results = await service.batch_georeference(db, defects_data)
    
    return {
        "total": len(results),
        "matched": sum(1 for r in results if r.get("matched")),
        "unmatched": sum(1 for r in results if not r.get("matched")),
        "results": results
    }


@router.post("/nearby", summary="Find nearby defects")
async def find_nearby_defects(
    request: NearbySearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Find all georeferenced defects within a radius of a point.
    
    Useful for showing defects near current location or area of interest.
    """
    service = GeoRefService()
    
    defects = await service.get_nearby_defects(
        db=db,
        latitude=request.latitude,
        longitude=request.longitude,
        radius_meters=request.radius_meters
    )
    
    return {
        "search_center": {
            "latitude": request.latitude,
            "longitude": request.longitude
        },
        "radius_meters": request.radius_meters,
        "count": len(defects),
        "defects": defects
    }


@router.get("/segment/{segment_id}", summary="Get defects on a road segment")
async def get_segment_defects(
    segment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all defects mapped to a specific road segment.
    
    Useful for maintenance planning and road condition reports.
    """
    service = GeoRefService()
    
    defects = await service.get_segment_defects(db, segment_id)
    
    return {
        "segment_id": segment_id,
        "defect_count": len(defects),
        "defects": defects
    }


@router.get("/stats", summary="Get georeferencing statistics")
async def get_georef_stats(db: AsyncSession = Depends(get_db)):
    """
    Get overall georeferencing statistics.
    """
    from sqlalchemy import select, func
    from app.database.models import GeoreferencedDefect, RoadSegment
    
    # Total defects
    total_query = select(func.count(GeoreferencedDefect.id))
    total_result = await db.execute(total_query)
    total = total_result.scalar()
    
    # Matched defects
    matched_query = select(func.count(GeoreferencedDefect.id)).where(
        GeoreferencedDefect.is_matched == True
    )
    matched_result = await db.execute(matched_query)
    matched = matched_result.scalar()
    
    # Defects needing review
    review_query = select(func.count(GeoreferencedDefect.id)).where(
        GeoreferencedDefect.needs_review == True
    )
    review_result = await db.execute(review_query)
    needs_review = review_result.scalar()
    
    # Total road segments
    segments_query = select(func.count(RoadSegment.id))
    segments_result = await db.execute(segments_query)
    total_segments = segments_result.scalar()
    
    return {
        "total_defects": total or 0,
        "matched_defects": matched or 0,
        "unmatched_defects": (total or 0) - (matched or 0),
        "needs_review": needs_review or 0,
        "match_rate": round((matched or 0) / (total or 1) * 100, 2),
        "total_road_segments": total_segments or 0
    }
