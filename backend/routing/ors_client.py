"""
OpenRouteService (ORS) Routing & Distance Matrix Client for DHRUVA.
Provides driving and walking matrix calculations with automatic caching,
rate-limit resilience, and zero-config Haversine road-winding fallback.
"""

from __future__ import annotations
import math
import time
import logging
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Any
import urllib.request
import urllib.error
import json

from backend.config import settings

logger = logging.getLogger("dhruva.routing")


@dataclass
class MatrixResult:
    """Distance and duration matrix between coordinates."""
    durations_minutes: List[List[float]]  # [i][j] in minutes
    distances_km: List[List[float]]       # [i][j] in kilometers
    locations: List[Tuple[float, float]]  # (lat, long) pairs
    source: str = "ors"                   # 'ors' or 'fallback'


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance between two points on Earth in kilometers.
    """
    R = 6371.0  # Earth radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


class ORSClient:
    """Client for OpenRouteService Matrix API with offline caching & fallback."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key if api_key is not None else settings.ors_api_key
        self.base_url = (base_url or settings.ors_base_url).rstrip("/")
        self.timeout = settings.ors_timeout_seconds
        # In-memory LRU-like distance cache: ((lat1, lon1), (lat2, lon2), profile) -> (duration_min, distance_km)
        self._cache: Dict[Tuple[Tuple[float, float], Tuple[float, float], str], Tuple[float, float]] = {}

    def calculate_matrix(
        self,
        coordinates: List[Tuple[float, float]],
        profile: str = "driving-car"
    ) -> MatrixResult:
        """
        Calculate NxN distance (km) and duration (minutes) matrix for coordinates [(lat, lon), ...].
        Uses live OpenRouteService Matrix API if ORS_API_KEY is present;
        falls back gracefully to road-adjusted Haversine calculations.
        """
        n = len(coordinates)
        if n == 0:
            return MatrixResult(durations_minutes=[], distances_km=[], locations=[], source="empty")

        if n == 1:
            return MatrixResult(durations_minutes=[[0.0]], distances_km=[[0.0]], locations=coordinates, source="identity")

        # Check if all pairs are in cache
        all_cached = True
        durations = [[0.0] * n for _ in range(n)]
        distances = [[0.0] * n for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if i == j:
                    durations[i][j] = 0.0
                    distances[i][j] = 0.0
                    continue
                pair_key = (coordinates[i], coordinates[j], profile)
                if pair_key in self._cache:
                    dur_min, dist_km = self._cache[pair_key]
                    distances[i][j] = dist_km
                    durations[i][j] = dur_min
                else:
                    all_cached = False

        if all_cached:
            return MatrixResult(durations_minutes=durations, distances_km=distances, locations=coordinates, source="cache")

        # Attempt ORS API call if API key exists
        if self.api_key and self.api_key.strip():
            try:
                res = self._query_ors_matrix(coordinates, profile)
                if res:
                    # Update cache with live results
                    for i in range(n):
                        for j in range(n):
                            pair_key = (coordinates[i], coordinates[j], profile)
                            self._cache[pair_key] = (res.durations_minutes[i][j], res.distances_km[i][j])
                    return res
            except Exception as e:
                logger.warning(f"ORS API request failed: {e}. Utilizing road-winding Haversine fallback.")

        # Deterministic fallback calculation
        return self._compute_fallback_matrix(coordinates, profile)

    def _query_ors_matrix(
        self,
        coordinates: List[Tuple[float, float]],
        profile: str
    ) -> Optional[MatrixResult]:
        """Send request to OpenRouteService Matrix API."""
        url = f"{self.base_url}/v2/matrix/{profile}"

        # ORS expects coordinates as [longitude, latitude]
        locations_payload = [[lon, lat] for lat, lon in coordinates]
        body = {
            "locations": locations_payload,
            "metrics": ["distance", "duration"]
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8",
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=self.timeout) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                # Durations in seconds -> convert to minutes
                raw_durations = data.get("durations", [])
                # Distances in meters -> convert to kilometers
                raw_distances = data.get("distances", [])

                n = len(coordinates)
                durations_min = [[0.0] * n for _ in range(n)]
                distances_km = [[0.0] * n for _ in range(n)]

                for i in range(n):
                    for j in range(n):
                        if i < len(raw_durations) and j < len(raw_durations[i]) and raw_durations[i][j] is not None:
                            durations_min[i][j] = round(raw_durations[i][j] / 60.0, 2)
                        if i < len(raw_distances) and j < len(raw_distances[i]) and raw_distances[i][j] is not None:
                            distances_km[i][j] = round(raw_distances[i][j] / 1000.0, 2)

                return MatrixResult(
                    durations_minutes=durations_min,
                    distances_km=distances_km,
                    locations=coordinates,
                    source="ors"
                )

        return None

    def _compute_fallback_matrix(
        self,
        coordinates: List[Tuple[float, float]],
        profile: str
    ) -> MatrixResult:
        """Compute distance and travel duration using road winding factor & city speed."""
        n = len(coordinates)
        durations = [[0.0] * n for _ in range(n)]
        distances = [[0.0] * n for _ in range(n)]

        speed_kmh = (
            settings.default_walking_speed_kmh
            if "foot" in profile or "walk" in profile
            else settings.default_driving_speed_kmh
        )
        winding = settings.road_winding_factor

        for i in range(n):
            lat1, lon1 = coordinates[i]
            for j in range(n):
                if i == j:
                    continue
                lat2, lon2 = coordinates[j]
                straight_km = haversine_distance_km(lat1, lon1, lat2, lon2)
                # Apply road network detour multiplier
                road_km = round(straight_km * winding, 2)
                # Duration in minutes
                duration_min = round((road_km / speed_kmh) * 60.0, 2)

                # Ensure a minimum 1 min travel time for non-identical locations
                if road_km > 0.05 and duration_min < 1.0:
                    duration_min = 1.0

                distances[i][j] = road_km
                durations[i][j] = duration_min

                # Populate cache
                pair_key = (coordinates[i], coordinates[j], profile)
                self._cache[pair_key] = (duration_min, road_km)

        return MatrixResult(
            durations_minutes=durations,
            distances_km=distances,
            locations=coordinates,
            source="fallback"
        )

    def get_travel_time_and_distance(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        profile: str = "driving-car"
    ) -> Tuple[float, float]:
        """
        Get (travel_time_minutes, travel_distance_km) between two coordinates.
        """
        if origin == destination:
            return (0.0, 0.0)

        pair_key = (origin, destination, profile)
        if pair_key in self._cache:
            return self._cache[pair_key]

        mat = self.calculate_matrix([origin, destination], profile=profile)
        time_min = mat.durations_minutes[0][1]
        dist_km = mat.distances_km[0][1]
        return (time_min, dist_km)


# Singleton ORS client
ors_client = ORSClient()
