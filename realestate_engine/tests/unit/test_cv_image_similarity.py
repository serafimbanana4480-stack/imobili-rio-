"""Unit tests for Image Similarity Detector."""
import pytest
from realestate_engine.cv.image_similarity import ImageSimilarityDetector


@pytest.fixture
def detector():
    """Create an ImageSimilarityDetector instance."""
    return ImageSimilarityDetector()


def test_detector_initialization(detector):
    """Test that detector initializes correctly."""
    assert detector.hash_size == 16
    assert detector.similarity_threshold == 0.95


def test_calculate_phash_with_invalid_url(detector):
    """Test pHash calculation with invalid URL."""
    phash = detector.calculate_phash("http://invalid-url.com/image.jpg")
    assert phash is None


def test_calculate_dhash_with_invalid_url(detector):
    """Test dHash calculation with invalid URL."""
    dhash = detector.calculate_dhash("http://invalid-url.com/image.jpg")
    assert dhash is None


def test_calculate_whash_with_invalid_url(detector):
    """Test wHash calculation with invalid URL."""
    whash = detector.calculate_whash("http://invalid-url.com/image.jpg")
    assert whash is None


def test_calculate_all_hashes_with_invalid_url(detector):
    """Test all hash calculations with invalid URL."""
    hashes = detector.calculate_all_hashes("http://invalid-url.com/image.jpg")
    
    assert 'phash' in hashes
    assert 'dhash' in hashes
    assert 'whash' in hashes
    assert hashes['phash'] is None
    assert hashes['dhash'] is None
    assert hashes['whash'] is None


def test_hamming_distance(detector):
    """Test Hamming distance calculation."""
    hash1 = "a1b2c3d4e5f6a1b2"
    hash2 = "a1b2c3d4e5f6a1b3"  # One bit different
    
    distance = detector.hamming_distance(hash1, hash2)
    assert distance >= 0
    assert isinstance(distance, int)


def test_hamming_distance_identical(detector):
    """Test Hamming distance for identical hashes."""
    hash1 = "a1b2c3d4e5f6a1b2"
    hash2 = "a1b2c3d4e5f6a1b2"
    
    distance = detector.hamming_distance(hash1, hash2)
    assert distance == 0


def test_similarity_score(detector):
    """Test similarity score calculation."""
    hash1 = "a1b2c3d4e5f6a1b2"
    hash2 = "a1b2c3d4e5f6a1b2"
    
    similarity = detector.similarity_score(hash1, hash2)
    assert similarity == 1.0


def test_are_similar_identical(detector):
    """Test similarity check for identical hashes."""
    hash1 = "a1b2c3d4e5f6a1b2"
    hash2 = "a1b2c3d4e5f6a1b2"
    
    assert detector.are_similar(hash1, hash2) == True


def test_are_similar_different(detector):
    """Test similarity check for different hashes."""
    hash1 = "a1b2c3d4e5f6a1b2"
    hash2 = "ffffffffffffffff"
    
    assert detector.are_similar(hash1, hash2) == False


def test_find_duplicates_empty(detector):
    """Test duplicate detection with empty dictionary."""
    duplicates = detector.find_duplicates({})
    assert duplicates == []


def test_find_duplicates_single(detector):
    """Test duplicate detection with single image."""
    image_hashes = {"img1": "a1b2c3d4e5f6a1b2"}
    duplicates = detector.find_duplicates(image_hashes)
    assert duplicates == []


def test_find_duplicates_multiple(detector):
    """Test duplicate detection with multiple images."""
    image_hashes = {
        "img1": "a1b2c3d4e5f6a1b2",
        "img2": "a1b2c3d4e5f6a1b2",  # Identical to img1
        "img3": "ffffffffffffffff"
    }
    duplicates = detector.find_duplicates(image_hashes)
    assert len(duplicates) > 0


def test_find_duplicates_across_listings_empty(detector):
    """Test duplicate detection across listings with empty list."""
    duplicates = detector.find_duplicates_across_listings([])
    assert duplicates == []


def test_find_duplicates_across_listings_no_photos(detector):
    """Test duplicate detection with listings that have no photos."""
    listings = [
        {"id": 1, "fotos_urls": []},
        {"id": 2, "fotos_urls": None}
    ]
    duplicates = detector.find_duplicates_across_listings(listings)
    assert duplicates == []


def test_calculate_listing_similarity_no_photos(detector):
    """Test listing similarity with no photos."""
    listing1 = {"fotos_urls": []}
    listing2 = {"fotos_urls": []}
    
    similarity = detector.calculate_listing_similarity(listing1, listing2)
    assert similarity['similar_images'] == 0
    assert similarity['is_duplicate'] == False
