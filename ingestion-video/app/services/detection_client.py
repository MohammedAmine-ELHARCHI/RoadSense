"""Client for Detection Service API"""
import httpx
import logging
from typing import Dict, List, Optional
import asyncio

from app.core.config import settings

logger = logging.getLogger(__name__)

class DetectionClient:
    """Client to communicate with Detection Service"""
    
    def __init__(self):
        self.base_url = settings.DETECTION_SERVICE_URL
        self.timeout = 30.0
    
    async def detect_defects(self, image_bytes: bytes, confidence_threshold: float = 0.15) -> Dict:
        """
        Send image to detection service
        
        Args:
            image_bytes: Image data as bytes
            confidence_threshold: Minimum confidence for detections
            
        Returns:
            Detection results dictionary
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {'image': ('frame.jpg', image_bytes, 'image/jpeg')}
                data = {
                    'confidence_threshold': confidence_threshold,
                    'return_masks': False,
                    'save_annotated': False
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v1/detection/detect",
                    files=files,
                    data=data
                )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling detection service: {e}")
            raise
        except Exception as e:
            logger.error(f"Error calling detection service: {e}")
            raise
    
    async def detect_frame_batch(
        self, 
        frames_data: List[tuple],  # [(frame_id, image_bytes), ...]
        confidence_threshold: float = 0.15
    ) -> List[Dict]:
        """
        Detect defects in multiple frames (batch processing)
        
        Args:
            frames_data: List of (frame_id, image_bytes) tuples
            confidence_threshold: Minimum confidence for detections
            
        Returns:
            List of detection results for each frame
        """
        results = []
        
        for frame_id, image_bytes in frames_data:
            try:
                detection_result = await self.detect_defects(
                    image_bytes,
                    confidence_threshold
                )
                
                results.append({
                    'frame_id': frame_id,
                    'success': True,
                    'detections': detection_result.get('detections', []),
                    'detections_count': len(detection_result.get('detections', [])),
                    'processing_time_ms': detection_result.get('processing_time_ms', 0)
                })
                
                logger.info(
                    f"Frame {frame_id}: {len(detection_result.get('detections', []))} defects detected"
                )
                
                # Small delay to avoid overwhelming detection service
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error detecting defects in frame {frame_id}: {e}")
                results.append({
                    'frame_id': frame_id,
                    'success': False,
                    'error': str(e)
                })
        
        return results


# Singleton instance
detection_client = DetectionClient()
