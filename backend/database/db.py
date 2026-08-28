"""
Database and repository layer for DHRUVA backend.
Provides data access to Cities, City Interests, Places, Opening Hours, Min Interests, Festivals,
and persists Trips, Time Windows, and Itineraries.
Supports both PostgreSQL/Supabase and zero-config CSV/In-Memory mode.
"""

from __future__ import annotations
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone

from backend.database.models import (
    City, CityInterest, Place, OpeningHour, MinInterest, Festival,
    Trip, TripTimeWindow, ItineraryItem
)
from backend.config import settings

logger = logging.getLogger("dhruva.db")


class DataRepository:
    """In-memory data store with CSV fallback & persistence capability."""

    def __init__(self, csv_dir: Optional[Path] = None):
        self.csv_dir = csv_dir or self._find_csv_dir()
        self.cities: Dict[int, City] = {}
        self.city_interests: Dict[int, CityInterest] = {}
        self.places: Dict[int, Place] = {}
        self.opening_hours: List[OpeningHour] = []
        self.min_interests: Dict[int, MinInterest] = {}
        self.festivals: List[Festival] = []

        # Persistent collections
        self.trips: Dict[int, Trip] = {}
        self._trip_id_counter = 1
        self._window_id_counter = 1
        self._item_id_counter = 1

        self._load_seed_data()

    def _find_csv_dir(self) -> Path:
        """Locate database/csv directory."""
        candidates = [
            Path(__file__).resolve().parent.parent.parent / "database" / "csv",
            Path("database/csv"),
            Path("../database/csv"),
        ]
        for c in candidates:
            if c.exists() and (c / "places.csv").exists():
                return c
        return Path("database/csv")

    def _load_csv(self, filename: str) -> List[Dict[str, str]]:
        fpath = self.csv_dir / filename
        if not fpath.exists():
            logger.warning(f"CSV file not found: {fpath}")
            return []
        with open(fpath, mode="r", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def _load_seed_data(self) -> None:
        """Load relational seed data from CSVs and construct object graph."""
        # 1. Cities
        cities_data = self._load_csv("cities.csv")
        for row in cities_data:
            c = City(
                id=int(row["id"]),
                name=row["name"],
                state=row["state"],
                lat=float(row["lat"]),
                long=float(row["long"]),
            )
            self.cities[c.id] = c

        # 2. City Interests (Default City Cultural Profiles)
        ci_data = self._load_csv("city_interest.csv")
        for row in ci_data:
            ci = CityInterest(
                id=int(row["id"]),
                city_id=int(row["city_id"]),
                architecture=float(row.get("architecture", 0.0)),
                history=float(row.get("history", 0.0)),
                spiritual=float(row.get("spiritual", 0.0)),
                nature=float(row.get("nature", 0.0)),
                culture=float(row.get("culture", 0.0)),
            )
            self.city_interests[ci.city_id] = ci
            if ci.city_id in self.cities:
                self.cities[ci.city_id].interest = ci

        # 3. Places
        places_data = self._load_csv("places.csv")
        for row in places_data:
            p = Place(
                id=int(row["id"]),
                name=row["name"],
                duration=float(row.get("duration", 2.0)),
                lat=float(row["lat"]),
                long=float(row["long"]),
                risk=row.get("risk", "Low"),
                city_id=int(row["city_id"]),
                category=row.get("category"),
                sub_category=row.get("sub_category"),
                duration_label=row.get("duration_label"),
                image_url=row.get("image_url"),
                entry_fee=row.get("entry_fee"),
                description=row.get("description"),
                source=row.get("source", "Wikipedia"),
                source_url=row.get("source_url"),
            )
            self.places[p.id] = p

        # 4. Opening Hours
        oh_data = self._load_csv("opening_hours.csv")
        for row in oh_data:
            oh = OpeningHour(
                id=int(row["id"]),
                place_id=int(row["place_id"]),
                day_of_week=row["day_of_week"],
                opens_at=row["opens_at"],
                closes_at=row["closes_at"],
            )
            self.opening_hours.append(oh)
            if oh.place_id in self.places:
                self.places[oh.place_id].opening_hours.append(oh)

        # 5. Min Interests
        interest_data = self._load_csv("min_interest.csv")
        for row in interest_data:
            mi = MinInterest(
                id=int(row["id"]),
                place_id=int(row["place_id"]),
                architecture=float(row.get("architecture", 0.0)),
                history=float(row.get("history", 0.0)),
                spiritual=float(row.get("spiritual", 0.0)),
                nature=float(row.get("nature", 0.0)),
                culture=float(row.get("culture", 0.0)),
            )
            self.min_interests[mi.place_id] = mi
            if mi.place_id in self.places:
                self.places[mi.place_id].interests = mi

        # 6. Festivals
        festivals_data = self._load_csv("festivals.csv")
        for row in festivals_data:
            f = Festival(
                id=int(row["id"]),
                name=row["name"],
                start_date=row["start_date"],
                end_date=row["end_date"],
                city_id=int(row["city_id"]),
                description=row.get("description"),
            )
            self.festivals.append(f)

        logger.info(f"Loaded {len(self.cities)} cities, {len(self.places)} places into repository.")

    # -----------------------------------------------------------------
    # Places & Cities Query API
    # -----------------------------------------------------------------
    def get_cities(self) -> List[City]:
        return list(self.cities.values())

    def get_city(self, city_id: int) -> Optional[City]:
        return self.cities.get(city_id)

    def get_city_interest(self, city_id: int) -> Optional[CityInterest]:
        return self.city_interests.get(city_id)

    def get_city_by_name(self, name: str) -> Optional[City]:
        for c in self.cities.values():
            if c.name.lower() == name.lower():
                return c
        return None

    def get_places_by_city(self, city_id: int) -> List[Place]:
        return [p for p in self.places.values() if p.city_id == city_id]

    def get_place(self, place_id: int) -> Optional[Place]:
        return self.places.get(place_id)

    def get_all_places(self) -> List[Place]:
        return list(self.places.values())

    def get_festivals_by_city(self, city_id: int) -> List[Festival]:
        return [f for f in self.festivals if f.city_id == city_id]

    # -----------------------------------------------------------------
    # Trip & Itinerary Persistence API
    # -----------------------------------------------------------------
    def save_trip(self, trip: Trip) -> Trip:
        if trip.id is None or trip.id == 0:
            trip.id = self._trip_id_counter
            self._trip_id_counter += 1

        if trip.created_at is None:
            trip.created_at = datetime.now(timezone.utc)

        # Assign IDs to time windows
        for tw in trip.time_windows:
            if tw.id is None:
                tw.id = self._window_id_counter
                self._window_id_counter += 1
            tw.trip_id = trip.id

        # Assign IDs to itinerary items
        for it in trip.itinerary_items:
            if it.id is None:
                it.id = self._item_id_counter
                self._item_id_counter += 1
            it.trip_id = trip.id

        self.trips[trip.id] = trip
        return trip

    def get_trip(self, trip_id: int) -> Optional[Trip]:
        trip = self.trips.get(trip_id)
        if trip:
            # Hydrate place references
            for it in trip.itinerary_items:
                if not it.place and it.place_id in self.places:
                    it.place = self.places[it.place_id]
        return trip

    def list_trips(self) -> List[Trip]:
        return list(self.trips.values())

    def delete_trip(self, trip_id: int) -> bool:
        if trip_id in self.trips:
            del self.trips[trip_id]
            return True
        return False


# Singleton data repository instance
db_repo = DataRepository()
