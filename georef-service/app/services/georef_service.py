import logging
from typing import Optional, List, Tuple
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points
from geopy.distance import geodesic
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.functions import ST_Distance, ST_Transform, ST_DWithin, ST_ClosestPoint, ST_LineLocatePoint

from app.database.models import RoadSegment, GeoreferencedDefect

logger = logging.getLogger(__name__)


class GeoRefService:
    """Service for georeferencing defects to road network"""
    
    def __init__(self, distance_threshold: float = 50.0):
        """
        Initialize GeoRef service
        
        Args:
            distance_threshold: Maximum distance in meters for map-matching
        """
        self.distance_threshold = distance_threshold
    
    async def georeference_defect(
        self,
        db: AsyncSession,
        detection_id: str,
        latitude: float,
        longitude: float,
        defect_type: Optional[str] = None,
        severity_score: Optional[float] = None,
        heading: Optional[float] = None
    ) -> dict:
        """
        Georeference a single defect to the road network
        
        Args:
            db: Database session
            detection_id: UUID of the detection
            latitude: GPS latitude
            longitude: GPS longitude
            defect_type: Type of defect (D00, D10, etc.)
            severity_score: Severity score (0-10)
            heading: Vehicle heading in degrees
            
        Returns:
            Dictionary with georeferencing results
        """
        try:
            # Create point geometry
            point_wkt = f"POINT({longitude} {latitude})"
            
            # Find nearest road segment within threshold
            query = select(
                RoadSegment.id,
                RoadSegment.osm_id,
                RoadSegment.name,
                RoadSegment.road_type,
                func.ST_Distance(
                    func.ST_Transform(RoadSegment.geometry, 3857),
                    func.ST_Transform(func.ST_GeomFromText(point_wkt, 4326), 3857)
                ).label("distance"),
                func.ST_AsText(
                    func.ST_ClosestPoint(
                        RoadSegment.geometry,
                        func.ST_GeomFromText(point_wkt, 4326)
                    )
                ).label("matched_point")
            ).where(
                func.ST_DWithin(
                    func.ST_Transform(RoadSegment.geometry, 3857),
                    func.ST_Transform(func.ST_GeomFromText(point_wkt, 4326), 3857),
                    self.distance_threshold
                )
            ).order_by(func.ST_Distance(
                func.ST_Transform(RoadSegment.geometry, 3857),
                func.ST_Transform(func.ST_GeomFromText(point_wkt, 4326), 3857)
            )).limit(1)
            
            result = await db.execute(query)
            road = result.first()
            
            if road:
                # Create georeferenced defect record
                georef_defect = GeoreferencedDefect(
                    detection_id=detection_id,
                    segment_id=road.id,
                    gps_location=point_wkt,
                    matched_location=road.matched_point,
                    distance_to_road=road.distance,
                    confidence=self._calculate_confidence(road.distance),
                    heading=heading,
                    defect_type=defect_type,
                    severity_score=severity_score,
                    is_matched=True,
                    needs_review=road.distance > self.distance_threshold * 0.6
                )
                
                db.add(georef_defect)
                await db.commit()
                await db.refresh(georef_defect)
                
                logger.info(f"Defect {detection_id} matched to road segment {road.osm_id} (distance: {road.distance:.2f}m)")
                
                return {
                    "georef_id": str(georef_defect.id),
                    "matched": True,
                    "road_segment": {
                        "id": road.id,
                        "osm_id": road.osm_id,
                        "name": road.name or "Unnamed road",
                        "type": road.road_type
                    },
                    "original_location": {"latitude": latitude, "longitude": longitude},
                    "matched_location": self._parse_point(road.matched_point),
                    "distance_to_road": round(road.distance, 2),
                    "confidence": round(georef_defect.confidence, 3),
                    "needs_review": georef_defect.needs_review
                }
            else:
                # No road found within threshold
                georef_defect = GeoreferencedDefect(
                    detection_id=detection_id,
                    gps_location=point_wkt,
                    defect_type=defect_type,
                    severity_score=severity_score,
                    heading=heading,
                    is_matched=False,
                    needs_review=True
                )
                
                db.add(georef_defect)
                await db.commit()
                await db.refresh(georef_defect)
                
                logger.warning(f"No road found within {self.distance_threshold}m for defect {detection_id}")
                
                return {
                    "georef_id": str(georef_defect.id),
                    "matched": False,
                    "original_location": {"latitude": latitude, "longitude": longitude},
                    "message": f"No road segment found within {self.distance_threshold}m",
                    "needs_review": True
                }
                
        except Exception as e:
            logger.error(f"Georeferencing failed: {e}")
            raise
    
    async def batch_georeference(
        self,
        db: AsyncSession,
        defects: List[dict]
    ) -> List[dict]:
        """
        Georeference multiple defects at once
        
        Args:
            db: Database session
            defects: List of defect dictionaries with detection_id, latitude, longitude
            
        Returns:
            List of georeferencing results
        """
        results = []
        for defect in defects:
            result = await self.georeference_defect(
                db,
                detection_id=defect["detection_id"],
                latitude=defect["latitude"],
                longitude=defect["longitude"],
                defect_type=defect.get("defect_type"),
                severity_score=defect.get("severity_score"),
                heading=defect.get("heading")
            )
            results.append(result)
        
        return results
    
    async def get_nearby_defects(
        self,
        db: AsyncSession,
        latitude: float,
        longitude: float,
        radius_meters: float = 100.0
    ) -> List[dict]:
        """
        Find defects near a location
        
        Args:
            db: Database session
            latitude: Center point latitude
            longitude: Center point longitude
            radius_meters: Search radius in meters
            
        Returns:
            List of nearby defects
        """
        point_wkt = f"POINT({longitude} {latitude})"
        
        query = select(
            GeoreferencedDefect,
            RoadSegment.name.label("road_name"),
            RoadSegment.road_type,
            func.ST_Distance(
                func.ST_Transform(GeoreferencedDefect.gps_location, 3857),
                func.ST_Transform(func.ST_GeomFromText(point_wkt, 4326), 3857)
            ).label("distance")
        ).outerjoin(
            RoadSegment, GeoreferencedDefect.segment_id == RoadSegment.id
        ).where(
            func.ST_DWithin(
                func.ST_Transform(GeoreferencedDefect.gps_location, 3857),
                func.ST_Transform(func.ST_GeomFromText(point_wkt, 4326), 3857),
                radius_meters
            )
        ).order_by("distance")
        
        result = await db.execute(query)
        rows = result.all()
        
        defects = []
        for row in rows:
            defect = row.GeoreferencedDefect
            location = self._parse_point(defect.gps_location)
            
            defects.append({
                "georef_id": str(defect.id),
                "detection_id": str(defect.detection_id),
                "defect_type": defect.defect_type,
                "severity_score": defect.severity_score,
                "location": location,
                "road_name": row.road_name or "Unknown",
                "road_type": row.road_type,
                "distance_meters": round(row.distance, 2),
                "needs_review": defect.needs_review
            })
        
        return defects
    
    async def get_segment_defects(
        self,
        db: AsyncSession,
        segment_id: int
    ) -> List[dict]:
        """
        Get all defects on a specific road segment
        
        Args:
            db: Database session
            segment_id: Road segment ID
            
        Returns:
            List of defects on the segment
        """
        query = select(GeoreferencedDefect).where(
            GeoreferencedDefect.segment_id == segment_id
        ).order_by(GeoreferencedDefect.created_at.desc())
        
        result = await db.execute(query)
        defects = result.scalars().all()
        
        return [
            {
                "georef_id": str(d.id),
                "detection_id": str(d.detection_id),
                "defect_type": d.defect_type,
                "severity_score": d.severity_score,
                "location": self._parse_point(d.gps_location),
                "matched_location": self._parse_point(d.matched_location) if d.matched_location else None,
                "distance_to_road": d.distance_to_road,
                "confidence": d.confidence,
                "needs_review": d.needs_review,
                "created_at": d.created_at.isoformat()
            }
            for d in defects
        ]
    
    def _calculate_confidence(self, distance: float) -> float:
        """Calculate confidence score based on distance to road"""
        if distance <= 5:
            return 1.0
        elif distance <= 15:
            return 0.9
        elif distance <= 30:
            return 0.7
        elif distance <= 50:
            return 0.5
        else:
            return 0.3
    
    def _parse_point(self, wkt: str) -> Optional[dict]:
        """Parse POINT WKT to lat/lon dict"""
        if not wkt:
            return None
        
        try:
            # Remove "POINT(" and ")"
            coords = wkt.replace("POINT(", "").replace(")", "")
            lon, lat = map(float, coords.split())
            return {"latitude": lat, "longitude": lon}
        except Exception as e:
            logger.error(f"Failed to parse point: {e}")
            return None
