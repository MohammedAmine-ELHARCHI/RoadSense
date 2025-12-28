import logging
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import PriorityScore, MaintenanceTask
from app.core.config import settings

logger = logging.getLogger(__name__)


class PriorityService:
    """Service for calculating and managing maintenance priorities."""
    
    @staticmethod
    def calculate_priority_score(
        severity_score: float,
        traffic_score: float = 50.0,
        density_score: float = 50.0,
        age_score: float = 50.0,
        accessibility_score: float = 50.0
    ) -> float:
        """
        Calculate priority score using weighted algorithm.
        
        Priority Score = (
            0.35 × Severity Score +
            0.25 × Traffic Importance +
            0.20 × Defect Density +
            0.15 × Age Score +
            0.05 × Accessibility
        )
        
        All inputs should be on 0-100 scale.
        Returns score on 0-100 scale.
        """
        score = (
            settings.WEIGHT_SEVERITY * severity_score +
            settings.WEIGHT_TRAFFIC * traffic_score +
            settings.WEIGHT_DENSITY * density_score +
            settings.WEIGHT_AGE * age_score +
            settings.WEIGHT_ACCESSIBILITY * accessibility_score
        )
        
        return round(max(settings.MIN_PRIORITY_SCORE, min(100.0, score)), 2)
    
    @staticmethod
    def get_priority_level(priority_score: float) -> str:
        """Determine priority level from score."""
        if priority_score >= settings.CRITICAL_PRIORITY_THRESHOLD:
            return "CRITICAL"
        elif priority_score >= settings.HIGH_PRIORITY_THRESHOLD:
            return "HIGH"
        elif priority_score >= 50.0:
            return "MEDIUM"
        else:
            return "LOW"
    
    @staticmethod
    def estimate_cost(defect_count: int, avg_severity: float, road_type: str) -> float:
        """
        Estimate maintenance cost based on defects and road type.
        
        Returns cost in currency units (e.g., USD).
        """
        # Base cost per defect
        base_cost = 500.0
        
        # Severity multiplier (1.0 - 2.0)
        severity_multiplier = 1.0 + (avg_severity / 10.0)
        
        # Road type multiplier
        road_multipliers = {
            "motorway": 2.5,
            "trunk": 2.0,
            "primary": 1.8,
            "secondary": 1.5,
            "tertiary": 1.2,
            "residential": 1.0,
            "unclassified": 0.8
        }
        road_multiplier = road_multipliers.get(road_type, 1.0)
        
        total_cost = base_cost * defect_count * severity_multiplier * road_multiplier
        
        return round(total_cost, 2)
    
    @staticmethod
    def estimate_duration(defect_count: int, road_type: str) -> int:
        """
        Estimate maintenance duration in days.
        """
        # Base time per defect (hours)
        base_hours = 4
        
        # Road type multiplier for complexity
        road_multipliers = {
            "motorway": 2.0,
            "trunk": 1.8,
            "primary": 1.5,
            "secondary": 1.2,
            "tertiary": 1.0,
            "residential": 0.8,
            "unclassified": 0.8
        }
        multiplier = road_multipliers.get(road_type, 1.0)
        
        total_hours = base_hours * defect_count * multiplier
        total_days = max(1, int(total_hours / 8))  # 8 hour work day
        
        return total_days
    
    @staticmethod
    async def compute_segment_priority(
        db: AsyncSession,
        segment_id: int,
        defects: List[dict]
    ) -> PriorityScore:
        """
        Compute priority score for a road segment based on its defects.
        
        Args:
            db: Database session
            segment_id: Road segment ID
            defects: List of defect dictionaries with severity_score, age_days, etc.
            
        Returns:
            PriorityScore instance
        """
        if not defects:
            raise ValueError("No defects provided for segment")
        
        # Extract defect metrics
        defect_count = len(defects)
        severities = [d.get("severity_score", 5.0) for d in defects]
        avg_severity = sum(severities) / len(severities)
        max_severity = max(severities)
        
        # Calculate component scores
        severity_score = (avg_severity / 10.0) * 100  # Convert 0-10 to 0-100
        
        # Traffic score (can be enriched with real traffic data)
        road_type = defects[0].get("road_type", "residential")
        traffic_importance = {
            "motorway": 100,
            "trunk": 90,
            "primary": 80,
            "secondary": 60,
            "tertiary": 40,
            "residential": 30,
            "unclassified": 20
        }
        traffic_score = traffic_importance.get(road_type, 50)
        
        # Density score (defects per km)
        segment_length = defects[0].get("segment_length_meters", 100) / 1000.0
        density = defect_count / max(segment_length, 0.1)
        density_score = min(100, density * 20)  # Cap at 100
        
        # Age score (older defects = higher priority)
        ages = [d.get("age_days", 0) for d in defects]
        avg_age_days = sum(ages) / len(ages) if ages else 0
        age_score = min(100, (avg_age_days / 365.0) * 100)  # 1 year = 100
        
        # Accessibility score (default 50 for now)
        accessibility_score = 50.0
        
        # Calculate total priority
        total_priority = PriorityService.calculate_priority_score(
            severity_score=severity_score,
            traffic_score=traffic_score,
            density_score=density_score,
            age_score=age_score,
            accessibility_score=accessibility_score
        )
        
        priority_level = PriorityService.get_priority_level(total_priority)
        
        # Estimate cost and duration
        estimated_cost = PriorityService.estimate_cost(
            defect_count=defect_count,
            avg_severity=avg_severity,
            road_type=road_type
        )
        
        estimated_duration = PriorityService.estimate_duration(
            defect_count=defect_count,
            road_type=road_type
        )
        
        # Check if priority score already exists
        result = await db.execute(
            select(PriorityScore).where(PriorityScore.segment_id == segment_id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing
            existing.severity_score = severity_score
            existing.traffic_score = traffic_score
            existing.density_score = density_score
            existing.age_score = age_score
            existing.accessibility_score = accessibility_score
            existing.total_priority_score = total_priority
            existing.priority_level = priority_level
            existing.defect_count = defect_count
            existing.avg_severity = avg_severity
            existing.max_severity = max_severity
            existing.estimated_cost = estimated_cost
            existing.estimated_duration_days = estimated_duration
            existing.updated_at = datetime.utcnow()
            existing.calculated_at = datetime.utcnow()
            priority_score = existing
        else:
            # Create new
            priority_score = PriorityScore(
                segment_id=segment_id,
                severity_score=severity_score,
                traffic_score=traffic_score,
                density_score=density_score,
                age_score=age_score,
                accessibility_score=accessibility_score,
                total_priority_score=total_priority,
                priority_level=priority_level,
                defect_count=defect_count,
                avg_severity=avg_severity,
                max_severity=max_severity,
                road_name=defects[0].get("road_name", "Unknown"),
                road_type=road_type,
                estimated_cost=estimated_cost,
                estimated_duration_days=estimated_duration
            )
            db.add(priority_score)
        
        await db.commit()
        await db.refresh(priority_score)
        
        return priority_score
    
    @staticmethod
    async def get_priority_list(
        db: AsyncSession,
        min_priority: Optional[float] = None,
        priority_level: Optional[str] = None,
        limit: int = 100
    ) -> List[PriorityScore]:
        """Get prioritized list of road segments."""
        query = select(PriorityScore).order_by(desc(PriorityScore.total_priority_score))
        
        if min_priority is not None:
            query = query.where(PriorityScore.total_priority_score >= min_priority)
        
        if priority_level:
            query = query.where(PriorityScore.priority_level == priority_level)
        
        query = query.limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_statistics(db: AsyncSession) -> dict:
        """Get priority statistics."""
        # Total segments
        total_query = select(func.count(PriorityScore.id))
        total_result = await db.execute(total_query)
        total = total_result.scalar()
        
        # By priority level
        critical_query = select(func.count(PriorityScore.id)).where(
            PriorityScore.priority_level == "CRITICAL"
        )
        critical_result = await db.execute(critical_query)
        critical = critical_result.scalar()
        
        high_query = select(func.count(PriorityScore.id)).where(
            PriorityScore.priority_level == "HIGH"
        )
        high_result = await db.execute(high_query)
        high = high_result.scalar()
        
        medium_query = select(func.count(PriorityScore.id)).where(
            PriorityScore.priority_level == "MEDIUM"
        )
        medium_result = await db.execute(medium_query)
        medium = medium_result.scalar()
        
        low_query = select(func.count(PriorityScore.id)).where(
            PriorityScore.priority_level == "LOW"
        )
        low_result = await db.execute(low_query)
        low = low_result.scalar()
        
        # Total estimated cost
        cost_query = select(func.sum(PriorityScore.estimated_cost))
        cost_result = await db.execute(cost_query)
        total_cost = cost_result.scalar() or 0.0
        
        # Total defects
        defects_query = select(func.sum(PriorityScore.defect_count))
        defects_result = await db.execute(defects_query)
        total_defects = defects_result.scalar() or 0
        
        return {
            "total_segments": total or 0,
            "by_priority_level": {
                "critical": critical or 0,
                "high": high or 0,
                "medium": medium or 0,
                "low": low or 0
            },
            "total_defects": total_defects,
            "total_estimated_cost": round(total_cost, 2),
            "avg_priority_score": round(
                (await db.execute(select(func.avg(PriorityScore.total_priority_score)))).scalar() or 0.0,
                2
            )
        }
