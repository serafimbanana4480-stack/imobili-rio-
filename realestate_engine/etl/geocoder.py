"""Geocoder for address to coordinates conversion with multi-provider fallback."""
import json
import os
import time
from typing import Optional, Tuple, Dict, List
from geopy.geocoders import Nominatim, GoogleV3
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from loguru import logger

from realestate_engine.utils.config import config
from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.database.models import GeocodingCache
from realestate_engine.infrastructure.redis_client import get_redis
import hashlib


class GeocoderProvider:
    """Base class for geocoding providers."""
    
    def __init__(self, name: str):
        self.name = name
        self._consecutive_failures = 0
        self._circuit_open = False
        self._last_failure_time = None
    
    def can_execute(self) -> bool:
        """Check if provider is not in circuit breaker state."""
        if not self._circuit_open:
            return True
        # Auto-reset after 5 minutes
        from datetime import datetime, timedelta
        if self._last_failure_time and datetime.now() > self._last_failure_time + timedelta(minutes=5):
            logger.info(f"[{self.name}] Circuit breaker auto-reset")
            self._circuit_open = False
            self._consecutive_failures = 0
            return True
        return False
    
    def record_success(self):
        """Record successful geocode."""
        self._consecutive_failures = 0
        self._circuit_open = False
        self._last_failure_time = None
    
    def record_failure(self):
        """Record failed geocode."""
        self._consecutive_failures += 1
        from datetime import datetime
        self._last_failure_time = datetime.now()
        if self._consecutive_failures >= 15:
            self._circuit_open = True
            logger.warning(f"[{self.name}] Circuit breaker OPEN after {self._consecutive_failures} failures")
    
    def geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """Geocode address - to be implemented by subclasses."""
        raise NotImplementedError


class NominatimProvider(GeocoderProvider):
    """Nominatim (OpenStreetMap) geocoding provider."""
    
    def __init__(self):
        super().__init__("nominatim")
        self.geolocator = Nominatim(
            user_agent="realestate-engine/3.0 (contact: admin@realestate-engine.pt)",
            timeout=30
        )
    
    def geocode(self, address: str) -> Optional[Tuple[float, float]]:
        if not self.can_execute():
            return None
        
        try:
            location = self.geolocator.geocode(address, timeout=30)
            if location:
                self.record_success()
                return (location.latitude, location.longitude)
            self.record_failure()
        except GeocoderTimedOut as e:
            logger.debug(f"[{self.name}] Timeout after 30s: {address[:40]}...")
            self.record_failure()
        except (GeocoderServiceError, Exception) as e:
            logger.debug(f"[{self.name}] Service error: {e}")
            self.record_failure()
        return None


class GoogleProvider(GeocoderProvider):
    """Google Maps geocoding provider (requires API key)."""
    
    def __init__(self):
        super().__init__("google")
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if api_key:
            self.geolocator = GoogleV3(api_key=api_key, timeout=10)
        else:
            self.geolocator = None
            logger.warning(f"[{self.name}] No API key configured, provider disabled")
    
    def geocode(self, address: str) -> Optional[Tuple[float, float]]:
        if not self.can_execute() or not self.geolocator:
            return None
        
        try:
            location = self.geolocator.geocode(address, timeout=10)
            if location:
                self.record_success()
                return (location.latitude, location.longitude)
            self.record_failure()
        except (GeocoderTimedOut, GeocoderServiceError, Exception) as e:
            logger.debug(f"[{self.name}] Error: {e}")
            self.record_failure()
        return None


class Geocoder:
    """Geocodes addresses to lat/lon with multi-provider fallback and caching.

    Provider fallback chain: Google (if API key) → Nominatim → None
    Includes per-provider circuit breakers and Redis L1 + DB L2 caching.
    """

    CB_THRESHOLD = 10

    def __init__(self):
        self.repo = DatabaseRepository()
        self.redis = get_redis()
        self._consecutive_failures = 0
        self._circuit_open = False
        self._last_all_failed_log = None
        self._last_request_time = 0.0  # For rate limiting
        
        # Initialize providers in priority order
        self.providers: List[GeocoderProvider] = []
        
        # Google Maps (if API key available)
        google = GoogleProvider()
        if google.geolocator:
            self.providers.append(google)
        
        # Nominatim (always available)
        self.providers.append(NominatimProvider())
        
        logger.info(f"Geocoder initialized with {len(self.providers)} providers: {[p.name for p in self.providers]}")

    def _get_address_hash(self, address: str) -> str:
        """Generate MD5 hash of address for indexing."""
        return hashlib.md5(address.lower().strip().encode()).hexdigest()

    def geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """Geocode address to (lat, lon) with multi-provider fallback."""
        if not address:
            return None

        addr_hash = self._get_address_hash(address)

        # L1: Redis cache (fast path, survives across processes)
        redis_key = f"geocode:{addr_hash}"
        cached_redis = self.redis.get_json(redis_key)
        if cached_redis and "lat" in cached_redis and "lon" in cached_redis:
            return (float(cached_redis["lat"]), float(cached_redis["lon"]))

        # L2: DB cache
        with self.repo.Session() as session:
            from sqlalchemy import select
            cached = session.execute(
                select(GeocodingCache).where(GeocodingCache.address_hash == addr_hash)
            ).scalar_one_or_none()
            
            if cached:
                logger.debug(f"Geocode cache hit (DB): {address[:40]}...")
                # Warm Redis L1 so next lookup stays hot
                self.redis.set_json(
                    redis_key,
                    {"lat": cached.latitude, "lon": cached.longitude},
                    ttl_seconds=86400,
                )
                return (cached.latitude, cached.longitude)

        # Try each provider in priority order
        for provider in self.providers:
            if not provider.can_execute():
                logger.debug(f"[{provider.name}] Skipping (circuit breaker open)")
                continue
            
            # Rate limiting: 1 request/second to respect Nominatim limits
            elapsed = time.time() - self._last_request_time
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
            self._last_request_time = time.time()
            
            logger.debug(f"[{provider.name}] Attempting geocode for: {address[:40]}...")
            coords = provider.geocode(address)
            
            if coords:
                # Success - cache and return
                self._consecutive_failures = 0
                
                # Save to DB cache (persistent)
                freg, conc = self.extract_freguesia_concelho(address)
                entry = GeocodingCache(
                    address_hash=addr_hash,
                    address_raw=address,
                    latitude=coords[0],
                    longitude=coords[1],
                    freguesia=freg,
                    concelho=conc,
                    provider=provider.name
                )
                with self.repo.Session() as session:
                    session.merge(entry)
                    session.commit()

                # Save to Redis L1
                self.redis.set_json(
                    redis_key,
                    {"lat": coords[0], "lon": coords[1]},
                    ttl_seconds=86400,
                )

                logger.info(f"Geocoded ({provider.name}): {address[:40]}... -> {coords}")
                return coords
            else:
                logger.debug(f"[{provider.name}] Failed for: {address[:40]}...")

        # All providers failed
        now_key = address[:40]
        if self._last_all_failed_log != now_key:
            logger.warning(f"All geocoding providers failed for: {address[:40]}...")
            self._last_all_failed_log = now_key
        return None
    
    def extract_freguesia_concelho(self, address: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract freguesia and concelho from address."""
        if not address:
            return None, None
        
        parts = [p.strip() for p in address.split(",")]
        if len(parts) >= 2:
            return parts[0], parts[-2] if len(parts) > 2 else parts[-1]
        return parts[0] if parts else None, None
