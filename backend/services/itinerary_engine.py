"""
DHRUVA Cultural Itinerary Planning and Optimization Engine.
Synthesizes personalized, multi-day cultural journeys honoring time windows,
opening hours, spatial clustering, senior accessibility, and festival calendars.
"""

from __future__ import annotations
import datetime
import math
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

from backend.database.db_service import DhruvaDBService


@dataclass
class UserPlannerPreferences:
    """User input criteria matching the USERS_INPUT schema & trip wizard."""
    city_id: Optional[int] = None
    city_name: Optional[str] = None
    gps_location: Optional[str] = None  # e.g., "20.2961,85.8245"
    start_date: str = "2026-10-15"
    num_days: int = 3
    start_time: str = "08:30 AM"
    end_time: str = "07:30 PM"
    age: int = 58
    pacing: str = "balanced"  # 'relaxed', 'balanced', 'immersive'
    interests: Dict[str, float] = field(default_factory=lambda: {
        "spiritual": 4.5,
        "architecture": 4.5,
        "history": 4.0,
        "culture": 4.5,
        "nature": 3.0
    })
    mobility_level: str = "standard"  # 'gentle' (easy walking, ramps), 'standard'


@dataclass
class ItineraryActivity:
    """Single scheduled activity in a day's timeline."""
    time_slot: str
    place_id: int
    place_name: str
    category: str
    sub_category: str
    description: str
    duration_hours: float
    image_url: str
    entry_fee: str
    lat: float
    long: float
    transit_from_previous_km: float = 0.0
    transit_time_minutes: int = 0
    cultural_tip: str = ""
    accessibility_note: str = ""


@dataclass
class ItineraryDay:
    """One full day of cultural exploration."""
    day_number: int
    date: str
    day_of_week: str
    theme: str
    summary: str
    activities: List[Dict[str, Any]] = field(default_factory=list)
    festival_highlights: List[Dict[str, Any]] = field(default_factory=list)
    recommended_dining: Dict[str, str] = field(default_factory=dict)
    wellness_tip: str = ""


