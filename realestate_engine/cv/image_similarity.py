"""
Image Similarity Detector for Duplicate Detection
Uses perceptual hashing to detect visually similar images across listings.
"""

import cv2
import numpy as np
from PIL import Image
import requests
from io import BytesIO
import imagehash
from typing import Dict, List, Tuple, Optional
from loguru import logger


class ImageSimilarityDetector:
    """Detects image similarity using perceptual hashing."""
    
    def __init__(self, hash_size: int = 16, similarity_threshold: float = 0.95):
        """
        Initialize the image similarity detector.
        
        Args:
            hash_size: Size of the perceptual hash (higher = more precise)
            similarity_threshold: Threshold for considering images as duplicates (0-1)
        """
        self.hash_size = hash_size
        self.similarity_threshold = similarity_threshold
        
    def download_image(self, image_url: str) -> Optional[Image.Image]:
        """
        Download image from URL and convert to PIL Image.
        
        Args:
            image_url: URL of the image to download
            
        Returns:
            PIL Image or None if download fails
        """
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            image = Image.open(BytesIO(response.content))
            image = image.convert('RGB')
            return image
        except Exception as e:
            logger.error(f"Failed to download image from {image_url}: {e}")
            return None
    
    def calculate_phash(self, image_url: str) -> Optional[str]:
        """
        Calculate perceptual hash of an image.
        
        Args:
            image_url: URL of the image
            
        Returns:
            Hex string of the perceptual hash or None if failed
        """
        try:
            image = self.download_image(image_url)
            if image is None:
                return None
            
            # Calculate perceptual hash
            phash = imagehash.phash(image, hash_size=self.hash_size)
            return str(phash)
        except Exception as e:
            logger.error(f"Failed to calculate phash for {image_url}: {e}")
            return None
    
    def calculate_dhash(self, image_url: str) -> Optional[str]:
        """
        Calculate difference hash of an image (faster but less precise).
        
        Args:
            image_url: URL of the image
            
        Returns:
            Hex string of the difference hash or None if failed
        """
        try:
            image = self.download_image(image_url)
            if image is None:
                return None
            
            # Calculate difference hash
            dhash = imagehash.dhash(image, hash_size=self.hash_size)
            return str(dhash)
        except Exception as e:
            logger.error(f"Failed to calculate dhash for {image_url}: {e}")
            return None
    
    def calculate_whash(self, image_url: str) -> Optional[str]:
        """
        Calculate wavelet hash of an image (more robust to scaling).
        
        Args:
            image_url: URL of the image
            
        Returns:
            Hex string of the wavelet hash or None if failed
        """
        try:
            image = self.download_image(image_url)
            if image is None:
                return None
            
            # Calculate wavelet hash
            whash = imagehash.whash(image, hash_size=self.hash_size)
            return str(whash)
        except Exception as e:
            logger.error(f"Failed to calculate whash for {image_url}: {e}")
            return None
    
    def calculate_all_hashes(self, image_url: str) -> Dict[str, Optional[str]]:
        """
        Calculate multiple hash types for an image.
        
        Args:
            image_url: URL of the image
            
        Returns:
            Dictionary with all hash types
        """
        return {
            'phash': self.calculate_phash(image_url),
            'dhash': self.calculate_dhash(image_url),
            'whash': self.calculate_whash(image_url)
        }
    
    def hamming_distance(self, hash1: str, hash2: str) -> int:
        """
        Calculate Hamming distance between two hashes.
        
        Args:
            hash1: First hash string
            hash2: Second hash string
            
        Returns:
            Number of differing bits
        """
        try:
            h1 = int(hash1, 16)
            h2 = int(hash2, 16)
            return bin(h1 ^ h2).count('1')
        except Exception as e:
            logger.error(f"Failed to calculate Hamming distance: {e}")
            return float('inf')
    
    def similarity_score(self, hash1: str, hash2: str, max_distance: int = None) -> float:
        """
        Calculate similarity score between two hashes.
        
        Args:
            hash1: First hash string
            hash2: Second hash string
            max_distance: Maximum possible Hamming distance (default: hash_size^2)
            
        Returns:
            Similarity score (0-1, where 1 is identical)
        """
        if max_distance is None:
            max_distance = self.hash_size * self.hash_size
        
        distance = self.hamming_distance(hash1, hash2)
        similarity = 1.0 - (distance / max_distance)
        return max(0.0, similarity)
    
    def are_similar(self, hash1: str, hash2: str) -> bool:
        """
        Check if two hashes represent similar images.
        
        Args:
            hash1: First hash string
            hash2: Second hash string
            
        Returns:
            True if images are similar above threshold
        """
        similarity = self.similarity_score(hash1, hash2)
        return similarity >= self.similarity_threshold
    
    def find_duplicates(self, image_hashes: Dict[str, str]) -> List[Tuple[str, str, float]]:
        """
        Find duplicate images among a set of image hashes.
        
        Args:
            image_hashes: Dictionary mapping image_id to hash string
            
        Returns:
            List of tuples (image_id1, image_id2, similarity_score)
        """
        duplicates = []
        image_ids = list(image_hashes.keys())
        
        for i in range(len(image_ids)):
            for j in range(i + 1, len(image_ids)):
                id1, id2 = image_ids[i], image_ids[j]
                hash1, hash2 = image_hashes[id1], image_hashes[id2]
                
                if hash1 and hash2:
                    similarity = self.similarity_score(hash1, hash2)
                    if similarity >= self.similarity_threshold:
                        duplicates.append((id1, id2, similarity))
        
        # Sort by similarity (highest first)
        duplicates.sort(key=lambda x: x[2], reverse=True)
        
        return duplicates
    
    def find_duplicates_across_listings(self, listings: List[Dict]) -> List[Dict]:
        """
        Find duplicate images across multiple listings.
        
        Args:
            listings: List of listing dictionaries with 'id' and 'fotos_urls'
            
        Returns:
            List of duplicate groups with similarity info
        """
        # Build hash map: hash -> list of (listing_id, image_index)
        hash_map = {}
        
        for listing in listings:
            listing_id = listing.get('id')
            fotos_urls = listing.get('fotos_urls', [])
            
            if not isinstance(fotos_urls, list):
                fotos_urls = []
            
            for idx, url in enumerate(fotos_urls):
                phash = self.calculate_phash(url)
                if phash:
                    if phash not in hash_map:
                        hash_map[phash] = []
                    hash_map[phash].append({
                        'listing_id': listing_id,
                        'image_index': idx,
                        'image_url': url
                    })
        
        # Find duplicates (hashes with multiple listings)
        duplicate_groups = []
        for phash, image_list in hash_map.items():
            if len(image_list) > 1:
                # Group by listing_id
                listing_groups = {}
                for img in image_list:
                    listing_id = img['listing_id']
                    if listing_id not in listing_groups:
                        listing_groups[listing_id] = []
                    listing_groups[listing_id].append(img)
                
                if len(listing_groups) > 1:
                    duplicate_groups.append({
                        'hash': phash,
                        'listings': listing_groups,
                        'image_count': len(image_list)
                    })
        
        return duplicate_groups
    
    def calculate_listing_similarity(self, listing1: Dict, listing2: Dict) -> Dict:
        """
        Calculate similarity between two listings based on their images.
        
        Args:
            listing1: First listing with 'fotos_urls'
            listing2: Second listing with 'fotos_urls'
            
        Returns:
            Dictionary with similarity metrics
        """
        fotos1 = listing1.get('fotos_urls', [])
        fotos2 = listing2.get('fotos_urls', [])
        
        if not isinstance(fotos1, list):
            fotos1 = []
        if not isinstance(fotos2, list):
            fotos2 = []
        
        if not fotos1 or not fotos2:
            return {
                'similar_images': 0,
                'total_comparisons': 0,
                'avg_similarity': 0.0,
                'max_similarity': 0.0,
                'is_duplicate': False
            }
        
        # Calculate hashes for all images
        hashes1 = [self.calculate_phash(url) for url in fotos1]
        hashes2 = [self.calculate_phash(url) for url in fotos2]
        
        # Filter out failed hashes
        hashes1 = [h for h in hashes1 if h]
        hashes2 = [h for h in hashes2 if h]
        
        # Compare all pairs
        similarities = []
        similar_count = 0
        
        for h1 in hashes1:
            for h2 in hashes2:
                sim = self.similarity_score(h1, h2)
                similarities.append(sim)
                if sim >= self.similarity_threshold:
                    similar_count += 1
        
        if not similarities:
            return {
                'similar_images': 0,
                'total_comparisons': 0,
                'avg_similarity': 0.0,
                'max_similarity': 0.0,
                'is_duplicate': False
            }
        
        return {
            'similar_images': similar_count,
            'total_comparisons': len(similarities),
            'avg_similarity': round(np.mean(similarities), 3),
            'max_similarity': round(np.max(similarities), 3),
            'is_duplicate': similar_count > 0
        }
