"""
Tests for RoadSense Detection Service
"""

import pytest
import numpy as np
import cv2
from pathlib import Path

# Import modules to test
from app.models.detector import RoadDefectDetector
from app.config import settings


@pytest.fixture
def detector():
    """Create detector instance for tests"""
    model_path = Path(settings.MODEL_PATH)
    if not model_path.exists():
        pytest.skip(f"Model not found at {model_path}")
    return RoadDefectDetector(str(model_path))


@pytest.fixture
def sample_image():
    """Create a sample test image"""
    # Create a 640x480 BGR image with some patterns
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add some patterns (simulating road defects)
    cv2.rectangle(image, (100, 100), (200, 200), (255, 255, 255), -1)
    cv2.circle(image, (400, 300), 50, (200, 200, 200), -1)
    
    return image


@pytest.fixture
def sample_image_bytes(sample_image):
    """Convert sample image to bytes"""
    _, buffer = cv2.imencode('.jpg', sample_image)
    return buffer.tobytes()


class TestRoadDefectDetector:
    """Test suite for RoadDefectDetector class"""
    
    def test_detector_initialization(self, detector):
        """Test detector loads successfully"""
        assert detector is not None
        assert detector.sess is not None
        assert detector.detection_graph is not None
    
    def test_detect_defects_returns_list(self, detector, sample_image):
        """Test detect_defects returns a list"""
        detections = detector.detect_defects(sample_image)
        assert isinstance(detections, list)
    
    def test_detect_defects_with_confidence_threshold(self, detector, sample_image):
        """Test detection with different confidence thresholds"""
        # High threshold should return fewer or no detections
        detections_high = detector.detect_defects(sample_image, confidence_threshold=0.8)
        
        # Low threshold should return more detections
        detections_low = detector.detect_defects(sample_image, confidence_threshold=0.1)
        
        assert len(detections_low) >= len(detections_high)
    
    def test_detection_format(self, detector, sample_image):
        """Test detection results have correct format"""
        detections = detector.detect_defects(sample_image, confidence_threshold=0.1)
        
        if len(detections) > 0:
            detection = detections[0]
            
            # Check required fields
            assert 'class_name' in detection
            assert 'confidence' in detection
            assert 'bounding_box' in detection
            
            # Check types
            assert isinstance(detection['class_name'], str)
            assert isinstance(detection['confidence'], float)
            assert isinstance(detection['bounding_box'], list)
            
            # Check confidence range
            assert 0.0 <= detection['confidence'] <= 1.0
            
            # Check bounding box format [y_min, x_min, y_max, x_max]
            assert len(detection['bounding_box']) == 4
            
            # Check class name is valid
            valid_classes = ['D00', 'D01', 'D10', 'D11', 'D20', 'D40', 'D43', 'D44']
            assert detection['class_name'] in valid_classes
    
    def test_class_name_mapping(self, detector):
        """Test class ID to name mapping"""
        class_map = {
            1: 'D00', 2: 'D01', 3: 'D10', 4: 'D11',
            5: 'D20', 6: 'D40', 7: 'D43', 8: 'D44'
        }
        
        for class_id, expected_name in class_map.items():
            result = detector._get_class_name(class_id)
            assert result == expected_name
        
        # Test unknown class
        assert detector._get_class_name(999) == 'Unknown'
    
    def test_detect_empty_image(self, detector):
        """Test detection on empty image"""
        empty_image = np.zeros((480, 640, 3), dtype=np.uint8)
        detections = detector.detect_defects(empty_image)
        
        # Empty image should have no or few detections
        assert isinstance(detections, list)
    
    def test_detect_various_image_sizes(self, detector):
        """Test detection works with different image sizes"""
        sizes = [(480, 640), (720, 1280), (1080, 1920)]
        
        for height, width in sizes:
            image = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
            detections = detector.detect_defects(image)
            assert isinstance(detections, list)
    
    def test_confidence_threshold_filtering(self, detector, sample_image):
        """Test that confidence threshold properly filters results"""
        # Get detections with very low threshold
        all_detections = detector.detect_defects(sample_image, confidence_threshold=0.01)
        
        # Get detections with high threshold
        filtered_detections = detector.detect_defects(sample_image, confidence_threshold=0.5)
        
        # All filtered detections should have confidence >= 0.5
        for detection in filtered_detections:
            assert detection['confidence'] >= 0.5
        
        # Filtered should be subset of all detections
        assert len(filtered_detections) <= len(all_detections)


class TestDetectionAPI:
    """Test detection API endpoints"""
    
    def test_model_config_exists(self):
        """Test model configuration is properly set"""
        assert hasattr(settings, 'MODEL_PATH')
        assert hasattr(settings, 'CONFIDENCE_THRESHOLD')
        assert 0.0 <= settings.CONFIDENCE_THRESHOLD <= 1.0
    
    def test_supported_classes(self):
        """Test all supported defect classes are defined"""
        expected_classes = {'D00', 'D01', 'D10', 'D11', 'D20', 'D40', 'D43', 'D44'}
        
        # This could be extended to check against actual model output
        assert len(expected_classes) == 8


class TestImageProcessing:
    """Test image preprocessing and handling"""
    
    def test_image_color_conversion(self, sample_image):
        """Test BGR to RGB conversion"""
        rgb_image = cv2.cvtColor(sample_image, cv2.COLOR_BGR2RGB)
        
        assert rgb_image.shape == sample_image.shape
        assert rgb_image.dtype == sample_image.dtype
    
    def test_image_normalization(self, sample_image):
        """Test image can be normalized for model input"""
        normalized = sample_image.astype(np.float32) / 255.0
        
        assert normalized.min() >= 0.0
        assert normalized.max() <= 1.0
    
    def test_image_batch_expansion(self, sample_image):
        """Test image batch dimension expansion"""
        batched = np.expand_dims(sample_image, axis=0)
        
        assert batched.shape[0] == 1
        assert batched.shape[1:] == sample_image.shape


@pytest.mark.integration
class TestDetectionPerformance:
    """Integration tests for detection performance"""
    
    def test_detection_speed(self, detector, sample_image):
        """Test detection completes in reasonable time"""
        import time
        
        start_time = time.time()
        detections = detector.detect_defects(sample_image)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Detection should complete in less than 1 second
        assert processing_time < 1.0, f"Detection took {processing_time:.2f}s, expected <1.0s"
    
    def test_batch_detection_efficiency(self, detector, sample_image):
        """Test batch detection is efficient"""
        import time
        
        num_images = 10
        
        # Time individual detections
        start_time = time.time()
        for _ in range(num_images):
            detector.detect_defects(sample_image)
        individual_time = time.time() - start_time
        
        # Average time per image
        avg_time = individual_time / num_images
        
        # Each detection should be reasonably fast
        assert avg_time < 0.5, f"Average detection time {avg_time:.2f}s too slow"


@pytest.mark.parametrize("confidence", [0.1, 0.15, 0.2, 0.3, 0.5, 0.7, 0.9])
def test_various_confidence_thresholds(detector, sample_image, confidence):
    """Test detection with various confidence thresholds"""
    detections = detector.detect_defects(sample_image, confidence_threshold=confidence)
    
    assert isinstance(detections, list)
    
    # All detections should meet confidence threshold
    for detection in detections:
        assert detection['confidence'] >= confidence


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app", "--cov-report=html"])
