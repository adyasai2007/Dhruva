"""
Spatial Geocoding and Coordinate Resolution Module for DHRUVA.
Automatically resolves latitude and longitude coordinates for cultural landmarks,
temples, and cities using OpenStreetMap Nominatim, Google Maps API, and persistent local caching.
Includes Odisha spatial bounding box validation.
"""

from __future__ import annotations
import json
import logging
import time
from pathlib import Path
from typing import Dict, Optional, Tuple
import requests

logger = logging.getLogger("dhruva.scraper.geocoder")

# Odisha Geographic Bounding Box
ODISHA_BBOX = {
    "min_lat": 17.5,
    "max_lat": 23.0,
    "min_lon": 81.0,
    "max_lon": 87.5,
}


def is_within_odisha_bounds(lat: float, lon: float) -> bool:
    """Check if given GPS coordinate pair falls within the geographic bounds of Odisha state."""
    return (
        ODISHA_BBOX["min_lat"] <= lat <= ODISHA_BBOX["max_lat"]
        and ODISHA_BBOX["min_lon"] <= lon <= ODISHA_BBOX["max_lon"]
    )


class DhruvaGeocoder:
    """
    Automated Geocoder with persistent disk caching, multi-query fallback strategies,
    spatial bounding box validation, and OpenStreetMap / Google Maps integration.
    """

    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    DEFAULT_USER_AGENT = "DhruvaCulturalTravelPlanner/1.0 (dev@dhruva.app; educational/heritage research)"

    def __init__(
        self,
        cache_file: Optional[Path] = None,
        google_api_key: Optional[str] = None,
        rate_limit_delay: float = 1.0,
        user_agent: Optional[str] = None
    ):
        self.cache_file = cache_file or Path("data/scraped/.geocache.json")
        self.google_api_key = google_api_key
        self.rate_limit_delay = rate_limit_delay
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self.last_request_time = 0.0
        self.cache: Dict[str, Dict[str, float]] = self._load_cache()

    def _load_cache(self) -> Dict[str, Dict[str, float]]:
        """Load cached coordinates from disk if available."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.debug(f"Loaded {len(data)} cached geolocations from {self.cache_file}")
                    return data
            except Exception as e:
                logger.warning(f"Failed to read geocache at {self.cache_file}: {e}")
        return {}

    def _save_cache(self) -> None:
        """Persist coordinate cache to disk."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Could not persist geocache: {e}")

    def _throttle(self) -> None:
        """Enforce rate limits between queries to respect OpenStreetMap usage policies."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def geocode_osm(self, query: str) -> Optional[Tuple[float, float]]:
        """Query OpenStreetMap Nominatim for GPS coordinates with bounding box sanity check."""
        self._throttle()
        headers = {
            "User-Agent": self.user_agent,
            "Accept-Language": "en"
        }
        params = {
            "q": query,
            "format": "json",
            "limit": 1,
            "addressdetails": 1
        }
        try:
            response = requests.get(self.NOMINATIM_URL, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                results = response.json()
                if results and len(results) > 0:
                    lat = float(results[0]["lat"])
                    lon = float(results[0]["lon"])
                    if is_within_odisha_bounds(lat, lon):
                        return round(lat, 6), round(lon, 6)
                    else:
                        logger.warning(f"OSM coordinate ({lat}, {lon}) for '{query}' fell outside Odisha bounding box.")
            else:
                logger.debug(f"Nominatim HTTP {response.status_code} for query: {query}")
        except Exception as e:
            logger.debug(f"Nominatim request error for '{query}': {e}")
        return None

    def geocode_google(self, query: str) -> Optional[Tuple[float, float]]:
        """Query Google Maps Geocoding API if key is available."""
        if not self.google_api_key:
            return None
        self._throttle()
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": query, "key": self.google_api_key}
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "OK" and data.get("results"):
                    loc = data["results"][0]["geometry"]["location"]
                    lat, lng = round(float(loc["lat"]), 6), round(float(loc["lng"]), 6)
                    if is_within_odisha_bounds(lat, lng):
                        return lat, lng
        except Exception as e:
            logger.debug(f"Google Maps geocode error for '{query}': {e}")
        return None

    def get_coordinates(
        self,
        place_name: str,
        city: str = "",
        state: str = "Odisha"
    ) -> Tuple[float, float]:
        """
        Resolve exact latitude and longitude with multi-stage fallback queries.

        Resolution Priority:
        1. Local Disk Cache
        2. Google Maps API (if key provided)
        3. OpenStreetMap Nominatim: Exact Place Query
        4. OpenStreetMap Nominatim: Simplified Place + City Query
        5. OpenStreetMap Nominatim: City Default Coordinates
        6. Default Regional Fallback Coordinates
        """
        cache_key = f"{place_name.lower().strip()}|{city.lower().strip()}|{state.lower().strip()}"
        if cache_key in self.cache:
            hit = self.cache[cache_key]
            lat, lon = hit["lat"], hit["long"]
            if is_within_odisha_bounds(lat, lon):
                return lat, lon

        clean_name = place_name.split("(")[0].strip()

        # Strategy 1: Google Maps (if available)
        if self.google_api_key:
            coords = self.geocode_google(f"{clean_name}, {city}, {state}, India")
            if coords:
                self.cache[cache_key] = {"lat": coords[0], "long": coords[1]}
                self._save_cache()
                return coords

        # Strategy 2: Exact Landmark in City
        search_queries = [
            f"{clean_name}, {city}, {state}, India",
            f"{clean_name}, {city}, India",
            f"{clean_name}, {state}, India",
            f"{clean_name} Temple, {city}",
            f"{clean_name}, India",
        ]

        for q in search_queries:
            coords = self.geocode_osm(q)
            if coords:
                logger.info(f"✓ Geocoded '{place_name}' -> ({coords[0]}, {coords[1]}) via query '{q}'")
                self.cache[cache_key] = {"lat": coords[0], "long": coords[1]}
                self._save_cache()
                return coords

        # Strategy 3: Fall back to City center coordinates
        city_key = f"__city__|{city.lower().strip()}|{state.lower().strip()}"
        if city_key in self.cache:
            city_coords = self.cache[city_key]
            lat, lon = city_coords["lat"], city_coords["long"]
            if is_within_odisha_bounds(lat, lon):
                return lat, lon

        city_coords = self.geocode_osm(f"{city}, {state}, India")
        if city_coords:
            logger.warning(f"⚠️ Landmark '{place_name}' not found; using city coordinates for {city}: {city_coords}")
            self.cache[city_key] = {"lat": city_coords[0], "long": city_coords[1]}
            self.cache[cache_key] = {"lat": city_coords[0], "long": city_coords[1]}
            self._save_cache()
            return city_coords

        # Strategy 4: Regional Default (Odisha center / Bhubaneswar)
        default_coords = (20.2961, 85.8245)
        logger.warning(f"⚠️ Geocoding failed completely for '{place_name}'; defaulted to {default_coords}")
        return default_coords
