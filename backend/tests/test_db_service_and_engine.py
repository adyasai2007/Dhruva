"""
Unit tests for DhruvaDBService and CulturalItineraryEngine.
"""

import pytest
from backend.database.db_service import DhruvaDBService, dhruva_db
from backend.services.itinerary_engine import (
    CulturalItineraryEngine,
    UserPlannerPreferences,
    CULTURAL_CATEGORY_TIPS,
    DAY_THEMES,
)


class TestDhruvaDBService:
    @pytest.fixture
    def service(self):
        return dhruva_db

    def test_get_cities(self, service):
        cities = service.get_cities()
        assert len(cities) == 3
        bhubaneswar = next((c for c in cities if c["name"] == "Bhubaneswar"), None)
        assert bhubaneswar is not None
        assert bhubaneswar["place_count"] > 0
        assert 0.0 <= bhubaneswar["avg_rating"] <= 5.0
        assert bhubaneswar["state"] == "Odisha"

    def test_get_city_by_name_and_id(self, service):
        puri_by_name = service.get_city_by_name("Puri")
        assert puri_by_name is not None
        puri_by_id = service.get_city_by_id(puri_by_name["id"])
        assert puri_by_id is not None
        assert puri_by_name["name"] == puri_by_id["name"] == "Puri"

    def test_get_places_filters(self, service):
        # 1. Filter by city_name
        bbsr_places = service.get_places(city_name="Bhubaneswar")
        assert len(bbsr_places) > 0
        for p in bbsr_places:
            assert p["city_id"] == 1

        # 2. Filter by category
        temples = service.get_places(category="Temple")
        assert len(temples) > 0
        for p in temples:
            assert "temple" in (p["category"] or "").lower()

        # 3. Filter by min_rating and limit
        top_rated = service.get_places(min_rating=4.5, limit=5)
        assert len(top_rated) <= 5
        for p in top_rated:
            assert p["popularity"] >= 4.5

        # 4. Check serialization of opening hours and interests
        sample = bbsr_places[0]
        assert "interests" in sample
        assert "opening_hours" in sample
        assert isinstance(sample["opening_hours"], list)

    def test_get_festivals(self, service):
        all_festivals = service.get_festivals()
        assert len(all_festivals) > 0
        puri_festivals = service.get_festivals(city_name="Puri")
        assert len(puri_festivals) > 0
        rath_yatra = next((f for f in puri_festivals if "Ratha" in f["name"] or "Rath" in f["name"]), None)
        assert rath_yatra is not None


class TestCulturalItineraryEngine:
    @pytest.fixture
    def engine(self):
        return CulturalItineraryEngine()

    def test_time_parsing_utilities(self, engine):
        assert engine._parse_time_to_24h("08:30 AM") == "08:30:00"
        assert engine._parse_time_to_24h("07:45 PM") == "19:45:00"
        assert engine._parse_time_to_24h("14:20") == "14:20:00"
        assert engine._parse_time_to_24h("09:00") == "09:00:00"

        assert engine._format_iso_to_ampm("2026-10-15 08:30:00") == "08:30 AM"
        assert engine._format_iso_to_ampm("2026-10-15 19:45:00") == "07:45 PM"

    def test_generate_itinerary_senior_friendly(self, engine):
        prefs = UserPlannerPreferences(
            city_name="Bhubaneswar",
            start_date="2026-10-15",
            num_days=2,
            start_time="08:30 AM",
            end_time="06:30 PM",
            age=62,  # Senior traveler (>= 50)
            pacing="relaxed",
            interests={"spiritual": 5.0, "architecture": 4.5, "history": 4.0},
        )

        plan = engine.generate_itinerary(prefs)
        assert plan["status"] == "success"
        assert plan["senior_friendly"] is True
        assert plan["destination"] == "Bhubaneswar"
        assert plan["pacing_profile"] == "relaxed"
        assert len(plan["days"]) == 2

        day1 = plan["days"][0]
        assert day1["day_number"] == 1
        assert day1["theme"] in DAY_THEMES
        assert len(day1["activities"]) > 0

        for act in day1["activities"]:
            assert "cultural_tip" in act
            assert len(act["cultural_tip"]) > 0
            assert "time_slot" in act
            assert " - " in act["time_slot"]
