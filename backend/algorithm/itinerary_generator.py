"""
Itinerary Optimization, Multi-Day Chaining & Dynamic Rebalancing Engine for DHRUVA.
Implements Quick Visit, Full Trip multi-day sequential routing, mandatory places
conflict detection, dynamic addition/removal, and 3-shuffle variation generator.
"""

from __future__ import annotations
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date, time
from typing import List, Dict, Tuple, Optional, Any, Set

from backend.database.models import (
    Trip, TripTimeWindow, ItineraryItem, Place, City
)
from backend.database.db import db_repo
from backend.routing.ors_client import ors_client, MatrixResult
from backend.algorithm.scoring import (
    score_place_candidate, PlaceScoreBreakdown, calculate_place_utility
)
from backend.config import settings


@dataclass
class ConflictReport:
    status: str = "conflict"
    conflict_type: str = "insufficient_time"
    available_minutes: int = 0
    required_minutes: int = 0
    deficit_minutes: int = 0
    unscheduled_mandatory_places: List[Dict[str, Any]] = field(default_factory=list)
    recommendation: str = ""

    @property
    def has_conflict(self) -> bool:
        return self.status == "conflict" or self.deficit_minutes > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "has_conflict": self.has_conflict,
            "conflict_type": self.conflict_type,
            "available_minutes": self.available_minutes,
            "required_minutes": self.required_minutes,
            "deficit_minutes": self.deficit_minutes,
            "unscheduled_mandatory_places": self.unscheduled_mandatory_places,
            "recommendation": self.recommendation,
        }


@dataclass
class GenerationResult:
    status: str = "success"  # 'success' or 'conflict'
    trip: Optional[Trip] = None
    conflict: Optional[ConflictReport] = None
    items: List[ItineraryItem] = field(default_factory=list)
    total_travel_minutes: float = 0.0
    total_travel_distance_km: float = 0.0
    total_visit_minutes: int = 0
    total_places_visited: int = 0
    score_breakdowns: List[PlaceScoreBreakdown] = field(default_factory=list)
    shuffle_index: int = 0

    @property
    def conflict_report(self) -> Optional[ConflictReport]:
        return self.conflict

    @property
    def shuffle_count(self) -> int:
        return self.shuffle_index

    def to_dict(self) -> Dict[str, Any]:
        if self.status == "conflict" and self.conflict:
            return self.conflict.to_dict()

        return {
            "status": self.status,
            "trip_id": self.trip.id if self.trip else None,
            "shuffle_index": self.shuffle_index,
            "total_places_visited": self.total_places_visited,
            "total_visit_minutes": self.total_visit_minutes,
            "total_travel_minutes": round(self.total_travel_minutes, 2),
            "total_travel_distance_km": round(self.total_travel_distance_km, 2),
            "items": [
                {
                    "id": item.id,
                    "day_number": item.day_number,
                    "sequence_order": item.sequence_order,
                    "place_id": item.place_id,
                    "place_name": item.place.name if item.place else (db_repo.get_place(item.place_id).name if db_repo.get_place(item.place_id) else ""),
                    "category": item.place.category if item.place else "",
                    "arrival_time": item.arrival_time,
                    "departure_time": item.departure_time,
                    "visit_duration_minutes": item.visit_duration_minutes,
                    "travel_time_from_prev_minutes": item.travel_time_from_prev_minutes,
                    "travel_distance_km": item.travel_distance_km,
                    "is_mandatory": item.is_mandatory,
                    "notes": item.notes,
                }
                for item in self.items
            ]
        }


