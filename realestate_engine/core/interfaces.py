"""Core interfaces (abstract base classes) for dependency inversion.

These interfaces allow high-level modules to depend on abstractions,
not concrete implementations. Enables testing, swapping implementations,
and following the Dependency Inversion Principle.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any


class IEnricher(ABC):
    """Interface for listing enrichment strategies."""

    @abstractmethod
    async def enrich(self, listing: Dict) -> Dict:
        """Enrich a listing with additional data."""
        ...


class INormalizer(ABC):
    """Interface for data normalization."""

    @abstractmethod
    def normalize(self, raw: Dict) -> Dict:
        """Normalize raw listing data into standard format."""
        ...


class IDeduplicator(ABC):
    """Interface for duplicate detection."""

    @abstractmethod
    def filter_duplicates(self, listings: List[Dict]) -> List[Dict]:
        """Filter out duplicate listings."""
        ...


class IGeocoder(ABC):
    """Interface for geocoding addresses."""

    @abstractmethod
    async def geocode(self, address: str) -> Tuple[Optional[float], Optional[float]]:
        """Convert address to lat/lon coordinates."""
        ...


class ISpider(ABC):
    """Interface for web scraping spiders."""

    @abstractmethod
    async def run(self, max_pages: int = 5, **kwargs) -> List[Dict]:
        """Run the spider and return scraped listings."""
        ...


class IValuationModel(ABC):
    """Interface for valuation models."""

    @abstractmethod
    def train(self, data: List[Dict]) -> None:
        """Train the model on historical data."""
        ...

    @abstractmethod
    def predict(self, listing: Dict) -> float:
        """Predict property value."""
        ...


class INotificationSender(ABC):
    """Interface for notification delivery."""

    @abstractmethod
    async def send(self, message: str, recipient: str) -> bool:
        """Send a notification."""
        ...
