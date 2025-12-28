import json
import os
import logging
from typing import List, Optional, Dict
from datetime import datetime
import geopandas as gpd
from shapely.geometry import Point
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting georeferenced defects to various GIS formats."""
    
    @staticmethod
    async def get_defects_data(
        db: AsyncSession,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Fetch georeferenced defects with filters.
        
        Args:
            db: Database session
            filters: Optional filters (priority_level, defect_type, date_range, etc.)
            
        Returns:
            List of defect dictionaries
        """
        where_clauses = []
        params = {}
        
        if filters:
            if filters.get("priority_level"):
                where_clauses.append("ps.priority_level = :priority_level")
                params["priority_level"] = filters["priority_level"]
            
            if filters.get("defect_type"):
                where_clauses.append("gd.defect_type = :defect_type")
                params["defect_type"] = filters["defect_type"]
            
            if filters.get("min_severity"):
                where_clauses.append("gd.severity_score >= :min_severity")
                params["min_severity"] = filters["min_severity"]
            
            if filters.get("segment_id"):
                where_clauses.append("gd.segment_id = :segment_id")
                params["segment_id"] = filters["segment_id"]
        
        where_clause = " AND " + " AND ".join(where_clauses) if where_clauses else ""
        
        query = text(f"""
            SELECT 
                gd.id,
                gd.detection_id,
                gd.segment_id,
                gd.gps_latitude,
                gd.gps_longitude,
                gd.matched_latitude,
                gd.matched_longitude,
                gd.distance_to_road,
                gd.confidence,
                gd.heading,
                gd.defect_type,
                gd.severity_score,
                gd.created_at,
                rs.name as road_name,
                rs.road_type,
                ps.total_priority_score,
                ps.priority_level,
                ps.estimated_cost
            FROM georeferenced_defects gd
            LEFT JOIN road_segments rs ON gd.segment_id = rs.id
            LEFT JOIN priority_scores ps ON gd.segment_id = ps.segment_id
            WHERE 1=1 {where_clause}
            ORDER BY gd.created_at DESC
        """)
        
        result = await db.execute(query, params)
        rows = result.fetchall()
        
        defects = []
        for row in rows:
            defects.append({
                "id": str(row.id),
                "detection_id": str(row.detection_id),
                "segment_id": row.segment_id,
                "gps_latitude": row.gps_latitude,
                "gps_longitude": row.gps_longitude,
                "matched_latitude": row.matched_latitude,
                "matched_longitude": row.matched_longitude,
                "distance_to_road": row.distance_to_road,
                "confidence": row.confidence,
                "heading": row.heading,
                "defect_type": row.defect_type,
                "severity_score": row.severity_score,
                "road_name": row.road_name,
                "road_type": row.road_type,
                "priority_score": row.total_priority_score,
                "priority_level": row.priority_level,
                "estimated_cost": row.estimated_cost,
                "created_at": row.created_at.isoformat() if row.created_at else None
            })
        
        return defects
    
    @staticmethod
    def export_to_geojson(
        defects: List[Dict],
        output_path: str,
        use_matched_location: bool = True
    ) -> str:
        """
        Export defects to GeoJSON format.
        
        Args:
            defects: List of defect dictionaries
            output_path: Path to save the GeoJSON file
            use_matched_location: Use matched coordinates instead of GPS
            
        Returns:
            Path to the created file
        """
        features = []
        
        for defect in defects:
            # Choose coordinates
            if use_matched_location and defect.get("matched_latitude"):
                lon = defect["matched_longitude"]
                lat = defect["matched_latitude"]
            else:
                lon = defect["gps_longitude"]
                lat = defect["gps_latitude"]
            
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [round(lon, settings.GEOJSON_PRECISION), 
                                   round(lat, settings.GEOJSON_PRECISION)]
                },
                "properties": {
                    "id": defect["id"],
                    "detection_id": defect["detection_id"],
                    "segment_id": defect["segment_id"],
                    "defect_type": defect["defect_type"],
                    "severity_score": defect["severity_score"],
                    "confidence": defect["confidence"],
                    "distance_to_road": defect["distance_to_road"],
                    "heading": defect["heading"],
                    "road_name": defect["road_name"],
                    "road_type": defect["road_type"],
                    "priority_score": defect["priority_score"],
                    "priority_level": defect["priority_level"],
                    "estimated_cost": defect["estimated_cost"],
                    "created_at": defect["created_at"]
                }
            }
            features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "crs": {
                "type": "name",
                "properties": {"name": settings.DEFAULT_COORDINATE_SYSTEM}
            },
            "features": features,
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "total_features": len(features),
                "coordinate_system": settings.DEFAULT_COORDINATE_SYSTEM
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(geojson, f, indent=2)
        
        logger.info(f"Exported {len(features)} defects to GeoJSON: {output_path}")
        return output_path
    
    @staticmethod
    def export_to_shapefile(
        defects: List[Dict],
        output_path: str,
        use_matched_location: bool = True
    ) -> str:
        """
        Export defects to Shapefile format.
        
        Args:
            defects: List of defect dictionaries
            output_path: Path to save the shapefile (without .shp extension)
            use_matched_location: Use matched coordinates instead of GPS
            
        Returns:
            Path to the created file
        """
        # Prepare data for GeoDataFrame
        geometries = []
        properties_list = []
        
        for defect in defects:
            # Choose coordinates
            if use_matched_location and defect.get("matched_latitude"):
                lon = defect["matched_longitude"]
                lat = defect["matched_latitude"]
            else:
                lon = defect["gps_longitude"]
                lat = defect["gps_latitude"]
            
            geometries.append(Point(lon, lat))
            
            # Shapefile column names limited to 10 characters
            properties = {
                "id": defect["id"][:36],
                "detect_id": defect["detection_id"][:36],
                "segment_id": defect["segment_id"],
                "defect_typ": defect["defect_type"][:10] if defect["defect_type"] else None,
                "severity": defect["severity_score"],
                "confidence": defect["confidence"],
                "dist_road": defect["distance_to_road"],
                "heading": defect["heading"],
                "road_name": defect["road_name"][:50] if defect["road_name"] else None,
                "road_type": defect["road_type"][:20] if defect["road_type"] else None,
                "priority": defect["priority_score"],
                "prior_lvl": defect["priority_level"][:10] if defect["priority_level"] else None,
                "est_cost": defect["estimated_cost"],
                "created_at": defect["created_at"][:19] if defect["created_at"] else None
            }
            properties_list.append(properties)
        
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(properties_list, geometry=geometries, crs=settings.DEFAULT_COORDINATE_SYSTEM)
        
        # Export to shapefile
        shapefile_path = output_path if output_path.endswith('.shp') else f"{output_path}.shp"
        gdf.to_file(shapefile_path, driver='ESRI Shapefile')
        
        logger.info(f"Exported {len(defects)} defects to Shapefile: {shapefile_path}")
        return shapefile_path
    
    @staticmethod
    def export_to_kml(
        defects: List[Dict],
        output_path: str,
        use_matched_location: bool = True
    ) -> str:
        """
        Export defects to KML format for Google Earth.
        
        Args:
            defects: List of defect dictionaries
            output_path: Path to save the KML file
            use_matched_location: Use matched coordinates instead of GPS
            
        Returns:
            Path to the created file
        """
        kml_header = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Road Defects</name>
    <description>Georeferenced road defects from RoadSense</description>
    
    <!-- Styles for priority levels -->
    <Style id="critical">
      <IconStyle>
        <color>ff0000ff</color>
        <scale>1.2</scale>
        <Icon><href>http://maps.google.com/mapfiles/kml/paddle/red-circle.png</href></Icon>
      </IconStyle>
    </Style>
    <Style id="high">
      <IconStyle>
        <color>ff0099ff</color>
        <scale>1.0</scale>
        <Icon><href>http://maps.google.com/mapfiles/kml/paddle/orange-circle.png</href></Icon>
      </IconStyle>
    </Style>
    <Style id="medium">
      <IconStyle>
        <color>ff00ffff</color>
        <scale>0.9</scale>
        <Icon><href>http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png</href></Icon>
      </IconStyle>
    </Style>
    <Style id="low">
      <IconStyle>
        <color>ff00ff00</color>
        <scale>0.8</scale>
        <Icon><href>http://maps.google.com/mapfiles/kml/paddle/grn-circle.png</href></Icon>
      </IconStyle>
    </Style>
