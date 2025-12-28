"""Video processing service using FFmpeg"""
import ffmpeg
import cv2
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import tempfile
import os
import json
import subprocess
import shutil
from datetime import datetime

from app.core.config import settings
from app.storage.minio_client import storage
from app.database.models import Video, Frame, ProcessingStatus
from app.services.detection_client import detection_client
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
    async def detect_frames(
        video_id: str,
        db_session: AsyncSession
    ) -> Dict:
        """Run detection on all extracted frames"""
        
        try:
            # Get all frames for this video
            result = await db_session.execute(
                select(Frame)
                .where(Frame.video_id == video_id)
                .where(Frame.detection_completed == False)
                .order_by(Frame.frame_number)
            )
            frames = result.scalars().all()
            
            if not frames:
                logger.info("No frames to process")
                return {'frames_processed': 0, 'total_detections': 0}
            
            logger.info(f"Processing {len(frames)} frames through detection service...")
            
            total_detections = 0
            frames_with_detections = 0
            
            # Process frames in batches
            batch_size = 10
            for i in range(0, len(frames), batch_size):
                batch = frames[i:i + batch_size]
                
                # Download frame images from MinIO
                frames_data = []
                for frame in batch:
                    try:
                        bucket, object_name = frame.storage_path.split('/', 1)
                        frame_bytes = await storage.get_object(bucket, object_name)
                        frames_data.append((str(frame.id), frame_bytes))
                    except Exception as e:
                        logger.error(f"Error downloading frame {frame.id}: {e}")
                
                # Run detection on batch
                detection_results = await detection_client.detect_frame_batch(frames_data)
                
                # Update frames with detection results
                for result in detection_results:
                    frame_id = result['frame_id']
                    
                    # Find corresponding frame
                    frame = next((f for f in batch if str(f.id) == frame_id), None)
                    if not frame:
                        continue
                    
                    if result['success']:
                        detections = result.get('detections', [])
                        frame.detection_completed = True
                        frame.defects_count = len(detections)
                        total_detections += len(detections)
                        
                        if len(detections) > 0:
                            frames_with_detections += 1
                        
                        # Store detection data for video annotation
                        frame.detection_data = str(detections)  # Store as JSON string
                        
                        logger.info(
                            f"Frame {frame.frame_number}: {len(detections)} defects detected"
                        )
                    else:
                        logger.error(f"Detection failed for frame {frame_id}: {result.get('error')}")
                
                # Commit batch
                await db_session.commit()
                
                logger.info(
                    f"Processed {min(i + batch_size, len(frames))}/{len(frames)} frames"
                )
            
            logger.info(
                f"✅ Detection complete: {total_detections} defects found in "
                f"{frames_with_detections}/{len(frames)} frames"
            )
            
            return {
                'frames_processed': len(frames),
                'frames_with_detections': frames_with_detections,
                'total_detections': total_detections
            }
            
        except Exception as e:
            logger.error(f"Error detecting frames: {e}")
            raise
    
    @staticmethod
    async def create_annotated_video(
        video_id: str,
        db_session: AsyncSession
    ) -> str:
        """Create annotated video with detection bounding boxes"""
        import tempfile
        import json
        import shutil
        from pathlib import Path
        
        try:
            # Get video info
            result = await db_session.execute(
                select(Video).where(Video.id == video_id)
            )
            video = result.scalar_one_or_none()
            if not video:
                raise ValueError(f"Video {video_id} not found")
            
            # Get all frames with detection data
            result = await db_session.execute(
                select(Frame)
                .where(Frame.video_id == video_id)
                .order_by(Frame.frame_number)
            )
            frames = result.scalars().all()
            
            if not frames:
                logger.warning("No frames to annotate")
                return None
            
            logger.info(f"Creating annotated video from {len(frames)} frames...")
            
            # Create temp directory for annotated frames
            temp_dir = Path(tempfile.mkdtemp())
            
            try:
                # Process each frame
                for frame in frames:
                    # Download original frame
                    bucket, object_name = frame.storage_path.split('/', 1)
                    frame_bytes = await storage.get_object(bucket, object_name)
                    
                    # Convert to OpenCV image
                    nparr = np.frombuffer(frame_bytes, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    # Parse detection data
                    if frame.detection_data:
                        try:
                            detections = json.loads(frame.detection_data.replace("'", '"'))
                            
                            # Draw bounding boxes
                            for det in detections:
                                bbox = det.get('bounding_box', {})
                                x_min = int(bbox.get('x_min', 0))
                                y_min = int(bbox.get('y_min', 0))
                                x_max = int(bbox.get('x_max', 0))
                                y_max = int(bbox.get('y_max', 0))
                                
                                class_name = det.get('class_name', 'Unknown')
                                confidence = det.get('confidence', 0.0)
                                
                                # Draw rectangle
                                color = (0, 255, 0)  # Green
                                cv2.rectangle(img, (x_min, y_min), (x_max, y_max), color, 2)
                                
                                # Draw label
                                label = f"{class_name}: {confidence:.2f}"
                                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                                cv2.rectangle(
                                    img,
                                    (x_min, y_min - label_size[1] - 10),
                                    (x_min + label_size[0], y_min),
                                    color,
                                    -1
                                )
                                cv2.putText(
                                    img,
                                    label,
                                    (x_min, y_min - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5,
                                    (0, 0, 0),
                                    2
                                )
                        except Exception as e:
                            logger.error(f"Error parsing detection data for frame {frame.id}: {e}")
                    
                    # Save annotated frame
                    output_path = temp_dir / f"frame_{frame.frame_number:06d}.jpg"
                    cv2.imwrite(str(output_path), img)
                
                # Stitch frames into video with FFmpeg
                output_video = temp_dir / "annotated.mp4"
                fps = video.fps or 2
                
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-framerate', str(fps),
                    '-i', str(temp_dir / 'frame_%06d.jpg'),
                    '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p',
                    '-crf', '23',
                    '-y',
                    str(output_video)
                ]
                
                logger.info(f"Running FFmpeg: {' '.join(ffmpeg_cmd)}")
                result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    raise RuntimeError(f"FFmpeg failed: {result.stderr}")
                
                # Upload annotated video to MinIO
                with open(output_video, 'rb') as f:
                    video_bytes = f.read()
                
                object_name = f"{video_id}_annotated.mp4"
                annotated_path = await storage.upload_video(video_bytes, object_name)
                
                # Update video record
                video.annotated_video_path = annotated_path
                await db_session.commit()
                
                logger.info(f"✅ Annotated video created: {annotated_path}")
                return annotated_path
                
            finally:
                # Cleanup temp directory
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            logger.error(f"Error creating annotated video: {e}")
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
            
            # Commit frames to database
            await db_session.commit()
            
            logger.info(f"🔍 Starting defect detection on {len(frames)} frames...")
            
            # Run detection on extracted frames
            await VideoProcessor.detect_frames(
                video_id=str(video_id),
                db_session=db_session
            )
            
            logger.info(f"🎬 Creating annotated video with detection overlays...")
            
            # Create annotated video with bounding boxes
            annotated_path = await VideoProcessor.create_annotated_video(
                video_id=str(video_id),
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
