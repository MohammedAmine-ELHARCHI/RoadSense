"""API routes for video ingestion"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional
import uuid
from datetime import datetime
import logging

from app.database.connection import database
from app.database.models import Video, Frame, ProcessingStatus
from app.storage.minio_client import storage
from app.services.video_processor import VideoProcessor
from app.core.config import settings
from sqlalchemy import select

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload")
async def upload_video(
    video: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """Upload a video for processing"""
    
    # Validate file format
    file_ext = video.filename.split('.')[-1].lower()
    if file_ext not in settings.supported_formats_list:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video format. Supported: {settings.SUPPORTED_VIDEO_FORMATS}"
        )
    
    # Read video data
    video_data = await video.read()
    file_size = len(video_data)
    
    # Check file size
    max_size = settings.MAX_VIDEO_SIZE_MB * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"Video too large. Max size: {settings.MAX_VIDEO_SIZE_MB}MB"
        )
    
    try:
        # Generate unique ID and filename
        video_id = uuid.uuid4()
        storage_filename = f"{video_id}.{file_ext}"
        
        # Upload to MinIO
        storage_path = await storage.upload_video(video_data, storage_filename)
        
        # Create database record
        async with database.get_session() as session:
            video_record = Video(
                id=video_id,
                filename=storage_filename,
                original_filename=video.filename,
                file_size=file_size,
                storage_path=storage_path,
                status=ProcessingStatus.PENDING,
                uploaded_at=datetime.utcnow()
            )
            session.add(video_record)
            await session.commit()
            
            # Start processing in background
            if background_tasks:
                background_tasks.add_task(
                    process_video_task,
                    video_id=str(video_id),
                    video_data=video_data
                )
        
        return {
            "video_id": str(video_id),
            "filename": video.filename,
            "file_size": file_size,
            "status": "uploaded",
            "message": "Video uploaded successfully. Processing started."
        }
        
    except Exception as e:
        logger.error(f"Error uploading video: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_video_task(video_id: str, video_data: bytes):
    """Background task to process video"""
    try:
        async with database.get_session() as session:
            result = await VideoProcessor.process_video(
                video_id=video_id,
                video_data=video_data,
                db_session=session
            )
            logger.info(f"Video {video_id} processed: {result}")
    except Exception as e:
        logger.error(f"Error in background processing for video {video_id}: {e}")


@router.get("/status/{video_id}")
async def get_video_status(video_id: str):
    """Get video processing status"""
    
    try:
        async with database.get_session() as session:
            result = await session.execute(
                select(Video).where(Video.id == video_id)
            )
            video = result.scalar_one_or_none()
            
            if not video:
                raise HTTPException(status_code=404, detail="Video not found")
            
            return {
                "video_id": str(video.id),
                "filename": video.original_filename,
                "status": video.status.value,
                "frames_extracted": video.frames_extracted,
                "frames_total": video.frames_total,
                "duration": video.duration,
                "fps": video.fps,
                "uploaded_at": video.uploaded_at.isoformat() if video.uploaded_at else None,
                "processing_started_at": video.processing_started_at.isoformat() if video.processing_started_at else None,
                "processing_completed_at": video.processing_completed_at.isoformat() if video.processing_completed_at else None,
                "error_message": video.error_message
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{video_id}/frames")
async def get_video_frames(
    video_id: str,
    limit: int = 100,
    offset: int = 0
):
    """Get frames extracted from a video"""
    
    try:
        async with database.get_session() as session:
            # Check if video exists
            video_result = await session.execute(
                select(Video).where(Video.id == video_id)
            )
            video = video_result.scalar_one_or_none()
            
            if not video:
                raise HTTPException(status_code=404, detail="Video not found")
            
            # Get frames
            frames_result = await session.execute(
                select(Frame)
                .where(Frame.video_id == video_id)
                .order_by(Frame.frame_number)
                .limit(limit)
                .offset(offset)
            )
            frames = frames_result.scalars().all()
            
            frames_data = []
            for frame in frames:
                # Generate presigned URL
                bucket, object_name = frame.storage_path.split('/', 1)
                frame_url = await storage.get_presigned_url(bucket, object_name, expires_seconds=3600)
                
                frames_data.append({
                    "frame_id": str(frame.id),
                    "frame_number": frame.frame_number,
                    "timestamp": frame.timestamp,
                    "url": frame_url,
                    "detection_completed": frame.detection_completed,
                    "extracted_at": frame.extracted_at.isoformat()
                })
            
            return {
                "video_id": video_id,
                "total_frames": video.frames_extracted,
                "frames": frames_data,
                "limit": limit,
                "offset": offset
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting frames: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{video_id}")
async def delete_video(video_id: str):
    """Delete a video and its frames"""
    
    try:
        async with database.get_session() as session:
            # Get video
            result = await session.execute(
                select(Video).where(Video.id == video_id)
            )
            video = result.scalar_one_or_none()
            
            if not video:
                raise HTTPException(status_code=404, detail="Video not found")
            
            # Delete frames from database
            frames_result = await session.execute(
                select(Frame).where(Frame.video_id == video_id)
            )
            frames = frames_result.scalars().all()
            
            for frame in frames:
                await session.delete(frame)
            
            # Delete video from database
            await session.delete(video)
            await session.commit()
            
            return {
                "message": "Video and frames deleted successfully",
                "video_id": video_id,
                "frames_deleted": len(frames)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting video: {e}")
        raise HTTPException(status_code=500, detail=str(e))
