"""
Unit tests for deterministic multi-factor scoring engine (backend/algorithm/scoring.py).
"""

import pytest
from backend.database.models import Place, MinInterest, OpeningHour
from backend.algorithm.scoring import (
    calculate_interest_similarity,
    calculate_cultural_relevance,
    calculate_place_utility,
    score_place_candidate,
    CATEGORY_CULTURAL_WEIGHTS,
    INTEREST_DIMENSIONS,
)


@pytest.fixture
def sample_interests():
    return MinInterest(
        place_id=1,
        architecture=5.0,
        history=4.0,
        spiritual=5.0,
        nature=1.0,
        culture=4.0
    )


@pytest.fixture
def sample_place(sample_interests):
    p = Place(
        id=1,
        name="Lingaraj Temple",
        duration=2.0,
        popularity=4.8,
        lat=20.2382,
        long=85.8338,
        risk="Low",
        city_id=1,
        category="Temple & Sacred Sanctum",
        interests=sample_interests,
    )
    p.opening_hours = [
        OpeningHour(id=1, place_id=1, day_of_week="Monday", opens_at="06:00:00", closes_at="21:00:00"),
        OpeningHour(id=2, place_id=1, day_of_week="Tuesday", opens_at="06:00:00", closes_at="21:00:00"),
    ]
    return p


class TestInterestSimilarity:
    def test_exact_match_similarity(self, sample_interests):
        user_prefs = {"architecture": 5.0, "history": 4.0, "spiritual": 5.0, "nature": 1.0, "culture": 4.0}
        sim = calculate_interest_similarity(user_prefs, sample_interests)
        assert pytest.approx(sim, 0.0001) == 1.0

    def test_orthogonal_vectors_similarity(self):
        # Place interested only in nature and architecture
        place_int = MinInterest(place_id=2, architecture=5.0, history=0.0, spiritual=0.0, nature=5.0, culture=0.0)
        # User interested only in spiritual and history
        user_prefs = {"architecture": 0.0, "history": 5.0, "spiritual": 5.0, "nature": 0.0, "culture": 0.0}
        sim = calculate_interest_similarity(user_prefs, place_int)
        assert pytest.approx(sim, 0.0001) == 0.0

    def test_none_place_interest_returns_default(self):
        user_prefs = {"architecture": 5.0, "spiritual": 5.0}
        sim = calculate_interest_similarity(user_prefs, None)
        assert sim == 0.5

    def test_empty_user_prefs_returns_average(self, sample_interests):
        user_prefs = {}
        sim = calculate_interest_similarity(user_prefs, sample_interests)
        assert 0.0 <= sim <= 1.0

    def test_zero_place_interest_profile(self):
        place_int = MinInterest(place_id=3, architecture=0.0, history=0.0, spiritual=0.0, nature=0.0, culture=0.0)
        user_prefs = {"spiritual": 5.0}
        sim = calculate_interest_similarity(user_prefs, place_int)
        assert sim == 0.3


class TestCulturalRelevance:
    def test_sacred_sanctum_weight(self, sample_place):
        sample_place.category = "Heritage & Sacred Sanctum"
        sample_place.name = "Ananta Vasudeva Temple"
        score = calculate_cultural_relevance(sample_place)
        assert score == CATEGORY_CULTURAL_WEIGHTS["heritage & sacred sanctum"]

    def test_flagship_unesco_boost(self, sample_place):
        sample_place.category = "Heritage & Sacred Sanctum"
        sample_place.name = "Lingaraj Temple"
        score = calculate_cultural_relevance(sample_place)
        # 0.95 base + 0.05 boost = 1.0
        assert pytest.approx(score, 0.01) == 1.0

    def test_konark_sun_temple_boost(self):
        p = Place(
            id=10,
            name="Konark Sun Temple",
            duration=2.5,
            popularity=4.9,
            lat=19.8876,
            long=86.0945,
            risk="Low",
            city_id=2,
            category="Heritage & Archaeological Site"
        )
        score = calculate_cultural_relevance(p)
        assert score == min(1.0, 0.90 + 0.05)

    def test_unknown_category_fallback(self, sample_place):
        sample_place.category = "Unknown Unique Spot"
        sample_place.name = "Local Viewpoint"
        score = calculate_cultural_relevance(sample_place)
        assert score == 0.70


class TestPlaceUtility:
    def test_utility_formula_with_defaults(self, sample_place):
        user_prefs = {"spiritual": 5.0, "architecture": 5.0, "history": 4.0, "culture": 4.0, "nature": 1.0}
        raw_utility, int_match, pop_score, cult_score = calculate_place_utility(sample_place, user_prefs)

        assert 0.0 <= raw_utility <= 1.0
        assert 0.0 <= int_match <= 1.0
        assert pop_score == pytest.approx(sample_place.popularity / 5.0, 0.01)
        assert 0.0 <= cult_score <= 1.0

    def test_utility_with_custom_weights(self, sample_place):
        user_prefs = {"spiritual": 5.0, "architecture": 5.0}
        # Heavy on interest match (1.0), zero on popularity and cultural
        raw_utility, int_match, pop_score, cult_score = calculate_place_utility(
            sample_place, user_prefs, w_interest=1.0, w_popularity=0.0, w_cultural=0.0
        )
        assert pytest.approx(raw_utility, 0.001) == int_match


class TestCandidateScoring:
    def test_score_candidate_open_hours(self, sample_place):
        user_prefs = {"spiritual": 5.0, "architecture": 5.0}
        # Arrive at 09:00 AM on Monday (540 minutes from midnight)
        breakdown = score_place_candidate(
            sample_place,
            user_prefs=user_prefs,
            travel_time_minutes=15.0,
            travel_distance_km=6.0,
            day_name="Monday",
            arrival_minute_from_midnight=540
        )

        assert breakdown.is_open is True
        assert breakdown.notes == "Open"
        assert breakdown.visit_duration_minutes == 120  # 2.0 hrs = 120 min
        assert breakdown.total_time_cost_minutes == 135.0  # 15 + 120
        assert breakdown.efficiency_score > 0

    def test_score_candidate_closed_hours_penalty(self, sample_place):
        user_prefs = {"spiritual": 5.0, "architecture": 5.0}
        # Arrive at 23:00 (1380 minutes from midnight) -> Closed (closes at 21:00)
        breakdown = score_place_candidate(
            sample_place,
            user_prefs=user_prefs,
            travel_time_minutes=15.0,
            travel_distance_km=6.0,
            day_name="Monday",
            arrival_minute_from_midnight=1380
        )

        assert breakdown.is_open is False
        assert "Closed" in breakdown.notes
        # Efficiency is penalized by 0.05 multiplier
        expected_unpenalized = (breakdown.raw_utility / breakdown.total_time_cost_minutes) * 100.0
        assert pytest.approx(breakdown.efficiency_score, 0.01) == expected_unpenalized * 0.05