"""
        
        placemarks = []
        for defect in defects:
            # Choose coordinates
            if use_matched_location and defect.get("matched_latitude"):
                lon = defect["matched_longitude"]
                lat = defect["matched_latitude"]
            else:
                lon = defect["gps_longitude"]
                lat = defect["gps_latitude"]
            
            priority_level = (defect.get("priority_level") or "low").lower()
            
            description = f"""
            <![CDATA[
            <b>Defect Type:</b> {defect['defect_type']}<br/>
            <b>Severity:</b> {defect['severity_score']}/10<br/>
            <b>Priority:</b> {defect['priority_level']} ({defect['priority_score']:.1f})<br/>
            <b>Road:</b> {defect['road_name']} ({defect['road_type']})<br/>
            <b>Confidence:</b> {defect['confidence']:.2f}<br/>
            <b>Distance to Road:</b> {defect['distance_to_road']:.1f}m<br/>
            <b>Estimated Cost:</b> ${defect['estimated_cost']:.2f}<br/>
            <b>Created:</b> {defect['created_at']}<br/>
            ]]>
            """
            
            placemark = f"""
    <Placemark>
      <name>{defect['defect_type']} - {defect['road_name']}</name>
      <description>{description}</description>
      <styleUrl>#{priority_level}</styleUrl>
      <Point>
        <coordinates>{lon},{lat},0</coordinates>
      </Point>
    </Placemark>"""
            placemarks.append(placemark)
        
        kml_footer = """
  </Document>
</kml>"""
        
        kml_content = kml_header + "\n".join(placemarks) + kml_footer
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(kml_content)
        
        logger.info(f"Exported {len(defects)} defects to KML: {output_path}")
        return output_path
    
    @staticmethod
    def export_to_csv(
        defects: List[Dict],
        output_path: str
    ) -> str:
        """
        Export defects to CSV format.
        
        Args:
            defects: List of defect dictionaries
            output_path: Path to save the CSV file
            
        Returns:
            Path to the created file
        """
        import csv
        
        if not defects:
            logger.warning("No defects to export to CSV")
            return output_path
        
        # Define CSV columns
        columns = [
            "id", "detection_id", "segment_id", "defect_type", "severity_score",
            "gps_latitude", "gps_longitude", "matched_latitude", "matched_longitude",
            "distance_to_road", "confidence", "heading", "road_name", "road_type",
            "priority_score", "priority_level", "estimated_cost", "created_at"
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            
            for defect in defects:
                row = {col: defect.get(col, "") for col in columns}
                writer.writerow(row)
        
        logger.info(f"Exported {len(defects)} defects to CSV: {output_path}")
        return output_path
