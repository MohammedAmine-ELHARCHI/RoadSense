import os
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database.connection import get_db
from app.services.export_service import ExportService
from app.core.config import settings

router = APIRouter()


# Request models
class ExportFilters(BaseModel):
    """Filters for export"""
    priority_level: Optional[str] = Field(None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    defect_type: Optional[str] = Field(None, description="Defect type (D00, D10, etc.)")
    min_severity: Optional[float] = Field(None, ge=0, le=10)
    segment_id: Optional[int] = Field(None, description="Specific road segment")
    use_matched_location: bool = Field(True, description="Use map-matched coordinates")


@router.post("/geojson", summary="Export to GeoJSON")
async def export_geojson(
    filters: ExportFilters,
    db: AsyncSession = Depends(get_db)
):
    """
    Export georeferenced defects to GeoJSON format.
    
    Returns a download link for the generated file.
    """
    # Fetch defects
    defects = await ExportService.get_defects_data(db, filters.dict(exclude_none=True, exclude={"use_matched_location"}))
    
    if not defects:
        raise HTTPException(status_code=404, detail="No defects found matching filters")
    
    # Generate filename
    filename = f"defects_{uuid.uuid4().hex[:8]}.geojson"
    output_path = os.path.join(settings.EXPORT_DIR, filename)
    
    # Export
    ExportService.export_to_geojson(defects, output_path, filters.use_matched_location)
    
    return {
        "format": "geojson",
        "filename": filename,
        "download_url": f"/exports/{filename}",
        "count": len(defects),
        "file_size_mb": round(os.path.getsize(output_path) / 1024 / 1024, 2)
    }


@router.get("/geojson/download", summary="Download GeoJSON file")
async def download_geojson(
    filename: str = Query(..., description="Filename to download")
):
    """Download a previously generated GeoJSON file."""
    file_path = os.path.join(settings.EXPORT_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type="application/geo+json",
        filename=filename
    )


@router.post("/shapefile", summary="Export to Shapefile")
async def export_shapefile(
    filters: ExportFilters,
    db: AsyncSession = Depends(get_db)
):
    """
    Export georeferenced defects to ESRI Shapefile format.
    
    Returns a download link for the generated shapefile.
    """
    # Fetch defects
    defects = await ExportService.get_defects_data(db, filters.dict(exclude_none=True, exclude={"use_matched_location"}))
    
    if not defects:
        raise HTTPException(status_code=404, detail="No defects found matching filters")
    
    # Generate filename (without extension)
    base_filename = f"defects_{uuid.uuid4().hex[:8]}"
    output_path = os.path.join(settings.EXPORT_DIR, base_filename)
    
    # Export
    shapefile_path = ExportService.export_to_shapefile(defects, output_path, filters.use_matched_location)
    
    # Shapefile creates multiple files (.shp, .shx, .dbf, .prj)
    shp_filename = os.path.basename(shapefile_path)
    
    return {
        "format": "shapefile",
        "filename": shp_filename,
        "download_url": f"/exports/{shp_filename}",
        "count": len(defects),
        "note": "Shapefile includes .shp, .shx, .dbf, and .prj files"
    }


@router.post("/kml", summary="Export to KML")
async def export_kml(
    filters: ExportFilters,
    db: AsyncSession = Depends(get_db)
):
    """
    Export georeferenced defects to KML format (Google Earth compatible).
    
    Returns a download link for the generated file.
    """
    # Fetch defects
    defects = await ExportService.get_defects_data(db, filters.dict(exclude_none=True, exclude={"use_matched_location"}))
    
    if not defects:
        raise HTTPException(status_code=404, detail="No defects found matching filters")
    
    # Generate filename
    filename = f"defects_{uuid.uuid4().hex[:8]}.kml"
    output_path = os.path.join(settings.EXPORT_DIR, filename)
    
    # Export
    ExportService.export_to_kml(defects, output_path, filters.use_matched_location)
    
    return {
        "format": "kml",
        "filename": filename,
        "download_url": f"/exports/{filename}",
        "count": len(defects),
        "file_size_mb": round(os.path.getsize(output_path) / 1024 / 1024, 2)
    }


@router.post("/csv", summary="Export to CSV")
async def export_csv(
    filters: ExportFilters,
    db: AsyncSession = Depends(get_db)
):
    """
    Export georeferenced defects to CSV format.
    
    Returns a download link for the generated file.
    """
    # Fetch defects
    defects = await ExportService.get_defects_data(db, filters.dict(exclude_none=True, exclude={"use_matched_location"}))
    
    if not defects:
        raise HTTPException(status_code=404, detail="No defects found matching filters")
    
    # Generate filename
    filename = f"defects_{uuid.uuid4().hex[:8]}.csv"
    output_path = os.path.join(settings.EXPORT_DIR, filename)
    
    # Export
    ExportService.export_to_csv(defects, output_path)
    
    return {
        "format": "csv",
        "filename": filename,
        "download_url": f"/exports/{filename}",
        "count": len(defects),
        "file_size_mb": round(os.path.getsize(output_path) / 1024 / 1024, 2)
    }


@router.get("/formats", summary="List supported export formats")
async def get_supported_formats():
    """Get list of supported export formats and their details."""
    return {
        "formats": [
            {
                "name": "GeoJSON",
                "extension": ".geojson",
                "mime_type": "application/geo+json",
                "description": "JSON-based geospatial data format, web-friendly",
                "supports_styling": False,
                "use_cases": ["Web mapping", "JavaScript libraries", "APIs"]
            },
            {
                "name": "Shapefile",
                "extension": ".shp",
                "mime_type": "application/x-shapefile",
                "description": "ESRI Shapefile format, industry standard for GIS",
                "supports_styling": True,
                "use_cases": ["ArcGIS", "QGIS", "Desktop GIS software"]
            },
            {
                "name": "KML",
                "extension": ".kml",
                "mime_type": "application/vnd.google-earth.kml+xml",
                "description": "Keyhole Markup Language for Google Earth",
                "supports_styling": True,
                "use_cases": ["Google Earth", "Google Maps", "Visualization"]
            },
            {
                "name": "CSV",
                "extension": ".csv",
                "mime_type": "text/csv",
                "description": "Comma-separated values with coordinates",
                "supports_styling": False,
                "use_cases": ["Excel", "Data analysis", "Import/Export"]
            }
        ],
        "coordinate_system": settings.DEFAULT_COORDINATE_SYSTEM,
        "max_export_size_mb": settings.MAX_EXPORT_SIZE_MB
    }


@router.get("/stats", summary="Get export statistics")
async def get_export_stats():
    """Get statistics about exported files."""
    export_dir = settings.EXPORT_DIR
    
    if not os.path.exists(export_dir):
        return {"total_files": 0, "total_size_mb": 0.0}
    
    files = os.listdir(export_dir)
    total_size = sum(os.path.getsize(os.path.join(export_dir, f)) for f in files if os.path.isfile(os.path.join(export_dir, f)))
    
    # Count by format
    format_counts = {
        "geojson": len([f for f in files if f.endswith('.geojson')]),
        "shapefile": len([f for f in files if f.endswith('.shp')]),
        "kml": len([f for f in files if f.endswith('.kml')]),
        "csv": len([f for f in files if f.endswith('.csv')])
    }
    
    return {
        "total_files": len(files),
        "total_size_mb": round(total_size / 1024 / 1024, 2),
        "by_format": format_counts,
        "export_directory": export_dir
    }
