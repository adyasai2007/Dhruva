"""
Domain and database data models for DHRUVA backend.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date, time
from typing import List, Dict, Optional, Any


@dataclass
class CityInterest:
    id: Optional[int] = None
    city_id: Optional[int] = None
    architecture: float = 0.0
    history: float = 0.0
    spiritual: float = 0.0
    nature: float = 0.0
    culture: float = 0.0

    def as_dict(self) -> Dict[str, float]:
        return {
            "architecture": self.architecture,
            "history": self.history,
            "spiritual": self.spiritual,
            "nature": self.nature,
            "culture": self.culture,
        }


@dataclass
class City:
    id: int
    name: str
    state: str
    lat: float
    long: float
    interest: Optional[CityInterest] = None


@dataclass
class OpeningHour:
    id: Optional[int] = None
    place_id: Optional[int] = None
    day_of_week: str = "Monday"  # e.g., 'Monday', 'Tuesday'
    opens_at: str = "08:00 AM"   # e.g., '08:00 AM'
    closes_at: str = "08:00 PM"  # e.g., '05:30 PM'

    def opens_at_minutes(self) -> int:
        """Parse '08:00 AM' into minutes from midnight."""
        return _parse_time_str(self.opens_at)

    def closes_at_minutes(self) -> int:
        """Parse '05:30 PM' into minutes from midnight."""
        return _parse_time_str(self.closes_at)

    def is_open_during(self, start_min: int, end_min: int) -> bool:
        """Check if open during the specified time interval (in minutes from midnight)."""
        op = self.opens_at_minutes()
        cl = self.closes_at_minutes()
        # If open 12:00 AM to 11:59 PM (24 hours)
        if op == 0 and cl >= 1439:
            return True
        return (start_min >= op) and (end_min <= cl)


def _parse_time_str(t_str: str) -> int:
    """Parse time string like '08:00 AM' or '17:30' into minutes from midnight."""
    t_str = t_str.strip()
    try:
        if "AM" in t_str.upper() or "PM" in t_str.upper():
            dt = datetime.strptime(t_str.upper(), "%I:%M %p")
            return dt.hour * 60 + dt.minute
        elif ":" in t_str:
            parts = t_str.split(":")
            return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        pass
    return 0


@dataclass
class MinInterest:
    id: Optional[int] = None
    place_id: Optional[int] = None
    architecture: float = 0.0
    history: float = 0.0
    spiritual: float = 0.0
    nature: float = 0.0
    culture: float = 0.0

    def as_dict(self) -> Dict[str, float]:
        return {
            "architecture": self.architecture,
            "history": self.history,
            "spiritual": self.spiritual,
            "nature": self.nature,
            "culture": self.culture,
        }


@dataclass
class Festival:
    id: int
    name: str
    start_date: str
    end_date: str
    city_id: int
    description: Optional[str] = None


@dataclass
class Place:
    id: int
    name: str
    duration: float  # In hours (e.g. 2.5)
    lat: float
    long: float
    risk: str = "Low"
    city_id: int = 1
    duration_label: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    entry_fee: Optional[str] = None
    source: Optional[str] = "Wikipedia"
    source_url: Optional[str] = None
    last_updated: Optional[datetime] = None
    popularity: Optional[float] = None  # Backward-compatible attribute; in schema, computed from MIN_INTEREST

    # Associated relations
    opening_hours: List[OpeningHour] = field(default_factory=list)
    interests: Optional[MinInterest] = None

    def __post_init__(self):
        if self.popularity is None and self.interests:
            scores = [
                self.interests.architecture,
                self.interests.history,
                self.interests.spiritual,
                self.interests.nature,
                self.interests.culture,
            ]
            avg = sum(scores) / max(1, len(scores))
            self.popularity = round(avg if avg > 1.0 else avg * 5.0, 2)
        elif self.popularity is None:
            self.popularity = 4.5

    @property
    def duration_minutes(self) -> int:
        return int(round(self.duration * 60))

    def is_open_on_day_time(self, day_name: str, start_minute: int, duration_min: int) -> bool:
        """Check if the place is open on a given weekday for the visit duration."""
        if not self.opening_hours:
            return True  # If no hours defined, default to open

        day_hours = [oh for oh in self.opening_hours if oh.day_of_week.lower() == day_name.lower()]
        if not day_hours:
            return True  # If day not specified, assume open

        end_minute = start_minute + duration_min
        for oh in day_hours:
            if oh.is_open_during(start_minute, end_minute):
                return True
        return False


@dataclass
class TripTimeWindow:
    id: Optional[int] = None
    trip_id: Optional[int] = None
    day_number: int = 1
    date_str: str = ""  # YYYY-MM-DD
    window_start: str = "09:00:00"  # HH:MM:SS
    window_end: str = "18:00:00"    # HH:MM:SS
    start_lat: Optional[float] = None
    start_long: Optional[float] = None
    end_lat: Optional[float] = None
    end_long: Optional[float] = None

    @property
    def start_minute(self) -> int:
        return _parse_time_str(self.window_start)

    @property
    def end_minute(self) -> int:
        return _parse_time_str(self.window_end)

    @property
    def total_available_minutes(self) -> int:
        diff = self.end_minute - self.start_minute
        return max(0, diff)


@dataclass
class ItineraryItem:
    id: Optional[int] = None
    trip_id: Optional[int] = None
    day_number: int = 1
    sequence_order: int = 1
    place_id: int = 0
    arrival_time: str = ""  # ISO format string or HH:MM
    departure_time: str = ""
    visit_duration_minutes: int = 0
    travel_time_from_prev_minutes: int = 0
    travel_distance_km: float = 0.0
    is_mandatory: bool = False
    notes: Optional[str] = None

    # Associated place object for hydration
    place: Optional[Place] = None


@dataclass
class Trip:
    id: Optional[int] = None
    title: str = "Odisha Heritage Tour"
    mode: str = "full_trip"  # 'quick_visit' | 'full_trip'
    city_id: int = 1
    start_lat: float = 20.2961
    start_long: float = 85.8245
    end_lat: Optional[float] = None
    end_long: Optional[float] = None
    start_datetime: str = ""
    end_datetime: str = ""
    total_minutes: Optional[int] = None
    preferences: Dict[str, float] = field(default_factory=dict)
    mandatory_place_ids: List[int] = field(default_factory=list)
    shuffle_count: int = 0
    created_at: Optional[datetime] = None

    # Child collections
    time_windows: List[TripTimeWindow] = field(default_factory=list)
    itinerary_items: List[ItineraryItem] = field(default_factory=list)
