"""
Deterministic Multi-Factor Utility Scoring Engine for DHRUVA.
Calculates transparent place utility and time-efficiency scores based on
user interest vectors, place popularity, cultural heritage significance,
travel duration, and opening hours constraints.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, List

from backend.database.models import Place, MinInterest
from backend.config import settings


@dataclass
class PlaceScoreBreakdown:
    """Detailed transparent breakdown of a place's utility score."""
    place_id: int
    place_name: str
    interest_match: float       # 0.0 to 1.0
    popularity_score: float     # 0.0 to 1.0
    cultural_score: float       # 0.0 to 1.0
    raw_utility: float          # Weighted combination (0.0 to 1.0)
    travel_time_minutes: float  # Minutes from current location
    travel_distance_km: float   # Km from current location
    visit_duration_minutes: int # Place duration in minutes
    total_time_cost_minutes: float
    efficiency_score: float     # Utility / TimeCost ratio
    is_open: bool               # Opening hours check
    notes: str = ""


# Cultural category base weights
CATEGORY_CULTURAL_WEIGHTS: Dict[str, float] = {
    "heritage & sacred sanctum": 0.95,
    "temple & sacred sanctum": 0.90,
    "heritage & archaeological site": 0.90,
    "arts, crafts & museum": 0.85,
    "monument & fort": 0.85,
    "nature & scenic sanctum": 0.75,
}

INTEREST_DIMENSIONS = ["architecture", "history", "spiritual", "nature", "culture"]


def calculate_interest_similarity(
    user_prefs: Dict[str, float],
    place_interest: Optional[MinInterest]
) -> float:
    """
    Compute cosine similarity / dot product between user preference vector
    and place interest profile.
    """
    if not place_interest:
        return 0.5  # Neutral default if no interest vector exists

    place_dict = place_interest.as_dict()

    # If user provided no non-zero preferences, return baseline average of place
    user_vals = [user_prefs.get(dim, 0.0) for dim in INTEREST_DIMENSIONS]
    place_vals = [place_dict.get(dim, 0.0) for dim in INTEREST_DIMENSIONS]

    user_magnitude = math.sqrt(sum(v * v for v in user_vals))
    place_magnitude = math.sqrt(sum(v * v for v in place_vals))

    if user_magnitude < 1e-5:
        # Default user preferences: average place interest normalized to [0.0, 1.0]
        return (sum(place_vals) / (len(place_vals) * 5.0)) if place_vals else 0.5

    if place_magnitude < 1e-5:
        return 0.3  # Place has zero interest tags

    # Cosine similarity
    dot_product = sum(u * p for u, p in zip(user_vals, place_vals))
    similarity = dot_product / (user_magnitude * place_magnitude)
    return max(0.0, min(1.0, similarity))


def calculate_cultural_relevance(place: Place) -> float:
    """
    Compute cultural heritage relevance score based on category, UNESCO designation,
    and historical significance.
    """
    cat = (place.category or "").lower().strip()
    base_weight = CATEGORY_CULTURAL_WEIGHTS.get(cat, 0.70)

    # Highlight flagship UNESCO / iconic sites
    if "konark" in place.name.lower() or "lingaraj" in place.name.lower():
        base_weight = min(1.0, base_weight + 0.05)

    return base_weight


def calculate_place_utility(
    place: Place,
    user_prefs: Dict[str, float],
    w_interest: Optional[float] = None,
    w_popularity: Optional[float] = None,
    w_cultural: Optional[float] = None
) -> Tuple[float, float, float, float]:
    """
    Compute composite utility score (0.0 to 1.0).
    Returns (raw_utility, interest_match, popularity_score, cultural_score).
    """
    wi = w_interest if w_interest is not None else settings.weight_interest
    wp = w_popularity if w_popularity is not None else settings.weight_popularity
    wc = w_cultural if w_cultural is not None else settings.weight_cultural

    # Normalize weights
    w_sum = wi + wp + wc
    if w_sum > 0:
        wi /= w_sum
        wp /= w_sum
        wc /= w_sum

    interest_match = calculate_interest_similarity(user_prefs, place.interests)
    popularity_score = max(0.0, min(1.0, place.popularity / 5.0))
    cultural_score = calculate_cultural_relevance(place)

    raw_utility = (wi * interest_match) + (wp * popularity_score) + (wc * cultural_score)
    return (raw_utility, interest_match, popularity_score, cultural_score)


def score_place_candidate(
    place: Place,
    user_prefs: Dict[str, float],
    travel_time_minutes: float,
    travel_distance_km: float,
    day_name: str = "Monday",
    arrival_minute_from_midnight: int = 540  # 09:00 AM default
) -> PlaceScoreBreakdown:
    """
    Compute full score breakdown and time-efficiency score for a candidate place.
    Efficiency = (Utility / TimeCost) * 100
    """
    raw_utility, int_match, pop_score, cult_score = calculate_place_utility(place, user_prefs)

    duration_min = place.duration_minutes
    total_time_cost = travel_time_minutes + duration_min

    # Check opening hours
    is_open = place.is_open_on_day_time(day_name, arrival_minute_from_midnight, duration_min)

    # Time efficiency ratio
    efficiency = (raw_utility / max(1.0, total_time_cost)) * 100.0

    if not is_open:
        notes = f"Closed during arrival window on {day_name}"
        # Heavily penalize closed places while maintaining diagnostic info
        efficiency *= 0.05
    else:
        notes = "Open"

    return PlaceScoreBreakdown(
        place_id=place.id,
        place_name=place.name,
        interest_match=round(int_match, 4),
        popularity_score=round(pop_score, 4),
        cultural_score=round(cult_score, 4),
        raw_utility=round(raw_utility, 4),
        travel_time_minutes=round(travel_time_minutes, 2),
        travel_distance_km=round(travel_distance_km, 2),
        visit_duration_minutes=duration_min,
        total_time_cost_minutes=round(total_time_cost, 2),
        efficiency_score=round(efficiency, 4),
        is_open=is_open,
        notes=notes,
    )
