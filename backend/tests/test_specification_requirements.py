"""
Comprehensive test suite verifying the 19 core specification requirements
for DHRUVA backend itinerary planning and optimization.

Requirements:
1. Single-window itinerary.
2. Multiple time windows.
3. Travel time from current node.
4. Visit duration inclusion.
5. Time-limit enforcement.
6. Opening-hour constraints.
7. Mandatory places.
8. Mandatory places that do not fit.
9. Dynamic removal of a place.
10. Dynamic reduction of available time.
11. Rebalancing across days.
12. Shuffle.
13. Maximum 3 shuffles.
14. No remaining feasible recommendations.
15. ORS failure.
16. Missing coordinates.
17. Empty city.
18. Persistence of itinerary.
19. Retrieval of saved itinerary.

Mock ORS in unit tests - no real network requests made.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, date, timedelta

from backend.database.db import db_repo, DataRepository
from backend.database.models import Trip, TripTimeWindow, Place, ItineraryItem, OpeningHour
from backend.algorithm.itinerary_generator import itinerary_generator, GenerationResult, ConflictReport
from backend.routing.ors_client import ors_client, MatrixResult, haversine_distance_km


@pytest.fixture
def repo():
    return db_repo


@pytest.fixture(autouse=True)
def mock_ors_calls():
    """Ensure no real ORS API network calls are made during tests."""
    with patch.object(ors_client, "_query_ors_matrix", return_value=None):
        yield


class TestDhruva19Requirements:

    # 1. Single-window itinerary
    def test_01_single_window_itinerary(self, repo):
        city = repo.get_city_by_name("Bhubaneswar")
        assert city is not None

        tw = TripTimeWindow(
            id=1,
            day_number=1,
            date_str="2026-10-15",
            window_start="09:00:00",
            window_end="15:00:00",  # 6 hours = 360 min
            start_lat=city.lat,
            start_long=city.long,
        )
        trip = Trip(
            id=201,
            title="Single Window Tour",
            mode="quick_visit",
            city_id=city.id,
            start_lat=city.lat,
            start_long=city.long,
            time_windows=[tw],
            preferences={"spiritual": 5.0, "architecture": 4.5}
        )

        res = itinerary_generator.generate(trip)
        assert res.status == "success"
        assert len(trip.itinerary_items) >= 1
        for it in trip.itinerary_items:
            assert it.day_number == 1
            arr_dt = datetime.strptime(it.arrival_time, "%Y-%m-%d %H:%M:%S")
            dep_dt = datetime.strptime(it.departure_time, "%Y-%m-%d %H:%M:%S")
            assert arr_dt >= datetime(2026, 10, 15, 9, 0, 0)
            assert dep_dt <= datetime(2026, 10, 15, 15, 5, 0)

    # 2. Multiple time windows
    def test_02_multiple_time_windows(self, repo):
        city = repo.get_city_by_name("Bhubaneswar")
        tw1 = TripTimeWindow(
            id=1,
            day_number=1,
            date_str="2026-10-15",
            window_start="10:00:00",
            window_end="18:00:00",
            start_lat=city.lat,
            start_long=city.long,
        )
        tw2 = TripTimeWindow(
            id=2,
            day_number=2,
            date_str="2026-10-16",
            window_start="09:00:00",
            window_end="17:00:00",
        )
        trip = Trip(
            id=202,
            title="Multi Window Tour",
            mode="full_trip",
            city_id=city.id,
            start_lat=city.lat,
            start_long=city.long,
            time_windows=[tw1, tw2],
            preferences={"spiritual": 4.5, "architecture": 4.5}
        )

        res = itinerary_generator.generate(trip)
        assert res.status == "success"
        day1_items = [it for it in trip.itinerary_items if it.day_number == 1]
        day2_items = [it for it in trip.itinerary_items if it.day_number == 2]
        assert len(day1_items) > 0
        assert len(day2_items) > 0

        # Verify Day 2 starts from location where Day 1 ended
        last_d1_place = day1_items[-1].place
        assert trip.time_windows[1].start_lat == last_d1_place.lat
        assert trip.time_windows[1].start_long == last_d1_place.long

    # 3. Travel time from current node
    def test_03_travel_time_from_current_node(self, repo):
        city = repo.get_city_by_name("Bhubaneswar")
        tw = TripTimeWindow(
            id=1,
            day_number=1,
            date_str="2026-10-15",
            window_start="08:00:00",
            window_end="19:00:00",
            start_lat=city.lat,
            start_long=city.long,
        )
        trip = Trip(
            id=203,
            city_id=city.id,
            start_lat=city.lat,
            start_long=city.long,
            time_windows=[tw],
            preferences={"spiritual": 5.0}
        )
        res = itinerary_generator.generate(trip)
        assert len(trip.itinerary_items) >= 2

        it1 = trip.itinerary_items[0]
        it2 = trip.itinerary_items[1]
        p1 = it1.place
        p2 = it2.place

        # Item 2's travel distance and time must correspond to distance between p1 and p2, not origin and p2
        _, exp_dist_p1_p2 = ors_client.get_travel_time_and_distance((p1.lat, p1.long), (p2.lat, p2.long))
        assert it2.travel_distance_km == pytest.approx(exp_dist_p1_p2, rel=1e-2)

    # 4. Visit duration inclusion
    def test_04_visit_duration_inclusion(self, repo):
        city = repo.get_city_by_name("Bhubaneswar")
        tw = TripTimeWindow(
            id=1,
            day_number=1,
            date_str="2026-10-15",
            window_start="09:00:00",
            window_end="18:00:00",
            start_lat=city.lat,
            start_long=city.long,
        )
        trip = Trip(
            id=204,
            city_id=city.id,
            start_lat=city.lat,
            start_long=city.long,
            time_windows=[tw],
            preferences={"spiritual": 5.0}
        )
        res = itinerary_generator.generate(trip)
        for it in trip.itinerary_items:
            arr = datetime.strptime(it.arrival_time, "%Y-%m-%d %H:%M:%S")
            dep = datetime.strptime(it.departure_time, "%Y-%m-%d %H:%M:%S")
            delta_min = int((dep - arr).total_seconds() / 60)
            assert delta_min == it.visit_duration_minutes
            assert it.visit_duration_minutes == it.place.duration_minutes

    # 5. Time-limit enforcement
    def test_05_time_limit_enforcement(self, repo):
        city = repo.get_city_by_name("Bhubaneswar")
        # Very short window: only 90 minutes
        tw = TripTimeWindow(
            id=1,
            day_number=1,
            date_str="2026-10-15",
            window_start="09:00:00",
            window_end="10:30:00",
            start_lat=city.lat,
            start_long=city.long,
        )
        trip = Trip(
            id=205,
            city_id=city.id,
            start_lat=city.lat,
            start_long=city.long,
            time_windows=[tw],
            preferences={"spiritual": 5.0}
        )
        res = itinerary_generator.generate(trip)
        for it in trip.itinerary_items:
            dep = datetime.strptime(it.departure_time, "%Y-%m-%d %H:%M:%S")
            assert dep <= datetime(2026, 10, 15, 10, 30, 0)

    # 6. Opening-hour constraints
    def test_06_opening_hour_constraints(self, repo):
        place = repo.get_place(1)
        assert place is not None
        # Verify check: place is open during its scheduled hours
        assert place.is_open_on_day_time("Monday", 600, 120) is True

        # Candidate place with strictly afternoon hours should not be open early morning
        test_place = Place(
            id=999,
            name="Afternoon Only Place",
            duration=1.0,
            popularity=5.0,
            lat=20.29,
            long=85.82,
            risk="low",
            city_id=1,
            opening_hours=[
                OpeningHour(id=1, place_id=999, day_of_week="Monday", opens_at="02:00 PM", closes_at="06:00 PM")
            ]
        )
        # At 09:00 AM (540 min from midnight), place is closed
        assert test_place.is_open_on_day_time("Monday", 540, 60) is False
        # At 03:00 PM (900 min from midnight), place is open
        assert test_place.is_open_on_day_time("Monday", 900, 60) is True

    # 7. Mandatory places
    def test_07_mandatory_places(self, repo):
        city = repo.get_city_by_name("Bhubaneswar")
        places = repo.get_places_by_city(city.id)
        mandatory_pids = [places[0].id, places[1].id]

        tw = TripTimeWindow(
            id=1,
            day_number=1,
            date_str="2026-10-15",
            window_start="08:00:00",
            window_end="20:00:00",
            start_lat=city.lat,
            start_long=city.long,
        )
        trip = Trip(
            id=207,
            city_id=city.id,
            start_lat=city.lat,
            start_long=city.long,
            time_windows=[tw],
            mandatory_place_ids=mandatory_pids
        )
        res = itinerary_generator.generate(trip)
        assert res.status == "success"
        scheduled_pids = {it.place_id for it in trip.itinerary_items}
        assert set(mandatory_pids).issubset(scheduled_pids)
        for it in trip.itinerary_items:
            if it.place_id in mandatory_pids:
                assert it.is_mandatory is True

    # 8. Mandatory places that do not fit
    def test_08_mandatory_places_that_do_not_fit(self, repo):
        city = repo.get_city_by_name("Bhubaneswar")
        places = repo.get_places_by_city(city.id)
        # 5 places take ~10+ hours
        mandatory_pids = [p.id for p in places[:5]]

        # Tiny window: 60 minutes
        tw = TripTimeWindow(
            id=1,
            day_number=1,
            date_str="2026-10-15",
            window_start="09:00:00",
            window_end="10:00:00",
            start_lat=city.lat,
            start_long=city.long,
        )
        trip = Trip(
            id=208,
            city_id=city.id,
            start_lat=city.lat,
            start_long=city.long,
            time_windows=[tw],
            mandatory_place_ids=mandatory_pids
        )
        res = itinerary_generator.generate(trip)
        assert res.status == "conflict"
        assert res.conflict is not None
        assert res.conflict.has_conflict is True
        assert res.conflict.deficit_minutes > 0
        assert len(res.conflict.unscheduled_mandatory_places) > 0
        assert "recommendation" in res.conflict.to_dict()

    # 9. Dynamic removal of a place
    def test_09_dynamic_removal_of_a_place(self, repo):
        city = repo.get_city_by_name("Bhubaneswar")
        tw = TripTimeWindow(
            id=1,
            day_number=1,
            date_str="2026-10-15",
            window_start="08:00:00",
            window_end="19:00:00",
            start_lat=city.lat,
            start_long=city.long,
        )
        trip = Trip(
            id=209,
            city_id=city.id,
            start_lat=city.lat,
            start_long=city.long,
            time_windows=[tw],
            preferences={"spiritual": 5.0}
        )
        itinerary_generator.generate(trip)
        initial_count = len(trip.itinerary_items)
        assert initial_count >= 2

        place_to_remove = trip.itinerary_items[0].place_id
        removed = itinerary_generator.remove_place_from_itinerary(trip, place_to_remove)
        assert removed is True
        assert len(trip.itinerary_items) == initial_count - 1
        assert place_to_remove not in {it.place_id for it in trip.itinerary_items}

        # Sequence orders must be continuous
        orders = [it.sequence_order for it in trip.itinerary_items]
        assert orders == list(range(1, len(trip.itinerary_items) + 1))

    # 10. Dynamic reduction of available time
    def test_10_dynamic_reduction_of_available_time(self, repo):
        city = repo.get_city_by_name("Bhubaneswar")
        tw = TripTimeWindow(
            id=1,
            day_number=1,
            date_str="2026-10-15",
            window_start="08:00:00",
            window_end="20:00:00",  # 12 hours
            start_lat=city.lat,
            start_long=city.long,
        )
        trip = Trip(
            id=210,
            city_id=city.id,
            start_lat=city.lat,
            start_long=city.long,
            time_windows=[tw],
            preferences={"spiritual": 5.0}
        )
        res_full = itinerary_generator.generate(trip)
        count_full = len(res_full.items)

        # Cut time window in half (4 hours instead of 12)
        trip.time_windows[0].window_end = "12:00:00"
        res_reduced = itinerary_generator.generate(trip)
        assert len(res_reduced.items) < count_full
        for it in res_reduced.items:
            dep = datetime.strptime(it.departure_time, "%Y-%m-%d %H:%M:%S")
            assert dep <= datetime(2026, 10, 15, 12, 5, 0)

    # 11. Rebalancing across days
    def test_11_rebalancing_across_days(self, repo):
        city = repo.get_city_by_name("Bhubaneswar")
        tw1 = TripTimeWindow(
            id=1,
            day_number=1,
            date_str="2026-10-15",
            window_start="08:00:00",
            window_end="18:00:00",
            start_lat=city.lat,
            start_long=city.long,
        )
        tw2 = TripTimeWindow(
            id=2,
            day_number=2,
            date_str="2026-10-16",
            window_start="08:00:00",
            window_end="18:00:00",
        )
        trip = Trip(
            id=211,
            city_id=city.id,
            start_lat=city.lat,
            start_long=city.long,
            time_windows=[tw1, tw2],
            preferences={"spiritual": 5.0}
        )
        itinerary_generator.generate(trip)
        d1_initial = [it for it in trip.itinerary_items if it.day_number == 1]
        assert len(d1_initial) >= 2

        # Shorten Day 1 window significantly so places overflow to Day 2
        trip.time_windows[0].window_end = "10:30:00"
        itinerary_generator.rebalance_itinerary(trip)

        # Some items should have rolled over to Day 2
        d1_after = [it for it in trip.itinerary_items if it.day_number == 1]
        d2_after = [it for it in trip.itinerary_items if it.day_number == 2]
        assert len(d1_after) < len(d1_initial)
        assert len(d2_after) > 0

    # 12. Shuffle
    def test_12_shuffle(self, repo):
        city = repo.get_city_by_name("Bhubaneswar")
        tw = TripTimeWindow(
            id=1,
            day_number=1,
            date_str="2026-10-15",
            window_start="08:00:00",
            window_end="19:00:00",
            start_lat=city.lat,
            start_long=city.long,
        )
        trip = Trip(
            id=212,
            city_id=city.id,
            start_lat=city.lat,
            start_long=city.long,
            time_windows=[tw],
            preferences={"spiritual": 5.0, "architecture": 4.5}
        )
        res_initial = itinerary_generator.generate(trip)
        repo.save_trip(trip)

        shuffle_res = itinerary_generator.generate_shuffle(trip)
        assert shuffle_res.status == "success"
        assert shuffle_res.shuffle_count == 1
        assert len(shuffle_res.items) > 0

    # 13. Maximum 3 shuffles
    def test_13_maximum_3_shuffles(self, repo):
        city = repo.get_city_by_name("Bhubaneswar")
        tw = TripTimeWindow(
            id=1,
            day_number=1,
            date_str="2026-10-15",
            window_start="08:00:00",
            window_end="19:00:00",
            start_lat=city.lat,
            start_long=city.long,
        )
        trip = Trip(
            id=213,
            city_id=city.id,
            start_lat=city.lat,
            start_long=city.long,
            time_windows=[tw],
        )
        itinerary_generator.generate(trip)
        repo.save_trip(trip)

        s1 = itinerary_generator.generate_shuffle(trip)
        assert s1.shuffle_count == 1
        s2 = itinerary_generator.generate_shuffle(trip)
        assert s2.shuffle_count == 2
        s3 = itinerary_generator.generate_shuffle(trip)
        assert s3.shuffle_count == 3

        with pytest.raises(ValueError) as exc:
            itinerary_generator.generate_shuffle(trip)
        assert "maximum shuffle limit of 3 reached" in str(exc.value).lower()

    # 14. No remaining feasible recommendations
    def test_14_no_remaining_feasible_recommendations(self, repo):
        city = repo.get_city_by_name("Bhubaneswar")
        # 15 minutes window: no place in Bhubaneswar has visit + travel <= 15 min
        tw = TripTimeWindow(
            id=1,
            day_number=1,
            date_str="2026-10-15",
            window_start="09:00:00",
            window_end="09:15:00",
            start_lat=city.lat,
            start_long=city.long,
        )
        trip = Trip(
            id=214,
            city_id=city.id,
            start_lat=city.lat,
            start_long=city.long,
            time_windows=[tw],
        )
        res = itinerary_generator.generate(trip)
        assert res.status in ("no_feasible_places", "success")
        assert len(res.items) == 0

    # 15. ORS failure
    def test_15_ors_failure(self, repo):
        # Simulate complete failure of live ORS API
        with patch.object(ors_client, "_query_ors_matrix", side_effect=Exception("ORS API Network Timeout")):
            coords = [(20.2961, 85.8245), (19.8135, 85.8312)]
            matrix_res = ors_client.calculate_matrix(coords)
            assert matrix_res is not None
            assert matrix_res.source == "fallback"
            assert matrix_res.durations_minutes[0][1] > 0
            assert matrix_res.distances_km[0][1] > 0

    # 16. Missing coordinates
    def test_16_missing_coordinates(self, repo):
        # Place with missing coordinates
        bad_place = Place(
            id=9999,
            name="Ghost Place",
            duration=1.0,
            popularity=4.0,
            lat=None,
            long=None,
            risk="low",
            city_id=1
        )
        repo.places[9999] = bad_place
        try:
            city = repo.get_city(1)
            tw = TripTimeWindow(
                id=1, day_number=1, date_str="2026-10-15",
                window_start="09:00:00", window_end="18:00:00",
                start_lat=city.lat, start_long=city.long
            )
            trip = Trip(id=216, city_id=1, start_lat=city.lat, start_long=city.long, time_windows=[tw])
            res = itinerary_generator.generate(trip)
            # Bad place must not be included
            assert 9999 not in {it.place_id for it in res.items}
        finally:
            del repo.places[9999]

    # 17. Empty city
    def test_17_empty_city(self, repo):
        # Query nonexistent city
        tw = TripTimeWindow(id=1, day_number=1, date_str="2026-10-15", window_start="09:00:00", window_end="18:00:00")
        trip = Trip(id=217, city_id=99999, time_windows=[tw])
        with pytest.raises(ValueError) as exc:
            itinerary_generator.generate(trip)
        assert "does not exist" in str(exc.value).lower() or "no places" in str(exc.value).lower()

    # 18. Persistence of itinerary
    def test_18_persistence_of_itinerary(self, repo):
        city = repo.get_city_by_name("Bhubaneswar")
        tw = TripTimeWindow(
            id=None,
            day_number=1,
            date_str="2026-10-15",
            window_start="09:00:00",
            window_end="18:00:00",
            start_lat=city.lat,
            start_long=city.long,
        )
        trip = Trip(
            id=None,
            title="Persisted Journey",
            mode="full_trip",
            city_id=city.id,
            start_lat=city.lat,
            start_long=city.long,
            time_windows=[tw],
            preferences={"spiritual": 5.0}
        )
        itinerary_generator.generate(trip)
        saved = repo.save_trip(trip)
        assert saved.id is not None
        assert saved.id > 0
        assert len(saved.itinerary_items) > 0
        for it in saved.itinerary_items:
            assert it.id is not None
            assert it.trip_id == saved.id

    # 19. Retrieval of saved itinerary
    def test_19_retrieval_of_saved_itinerary(self, repo):
        city = repo.get_city_by_name("Bhubaneswar")
        tw = TripTimeWindow(
            id=None,
            day_number=1,
            date_str="2026-10-15",
            window_start="09:00:00",
            window_end="18:00:00",
            start_lat=city.lat,
            start_long=city.long,
        )
        trip = Trip(
            id=None,
            title="Retrieve Journey",
            mode="full_trip",
            city_id=city.id,
            start_lat=city.lat,
            start_long=city.long,
            time_windows=[tw],
            preferences={"spiritual": 5.0}
        )
        itinerary_generator.generate(trip)
        saved = repo.save_trip(trip)

        # Retrieve by trip ID
        retrieved = repo.get_trip(saved.id)
        assert retrieved is not None
        assert retrieved.id == saved.id
        assert retrieved.title == "Retrieve Journey"
        assert len(retrieved.itinerary_items) == len(saved.itinerary_items)
        assert retrieved.itinerary_items[0].place is not None
        assert retrieved.itinerary_items[0].place.name != ""
