from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid
import cv2
import numpy as np
import time
from datetime import datetime

from app.schemas import DetectionResponse, DetectionRequest
from app.database.connection import get_db
from app.database.models import DetectionResult as DBDetectionResult, Defect
from app.models.detector import detector
from app.storage.minio_client import storage
from app.config import settings

router = APIRouter()

@router.on_event("startup")
async def startup_event():
    """Load models on startup"""
    await detector.load_models()
    await storage.connect()

@router.post("/detect", response_model=DetectionResponse)
async def detect_defects(
    image: UploadFile = File(..., description="Image file to analyze"),
    confidence_threshold: float = Form(0.15, ge=0.0, le=1.0),
    return_masks: bool = Form(True),
    save_annotated: bool = Form(True),
    db: AsyncSession = Depends(get_db)
):
    """
    Detect road defects in an uploaded image
    
    - **image**: Image file (JPEG, PNG)
    - **confidence_threshold**: Minimum confidence for detections (0.0-1.0)
    - **return_masks**: Whether to return segmentation masks
    - **save_annotated**: Whether to save annotated image to MinIO
    """
    start_time = time.time()
    
    try:
        # Read image
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Generate unique image ID
        image_id = str(uuid.uuid4())
        
        # Detect defects
        detections = detector.detect_defects(
            img,
            confidence_threshold=confidence_threshold,
            return_masks=return_masks
        )
        
        # Save annotated image if requested
        annotated_image_url = None
        if save_annotated and len(detections) > 0:
            annotated_img = detector.draw_detections(img, detections)
            _, buffer = cv2.imencode('.jpg', annotated_img)
            annotated_bytes = buffer.tobytes()
            
            object_name = f"{image_id}_annotated.jpg"
            await storage.upload_image(
                "annotated-images",
                object_name,
                annotated_bytes
            )
            
            # Generate presigned URL
            annotated_image_url = await storage.get_presigned_url(
                "annotated-images",
                object_name
            )
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Save to database
        db_detection = DBDetectionResult(
            image_id=image_id,
            frame_path=None,
            annotated_image_path=annotated_image_url,
            total_defects=len(detections),
            detection_timestamp=datetime.utcnow(),
            model_version=detector.model_version,
            processing_time_ms=processing_time_ms
        )
        
        db.add(db_detection)
        await db.flush()
        
        # Save defects
        for det in detections:
            db_defect = Defect(
                detection_result_id=db_detection.id,
                class_name=det["class_name"],
                confidence=det["confidence"],
                bbox_x_min=det["bounding_box"]["x_min"],
                bbox_y_min=det["bounding_box"]["y_min"],
                bbox_x_max=det["bounding_box"]["x_max"],
                bbox_y_max=det["bounding_box"]["y_max"],
                area_pixels=det["area_pixels"],
                mask_path=None
            )
            db.add(db_defect)
        
        await db.commit()
        
        # Prepare response
        response = DetectionResponse(
            image_id=image_id,
            detections=detections,
            processing_time_ms=processing_time_ms,
            model_version=detector.model_version,
            annotated_image_url=annotated_image_url
        )
        
        return response
        
    except Exception as e:
        await db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

@router.post("/detect/batch", response_model=List[DetectionResponse])
async def detect_batch(
    images: List[UploadFile] = File(..., description="Multiple image files"),
    confidence_threshold: float = Form(0.5),
    db: AsyncSession = Depends(get_db)
):
    """
    Batch detection for multiple images
    
    - **images**: List of image files
    - **confidence_threshold**: Minimum confidence for detections
    """
    results = []
    
    for image in images:
        try:
            result = await detect_defects(
                image=image,
                confidence_threshold=confidence_threshold,
                return_masks=False,
                save_annotated=True,
                db=db
            )
            results.append(result)
        except Exception as e:
            print(f"Error processing {image.filename}: {e}")
            continue
    
    return results

@router.get("/results/{image_id}")
async def get_detection_results(
    image_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve previously computed detection results
    
    - **image_id**: Unique image identifier
    """
    try:
        from sqlalchemy import select
        from app.database.models import DetectionResult as DBDetectionResult, Defect
        
        # Query detection result
        stmt = select(DBDetectionResult).where(DBDetectionResult.image_id == image_id)
        result = await db.execute(stmt)
        detection = result.scalar_one_or_none()
        
        if not detection:
            raise HTTPException(status_code=404, detail="Detection result not found")
        
        # Query defects
        stmt = select(Defect).where(Defect.detection_result_id == detection.id)
        result = await db.execute(stmt)
        defects = result.scalars().all()
        
        # Format response
        detections_list = []
        for defect in defects:
            detections_list.append({
                "class_name": defect.class_name,
                "confidence": defect.confidence,
                "bounding_box": {
                    "x_min": defect.bbox_x_min,
                    "y_min": defect.bbox_y_min,
                    "x_max": defect.bbox_x_max,
                    "y_max": defect.bbox_y_max
                },
                "area_pixels": defect.area_pixels,
                "mask": None
            })
        
        return {
            "image_id": detection.image_id,
            "detections": detections_list,
            "total_defects": detection.total_defects,
            "processing_time_ms": detection.processing_time_ms,
            "model_version": detection.model_version,
            "annotated_image_url": detection.annotated_image_path,
            "detection_timestamp": detection.detection_timestamp
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving results: {str(e)}")

@router.get("/stats")
async def get_detection_stats(db: AsyncSession = Depends(get_db)):
    """
    Get detection statistics
    """
    try:
        from sqlalchemy import select, func
        from app.database.models import DetectionResult as DBDetectionResult, Defect
        
        # Total detections
        stmt = select(func.count(DBDetectionResult.id))
        result = await db.execute(stmt)
        total_detections = result.scalar()
        
        # Total defects
        stmt = select(func.count(Defect.id))
        result = await db.execute(stmt)
        total_defects = result.scalar()
        
        # Defects by class
        stmt = select(
            Defect.class_name,
            func.count(Defect.id).label('count')
        ).group_by(Defect.class_name)
        result = await db.execute(stmt)
        defects_by_class = {row[0]: row[1] for row in result}
        
        # Average processing time
        stmt = select(func.avg(DBDetectionResult.processing_time_ms))
        result = await db.execute(stmt)
        avg_processing_time = result.scalar() or 0
        
        return {
            "total_detections": total_detections,
            "total_defects": total_defects,
            "defects_by_class": defects_by_class,
            "avg_processing_time_ms": float(avg_processing_time)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")
