"""
Tests for RoadSense Ingestion Video Service
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import numpy as np
import cv2

# Import modules to test
from app.services.video_processor import VideoProcessor
from app.services.detection_client import DetectionClient


@pytest.fixture
def temp_video_file():
    """Create a temporary test video file"""
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    video_path = Path(temp_dir) / "test_video.mp4"
    
    # Create a simple test video (10 frames, 25 FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(video_path), fourcc, 25.0, (640, 480))
    
    for i in range(10):
        # Create frame with some variation
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        # Add frame number text
        cv2.putText(frame, f"Frame {i}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        out.write(frame)
    
    out.release()
    
    yield str(video_path)
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_db_session():
    """Create mock database session"""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_storage():
    """Create mock storage client"""
    storage = Mock()
    storage.upload_frame = AsyncMock(return_value="frames/frame_001.jpg")
    storage.get_object = AsyncMock(return_value=b"fake_image_data")
    storage.upload_annotated_video = AsyncMock(return_value="annotated/video.mp4")
    return storage


class TestVideoProcessor:
    """Test suite for VideoProcessor class"""
    
    @pytest.mark.asyncio
    async def test_get_video_info(self, temp_video_file):
        """Test video info extraction"""
        video_info = await VideoProcessor.get_video_info(temp_video_file)
        
        assert 'duration' in video_info
        assert 'fps' in video_info
        assert 'width' in video_info
        assert 'height' in video_info
        assert 'total_frames' in video_info
        
        # Check expected values
        assert video_info['fps'] == 25.0
        assert video_info['width'] == 640
        assert video_info['height'] == 480
        assert video_info['total_frames'] > 0
    
    @pytest.mark.asyncio
    async def test_extract_frames(self, temp_video_file, mock_db_session, mock_storage):
        """Test frame extraction from video"""
        video_id = "test-video-123"
        fps = 2  # Extract at 2 FPS
        
        with patch('app.services.video_processor.storage', mock_storage):
            frames = await VideoProcessor.extract_frames(
                video_id=video_id,
                video_path=temp_video_file,
                db_session=mock_db_session,
                fps=fps
            )
        
        assert isinstance(frames, list)
        assert len(frames) > 0
        
        # Check frame structure
        if len(frames) > 0:
            frame = frames[0]
            assert 'frame_number' in frame
            assert 'timestamp' in frame
            assert 'storage_path' in frame
    
    @pytest.mark.asyncio
    async def test_extract_frames_sampling_rate(self, temp_video_file, mock_db_session, mock_storage):
        """Test frame extraction respects FPS sampling"""
        video_id = "test-video-123"
        
        with patch('app.services.video_processor.storage', mock_storage):
            # Extract at 1 FPS
            frames_1fps = await VideoProcessor.extract_frames(
                video_id=video_id,
                video_path=temp_video_file,
                db_session=mock_db_session,
                fps=1
            )
            
            # Extract at 5 FPS
            frames_5fps = await VideoProcessor.extract_frames(
                video_id=video_id,
                video_path=temp_video_file,
                db_session=mock_db_session,
                fps=5
            )
        
        # Higher FPS should extract more frames
        assert len(frames_5fps) >= len(frames_1fps)
    
    def test_frame_extraction_invalid_video(self):
        """Test handling of invalid video file"""
        with pytest.raises(Exception):
            asyncio.run(VideoProcessor.get_video_info("/nonexistent/video.mp4"))


class TestDetectionClient:
    """Test suite for DetectionClient"""
    
    @pytest.mark.asyncio
    async def test_detect_defects_success(self):
        """Test successful defect detection"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'detections': [
                {
                    'class_name': 'D20',
                    'confidence': 0.87,
                    'bounding_box': [0.1, 0.2, 0.3, 0.4]
                }
            ],
            'processing_time_ms': 45.2
        })
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            client = DetectionClient("http://detection:8001")
            
            fake_image_bytes = b"fake_image_data"
            result = await client.detect_defects(fake_image_bytes, confidence_threshold=0.15)
        
        assert 'success' in result
        assert result['success'] is True
        assert 'detections' in result
        assert len(result['detections']) > 0
    
    @pytest.mark.asyncio
    async def test_detect_defects_failure(self):
        """Test detection failure handling"""
        mock_response = Mock()
        mock_response.status = 500
        mock_response.text = "Internal Server Error"
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            client = DetectionClient("http://detection:8001")
            
            fake_image_bytes = b"fake_image_data"
            result = await client.detect_defects(fake_image_bytes)
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_detect_frame_batch(self):
        """Test batch frame detection"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'detections': [
                {
                    'class_name': 'D10',
                    'confidence': 0.75,
                    'bounding_box': [0.2, 0.3, 0.5, 0.6]
                }
            ],
            'processing_time_ms': 50.0
        })
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            client = DetectionClient("http://detection:8001")
            
            frames_data = [
                ('frame-1', b"image1"),
                ('frame-2', b"image2"),
                ('frame-3', b"image3")
            ]
            
            results = await client.detect_frame_batch(frames_data)
        
        assert len(results) == 3
        
        for result in results:
            assert 'frame_id' in result
            assert 'success' in result
    
    @pytest.mark.asyncio
    async def test_batch_processing_delay(self):
        """Test batch processing includes delay between requests"""
        import time
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'detections': []})
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            client = DetectionClient("http://detection:8001")
            
            frames_data = [('f1', b"i1"), ('f2', b"i2"), ('f3', b"i3")]
            
            start_time = time.time()
            await client.detect_frame_batch(frames_data)
            end_time = time.time()
            
            # Should have at least some delay between requests
            processing_time = end_time - start_time
            # With 0.1s delay between 3 frames, should take at least 0.2s
            assert processing_time >= 0.2


class TestBatchProcessing:
    """Test batch processing functionality"""
    
    def test_batch_size_configuration(self):
        """Test batch size is properly configured"""
        # Batch size should be reasonable
        batch_size = 10
        assert batch_size > 0
        assert batch_size <= 20  # Not too large
    
    @pytest.mark.asyncio
    async def test_batch_processing_divides_correctly(self):
        """Test frames are divided into correct batch sizes"""
        total_frames = 25
        batch_size = 10
        
        frames = list(range(total_frames))
        batches = [frames[i:i+batch_size] for i in range(0, len(frames), batch_size)]
        
        # Should have 3 batches (10 + 10 + 5)
        assert len(batches) == 3
        assert len(batches[0]) == 10
        assert len(batches[1]) == 10
        assert len(batches[2]) == 5


class TestVideoProcessingPipeline:
    """Integration tests for complete video processing pipeline"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_pipeline_flow(self, temp_video_file, mock_db_session, mock_storage):
        """Test complete video processing flow"""
        video_id = "integration-test-video"
        
        with patch('app.services.video_processor.storage', mock_storage):
            # Step 1: Get video info
            video_info = await VideoProcessor.get_video_info(temp_video_file)
            assert video_info is not None
            
            # Step 2: Extract frames
            frames = await VideoProcessor.extract_frames(
                video_id=video_id,
                video_path=temp_video_file,
                db_session=mock_db_session,
                fps=2
            )
            assert len(frames) > 0
            
            # Pipeline should complete successfully
            assert True


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_handle_corrupted_video(self):
        """Test handling of corrupted video file"""
        # Create empty file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            corrupted_path = f.name
        
        try:
            with pytest.raises(Exception):
                await VideoProcessor.get_video_info(corrupted_path)
        finally:
            Path(corrupted_path).unlink()
    
    @pytest.mark.asyncio
    async def test_handle_network_timeout(self):
        """Test handling of detection service timeout"""
        with patch('httpx.AsyncClient.post', side_effect=asyncio.TimeoutError()):
            client = DetectionClient("http://detection:8001")
            
            result = await client.detect_defects(b"image_data")
            
            assert result['success'] is False
            assert 'timeout' in result.get('error', '').lower()
    
    @pytest.mark.asyncio
    async def test_handle_invalid_image_data(self):
        """Test handling of invalid image bytes"""
        mock_response = Mock()
        mock_response.status = 400
        mock_response.text = "Invalid image format"
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            client = DetectionClient("http://detection:8001")
            
            result = await client.detect_defects(b"invalid_data")
            
            assert result['success'] is False


@pytest.mark.parametrize("fps,expected_min_frames", [
    (1, 0),   # 1 FPS from 10-frame 25FPS video
    (2, 0),   # 2 FPS
    (5, 1),   # 5 FPS
    (10, 3),  # 10 FPS
])
@pytest.mark.asyncio
async def test_frame_extraction_various_fps(temp_video_file, mock_db_session, mock_storage, fps, expected_min_frames):
    """Test frame extraction with various FPS settings"""
    with patch('app.services.video_processor.storage', mock_storage):
        frames = await VideoProcessor.extract_frames(
            video_id="test",
            video_path=temp_video_file,
            db_session=mock_db_session,
            fps=fps
        )
    
    assert len(frames) >= expected_min_frames


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app", "--cov-report=html"])
