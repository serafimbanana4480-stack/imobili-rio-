"""Client for OpenStreetMap Overpass API to find Points of Interest."""
import requests
import asyncio
from typing import Dict, List, Optional, Tuple
from loguru import logger
import time

class POIClient:
    """Finds distances to nearby amenities using OSM Overpass API with caching."""
    
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"
    
    def __init__(self):
        self.last_request = 0
        self.cooldown = 1.0  # Respect Overpass API rate limit (~1 req/s)
        self.cache: Dict[str, Optional[float]] = {}
    
    async def _query(self, lat: float, lon: float, amenity: str, radius: int = 1500) -> List[Dict]:
        """Query Overpass for specific amenities near coordinates (async)."""
        now = time.time()
        if now - self.last_request < self.cooldown:
            await asyncio.sleep(self.cooldown - (now - self.last_request))
        
        # Example query for metro stations - filtered to Portugal
        query = f"""
        [out:json];
        area["name"="Portugal"]->.searchArea;
        (
          node["railway"="station"]["station"="subway"](around.searchArea:{radius},{lat},{lon});
          node["amenity"="{amenity}"](around.searchArea:{radius},{lat},{lon});
        );
        out body;
        """
        try:
            response = requests.post(self.OVERPASS_URL, data={"data": query}, timeout=15)
            self.last_request = time.time()
            if response.status_code == 200:
                return response.json().get('elements', [])
        except Exception as e:
            logger.error(f"POI Query failed: {e}")
        return []

    async def get_nearest_distance(self, lat: float, lon: float, category: str) -> Optional[float]:
        """Calculate distance to nearest amenity of category with coordinate caching (async)."""
        if not lat or not lon:
            return None
            
        # Create a grid-based cache key (approx 500m precision)
        cache_key = f"{category}_{round(lat, 3)}_{round(lon, 3)}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        amenity_map = {
            "metro": "subway",
            "school": "school",
            "market": "supermarket"
        }
        
        elements = await self._query(lat, lon, amenity_map.get(category, category))
        if not elements:
            return None
            
        # Calculate Haversine distance for all and take min
        from geopy.distance import geodesic
        distances = [geodesic((lat, lon), (el['lat'], el['lon'])).meters for el in elements if 'lat' in el]
        
        result = min(distances) if distances else None
        self.cache[cache_key] = result
        return result
