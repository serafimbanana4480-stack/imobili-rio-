"""
Room Detector for Real Estate Images
Uses YOLOv8 to detect rooms (kitchen, bedroom, bathroom, living room) from property photos.
"""

import numpy as np
from PIL import Image
import requests
from io import BytesIO
from typing import Dict, Optional, List
from loguru import logger

try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False
    logger.warning("ultralytics not available, room detection will be disabled")


class RoomDetector:
    """YOLO-based room detector for real estate images."""
    
    # COCO class names relevant to real estate
    ROOM_CLASSES = {
        0: 'person',
        1: 'bicycle',
        2: 'car',
        3: 'motorcycle',
        4: 'airplane',
        5: 'bus',
        6: 'train',
        7: 'truck',
        8: 'boat',
        9: 'traffic light',
        10: 'fire hydrant',
        11: 'stop sign',
        12: 'parking meter',
        13: 'bench',
        14: 'bird',
        15: 'cat',
        16: 'dog',
        17: 'horse',
        18: 'sheep',
        19: 'cow',
        20: 'elephant',
        21: 'bear',
        22: 'zebra',
        23: 'giraffe',
        24: 'backpack',
        25: 'umbrella',
        26: 'handbag',
        27: 'tie',
        28: 'suitcase',
        29: 'frisbee',
        30: 'skis',
        31: 'snowboard',
        32: 'sports ball',
        33: 'kite',
        34: 'baseball bat',
        35: 'baseball glove',
        36: 'skateboard',
        37: 'surfboard',
        38: 'tennis racket',
        39: 'bottle',
        40: 'wine glass',
        41: 'cup',
        42: 'fork',
        43: 'knife',
        44: 'spoon',
        45: 'bowl',
        46: 'banana',
        47: 'apple',
        48: 'sandwich',
        49: 'orange',
        50: 'broccoli',
        51: 'carrot',
        52: 'hot dog',
        53: 'pizza',
        54: 'donut',
        55: 'cake',
        56: 'chair',
        57: 'couch',
        58: 'potted plant',
        59: 'bed',
        60: 'dining table',
        61: 'toilet',
        62: 'tv',
        63: 'laptop',
        64: 'mouse',
        65: 'remote',
        66: 'keyboard',
        67: 'cell phone',
        68: 'microwave',
        69: 'oven',
        70: 'toaster',
        71: 'sink',
        72: 'refrigerator',
        73: 'book',
        74: 'clock',
        75: 'vase',
        76: 'scissors',
        77: 'teddy bear',
        78: 'hair drier',
        79: 'toothbrush',
    }
    
    # Map COCO classes to room types
    ROOM_TYPE_MAPPING = {
        'bed': 'bedroom',
        'dining table': 'dining_room',
        'toilet': 'bathroom',
        'sink': 'bathroom',
        'refrigerator': 'kitchen',
        'oven': 'kitchen',
        'microwave': 'kitchen',
        'couch': 'living_room',
        'tv': 'living_room',
        'chair': 'living_room',
        'potted plant': 'living_room',
    }
    
    def __init__(self, model_name: str = 'yolov8n.pt'):
        """
        Initialize the room detector.
        
        Args:
            model_name: YOLO model name (yolov8n.pt for nano, yolov8s.pt for small)
        """
        self.model_name = model_name
        self.model = None
        
        if ULTRALYTICS_AVAILABLE:
            self._load_model()
    
    def _load_model(self):
        """Load YOLO model."""
        try:
            logger.info(f"Loading YOLO model: {self.model_name}")
            self.model = YOLO(self.model_name)
            logger.info(f"Successfully loaded YOLO model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.model = None
    
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
    
    def detect_rooms(self, image_url: str, confidence_threshold: float = 0.5) -> Dict:
        """
        Detect rooms from an image.
        
        Args:
            image_url: URL of the image
            confidence_threshold: Minimum confidence for detection
            
        Returns:
            Dictionary with room detection results
        """
        if not ULTRALYTICS_AVAILABLE or self.model is None:
            return {
                'detected_rooms': {},
                'room_counts': {},
                'confidence': 0.0,
                'error': 'YOLO model not available'
            }
        
        image = self.download_image(image_url)
        if image is None:
            return {
                'detected_rooms': {},
                'room_counts': {},
                'confidence': 0.0,
                'error': 'Failed to download image'
            }
        
        try:
            # Run inference
            results = self.model(image, verbose=False)
            
            # Process results
            room_counts = {}
            detected_objects = []
            total_confidence = 0.0
            detection_count = 0
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    confidence = float(box.conf[0])
                    if confidence >= confidence_threshold:
                        class_id = int(box.cls[0])
                        class_name = self.ROOM_CLASSES.get(class_id, 'unknown')
                        
                        # Map to room type
                        room_type = self.ROOM_TYPE_MAPPING.get(class_name, 'other')
                        
                        # Count room types
                        if room_type not in room_counts:
                            room_counts[room_type] = 0
                        room_counts[room_type] += 1
                        
                        detected_objects.append({
                            'class': class_name,
                            'room_type': room_type,
                            'confidence': confidence,
                            'bbox': box.xyxy[0].tolist()
                        })
                        
                        total_confidence += confidence
                        detection_count += 1
            
            # Calculate average confidence
            avg_confidence = total_confidence / detection_count if detection_count > 0 else 0.0
            
            return {
                'detected_rooms': detected_objects,
                'room_counts': room_counts,
                'confidence': round(avg_confidence, 3),
                'total_detections': detection_count
            }
        except Exception as e:
            logger.error(f"Failed to detect rooms: {e}")
            return {
                'detected_rooms': {},
                'room_counts': {},
                'confidence': 0.0,
                'error': str(e)
            }
    
    def detect_rooms_batch(self, image_urls: List[str], confidence_threshold: float = 0.5) -> Dict:
        """
        Detect rooms from multiple images and aggregate results.
        
        Args:
            image_urls: List of image URLs
            confidence_threshold: Minimum confidence for detection
            
        Returns:
            Dictionary with aggregated room detection results
        """
        if not image_urls:
            return {
                'room_counts': {},
                'confidence': 0.0,
                'total_images': 0,
                'total_detections': 0
            }
        
        aggregated_counts = {}
        total_confidence = 0.0
        total_detections = 0
        successful_images = 0
        
        for url in image_urls:
            result = self.detect_rooms(url, confidence_threshold)
            
            if 'error' not in result:
                # Aggregate room counts
                for room_type, count in result['room_counts'].items():
                    if room_type not in aggregated_counts:
                        aggregated_counts[room_type] = 0
                    aggregated_counts[room_type] += count
                
                total_confidence += result['confidence']
                total_detections += result['total_detections']
                successful_images += 1
        
        avg_confidence = total_confidence / successful_images if successful_images > 0 else 0.0
        
        return {
            'room_counts': aggregated_counts,
            'confidence': round(avg_confidence, 3),
            'total_images': len(image_urls),
            'successful_images': successful_images,
            'total_detections': total_detections
        }
    
    def is_available(self) -> bool:
        """Check if YOLO model is available."""
        return ULTRALYTICS_AVAILABLE and self.model is not None


# Global instance for reuse
_room_detector = None

def get_room_detector() -> RoomDetector:
    """Get singleton instance of room detector."""
    global _room_detector
    if _room_detector is None:
        _room_detector = RoomDetector()
    return _room_detector
