"""Video processing service using FFmpeg"""
import ffmpeg
import cv2
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import tempfile
import os
from datetime import datetime

from app.core.config import settings
from app.storage.minio_client import storage
from app.database.models import Video, Frame, ProcessingStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)

class VideoProcessor:
    """Process videos and extract frames"""
    
    @staticmethod
    async def get_video_info(video_path: str) -> Dict:
        """Extract video metadata using FFmpeg"""
        try:
            probe = ffmpeg.probe(video_path)
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            
            return {
                'duration': float(probe['format']['duration']),
                'fps': eval(video_info['r_frame_rate']),
                'width': int(video_info['width']),
                'height': int(video_info['height']),
                'codec': video_info['codec_name'],
                'file_size': int(probe['format']['size'])
            }
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            raise
    
    @staticmethod
    async def extract_frames(
        video_id: str,
        video_path: str,
        fps: int = None,
        db_session: AsyncSession = None
    ) -> List[Dict]:
        """Extract frames from video at specified FPS"""
        
        extraction_fps = fps or settings.FRAME_EXTRACTION_FPS
        frames_data = []
        
        try:
            # Open video with OpenCV
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise ValueError(f"Cannot open video: {video_path}")
            
            video_fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Calculate frame interval
            frame_interval = int(video_fps / extraction_fps)
            
            logger.info(f"Extracting frames at {extraction_fps} FPS (interval: {frame_interval} frames)")
            
            frame_count = 0
            extracted_count = 0
            
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # Extract frame at interval
                if frame_count % frame_interval == 0:
                    timestamp = frame_count / video_fps
                    
                    # Encode frame as JPEG
                    success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    
                    if success:
                        frame_data = buffer.tobytes()
                        
                        # Generate unique filename
                        frame_filename = f"{video_id}/frame_{extracted_count:06d}_{timestamp:.2f}s.jpg"
                        
                        # Upload to MinIO
                        storage_path = await storage.upload_frame(frame_data, frame_filename)
                        
                        frame_info = {
                            'video_id': video_id,
                            'frame_number': extracted_count,
                            'timestamp': timestamp,
                            'storage_path': storage_path,
                            'file_size': len(frame_data)
                        }
                        
                        frames_data.append(frame_info)
                        
                        # Save to database if session provided
                        if db_session:
                            frame_record = Frame(**frame_info)
                            db_session.add(frame_record)
                        
                        extracted_count += 1
                        
                        if extracted_count % 10 == 0:
                            logger.info(f"Extracted {extracted_count} frames...")
                
                frame_count += 1
            
            cap.release()
            
            logger.info(f"✅ Extracted {extracted_count} frames from {total_frames} total frames")
            
            return frames_data
            
        except Exception as e:
            logger.error(f"Error extracting frames: {e}")
            raise
    
    @staticmethod
    async def process_video(
        video_id: str,
        video_data: bytes,
        db_session: AsyncSession
    ) -> Dict:
        """Complete video processing pipeline"""
        
        # Update status to processing
        result = await db_session.execute(
            select(Video).where(Video.id == video_id)
        )
        video = result.scalar_one_or_none()
        
        if not video:
            raise ValueError(f"Video {video_id} not found")
        
        video.status = ProcessingStatus.PROCESSING
        video.processing_started_at = datetime.utcnow()
        await db_session.commit()
        
        try:
            # Save video to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                tmp_file.write(video_data)
                tmp_path = tmp_file.name
            
            # Get video info
            video_info = await VideoProcessor.get_video_info(tmp_path)
            
            # Update video metadata
            video.duration = video_info['duration']
            video.fps = video_info['fps']
            video.width = video_info['width']
            video.height = video_info['height']
            video.codec = video_info['codec']
            
            # Calculate expected frames
            video.frames_total = int(video_info['duration'] * settings.FRAME_EXTRACTION_FPS)
            await db_session.commit()
            
            # Extract frames
            frames = await VideoProcessor.extract_frames(
                video_id=str(video_id),
                video_path=tmp_path,
                db_session=db_session
            )
            
            # Update video status
            video.status = ProcessingStatus.COMPLETED
            video.frames_extracted = len(frames)
            video.processing_completed_at = datetime.utcnow()
            await db_session.commit()
            
            # Cleanup temp file
            os.unlink(tmp_path)
            
            return {
                'video_id': str(video_id),
                'status': 'completed',
                'frames_extracted': len(frames),
                'duration': video_info['duration'],
                'fps': video_info['fps']
            }
            
        except Exception as e:
            logger.error(f"Error processing video {video_id}: {e}")
            
            # Update status to failed
            video.status = ProcessingStatus.FAILED
            video.error_message = str(e)
            await db_session.commit()
            
            raise
