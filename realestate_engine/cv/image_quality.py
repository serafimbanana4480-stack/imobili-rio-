"""
Image Quality Analyzer for Real Estate Listings
Assesses image quality using blur detection, brightness, contrast, and resolution metrics.
"""

import cv2
import numpy as np
from PIL import Image
import requests
from io import BytesIO
from typing import Dict, Optional
from loguru import logger


class ImageQualityAnalyzer:
    """Analyzes image quality for real estate photos."""
    
    def __init__(self, min_resolution: tuple = (800, 600)):
        """
        Initialize the image quality analyzer.
        
        Args:
            min_resolution: Minimum acceptable resolution (width, height)
        """
        self.min_resolution = min_resolution
        self.min_blur_score = 100.0  # Laplacian variance threshold
        self.min_brightness = 30.0
        self.max_brightness = 220.0
        
    def download_image(self, image_url: str) -> Optional[np.ndarray]:
        """
        Download image from URL and convert to numpy array.
        
        Args:
            image_url: URL of the image to download
            
        Returns:
            Image as numpy array or None if download fails
        """
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            image = Image.open(BytesIO(response.content))
            image = image.convert('RGB')
            return np.array(image)
        except Exception as e:
            logger.error(f"Failed to download image from {image_url}: {e}")
            return None
    
    def calculate_blur_score(self, image: np.ndarray) -> float:
        """
        Calculate blur score using Laplacian variance.
        Higher values indicate sharper images.
        
        Args:
            image: Image as numpy array
            
        Returns:
            Blur score (0-1, where 1 is sharp)
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Normalize to 0-1 range
            normalized_score = min(laplacian_var / 500.0, 1.0)
            return normalized_score
        except Exception as e:
            logger.error(f"Failed to calculate blur score: {e}")
            return 0.0
    
    def calculate_brightness(self, image: np.ndarray) -> float:
        """
        Calculate average brightness of the image.
        
        Args:
            image: Image as numpy array
            
        Returns:
            Brightness score (0-1, where 0.5 is optimal)
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            avg_brightness = np.mean(gray)
            
            # Normalize to 0-1 range (0-255 -> 0-1)
            normalized = avg_brightness / 255.0
            return normalized
        except Exception as e:
            logger.error(f"Failed to calculate brightness: {e}")
            return 0.5
    
    def calculate_contrast(self, image: np.ndarray) -> float:
        """
        Calculate contrast using standard deviation of pixel intensities.
        
        Args:
            image: Image as numpy array
            
        Returns:
            Contrast score (0-1, where higher is better)
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            contrast = np.std(gray)
            
            # Normalize to 0-1 range
            normalized_score = min(contrast / 128.0, 1.0)
            return normalized_score
        except Exception as e:
            logger.error(f"Failed to calculate contrast: {e}")
            return 0.0
    
    def check_resolution(self, image: np.ndarray) -> Dict:
        """
        Check if image meets minimum resolution requirements.
        
        Args:
            image: Image as numpy array
            
        Returns:
            Dictionary with resolution info
        """
        height, width = image.shape[:2]
        min_width, min_height = self.min_resolution
        
        meets_min = width >= min_width and height >= min_height
        
        return {
            'width': width,
            'height': height,
            'meets_minimum': meets_min,
            'min_width': min_width,
            'min_height': min_height
        }
    
    def check_aspect_ratio(self, image: np.ndarray) -> Dict:
        """
        Check aspect ratio of the image.
        
        Args:
            image: Image as numpy array
            
        Returns:
            Dictionary with aspect ratio info
        """
        height, width = image.shape[:2]
        aspect_ratio = width / height
        
        # Common aspect ratios for real estate photos
        is_standard = 0.75 <= aspect_ratio <= 1.5  # 4:3 to 3:2
        
        return {
            'aspect_ratio': round(aspect_ratio, 2),
            'is_standard': is_standard
        }
    
    def analyze_image(self, image_url: str) -> Dict:
        """
        Perform comprehensive image quality analysis.
        
        Args:
            image_url: URL of the image to analyze
            
        Returns:
            Dictionary with all quality metrics
        """
        image = self.download_image(image_url)
        
        if image is None:
            return {
                'image_quality_score': 0.0,
                'blur_score': 0.0,
                'brightness_score': 0.5,
                'contrast_score': 0.0,
                'resolution': None,
                'aspect_ratio': None,
                'error': 'Failed to download image'
            }
        
        # Calculate individual metrics
        blur_score = self.calculate_blur_score(image)
        brightness_score = self.calculate_brightness(image)
        contrast_score = self.calculate_contrast(image)
        resolution_info = self.check_resolution(image)
        aspect_ratio_info = self.check_aspect_ratio(image)
        
        # Calculate overall quality score
        # Weight: blur (40%), brightness (20%), contrast (20%), resolution (20%)
        resolution_score = 1.0 if resolution_info['meets_minimum'] else 0.5
        aspect_score = 1.0 if aspect_ratio_info['is_standard'] else 0.7
        
        # Adjust brightness score for optimal range (0.3-0.7)
        brightness_adjusted = 1.0 - abs(brightness_score - 0.5) * 2
        brightness_adjusted = max(0.0, brightness_adjusted)
        
        overall_score = (
            blur_score * 0.4 +
            brightness_adjusted * 0.2 +
            contrast_score * 0.2 +
            resolution_score * 0.1 +
            aspect_score * 0.1
        )
        
        return {
            'image_quality_score': round(overall_score, 3),
            'blur_score': round(blur_score, 3),
            'brightness_score': round(brightness_score, 3),
            'contrast_score': round(contrast_score, 3),
            'resolution': resolution_info,
            'aspect_ratio': aspect_ratio_info
        }
    
    def analyze_images_batch(self, image_urls: list) -> Dict:
        """
        Analyze multiple images and return aggregated metrics.
        
        Args:
            image_urls: List of image URLs
            
        Returns:
            Dictionary with aggregated quality metrics
        """
        if not image_urls:
            return {
                'avg_quality_score': 0.0,
                'min_quality_score': 0.0,
                'max_quality_score': 0.0,
                'total_images': 0,
                'individual_scores': []
            }
        
        results = []
        for url in image_urls:
            result = self.analyze_image(url)
            results.append(result)
        
        quality_scores = [r['image_quality_score'] for r in results]
        
        return {
            'avg_quality_score': round(np.mean(quality_scores), 3),
            'min_quality_score': round(np.min(quality_scores), 3),
            'max_quality_score': round(np.max(quality_scores), 3),
            'total_images': len(results),
            'individual_scores': results
        }
