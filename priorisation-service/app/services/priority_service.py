# Import logging module for service-level logging
import logging
# Import type hints for better code documentation
from typing import List, Optional
# Import datetime utilities for time-based calculations
from datetime import datetime, timedelta
# Import SQLAlchemy query components for database operations
from sqlalchemy import select, func, and_, desc
# Import async session for asynchronous database access
from sqlalchemy.ext.asyncio import AsyncSession

# Import database models for priority and maintenance
from app.database.models import PriorityScore, MaintenanceTask
# Import application configuration settings
from app.core.config import settings

# Create logger instance for this module
logger = logging.getLogger(__name__)


# Define service class for priority calculation and management logic
class PriorityService:
    """Service for calculating and managing maintenance priorities."""
    
    # Static method - doesn't need class instance to execute
    @staticmethod
    # Define method signature with type hints for all parameters
    def calculate_priority_score(
        # Severity score input (0-100 scale, required parameter)
        severity_score: float,
        # Traffic importance score (0-100 scale, defaults to 50)
        traffic_score: float = 50.0,
        # Defect density score (0-100 scale, defaults to 50)
        density_score: float = 50.0,
        # Age of defects score (0-100 scale, defaults to 50)
        age_score: float = 50.0,
        # Accessibility for maintenance score (0-100 scale, defaults to 50)
        accessibility_score: float = 50.0
    # Return type is float
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
        # Calculate weighted sum of all component scores
        score = (
            # Multiply severity by its weight (35%)
            settings.WEIGHT_SEVERITY * severity_score +
            # Multiply traffic by its weight (25%)
            settings.WEIGHT_TRAFFIC * traffic_score +
            # Multiply density by its weight (20%)
            settings.WEIGHT_DENSITY * density_score +
            # Multiply age by its weight (15%)
            settings.WEIGHT_AGE * age_score +
            # Multiply accessibility by its weight (5%)
            settings.WEIGHT_ACCESSIBILITY * accessibility_score
        )
        
        # Return rounded score, clamped between min and 100
        return round(max(settings.MIN_PRIORITY_SCORE, min(100.0, score)), 2)
    
    # Static method for determining priority classification
    @staticmethod
    # Method takes a numeric score and returns a string level
    def get_priority_level(priority_score: float) -> str:
        """
        Determine priority level classification from numeric score.
        Maps score to one of four levels: CRITICAL, HIGH, MEDIUM, or LOW.
        """
        # Check if score meets CRITICAL threshold (85+)
        if priority_score >= settings.CRITICAL_PRIORITY_THRESHOLD:
            # Return CRITICAL classification
            return "CRITICAL"
        # Check if score meets HIGH threshold (70+)
        elif priority_score >= settings.HIGH_PRIORITY_THRESHOLD:
            # Return HIGH classification
            return "HIGH"
        # Check if score is 50 or above (MEDIUM range)
        elif priority_score >= 50.0:
            # Return MEDIUM classification
            return "MEDIUM"
        # Score is below 50 (LOW priority)
        else:
            # Return LOW classification
            return "LOW"
    
    # Static method for estimating maintenance cost
    @staticmethod
    # Method takes defect count, severity, and road type to estimate cost
    def estimate_cost(defect_count: int, avg_severity: float, road_type: str) -> float:
        """
        Estimate maintenance cost based on defects and road type.
        
        Returns cost in currency units (e.g., USD).
        """
        # Base cost per defect in currency units (baseline $500)
        base_cost = 500.0
        
        # Severity multiplier (ranges from 1.0 to 2.0)
        # Higher severity increases cost proportionally
        severity_multiplier = 1.0 + (avg_severity / 10.0)
        
        # Road type multiplier - more complex roads cost more to repair
        # Dictionary mapping road types to their cost multipliers
        road_multipliers = {
            # Motorway repairs are most expensive (2.5x)
            "motorway": 2.5,
            # Trunk roads are very expensive (2.0x)
            "trunk": 2.0,
            # Primary roads are expensive (1.8x)
            "primary": 1.8,
            # Secondary roads are moderately expensive (1.5x)
            "secondary": 1.5,
            # Tertiary roads are slightly above baseline (1.2x)
            "tertiary": 1.2,
            # Residential roads are baseline cost (1.0x)
            "residential": 1.0,
            # Unclassified roads are cheapest (0.8x)
            "unclassified": 0.8
        }
        # Get multiplier for this road type, default to 1.0 if type not found
        road_multiplier = road_multipliers.get(road_type, 1.0)
        
        # Calculate total estimated cost by multiplying all factors
        total_cost = base_cost * defect_count * severity_multiplier * road_multiplier
        
        # Return cost rounded to 2 decimal places
        return round(total_cost, 2)
    
    # Static method for estimating maintenance duration
    @staticmethod
    # Method takes defect count and road type to calculate time needed
    def estimate_duration(defect_count: int, road_type: str) -> int:
        """
        Estimate maintenance duration in days.
        """
        # Base time per defect in hours (4 hours per defect)
        base_hours = 4
        
        # Road type multiplier for complexity - more complex roads take longer
        # Dictionary mapping road types to time multipliers
        road_multipliers = {
            # Motorway work takes twice as long (complex logistics, traffic management)
            "motorway": 2.0,
            # Trunk roads take 1.8x time
            "trunk": 1.8,
            # Primary roads take 1.5x time
            "primary": 1.5,
            # Secondary roads take 1.2x time
            "secondary": 1.2,
            # Tertiary roads are baseline (1.0x)
            "tertiary": 1.0,
            # Residential roads are faster (0.8x)
            "residential": 0.8,
            # Unclassified roads are fastest (0.8x)
            "unclassified": 0.8
        }
        # Get time multiplier for this road type, default to 1.0
        multiplier = road_multipliers.get(road_type, 1.0)
        
        # Calculate total hours needed
        total_hours = base_hours * defect_count * multiplier
        # Convert to days (8 hour work day), minimum 1 day
        total_days = max(1, int(total_hours / 8))  # 8 hour work day
        
        # Return estimated number of days
        return total_days
    
    # Static method for computing complete priority score for a road segment
    @staticmethod
    # Async method that requires database access
    async def compute_segment_priority(
        # Database session for data access
        db: AsyncSession,
        # Unique identifier for the road segment
        segment_id: int,
        # List of defect dictionaries with metrics
        defects: List[dict]
    # Returns a PriorityScore model instance
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
        # Validate that defects list is not empty
        if not defects:
            # Raise error if no defects provided
            raise ValueError("No defects provided for segment")
        
        # Extract defect metrics from the list
        # Count total number of defects
        defect_count = len(defects)
        # Extract severity scores from each defect, default to 5.0 if missing
        severities = [d.get("severity_score", 5.0) for d in defects]
        # Calculate average severity across all defects
        avg_severity = sum(severities) / len(severities)
        # Find the highest severity score among all defects
        max_severity = max(severities)
        
        # Calculate component scores section
        # Convert severity from 0-10 scale to 0-100 scale for uniformity
        severity_score = (avg_severity / 10.0) * 100  # Convert 0-10 to 0-100
        
        # Traffic score (can be enriched with real traffic data later)
        # Get road type from first defect, default to residential
        road_type = defects[0].get("road_type", "residential")
        # Map road types to traffic importance scores (0-100)
        traffic_importance = {
            # Motorways have highest traffic importance (100)
            "motorway": 100,
            # Trunk roads have very high traffic (90)
            "trunk": 90,
            # Primary roads have high traffic (80)
            "primary": 80,
            # Secondary roads have moderate traffic (60)
            "secondary": 60,
            # Tertiary roads have lower traffic (40)
            "tertiary": 40,
            # Residential roads have low traffic (30)
            "residential": 30,
            # Unclassified roads have lowest traffic (20)
            "unclassified": 20
        }
        # Get traffic score for this road type, default to 50
        traffic_score = traffic_importance.get(road_type, 50)
        
        # Density score (defects per kilometer)
        # Get segment length in meters and convert to kilometers
        segment_length = defects[0].get("segment_length_meters", 100) / 1000.0
        # Calculate defect density (defects/km), avoid division by zero
        density = defect_count / max(segment_length, 0.1)
        # Convert density to 0-100 scale (5 defects/km = 100), cap at 100
        density_score = min(100, density * 20)  # Cap at 100
        
        # Age score (older defects = higher priority for repair)
        # Extract age in days for each defect, default to 0
        ages = [d.get("age_days", 0) for d in defects]
        # Calculate average age across all defects, handle empty list
        avg_age_days = sum(ages) / len(ages) if ages else 0
        # Convert age to 0-100 scale (365 days = 100), cap at 100
        age_score = min(100, (avg_age_days / 365.0) * 100)  # 1 year = 100
        
        # Accessibility score (default 50 for now, can be enhanced with GIS data)
        accessibility_score = 50.0
        
        # Calculate total priority using weighted algorithm
        # Call the calculate_priority_score method with all components
        total_priority = PriorityService.calculate_priority_score(
            # Pass severity component
            severity_score=severity_score,
            # Pass traffic component
            traffic_score=traffic_score,
            # Pass density component
            density_score=density_score,
            # Pass age component
            age_score=age_score,
            # Pass accessibility component
            accessibility_score=accessibility_score
        )
        
        # Get priority level classification from the score
        priority_level = PriorityService.get_priority_level(total_priority)
        
        # Estimate cost and duration for maintenance planning
        # Calculate estimated maintenance cost
        estimated_cost = PriorityService.estimate_cost(
            # Pass number of defects
            defect_count=defect_count,
            # Pass average severity
            avg_severity=avg_severity,
            # Pass road type
            road_type=road_type
        )
        
        # Calculate estimated time needed for repairs
        estimated_duration = PriorityService.estimate_duration(
            # Pass number of defects
            defect_count=defect_count,
            # Pass road type
            road_type=road_type
        )
        
        # Check if priority score already exists in database
        # Execute query to find existing priority score for this segment
        result = await db.execute(
            # Select PriorityScore where segment_id matches
            select(PriorityScore).where(PriorityScore.segment_id == segment_id)
        )
        # Get first result or None if not found
        existing = result.scalar_one_or_none()
        
        # Branch based on whether record exists
        if existing:
            # Update existing record with new calculations
            # Update severity component
            existing.severity_score = severity_score
            # Update traffic component
            existing.traffic_score = traffic_score
            # Update density component
            existing.density_score = density_score
            # Update age component
            existing.age_score = age_score
            # Update accessibility component
            existing.accessibility_score = accessibility_score
            # Update total priority score
            existing.total_priority_score = total_priority
            # Update priority level classification
            existing.priority_level = priority_level
            # Update defect count
            existing.defect_count = defect_count
            # Update average severity
            existing.avg_severity = avg_severity
            # Update max severity
            existing.max_severity = max_severity
            # Update cost estimate
            existing.estimated_cost = estimated_cost
            # Update duration estimate
            existing.estimated_duration_days = estimated_duration
            # Set updated timestamp to now
            existing.updated_at = datetime.utcnow()
            # Set calculation timestamp to now
            existing.calculated_at = datetime.utcnow()
            # Use existing record as return value
            priority_score = existing
        else:
            # Create new priority score record
            # Instantiate new PriorityScore model
            priority_score = PriorityScore(
                # Set segment ID
                segment_id=segment_id,
                # Set severity score
                severity_score=severity_score,
                # Set traffic score
                # Set traffic score
                traffic_score=traffic_score,
                # Set density score
                density_score=density_score,
                # Set age score
                age_score=age_score,
                # Set accessibility score
                accessibility_score=accessibility_score,
                # Set total priority score
                total_priority_score=total_priority,
                # Set priority level
                priority_level=priority_level,
                # Set defect count
                defect_count=defect_count,
                # Set average severity
                avg_severity=avg_severity,
                # Set max severity
                max_severity=max_severity,
                # Set road name from first defect or "Unknown"
                road_name=defects[0].get("road_name", "Unknown"),
                # Set road type
                road_type=road_type,
                # Set estimated cost
                estimated_cost=estimated_cost,
                # Set estimated duration in days
                estimated_duration_days=estimated_duration
            )
            # Add new record to database session
            db.add(priority_score)
        
        # Commit transaction to save changes to database
        await db.commit()
        # Refresh object to get any database-generated values
        await db.refresh(priority_score)
        
        # Return the priority score record (either updated or newly created)
        return priority_score
    
    # Static method to get prioritized list of segments
    @staticmethod
    # Async method requiring database access
    async def get_priority_list(
        # Database session
        db: AsyncSession,
        # Optional minimum priority filter
        min_priority: Optional[float] = None,
        # Optional priority level filter (CRITICAL, HIGH, MEDIUM, LOW)
        priority_level: Optional[str] = None,
        # Maximum number of results to return
        limit: int = 100
    # Returns list of PriorityScore objects
    ) -> List[PriorityScore]:
        # """Get prioritized list of road segments."""
        
        # Build query selecting all PriorityScore records
        # Order by total_priority_score in descending order (highest first)
        query = select(PriorityScore).order_by(desc(PriorityScore.total_priority_score))
        
        # If minimum priority filter provided
        if min_priority is not None:
            # Add WHERE clause to filter by minimum score
            query = query.where(PriorityScore.total_priority_score >= min_priority)
        
        # If priority level filter provided
        if priority_level:
            # Add WHERE clause to filter by priority level
            query = query.where(PriorityScore.priority_level == priority_level)
        
        # Limit number of results
        query = query.limit(limit)
        
        # Execute the query
        result = await db.execute(query)
        # Return all results as a list
        return result.scalars().all()
    
    # Static method to get overall statistics
    @staticmethod
    # Async method requiring database access
    async def get_statistics(db: AsyncSession) -> dict:
        # """Get priority statistics."""
        
        # Total segments section
        # Build query to count all priority score records
        total_query = select(func.count(PriorityScore.id))
        # Execute count query
        total_result = await db.execute(total_query)
        # Extract scalar result (single number)
        total = total_result.scalar()
        
        # By priority level section - count each priority level
        # Query to count CRITICAL priority segments
        critical_query = select(func.count(PriorityScore.id)).where(
            # Filter for CRITICAL level
            # Filter for CRITICAL level
            PriorityScore.priority_level == "CRITICAL"
        )
        # Execute query for CRITICAL count
        critical_result = await db.execute(critical_query)
        # Get CRITICAL count
        critical = critical_result.scalar()
        
        # Query to count HIGH priority segments
        high_query = select(func.count(PriorityScore.id)).where(
            # Filter for HIGH level
            PriorityScore.priority_level == "HIGH"
        )
        # Execute query for HIGH count
        high_result = await db.execute(high_query)
        # Get HIGH count
        high = high_result.scalar()
        
        # Query to count MEDIUM priority segments
        medium_query = select(func.count(PriorityScore.id)).where(
            # Filter for MEDIUM level
            PriorityScore.priority_level == "MEDIUM"
        )
        # Execute query for MEDIUM count
        medium_result = await db.execute(medium_query)
        # Get MEDIUM count
        medium = medium_result.scalar()
        
        # Query to count LOW priority segments
        low_query = select(func.count(PriorityScore.id)).where(
            # Filter for LOW level
            PriorityScore.priority_level == "LOW"
        )
        # Execute query for LOW count
        low_result = await db.execute(low_query)
        # Get LOW count
        low = low_result.scalar()
        
        # Total estimated cost section
        # Build query to sum all estimated costs
        cost_query = select(func.sum(PriorityScore.estimated_cost))
        # Execute sum query
        cost_result = await db.execute(cost_query)
        # Get total cost, default to 0.0 if None (no records)
        total_cost = cost_result.scalar() or 0.0
        
        # Total defects section
        # Build query to sum all defect counts
        defects_query = select(func.sum(PriorityScore.defect_count))
        # Execute sum query
        defects_result = await db.execute(defects_query)
        # Get total defects, default to 0 if None (no records)
        total_defects = defects_result.scalar() or 0
        
        # Build and return statistics dictionary
        return {
            # Total number of segments with priority scores
            "total_segments": total or 0,
            # Breakdown by priority level
            "by_priority_level": {
                # Number of CRITICAL priority segments
                "critical": critical or 0,
                # Number of HIGH priority segments
                "high": high or 0,
                # Number of MEDIUM priority segments
                "medium": medium or 0,
                # Number of LOW priority segments
                "low": low or 0
            },
            # Total number of defects across all segments
            "total_defects": total_defects,
            # Total estimated cost for all repairs
            "total_estimated_cost": round(total_cost, 2),
            # Average priority score across all segments
            "avg_priority_score": round(
                # Execute query to get average priority score
                (await db.execute(select(func.avg(PriorityScore.total_priority_score)))).scalar() or 0.0,
                # Round to 2 decimal places
                2
            )
        }
