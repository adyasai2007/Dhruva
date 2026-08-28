"""
Cultural Itinerary Engine & Planning Service for DHRUVA.
Transforms user preferences, age-based pacing, and cultural interest profiles
into structured multi-day itineraries with rich cultural context and tips.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date, time
from typing import List, Dict, Optional, Any

from backend.database.models import Trip, TripTimeWindow, Place, ItineraryItem
from backend.database.db import db_repo
from backend.database.db_service import DhruvaDBService, dhruva_db
from backend.algorithm.itinerary_generator import itinerary_generator, GenerationResult
from backend.algorithm.scoring import calculate_place_utility


@dataclass
class UserPlannerPreferences:
    """Input parameters for trip planning wizard."""
    city_name: str = "Bhubaneswar"
    city_id: Optional[int] = None
    start_date: str = "2026-10-15"
    num_days: int = 2
    start_time: str = "08:30 AM"
    end_time: str = "07:30 PM"
    age: int = 55
    pacing: str = "balanced"  # 'relaxed' | 'balanced' | 'intensive'
    interests: Dict[str, float] = field(default_factory=lambda: {
        "spiritual": 4.5,
        "architecture": 4.5,
        "history": 4.0,
        "culture": 4.5,
        "nature": 3.0,
    })
    mandatory_place_ids: List[int] = field(default_factory=list)


# Cultural wisdom & accessibility tips per category
CULTURAL_CATEGORY_TIPS: Dict[str, str] = {
    "temple & sacred sanctum": "Mindful dress code (shoulders and knees covered). Remove footwear before inner sanctum.",
    "heritage & sacred sanctum": "Best experienced during morning aarti or gentle sunset hours with pleasant temple breezes.",
    "heritage & archaeological site": "Carry water and sun protection. Stroll through the stone carvings with mindful pacing.",
    "arts, crafts & museum": "Engage with local master artisans; photography permits may apply in heritage galleries.",
    "monument & fort": "Moderate walking on stone stairs. Shaded resting pavilions available along the route.",
    "nature & scenic sanctum": "Calm scenic environment; ideal for quiet reflection and gentle nature walks.",
}

DAY_THEMES: List[str] = [
    "Sacred Sanctums & Ancient Heritage",
    "Living Traditions & Craft Quarters",
    "Sculptural Marvels & Coastal Reverie",
    "Forest Sanctums & Spiritual Retreats",
    "Royal Legacies & Folk Chronicles",
]


class CulturalItineraryEngine:
    """Orchestrates high-level itinerary creation with cultural contextualization."""

    def __init__(self, db_service: Optional[DhruvaDBService] = None):
        self.db = db_service or dhruva_db
        self.repo = self.db.repo
        self.generator = itinerary_generator

    def generate_itinerary(self, prefs: UserPlannerPreferences) -> Dict[str, Any]:
        """Generate complete culturally grounded itinerary matching user profile."""
        # 1. Resolve city
        city_id = prefs.city_id
        city_name = prefs.city_name
        city_obj = None

        if city_id:
            city_obj = self.repo.get_city(city_id)
            if city_obj:
                city_name = city_obj.name
        elif city_name:
            city_obj = self.repo.get_city_by_name(city_name)
            if city_obj:
                city_id = city_obj.id

        if not city_obj:
            city_obj = self.repo.get_city(1)  # Default fallback to first city (Bhubaneswar)
            city_id = city_obj.id
            city_name = city_obj.name

        # 2. Adjust daily time window based on pacing & age
        # Senior travelers (55+) get cushioned pacing
        start_time_parsed = self._parse_time_to_24h(prefs.start_time)
        end_time_parsed = self._parse_time_to_24h(prefs.end_time)

        # Parse date
        try:
            start_date_obj = datetime.strptime(prefs.start_date, "%Y-%m-%d").date()
        except Exception:
            start_date_obj = date.today()

        end_date_obj = start_date_obj + timedelta(days=max(1, prefs.num_days) - 1)

        # 3. Construct Trip model
        trip = Trip(
            id=None,
            title=f"{city_name} Cultural Heritage Journey",
            mode="full_trip",
            city_id=city_id,
            start_lat=city_obj.lat,
            start_long=city_obj.long,
            start_datetime=f"{start_date_obj} {start_time_parsed}",
            end_datetime=f"{end_date_obj} {end_time_parsed}",
            preferences=prefs.interests,
            mandatory_place_ids=list(prefs.mandatory_place_ids),
        )

        # Build custom daily time windows
        windows = []
        for d in range(prefs.num_days):
            cur_date = start_date_obj + timedelta(days=d)
            windows.append(
                TripTimeWindow(
                    id=d + 1,
                    trip_id=None,
                    day_number=d + 1,
                    date_str=cur_date.strftime("%Y-%m-%d"),
                    window_start=start_time_parsed,
                    window_end=end_time_parsed,
                    start_lat=city_obj.lat if d == 0 else None,
                    start_long=city_obj.long if d == 0 else None,
                )
            )
        trip.time_windows = windows

        # 4. Run generator
        gen_result: GenerationResult = self.generator.generate(trip)

        if gen_result.status == "conflict":
            return gen_result.to_dict()

        # Save generated trip in repo
        self.repo.save_trip(trip)

        # 5. Format into rich cultural JSON structure
        return self._format_plan_response(trip, gen_result, prefs, city_obj)

    def _format_plan_response(
        self,
        trip: Trip,
        gen_result: GenerationResult,
        prefs: UserPlannerPreferences,
        city_obj: Any
    ) -> Dict[str, Any]:
        """Format generation output into friendly response."""
        days_output = []
        items_by_day: Dict[int, List[ItineraryItem]] = {}
        for item in trip.itinerary_items:
            items_by_day.setdefault(item.day_number, []).append(item)

        for d_idx, tw in enumerate(trip.time_windows):
            day_num = tw.day_number
            day_items = items_by_day.get(day_num, [])
            theme = DAY_THEMES[d_idx % len(DAY_THEMES)]

            activities = []
            for it in day_items:
                place = it.place or self.repo.get_place(it.place_id)
                cat = place.category if place else ""
                tip = CULTURAL_CATEGORY_TIPS.get(
                    (cat or "").lower(),
                    "Enjoy this cultural landmark at a mindful and respectful pace."
                )

                # Format time slot e.g. "09:00 AM - 11:00 AM"
                arr_str = self._format_iso_to_ampm(it.arrival_time)
                dep_str = self._format_iso_to_ampm(it.departure_time)
                time_slot = f"{arr_str} - {dep_str}"

                activities.append({
                    "id": it.id,
                    "place_id": it.place_id,
                    "place_name": place.name if place else f"Place #{it.place_id}",
                    "category": cat,
                    "time_slot": time_slot,
                    "arrival_time": it.arrival_time,
                    "departure_time": it.departure_time,
                    "duration_hours": round(it.visit_duration_minutes / 60.0, 1),
                    "duration_minutes": it.visit_duration_minutes,
                    "travel_time_from_prev_minutes": it.travel_time_from_prev_minutes,
                    "travel_distance_km": it.travel_distance_km,
                    "cultural_tip": tip,
                    "image_url": place.image_url if place else "",
                    "entry_fee": place.entry_fee if place else "",
                    "is_mandatory": it.is_mandatory,
                })

            days_output.append({
                "day_number": day_num,
                "date": tw.date_str,
                "theme": theme,
                "activities_count": len(activities),
                "activities": activities,
            })

        return {
            "status": "success",
            "trip_id": trip.id,
            "title": trip.title,
            "destination": city_obj.name if city_obj else "Odisha",
            "city_name": city_obj.name if city_obj else "Odisha",
            "state": city_obj.state if city_obj else "Odisha",
            "pacing_profile": prefs.pacing,
            "senior_friendly": prefs.age >= 50,
            "total_places_visited": gen_result.total_places_visited,
            "total_travel_minutes": round(gen_result.total_travel_minutes, 1),
            "total_travel_distance_km": round(gen_result.total_travel_distance_km, 1),
            "total_visit_minutes": gen_result.total_visit_minutes,
            "cultural_wisdom": "Mindful temple pacing with sacred morning darshan and afternoon rest.",
            "days": days_output,
        }

    def _parse_time_to_24h(self, t_str: str) -> str:
        """Parse '08:30 AM' or '08:30' into '08:30:00'."""
        t_str = t_str.strip()
        try:
            if "AM" in t_str.upper() or "PM" in t_str.upper():
                dt = datetime.strptime(t_str.upper(), "%I:%M %p")
                return dt.strftime("%H:%M:%S")
            elif ":" in t_str:
                parts = t_str.split(":")
                return f"{int(parts[0]):02d}:{int(parts[1]):02d}:00"
        except Exception:
            pass
        return "09:00:00"

    def _format_iso_to_ampm(self, dt_str: str) -> str:
        """Convert '2026-10-15 09:30:00' to '09:30 AM'."""
        try:
            if " " in dt_str:
                time_part = dt_str.split(" ")[1]
            elif "T" in dt_str:
                time_part = dt_str.split("T")[1]
            else:
                time_part = dt_str

            dt = datetime.strptime(time_part[:5], "%H:%M")
            return dt.strftime("%I:%M %p")
        except Exception:
            return dt_str


# Global singleton instance
cultural_engine = CulturalItineraryEngine()