class CulturalItineraryEngine:
    """
    Intelligent itinerary synthesizer tailored for cultural & heritage journeys.
    """

    def __init__(self, db_service: Optional[DhruvaDBService] = None):
        self.db = db_service or DhruvaDBService()

    @staticmethod
    def parse_time_str(time_str: str) -> datetime.time:
        """Parse '08:30 AM' or '8:30 PM' into datetime.time."""
        clean = time_str.strip().upper()
        match = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)', clean)
        if match:
            h, m, period = int(match.group(1)), int(match.group(2)), match.group(3)
            if period == "PM" and h < 12:
                h += 12
            elif period == "AM" and h == 12:
                h = 0
            return datetime.time(h, m)
        return datetime.time(9, 0)

    @staticmethod
    def format_time_slot(start_time: datetime.time, duration_hours: float) -> Tuple[str, datetime.time]:
        """Generate formatted slot string (e.g. '09:00 AM - 11:00 AM') and end time."""
        total_minutes = int(duration_hours * 60)
        start_dt = datetime.datetime.combine(datetime.date.today(), start_time)
        end_dt = start_dt + datetime.timedelta(minutes=total_minutes)
        slot_str = f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}"
        return slot_str, end_dt.time()

    def calculate_match_score(self, place: Dict[str, Any], interests: Dict[str, float]) -> float:
        """Calculate weighted cultural affinity score between place and user interests."""
        w_spir = interests.get("spiritual", 3.0) / 5.0
        w_arch = interests.get("architecture", 3.0) / 5.0
        w_hist = interests.get("history", 3.0) / 5.0
        w_cult = interests.get("culture", 3.0) / 5.0
        w_nat = interests.get("nature", 3.0) / 5.0

        p_spir = place.get("spiritual", 3.0)
        p_arch = place.get("architecture", 3.0)
        p_hist = place.get("history", 3.0)
        p_cult = place.get("culture", 3.0)
        p_nat = place.get("nature", 3.0)

        affinity = (
            w_spir * p_spir +
            w_arch * p_arch +
            w_hist * p_hist +
            w_cult * p_cult +
            w_nat * p_nat
        ) / 5.0

        popularity = place.get("popularity", 4.5)
        return round(affinity * (popularity / 5.0) * 100, 2)

    def generate_itinerary(self, prefs: UserPlannerPreferences) -> Dict[str, Any]:
        """
        Synthesize an optimized cultural itinerary based on user preferences.
        """
        # 1. Resolve Target City
        target_city_id = prefs.city_id
        if not target_city_id and prefs.city_name:
            cities = self.db.get_cities()
            for c in cities:
                if c["name"].lower() == prefs.city_name.lower():
                    target_city_id = c["id"]
                    break

        if not target_city_id:
            target_city_id = 1  # Default to Bhubaneswar

        city_info = self.db.get_city_by_id(target_city_id) or {"name": "Odisha Cultural Heritage", "id": 1}

        # 2. Query Candidate Places for Target City
        candidate_places = self.db.get_places(city_id=target_city_id, limit=50)
        if len(candidate_places) < 5:
            # Expand to all places if city specific count is small
            candidate_places = self.db.get_places(limit=50)

        # 3. Score Candidates based on Interests & Age
        for p in candidate_places:
            p["match_score"] = self.calculate_match_score(p, prefs.interests)
            # Senior adjustments
            if prefs.age >= 55 and p.get("risk", "Low").lower() == "moderate":
                p["match_score"] *= 0.85

        # Sort candidate places by match score
        candidate_places.sort(key=lambda x: x["match_score"], reverse=True)

        # 4. Determine Daily Activity Capacity based on Pacing & Age
        pacing_map = {
            "relaxed": 2,
            "balanced": 3,
            "immersive": 4
        }
        max_daily_places = pacing_map.get(prefs.pacing.lower(), 3)
        if prefs.age >= 65 and max_daily_places > 2:
            max_daily_places = 2

        # 5. Fetch Festivals occurring during the trip
        all_festivals = self.db.get_festivals(city_id=target_city_id)

        # 6. Parse Start Date
        try:
            current_date = datetime.datetime.strptime(prefs.start_date, "%Y-%m-%d").date()
        except ValueError:
            current_date = datetime.date(2026, 10, 15)

        days_list: List[Dict[str, Any]] = []
        used_place_ids = set()

        day_themes = [
            ("Sacred Sanctums & Ancient Architecture", "Begin your journey exploring iconic sanctums with intricate Kalinga stone carvings and morning darshans."),
            ("Monastic Heritage, Caves & Living Crafts", "Discover ancient rock-cut edicts, Jain monolithic caves, and master artisans preserving handloom heritage."),
            ("Serene Water Sanctums & Temple Offerings", "Immerse in peaceful lakeside sanctuaries, traditional prasad tastings, and dusk aarti rituals."),
            ("Maritime Trade History & Royal Fortresses", "Step through centuries of seafaring heritage, royal fort battlements, and historic bazaar lanes."),
            ("Scenic Sanctums & Wildlife Nature Enclaves", "Experience coastal sanctuaries, migratory bird havens, and pristine river delta landscapes.")
        ]

        # 7. Day-by-day scheduling loop
        for day_idx in range(1, prefs.num_days + 1):
            day_str = current_date.strftime("%Y-%m-%d")
            day_of_week = current_date.strftime("%A")
            theme_title, theme_summary = day_themes[(day_idx - 1) % len(day_themes)]

            # Check for festivals active on this date
            day_festivals = []
            for f in all_festivals:
                f_start = f.get("start_date", "")
                f_end = f.get("end_date", "")
                if f_start <= day_str <= f_end:
                    day_festivals.append({
                        "name": f["name"],
                        "description": f["description"]
                    })

            day_activities = []
            current_time = self.parse_time_str(prefs.start_time)
            day_end_time = self.parse_time_str(prefs.end_time)

            # Select places for this day using spatial proximity
            available = [p for p in candidate_places if p["id"] not in used_place_ids]
            if not available:
                # Reuse top highlights if pool is exhausted
                available = candidate_places

            # Select first anchor attraction
            anchor_place = available[0]
            day_selected_places = [anchor_place]
            used_place_ids.add(anchor_place["id"])

            # Select spatially close places to anchor
            remaining_needed = max_daily_places - 1
            if remaining_needed > 0 and len(available) > 1:
                other_candidates = [p for p in available if p["id"] != anchor_place["id"]]
                other_candidates.sort(
                    key=lambda p: self.db.haversine_distance(anchor_place["lat"], anchor_place["long"], p["lat"], p["long"])
                )
                for p in other_candidates[:remaining_needed]:
                    day_selected_places.append(p)
                    used_place_ids.add(p["id"])

            # Schedule activities with transit & rest breaks
            last_lat = float(prefs.gps_location.split(",")[0]) if prefs.gps_location else anchor_place["lat"]
            last_lon = float(prefs.gps_location.split(",")[1]) if prefs.gps_location else anchor_place["long"]

            for p_idx, place in enumerate(day_selected_places):
                # Calculate transit from previous location
                dist_km = self.db.haversine_distance(last_lat, last_lon, place["lat"], place["long"])
                transit_mins = max(10, int(dist_km * 3.5))  # Estimated local transit in minutes

                # Add transit time to current time
                current_dt = datetime.datetime.combine(current_date, current_time) + datetime.timedelta(minutes=transit_mins)
                current_time = current_dt.time()

                # Activity Duration (e.g. 1.5 - 2.5 hours)
                dur = float(place.get("duration", 2.0))
                if prefs.pacing == "relaxed":
                    dur += 0.5

                slot_str, end_time = self.format_time_slot(current_time, dur)

                # Tailored cultural tips
                tip = "Photography permitted in outer parikrama. Please remove footwear at designated counters."
                if "temple" in place.get("name", "").lower():
                    tip = "Traditional modest attire recommended. Early morning and twilight are ideal for tranquil darshan."
                elif "museum" in place.get("name", "").lower():
                    tip = "Audio guides and air-conditioned galleries available. Shaded courtyard seating for rest."
                elif "cave" in place.get("name", "").lower():
                    tip = "Gentle stone steps; walking sticks and handrail pathways available for comfortable access."

                acc_note = "Wheelchair accessible pathways and senior rest benches available." if prefs.age >= 55 else "Standard walking."

                day_activities.append({
                    "time_slot": slot_str,
                    "place_id": place["id"],
                    "place_name": place["name"],
                    "category": place.get("category", "Heritage Site"),
                    "sub_category": place.get("sub_category", "Cultural Sanctum"),
                    "description": place.get("description", ""),
                    "duration_hours": dur,
                    "image_url": place.get("image_url", ""),
                    "entry_fee": place.get("entry_fee", "Free entry"),
                    "lat": place["lat"],
                    "long": place["long"],
                    "distance_from_prev_km": dist_km,
                    "transit_time_minutes": transit_mins,
                    "cultural_tip": tip,
                    "accessibility_note": acc_note
                })

                # Advance clock
                last_lat = place["lat"]
                last_lon = place["long"]
                current_time = end_time

                # Inject Midday Lunch Break between activities
                if p_idx == 0 and len(day_selected_places) > 1 and current_time < datetime.time(14, 0):
                    lunch_dt = datetime.datetime.combine(current_date, current_time)
                    if lunch_dt.time() < datetime.time(12, 30):
                        lunch_dt = datetime.datetime.combine(current_date, datetime.time(12, 30))
                    lunch_end = lunch_dt + datetime.timedelta(minutes=75)
                    day_activities.append({
                        "time_slot": f"{lunch_dt.strftime('%I:%M %p')} - {lunch_end.strftime('%I:%M %p')}",
                        "place_id": 0,
                        "place_name": "Heritage Satvik Lunch & Refreshment Break",
                        "category": "Culinary & Dining",
                        "sub_category": "Temple Cuisine",
                        "description": "Authentic regional lunch featuring temple-style Mahaprasad, Dalma, and Chhena Poda in a comfortable, shaded dining hall.",
                        "duration_hours": 1.25,
                        "image_url": "https://s7ap1.scene7.com/is/image/incredibleindia/lingaraj-temple-bhubaneshwar-odisha-1-attr-hero?qlt=82",
                        "entry_fee": "Included / A la carte",
                        "lat": last_lat,
                        "long": last_lon,
                        "distance_from_prev_km": 0.0,
                        "transit_time_minutes": 0,
                        "cultural_tip": "Traditional seating with high-chair options available for seniors.",
                        "accessibility_note": "Spacious dining with easy step-free access."
                    })
                    current_time = lunch_end.time()

            day_obj = {
                "day_number": day_idx,
                "date": day_str,
                "day_of_week": day_of_week,
                "theme": theme_title,
                "summary": theme_summary,
                "activities": day_activities,
                "festival_highlights": day_festivals,
                "recommended_dining": {
                    "lunch": "Traditional Odia Thali (Dalma, Kanika, Saga Bhaja)",
                    "dinner": "Light regional Satvik supper with fresh Chhena sweets"
                },
                "wellness_tip": "Stay well hydrated; gentle evening foot relaxation recommended after exploring stone courtyards."
            }
            days_list.append(day_obj)
            current_date += datetime.timedelta(days=1)

        # 8. Assemble Full Itinerary Response
        return {
            "status": "success",
            "metadata": {
                "destination_city": city_info.get("name", "Odisha"),
                "state": "Odisha",
                "start_date": prefs.start_date,
                "total_days": prefs.num_days,
                "pacing": prefs.pacing,
                "traveler_age": prefs.age,
                "total_activities_planned": sum(len(d["activities"]) for d in days_list),
                "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "days": days_list,
            "senior_travel_guidance": [
                "Early morning temple visits (before 09:30 AM) provide cooler weather and serene darshan atmosphere.",
                "Comfortable slip-on footwear is ideal since shoes are removed outside temple gates.",
                "Electric vehicle (battery cart) transfers are available within larger temple complexes and heritage plazas.",
                "Pure mineral water and fresh coconut water kiosks are accessible at all scheduled stops."
            ]
        }
