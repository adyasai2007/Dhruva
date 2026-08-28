"""
Unit tests for routing service, Haversine formula, road detour, and ORS matrix client.
"""

import pytest
from backend.config import settings
from backend.routing.ors_client import (
    haversine_distance_km,
    ORSClient,
    MatrixResult,
)


class TestHaversineAndDetour:
    def test_haversine_same_point(self):
        lat, lon = 20.2961, 85.8245
        dist = haversine_distance_km(lat, lon, lat, lon)
        assert dist == 0.0

    def test_haversine_bhubaneswar_to_puri(self):
        # Bhubaneswar: 20.2961, 85.8245; Puri: 19.8135, 85.8312
        dist = haversine_distance_km(20.2961, 85.8245, 19.8135, 85.8312)
        # Straight line is ~53.6 km
        assert 50.0 <= dist <= 60.0


class TestORSClient:
    @pytest.fixture
    def client(self):
        # Client initialized with empty/mock key to test robust fallback
        return ORSClient(api_key="")

    def test_single_pair_distance_and_duration(self, client):
        origin = (20.2961, 85.8245)
        dest = (20.2382, 85.8338)  # ~6.5 km in Bhubaneswar
        dur_min, dist_km = client.get_travel_time_and_distance(origin, dest)

        assert dist_km > 0.0
        assert dur_min > 0.0
        # In-memory cache should now contain this pair
        cache_key = (origin, dest, "driving-car")
        assert cache_key in client._cache

    def test_cache_hits_on_subsequent_calls(self, client):
        origin = (20.2961, 85.8245)
        dest = (20.2382, 85.8338)

        # First call
        t1, d1 = client.get_travel_time_and_distance(origin, dest)
        # Second call
        t2, d2 = client.get_travel_time_and_distance(origin, dest)

        assert d1 == d2
        assert t1 == t2

    def test_calculate_matrix_dimensions_and_diagonal(self, client):
        coords = [
            (20.2961, 85.8245),  # City Center
            (20.2382, 85.8338),  # Lingaraj Temple
            (20.2588, 85.7891),  # Udayagiri & Khandagiri
        ]
        matrix_res: MatrixResult = client.calculate_matrix(coords)

        durations = matrix_res.durations_minutes
        distances = matrix_res.distances_km

        assert len(durations) == 3
        assert len(distances) == 3
        for i in range(3):
            assert len(durations[i]) == 3
            assert len(distances[i]) == 3
            # Diagonal must be zero
            assert durations[i][i] == 0.0
            assert distances[i][i] == 0.0
            # Non-diagonal must be positive
            for j in range(3):
                if i != j:
                    assert durations[i][j] > 0.0
                    assert distances[i][j] > 0.0

    def test_fallback_road_winding_calculation(self, client):
        origin = (20.0, 85.0)
        dest = (20.0, 85.1)
        straight_km = haversine_distance_km(origin[0], origin[1], dest[0], dest[1])
        dur_min, road_km = client.get_travel_time_and_distance(origin, dest, profile="driving-car")

        # Road distance applies 1.3x detour factor
        expected_road_km = round(straight_km * settings.road_winding_factor, 2)
        assert pytest.approx(road_km, 0.05) == expected_road_km
        # Driving speed check (30 km/h)
        expected_dur_min = round((road_km / settings.default_driving_speed_kmh) * 60.0, 2)
        assert pytest.approx(dur_min, 0.05) == expected_dur_min
