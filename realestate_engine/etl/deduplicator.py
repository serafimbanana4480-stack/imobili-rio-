"""Listing deduplicator.

Identifies and merges duplicate listings across different portals
using a deterministic fingerprinting algorithm based on location,
type, area, and price.
"""
import hashlib
from typing import Dict, List, Optional
from loguru import logger

from realestate_engine.database.models import RawListing


class Deduplicator:
    """Handles identification and merging of duplicate real estate listings."""

    @staticmethod
    def generate_fingerprint(listing: RawListing) -> str:
        """
        Generates a unique deterministic hash for a listing.
        
        Cross-portal deduplication strategy:
        We assume a listing is the SAME property if it shares:
        - Freguesia (Parish)
        - Tipologia (e.g., T2)
        - Area util (+/- small margin, we bucket it by 5m2 chunks)
        - Price (+/- small margin, we bucket it by 5000 EUR chunks)
        
        This prevents an Idealista listing and an Imovirtual listing of the
        same property from creating two alerts on Telegram.
        """
        try:
            # Handle both ORM objects and dicts
            get_val = lambda key: listing.get(key) if isinstance(listing, dict) else getattr(listing, key, None)
            
            # 1. Normalize Freguesia
            freguesia = (get_val("freguesia") or "Unknown").strip().lower()
            
            # 2. Normalize Tipologia
            tipologia = (get_val("tipologia") or "Unknown").strip().upper()
            
            # 3. Bucket Area (round to nearest 5 to reduce false positives)
            area = get_val("area_util_m2")
            if area:
                area_bucket = round(area / 5) * 5
            else:
                area_bucket = 0
                
            # 4. Bucket Price (round to nearest 5000)
            price = get_val("preco_pedido")
            if price:
                price_bucket = round(price / 5000) * 5000
            else:
                price_bucket = 0
                
            # 5. Geolocation Bucket (round to ~100m precision)
            lat = get_val("lat")
            lon = get_val("lon")
            if lat and lon:
                geo_bucket = f"{round(lat, 3)}_{round(lon, 3)}"
            else:
                geo_bucket = "NoGeo"

            # 6. Source disambiguation — different source_ids from the same
            #    portal are distinct properties even when content-fingerprint
            #    collides (e.g. multiple units in a development).  Cross-portal
            #    dedup only fires when geo coords resolve to the same bucket.
            source_id = get_val("source_id") or ""
            source_portal = get_val("source_portal") or ""
            if geo_bucket == "NoGeo" and source_id:
                source_disambig = f"{source_portal}_{source_id}"
            else:
                source_disambig = ""

            # Create a string representation
            fingerprint_str = f"{freguesia}_{tipologia}_{area_bucket}_{price_bucket}_{geo_bucket}_{source_disambig}"
            
            # Create a secure hash
            return hashlib.md5(fingerprint_str.encode("utf-8")).hexdigest()
            
        except Exception as e:
            source_id = get_val("source_id") or get_val("id") or "unknown"
            logger.error(f"Error generating fingerprint for {source_id}: {e}")
            # Fallback to source ID to ensure it doesn't collide randomly
            return hashlib.md5(str(source_id).encode("utf-8")).hexdigest()

    @classmethod
    def filter_duplicates(cls, raw_listings: List[RawListing], existing_fingerprints: set) -> List[RawListing]:
        """
        Filters out listings that have a fingerprint already present in the system.
        """
        unique_listings = []
        session_fingerprints = set()
        
        for listing in raw_listings:
            fingerprint = cls.generate_fingerprint(listing)
            
            if fingerprint in existing_fingerprints or fingerprint in session_fingerprints:
                title = listing.get("titulo", "") if isinstance(listing, dict) else getattr(listing, "titulo", "")
                portal = listing.get("source_portal", "") if isinstance(listing, dict) else getattr(listing, "source_portal", "")
                logger.debug(f"Duplicate filtered: {title} (Portal: {portal})")
                continue
                
            # Keep it
            session_fingerprints.add(fingerprint)
            unique_listings.append(listing)
            
        return unique_listings
