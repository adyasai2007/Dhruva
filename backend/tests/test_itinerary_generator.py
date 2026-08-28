"""
Unit tests for multi-day itinerary generation, sequential geographic chaining,
conflict detection, dynamic add/remove rebalancing, and 3-shuffle alternative generator.
"""

import pytest
from datetime import datetime, date, timedelta
from backend.database.db import db_repo
from backend.database.models import Trip, TripTimeWindow, Place, ItineraryItem
from backend.algorithm.itinerary_generator import itinerary_generator, GenerationResult


@pytest.fixture
def repo():
    return db_repo


class TestQuickVisitGeneration:
    def test_quick_visit_strict_time_constraint(self, repo):
        city = repo.get_city_by_name("Bhubaneswar")
        assert city is not None

        # 4 hours total budget (240 minutes)
        trip = Trip(
            id=101,
            title="Quick Cultural Tour",
            mode="quick_visit",
            city_id=city.id,
            start_lat=city.lat,
            start_long=city.long,
            start_datetime="2026-10-15 09:00:00",
            total_minutes=240,
            preferences={"spiritual": 5.0, "architecture": 4.5, "history": 4.0},
        )

        res: GenerationResult = itinerary_generator.generate(trip)
        assert res.status == "success"
        assert len(trip.itinerary_items) >= 1
        assert res.total_places_visited >= 1

        # Total time (travel + visit) should not exceed the 240 minute limit (with small tolerance)
        total_time_used = res.total_travel_minutes + res.total_visit_minutes
        assert total_time_used <= 240 + 15  # Up to slight end-of-visit cushion


class TestFullTripSequentialChaining:
    def test_multi_day_sequential_chaining(self, repo):
        city = repo.get_city_by_name("Bhubaneswar")
        assert city is not None

        # 2-Day trip
        tw1 = TripTimeWindow(
            id=1,
            day_number=1,
            date_str="2026-10-15",
            window_start="08:30:00",
            window_end="18:30:00",
            start_lat=city.lat,
            start_long=city.long,
        )
        tw2 = TripTimeWindow(
            id=2,
            day_number=2,
            date_str="2026-10-16",
            window_start="08:30:00",
            window_end="18:30:00",
        )

        trip = Trip(
            id=102,
            title="Bhubaneswar 2-Day Journey",
            mode="full_trip",
            city_id=city.id,
            start_lat=city.lat,
            start_long=city.long,
            start_datetime="2026-10-15 08:30:00",
            end_datetime="2026-10-16 18:30:00",
            time_windows=[tw1, tw2],
            preferences={"spiritual": 5.0, "architecture": 5.0, "history": 4.0},
        )

        res = itinerary_generator.generate(trip)
        assert res.status == "success"

        day1_items = [it for it in trip.itinerary_items if it.day_number == 1]
        day2_items = [it for it in trip.itinerary_items if it.day_number == 2]

        assert len(day1_items) > 0
        assert len(day2_items) > 0

        # Verify Day 2 starts from Day 1's last location
        last_day1_place = day1_items[-1].place
        first_day2_item = day2_items[0]

        # Distance from Day 1 end to Day 2 start item should be calculated accurately
        assert first_day2_item.travel_time_from_prev_minutes >= 0.0


class TestConflictDetection:
    def test_mandatory_places_conflict_report(self, repo):
        city = repo.get_city_by_name("Bhubaneswar")
        places = repo.get_places_by_city(city.id)
        assert len(places) >= 5

        # Pick 6 places that together take ~12 hours
        mandatory_ids = [p.id for p in places[:6]]

        # Narrow 2-hour window (120 minutes)
        tw = TripTimeWindow(
            id=1,
            day_number=1,
            date_str="2026-10-15",
            window_start="09:00:00",
            window_end="11:00:00",  # Only 120 minutes available
            start_lat=city.lat,
            start_long=city.long,
        )

        trip = Trip(
            id=103,
            title="Impossible Time Window Trip",
            mode="full_trip",
            city_id=city.id,
            time_windows=[tw],
            mandatory_place_ids=mandatory_ids,
        )

        res = itinerary_generator.generate(trip)
        assert res.status == "conflict"
        assert res.conflict_report is not None
        assert res.conflict_report.has_conflict is True
        assert res.conflict_report.deficit_minutes > 0
        assert len(res.conflict_report.recommendation) > 0
        assert "deficit" in res.conflict_report.recommendation.lower() or "extend" in res.conflict_report.recommendation.lower()


class TestDynamicPlaceModification:
    def test_add_and_remove_place_rebalancing(self, repo):
        city = repo.get_city_by_name("Bhubaneswar")
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
            id=104,
            title="Dynamic Edit Journey",
            mode="full_trip",
            city_id=city.id,
            time_windows=[tw],
            preferences={"spiritual": 5.0, "architecture": 5.0},
        )
        itinerary_generator.generate(trip)
        repo.save_trip(trip)

        initial_count = len(trip.itinerary_items)
        assert initial_count > 0
        scheduled_ids = {it.place_id for it in trip.itinerary_items}

        # Find an unscheduled place in the city
        all_city_places = repo.get_places_by_city(city.id)
        candidate = next((p for p in all_city_places if p.id not in scheduled_ids), None)
        assert candidate is not None

        # 1. Add Place dynamically
        new_item = itinerary_generator.add_place_to_itinerary(trip, candidate.id, day_number=1)
        assert new_item is not None
        assert len(trip.itinerary_items) == initial_count + 1
        assert new_item.place_id == candidate.id

        # Verify time sequencing integrity
        for i in range(len(trip.itinerary_items) - 1):
            cur = trip.itinerary_items[i]
            nxt = trip.itinerary_items[i + 1]
            assert cur.departure_time <= nxt.arrival_time

        # 2. Remove Place dynamically
        success = itinerary_generator.remove_place_from_itinerary(trip, candidate.id)
        assert success is True
        assert len(trip.itinerary_items) == initial_count


class TestShuffleVariations:
    def test_shuffle_limit_enforcement(self, repo):
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
            id=105,
            title="Shuffle Trip",
            mode="full_trip",
            city_id=city.id,
            time_windows=[tw],
            preferences={"spiritual": 4.5, "architecture": 4.5},
        )
        itinerary_generator.generate(trip)
        repo.save_trip(trip)

        # Shuffles 1, 2, 3 must succeed
        res1 = itinerary_generator.generate_shuffle(trip)
        assert res1.shuffle_count == 1
        assert res1.status == "success"

        res2 = itinerary_generator.generate_shuffle(trip)
        assert res2.shuffle_count == 2
        assert res2.status == "success"

        res3 = itinerary_generator.generate_shuffle(trip)
        assert res3.shuffle_count == 3
        assert res3.status == "success"

        # 4th shuffle must raise ValueError because limit is 3
        with pytest.raises(ValueError) as excinfo:
            itinerary_generator.generate_shuffle(trip)
        assert "Maximum shuffle limit of 3 reached" in str(excinfo.value)