class ItineraryGenerator:
    """Core optimization engine for DHRUVA itineraries."""

    def __init__(self, repo=db_repo, router=ors_client):
        self.repo = repo
        self.router = router

    def generate(self, trip: Trip, shuffle_seed: Optional[int] = None) -> GenerationResult:
        """
        Main entry point to generate a complete itinerary for Quick Visit or Full Trip.
        """
        # Ensure time windows are initialized
        if not trip.time_windows:
            self._initialize_time_windows(trip)

        # 1. Check mandatory places feasibility
        mandatory_places = [
            self.repo.get_place(pid) for pid in trip.mandatory_place_ids
            if self.repo.get_place(pid) is not None
        ]

        total_avail_min = sum(tw.total_available_minutes for tw in trip.time_windows)
        mandatory_visit_min = sum(p.duration_minutes for p in mandatory_places)

        # Estimate minimal travel time for mandatory places
        min_est_travel = max(0, (len(mandatory_places) - 1) * 15 + 15) if mandatory_places else 0
        total_mandatory_required = mandatory_visit_min + min_est_travel

        if total_mandatory_required > total_avail_min and len(mandatory_places) > 0:
            deficit = total_mandatory_required - total_avail_min
            conflict = ConflictReport(
                status="conflict",
                conflict_type="insufficient_time",
                available_minutes=total_avail_min,
                required_minutes=total_mandatory_required,
                deficit_minutes=deficit,
                unscheduled_mandatory_places=[
                    {"id": p.id, "name": p.name, "duration_minutes": p.duration_minutes}
                    for p in mandatory_places
                ],
                recommendation=f"Available time window is {total_avail_min} mins, but selected mandatory places require at least {total_mandatory_required} mins. Please extend daily window by {deficit} mins or add an additional day."
            )
            return GenerationResult(status="conflict", trip=trip, conflict=conflict)

        # 2. Candidate places selection
        city = self.repo.get_city(trip.city_id)
        if not city:
            raise ValueError(f"City with id {trip.city_id} does not exist.")

        candidate_places = self.repo.get_places_by_city(trip.city_id)
        if not candidate_places:
            raise ValueError(f"City '{city.name}' has no places available for itinerary generation.")

        valid_candidates = [p for p in candidate_places if p.lat is not None and p.long is not None]
        if not valid_candidates:
            raise ValueError(f"City '{city.name}' has no places with valid coordinates.")
        candidate_places = valid_candidates

        # Pre-build ORS matrix for all candidates + trip start location
        all_coords = [(trip.start_lat, trip.start_long)] + [(p.lat, p.long) for p in candidate_places]
        try:
            self.router.calculate_matrix(all_coords)
        except Exception as e:
            logger.warning(f"ORS matrix prefetch notice: {e}. Fallback routing in effect.")

        # 3. Schedule day by day with sequential chaining
        scheduled_items: List[ItineraryItem] = []
        visited_place_ids: Set[int] = set()
        all_breakdowns: List[PlaceScoreBreakdown] = []

        total_travel_min = 0.0
        total_dist_km = 0.0
        total_visit_min = 0

        # Current location starts at trip origin
        current_lat = trip.start_lat
        current_long = trip.start_long

        # Mandatory places pool to place across days
        remaining_mandatory = list(mandatory_places)

        rng = random.Random(shuffle_seed) if shuffle_seed is not None else None

        for day_idx, tw in enumerate(trip.time_windows):
            day_number = tw.day_number
            date_obj = datetime.strptime(tw.date_str, "%Y-%m-%d").date() if tw.date_str else date.today()
            day_name = date_obj.strftime("%A")

            # Day starting coordinates: chained from previous day
            if tw.start_lat is not None and tw.start_long is not None:
                current_lat = tw.start_lat
                current_long = tw.start_long

            # Day starting time
            window_start_dt = datetime.combine(
                date_obj,
                datetime.strptime(tw.window_start, "%H:%M:%S").time()
                if ":" in tw.window_start and len(tw.window_start) >= 7
                else datetime.strptime(tw.window_start, "%H:%M").time()
            )
            window_end_dt = datetime.combine(
                date_obj,
                datetime.strptime(tw.window_end, "%H:%M:%S").time()
                if ":" in tw.window_end and len(tw.window_end) >= 7
                else datetime.strptime(tw.window_end, "%H:%M").time()
            )

            current_time = window_start_dt
            seq_order = 1

            while current_time < window_end_dt:
                remaining_day_min = int((window_end_dt - current_time).total_seconds() / 60)
                if remaining_day_min < 45:  # Less than 45 min remaining, end day
                    break

                current_min_from_midnight = current_time.hour * 60 + current_time.minute

                # Score all unvisited candidate places
                scored_candidates: List[Tuple[Place, PlaceScoreBreakdown]] = []

                # First prioritize remaining mandatory places that fit
                mandatory_to_evaluate = [p for p in remaining_mandatory if p.id not in visited_place_ids]
                pool = mandatory_to_evaluate if mandatory_to_evaluate else [
                    p for p in candidate_places if p.id not in visited_place_ids
                ]

                for p in pool:
                    travel_time, travel_dist = self.router.get_travel_time_and_distance(
                        (current_lat, current_long),
                        (p.lat, p.long)
                    )
                    breakdown = score_place_candidate(
                        place=p,
                        user_prefs=trip.preferences,
                        travel_time_minutes=travel_time,
                        travel_distance_km=travel_dist,
                        day_name=day_name,
                        arrival_minute_from_midnight=int(current_min_from_midnight + travel_time)
                    )

                    total_needed = travel_time + p.duration_minutes
                    if total_needed <= remaining_day_min and (breakdown.is_open or p.id in trip.mandatory_place_ids):
                        scored_candidates.append((p, breakdown))

                if not scored_candidates:
                    # No candidates fit in remaining window
                    break

                # Sort by efficiency score descending
                scored_candidates.sort(key=lambda x: x[1].efficiency_score, reverse=True)

                # Pick place (deterministic greedy or stochastic shuffle selection)
                if rng is not None and len(scored_candidates) > 1 and not mandatory_to_evaluate:
                    # Select from top 3 candidates for shuffle variation
                    top_k = scored_candidates[:min(3, len(scored_candidates))]
                    chosen_place, chosen_breakdown = rng.choice(top_k)
                else:
                    chosen_place, chosen_breakdown = scored_candidates[0]

                # Compute arrival and departure
                arrival_dt = current_time + timedelta(minutes=chosen_breakdown.travel_time_minutes)
                departure_dt = arrival_dt + timedelta(minutes=chosen_place.duration_minutes)

                is_mand = chosen_place.id in trip.mandatory_place_ids

                item = ItineraryItem(
                    id=None,
                    trip_id=trip.id,
                    day_number=day_number,
                    sequence_order=seq_order,
                    place_id=chosen_place.id,
                    arrival_time=arrival_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    departure_time=departure_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    visit_duration_minutes=chosen_place.duration_minutes,
                    travel_time_from_prev_minutes=int(round(chosen_breakdown.travel_time_minutes)),
                    travel_distance_km=chosen_breakdown.travel_distance_km,
                    is_mandatory=is_mand,
                    notes=f"{chosen_place.name} ({chosen_breakdown.notes})",
                    place=chosen_place
                )

                scheduled_items.append(item)
                visited_place_ids.add(chosen_place.id)
                if chosen_place in remaining_mandatory:
                    remaining_mandatory.remove(chosen_place)

                all_breakdowns.append(chosen_breakdown)

                total_travel_min += chosen_breakdown.travel_time_minutes
                total_dist_km += chosen_breakdown.travel_distance_km
                total_visit_min += chosen_place.duration_minutes

                # Advance state
                current_lat = chosen_place.lat
                current_long = chosen_place.long
                current_time = departure_dt
                seq_order += 1

            # Day ends: if custom end_lat/long specified for day window, update current_lat/long
            if tw.end_lat is not None and tw.end_long is not None:
                current_lat = tw.end_lat
                current_long = tw.end_long

            # Set starting coords for next day window in trip
            if day_idx + 1 < len(trip.time_windows):
                trip.time_windows[day_idx + 1].start_lat = current_lat
                trip.time_windows[day_idx + 1].start_long = current_long

        # Check if any mandatory place was left unscheduled
        if remaining_mandatory:
            deficit_min = sum(p.duration_minutes for p in remaining_mandatory) + 30
            conflict = ConflictReport(
                status="conflict",
                conflict_type="insufficient_time",
                available_minutes=total_avail_min,
                required_minutes=total_avail_min + deficit_min,
                deficit_minutes=deficit_min,
                unscheduled_mandatory_places=[
                    {"id": p.id, "name": p.name, "duration_minutes": p.duration_minutes}
                    for p in remaining_mandatory
                ],
                recommendation=f"Could not fit {len(remaining_mandatory)} mandatory places within scheduled daily exploration windows. Please expand daily time window or add an additional day."
            )
            return GenerationResult(status="conflict", trip=trip, conflict=conflict)

        trip.itinerary_items = scheduled_items

        return GenerationResult(
            status="success",
            trip=trip,
            items=scheduled_items,
            total_travel_minutes=total_travel_min,
            total_travel_distance_km=total_dist_km,
            total_visit_minutes=total_visit_min,
            total_places_visited=len(scheduled_items),
            score_breakdowns=all_breakdowns,
            shuffle_index=trip.shuffle_count
        )

    def _initialize_time_windows(self, trip: Trip) -> None:
        """Construct default daily time windows if not provided."""
        if trip.mode == "quick_visit":
            today_str = date.today().strftime("%Y-%m-%d")
            total_mins = trip.total_minutes or 240  # 4 hours default
            start_time_str = "09:00:00"
            if trip.start_datetime and "T" in trip.start_datetime:
                parts = trip.start_datetime.split("T")
                today_str = parts[0]
                start_time_str = parts[1] if len(parts[1]) == 8 else f"{parts[1]}:00"
            elif trip.start_datetime and " " in trip.start_datetime:
                parts = trip.start_datetime.split(" ")
                today_str = parts[0]
                start_time_str = parts[1]

            s_hour, s_min = int(start_time_str.split(":")[0]), int(start_time_str.split(":")[1])
            start_dt = datetime.combine(datetime.strptime(today_str, "%Y-%m-%d").date(), time(s_hour, s_min))
            end_dt = start_dt + timedelta(minutes=total_mins)

            tw = TripTimeWindow(
                id=1,
                trip_id=trip.id,
                day_number=1,
                date_str=today_str,
                window_start=start_dt.strftime("%H:%M:%S"),
                window_end=end_dt.strftime("%H:%M:%S"),
                start_lat=trip.start_lat,
                start_long=trip.start_long,
                end_lat=trip.end_lat,
                end_long=trip.end_long
            )
            trip.time_windows = [tw]
        else:
            # Full trip multi-day default: determine number of days
            start_date = date.today()
            end_date = start_date + timedelta(days=2)  # 3 days default

            if trip.start_datetime:
                try:
                    s_str = trip.start_datetime.split("T")[0] if "T" in trip.start_datetime else trip.start_datetime.split(" ")[0]
                    start_date = datetime.strptime(s_str, "%Y-%m-%d").date()
                except Exception:
                    pass

            if trip.end_datetime:
                try:
                    e_str = trip.end_datetime.split("T")[0] if "T" in trip.end_datetime else trip.end_datetime.split(" ")[0]
                    end_date = datetime.strptime(e_str, "%Y-%m-%d").date()
                except Exception:
                    pass

            num_days = max(1, (end_date - start_date).days + 1)
            windows = []
            cur_lat = trip.start_lat
            cur_long = trip.start_long

            for d in range(num_days):
                cur_d = start_date + timedelta(days=d)
                tw = TripTimeWindow(
                    id=d + 1,
                    trip_id=trip.id,
                    day_number=d + 1,
                    date_str=cur_d.strftime("%Y-%m-%d"),
                    window_start="09:00:00",
                    window_end="18:00:00",
                    start_lat=cur_lat if d == 0 else None,
                    start_long=cur_long if d == 0 else None,
                    end_lat=trip.end_lat if d == num_days - 1 else None,
                    end_long=trip.end_long if d == num_days - 1 else None
                )
                windows.append(tw)

            trip.time_windows = windows

    # -----------------------------------------------------------------
    # Dynamic Modification & Multi-Day Rebalancing
    # -----------------------------------------------------------------
    def add_place_to_itinerary(
        self,
        trip: Trip,
        place_id: int,
        day_number: int = 1,
        target_day: Optional[int] = None,
        target_sequence: Optional[int] = None
    ) -> ItineraryItem:
        """
        Dynamically insert a place into the itinerary and rebalance downstream items.
        """
        place = self.repo.get_place(place_id)
        if not place:
            raise ValueError(f"Place with id {place_id} does not exist.")

        actual_day = target_day if target_day is not None else day_number

        # If place is already scheduled, return that item
        for it in trip.itinerary_items:
            if it.place_id == place_id:
                return it

        # Mark as mandatory
        if place_id not in trip.mandatory_place_ids:
            trip.mandatory_place_ids.append(place_id)

        # Create new item
        day_items = [it for it in trip.itinerary_items if it.day_number == actual_day]
        seq = len(day_items) + 1 if target_sequence is None else target_sequence

        new_item = ItineraryItem(
            id=None,
            trip_id=trip.id,
            day_number=actual_day,
            sequence_order=seq,
            place_id=place.id,
            visit_duration_minutes=place.duration_minutes,
            is_mandatory=True,
            place=place
        )
        trip.itinerary_items.append(new_item)
        self.rebalance_itinerary(trip)

        added = next((it for it in trip.itinerary_items if it.place_id == place_id), new_item)
        return added

    def remove_place_from_itinerary(
        self,
        trip: Trip,
        place_id: int
    ) -> bool:
        """
        Dynamically remove a place from the itinerary and compress schedule.
        """
        if place_id in trip.mandatory_place_ids:
            trip.mandatory_place_ids.remove(place_id)

        # Filter out from current items
        trip.itinerary_items = [it for it in trip.itinerary_items if it.place_id != place_id]

        # Rebalance remaining items
        self.rebalance_itinerary(trip)
        return True

    def rebalance_itinerary(self, trip: Trip) -> GenerationResult:
        """
        Recalculate arrival/departure times and travel matrix for existing items across days.
        """
        if not trip.itinerary_items:
            return self.generate(trip)

        scheduled_items = sorted(trip.itinerary_items, key=lambda x: (x.day_number, x.sequence_order))

        # Group by day
        day_map: Dict[int, List[ItineraryItem]] = {}
        for it in scheduled_items:
            day_map.setdefault(it.day_number, []).append(it)

        rebalanced: List[ItineraryItem] = []
        total_travel_min = 0.0
        total_dist_km = 0.0
        total_visit_min = 0

        current_lat = trip.start_lat
        current_long = trip.start_long

        pending_items: List[ItineraryItem] = []

        for day_idx, tw in enumerate(trip.time_windows):
            day_items = pending_items + day_map.get(tw.day_number, [])
            pending_items = []
            if not day_items:
                continue

            date_obj = datetime.strptime(tw.date_str, "%Y-%m-%d").date() if tw.date_str else date.today()
            window_start_dt = datetime.combine(
                date_obj,
                datetime.strptime(tw.window_start, "%H:%M:%S").time()
                if ":" in tw.window_start and len(tw.window_start) >= 7
                else datetime.strptime(tw.window_start, "%H:%M").time()
            )
            window_end_dt = datetime.combine(
                date_obj,
                datetime.strptime(tw.window_end, "%H:%M:%S").time()
                if ":" in tw.window_end and len(tw.window_end) >= 7
                else datetime.strptime(tw.window_end, "%H:%M").time()
            )

            current_time = window_start_dt
            seq = 1

            for it in day_items:
                place = it.place or self.repo.get_place(it.place_id)
                if not place:
                    continue

                travel_time, travel_dist = self.router.get_travel_time_and_distance(
                    (current_lat, current_long),
                    (place.lat, place.long)
                )

                arrival_dt = current_time + timedelta(minutes=travel_time)
                departure_dt = arrival_dt + timedelta(minutes=place.duration_minutes)

                # If item overflows this day's window and more days exist, spill over to next day
                if departure_dt > window_end_dt and day_idx + 1 < len(trip.time_windows):
                    pending_items.append(it)
                    continue

                it.day_number = tw.day_number
                it.sequence_order = seq
                it.arrival_time = arrival_dt.strftime("%Y-%m-%d %H:%M:%S")
                it.departure_time = departure_dt.strftime("%Y-%m-%d %H:%M:%S")
                it.travel_time_from_prev_minutes = int(round(travel_time))
                it.travel_distance_km = travel_dist
                it.visit_duration_minutes = place.duration_minutes
                it.place = place

                rebalanced.append(it)
                total_travel_min += travel_time
                total_dist_km += travel_dist
                total_visit_min += place.duration_minutes

                current_lat = place.lat
                current_long = place.long
                current_time = departure_dt
                seq += 1

        trip.itinerary_items = rebalanced

        return GenerationResult(
            status="success",
            trip=trip,
            items=rebalanced,
            total_travel_minutes=total_travel_min,
            total_travel_distance_km=total_dist_km,
            total_visit_minutes=total_visit_min,
            total_places_visited=len(rebalanced)
        )

    # -----------------------------------------------------------------
    # Shuffle Generator (Up to 3 Unique Itineraries)
    # -----------------------------------------------------------------
    def generate_shuffle(self, trip: Trip) -> GenerationResult:
        """
        Generate a new valid alternative itinerary variation (up to 3 times per trip).
        """
        if trip.shuffle_count >= settings.max_shuffle_count:
            raise ValueError(
                f"Maximum shuffle limit of {settings.max_shuffle_count} reached ({settings.max_shuffle_count} variations generated). No further shuffles allowed for this trip."
            )

        trip.shuffle_count += 1
        # Use deterministic seed based on trip ID and shuffle count
        seed = (trip.id or 1) * 1000 + trip.shuffle_count * 37 + 42

        result = self.generate(trip, shuffle_seed=seed)
        result.shuffle_index = trip.shuffle_count
        return result


# Singleton generator instance
itinerary_generator = ItineraryGenerator()
