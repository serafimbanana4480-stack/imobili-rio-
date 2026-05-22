"""Unit tests for Image Quality Analyzer."""
import pytest

pytest.importorskip("cv2", reason="opencv not installed (CV extras)")
pytest.importorskip("PIL", reason="Pillow not installed (CV extras)")

import numpy as np
from PIL import Image
from realestate_engine.cv.image_quality import ImageQualityAnalyzer


@pytest.fixture
def analyzer():
    """Create an ImageQualityAnalyzer instance."""
    return ImageQualityAnalyzer()


@pytest.fixture
def sample_image():
    """Create a sample test image."""
    # Create a simple 100x100 RGB image
    img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    return Image.fromarray(img_array)


def test_analyzer_initialization(analyzer):
    """Test that analyzer initializes correctly."""
    assert analyzer.min_resolution == (800, 600)
    assert analyzer.min_blur_score == 100.0
    assert analyzer.min_brightness == 30.0
    assert analyzer.max_brightness == 220.0


def test_calculate_blur_score(analyzer, sample_image):
    """Test blur score calculation."""
    img_array = np.array(sample_image)
    blur_score = analyzer.calculate_blur_score(img_array)
    
    assert 0.0 <= blur_score <= 1.0
    assert isinstance(blur_score, float)


def test_calculate_brightness(analyzer, sample_image):
    """Test brightness calculation."""
    img_array = np.array(sample_image)
    brightness = analyzer.calculate_brightness(img_array)
    
    assert 0.0 <= brightness <= 1.0
    assert isinstance(brightness, float)


def test_calculate_contrast(analyzer, sample_image):
    """Test contrast calculation."""
    img_array = np.array(sample_image)
    contrast = analyzer.calculate_contrast(img_array)
    
    assert 0.0 <= contrast <= 1.0
    assert isinstance(contrast, float)


def test_check_resolution(analyzer, sample_image):
    """Test resolution checking."""
    img_array = np.array(sample_image)
    resolution_info = analyzer.check_resolution(img_array)
    
    assert 'width' in resolution_info
    assert 'height' in resolution_info
    assert 'meets_minimum' in resolution_info
    assert resolution_info['width'] == 100
    assert resolution_info['height'] == 100
    assert resolution_info['meets_minimum'] == False  # 100x100 < 800x600


def test_check_aspect_ratio(analyzer, sample_image):
    """Test aspect ratio checking."""
    img_array = np.array(sample_image)
    aspect_info = analyzer.check_aspect_ratio(img_array)
    
    assert 'aspect_ratio' in aspect_info
    assert 'is_standard' in aspect_info
    assert aspect_info['aspect_ratio'] == 1.0
    assert aspect_info['is_standard'] == True


def test_analyze_image_with_invalid_url(analyzer):
    """Test analysis with invalid image URL."""
    result = analyzer.analyze_image("http://invalid-url-that-does-not-exist-12345.com/image.jpg")
    
    # Should return error indicators when download fails
    assert result['image_quality_score'] == 0.0
    assert result['blur_score'] == 0.0
    assert result['brightness_score'] == 0.5
    assert 'error' in result


def test_analyze_images_batch_empty(analyzer):
    """Test batch analysis with empty list."""
    result = analyzer.analyze_images_batch([])
    
    assert result['avg_quality_score'] == 0.0
    assert result['min_quality_score'] == 0.0
    assert result['max_quality_score'] == 0.0
    assert result['total_images'] == 0
    assert result['individual_scores'] == []


def test_analyze_images_batch_with_urls(analyzer):
    """Test batch analysis with image URLs."""
    # Use a public test image URL
    test_urls = [
        "https://via.placeholder.com/800x600.png",
        "https://via.placeholder.com/1024x768.png"
    ]
    
    result = analyzer.analyze_images_batch(test_urls)
    
    assert result['total_images'] == 2
    assert 0.0 <= result['avg_quality_score'] <= 1.0
    assert len(result['individual_scores']) == 2
