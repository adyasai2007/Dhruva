"""
High-Performance, Zero-Dependency HTTP & REST API Server for DHRUVA.
Serves frontend static assets and exposes complete travel-planning REST APIs:
- Quick Visit & Full Trip Multi-Day Optimization
- Multi-Factor Transparent Utility Scoring Breakdown
- Dynamic Place Insertion & Removal with Downstream Rebalancing
- 3-Shuffle Alternative Itinerary Variation Generator
- Mandatory Place Conflict Detection & Time-Window Analysis
- OpenRouteService Matrix Routing with Road-Winding Haversine Fallback
"""

from __future__ import annotations
import os
import sys
import json
import mimetypes
import logging
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, date, time, timedelta, timezone

# Ensure project root is in sys.path when running standalone
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import settings
from backend.database.models import Trip, TripTimeWindow, Place, ItineraryItem
from backend.database.db import db_repo
from backend.database.db_service import dhruva_db, DhruvaDBService
from backend.services.itinerary_engine import cultural_engine, UserPlannerPreferences
from backend.algorithm.itinerary_generator import itinerary_generator, GenerationResult
from backend.algorithm.scoring import (
    score_place_candidate, calculate_place_utility, calculate_interest_similarity,
    calculate_cultural_relevance
)
from backend.routing.ors_client import ors_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("dhruva.server")


# Locate frontend root directory
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


class DhruvaAPIRequestHandler(BaseHTTPRequestHandler):
    """Integrated HTTP request handler for static frontend assets & REST API."""

    def __init__(self, *args, **kwargs):
        self.db = dhruva_db
        self.repo = db_repo
        self.generator = itinerary_generator
        self.engine = cultural_engine
        self.router = ors_client
        super().__init__(*args, **kwargs)

    # -----------------------------------------------------------------
    # HTTP Utilities & Headers
    # -----------------------------------------------------------------
    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, PUT, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def _send_json(self, data: Any, status_code: int = 200) -> None:
        payload = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(payload)

    def _send_error_json(self, message: str, status_code: int = 400, details: Any = None) -> None:
        body = {
            "status": "error",
            "message": message,
            "error": message,
        }
        if details:
            body["details"] = details
        self._send_json(body, status_code=status_code)

    def _read_json_body(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0:
            return {}
        raw_body = self.rfile.read(content_length).decode("utf-8")
        try:
            return json.loads(raw_body)
        except Exception as e:
            logger.warning(f"Malformed JSON body: {e}")
            return {}

    def do_OPTIONS(self) -> None:
        """Handle CORS pre-flight requests."""
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    # -----------------------------------------------------------------
    # Object Serializers
    # -----------------------------------------------------------------
    def _serialize_item(self, it: ItineraryItem) -> Dict[str, Any]:
        place_name = ""
        category = ""
        if it.place:
            place_name = it.place.name
            category = it.place.category or ""
        else:
            p = self.repo.get_place(it.place_id)
            if p:
                place_name = p.name
                category = p.category or ""
        return {
            "id": it.id,
            "day_number": it.day_number,
            "sequence_order": it.sequence_order,
            "place_id": it.place_id,
            "place_name": place_name,
            "category": category,
            "arrival_time": it.arrival_time,
            "departure_time": it.departure_time,
            "visit_duration_minutes": it.visit_duration_minutes,
            "travel_time_from_prev_minutes": it.travel_time_from_prev_minutes,
            "travel_distance_km": it.travel_distance_km,
            "is_mandatory": it.is_mandatory,
            "notes": it.notes,
        }

    def _serialize_trip(self, trip: Trip) -> Dict[str, Any]:
        return {
            "id": trip.id,
            "title": trip.title,
            "mode": trip.mode,
            "city_id": trip.city_id,
            "start_lat": trip.start_lat,
            "start_long": trip.start_long,
            "end_lat": trip.end_lat,
            "end_long": trip.end_long,
            "start_datetime": trip.start_datetime,
            "end_datetime": trip.end_datetime,
            "total_minutes": trip.total_minutes,
            "shuffle_count": trip.shuffle_count,
            "preferences": trip.preferences,
            "mandatory_place_ids": trip.mandatory_place_ids,
            "time_windows": [
                {
                    "id": tw.id,
                    "day_number": tw.day_number,
                    "date": tw.date_str,
                    "date_str": tw.date_str,
                    "window_start": tw.window_start,
                    "window_end": tw.window_end,
                    "start_lat": tw.start_lat,
                    "start_long": tw.start_long,
                    "end_lat": tw.end_lat,
                    "end_long": tw.end_long,
                }
                for tw in trip.time_windows
            ],
            "itinerary_items": [self._serialize_item(it) for it in trip.itinerary_items],
        }

    # -----------------------------------------------------------------
    # GET Dispatcher
    # -----------------------------------------------------------------
    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)

        norm_path = path[4:] if path.startswith("/api") else path
        api_prefixes = (
            "/health", "/cities", "/places", "/festivals", "/trips",
            "/scoring", "/routing", "/itinerary"
        )
        if path.startswith("/api/") or any(norm_path.startswith(p) for p in api_prefixes):
            self._handle_api_get(norm_path, query_params)
            return

        # 2. Static File Serving from frontend/
        self._serve_static_file(path)

    def _handle_api_get(self, norm_path: str, query: Dict[str, List[str]]) -> None:
        # GET /health
        if norm_path == "/health":
            cities_count = len(self.repo.get_cities())
            places_count = len(self.repo.get_all_places())
            festivals_count = len(self.repo.festivals)
            self._send_json({
                "status": "healthy",
                "service": "dhruva-backend",
                "app": settings.app_name,
                "version": settings.app_version,
                "records": {
                    "cities_count": cities_count,
                    "places_count": places_count,
                    "festivals_count": festivals_count,
                },
                "ors_configured": bool(settings.ors_api_key),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            return

        # GET /cities
        if norm_path == "/cities":
            cities = self.db.get_cities()
            self._send_json(cities)
            return

        # GET /cities/<id>
        if norm_path.startswith("/cities/"):
            try:
                city_id = int(norm_path.split("/cities/")[1])
                city = self.db.get_city_by_id(city_id)
                if city:
                    self._send_json({"status": "success", "data": city})
                else:
                    self._send_error_json("City not found", status_code=404)
            except ValueError:
                self._send_error_json("Invalid city ID", status_code=400)
            return

        # GET /places or GET /places/ranked
        if norm_path in ("/places", "/places/ranked"):
            city_param = query.get("city_name", query.get("city", [None]))[0]
            city_id_param = query.get("city_id", [None])[0]
            category_param = query.get("category", [None])[0]
            min_rating_param = query.get("min_rating", [None])[0]
            limit_param = query.get("limit", [None])[0]

            cid = int(city_id_param) if city_id_param and city_id_param.isdigit() else None
            m_rate = float(min_rating_param) if min_rating_param else None
            lim = int(limit_param) if limit_param and limit_param.isdigit() else None

            # Extract optional interest preferences from query params (e.g. ?spiritual=5&architecture=4)
            user_interests = None
            interest_dims = ["spiritual", "architecture", "history", "nature", "culture"]
            found_interests = {}
            for dim in interest_dims:
                val = query.get(dim, [None])[0]
                if val:
                    try:
                        found_interests[dim] = float(val)
                    except ValueError:
                        pass
            if found_interests:
                user_interests = found_interests

            places = self.db.get_places(
                city_id=cid,
                city_name=city_param,
                category=category_param,
                min_rating=m_rate,
                user_interests=user_interests,
                limit=lim
            )
            self._send_json(places)
            return

        # GET /places/<id>
        if norm_path.startswith("/places/"):
            try:
                place_id = int(norm_path.split("/places/")[1])
                place = self.db.get_place_by_id(place_id)
                if place:
                    self._send_json({"status": "success", "data": place})
                else:
                    self._send_error_json("Place not found", status_code=404)
            except ValueError:
                self._send_error_json("Invalid place ID", status_code=400)
            return

        # GET /festivals
        if norm_path == "/festivals":
            city_param = query.get("city_name", query.get("city", [None]))[0]
            city_id_param = query.get("city_id", [None])[0]
            cid = int(city_id_param) if city_id_param and city_id_param.isdigit() else None

            festivals = self.db.get_festivals(city_id=cid, city_name=city_param)
            self._send_json(festivals)
            return

        # GET /trips/<id>
        if norm_path.startswith("/trips/"):
            sub_path = norm_path[len("/trips/"):]
            if sub_path.isdigit():
                trip_id = int(sub_path)
                trip = self.repo.get_trip(trip_id)
                if not trip:
                    self._send_error_json("Trip not found", status_code=404)
                    return
                self._send_json(self._serialize_trip(trip))
                return

        # GET /voice/tools
        if norm_path in ("/voice/tools", "/voice/schema"):
            from backend.services.voice_assistant import VOICE_TOOL_DECLARATIONS
            self._send_json({"status": "success", "tools": VOICE_TOOL_DECLARATIONS})
            return

        # GET /voice/status
        if norm_path == "/voice/status":
            self._send_json({
                "status": "success",
                "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
                "model": os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
            })
            return

        self._send_error_json(f"API endpoint not found: {norm_path}", status_code=404)

    # -----------------------------------------------------------------
    # POST Dispatcher
    # -----------------------------------------------------------------
    def do_POST(self) -> None:
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        body = self._read_json_body()
        norm_path = path[4:] if path.startswith("/api") else path

        # 1. POST /itinerary/plan
        if norm_path == "/itinerary/plan":
            self._handle_plan_itinerary(body)
            return

        # 2. POST /trips/full-trip
        if norm_path == "/trips/full-trip":
            self._handle_full_trip(body)
            return

        # 3. POST /trips/quick-visit
        if norm_path == "/trips/quick-visit":
            self._handle_quick_visit(body)
            return

        # 4. POST /trips
        if norm_path == "/trips":
            mode = body.get("mode", "full_trip")
            if mode == "quick_visit" or "total_minutes" in body:
                self._handle_quick_visit(body)
            elif "time_windows" in body:
                self._handle_full_trip(body)
            elif "num_days" in body or "start_date" in body:
                self._handle_plan_itinerary(body)
            else:
                self._handle_full_trip(body)
            return

        # 5. POST /trips/<id>/...
        if norm_path.startswith("/trips/"):
            sub = norm_path[len("/trips/"):]
            parts = sub.split("/")
            if parts and parts[0].isdigit():
                trip_id = int(parts[0])
                rest = "/" + "/".join(parts[1:]) if len(parts) > 1 else ""
                if rest in ("/itinerary/places", "/add-place", "/places"):
                    self._handle_add_place(trip_id, body)
                    return
                if rest in ("/remove-place",):
                    place_id = int(body.get("place_id", 0))
                    self._handle_remove_place(trip_id, place_id)
                    return
                if rest in ("/itinerary/shuffle", "/shuffle"):
                    self._handle_shuffle(trip_id)
                    return
                if rest in ("/generate", "/itinerary/generate"):
                    self._handle_generate_itinerary(trip_id)
                    return

        # 6. POST /scoring/breakdown
        if norm_path == "/scoring/breakdown":
            self._handle_scoring_breakdown(body)
            return

        # 7. POST /routing/matrix
        if norm_path == "/routing/matrix":
            self._handle_routing_matrix(body)
            return

        # 8. POST /places/rank or /places/search
        if norm_path in ("/places/rank", "/places/search"):
            city_param = body.get("city_name")
            city_id = body.get("city_id")
            category = body.get("category")
            prefs = body.get("preferences") or body.get("interests")
            limit = body.get("limit")
            min_rating = body.get("min_rating")

            ranked_places = self.db.get_places(
                city_id=city_id,
                city_name=city_param,
                category=category,
                user_interests=prefs,
                min_rating=min_rating,
                limit=limit
            )
            ref_city_id = city_id or 1
            city_int = self.db.get_city_interest(ref_city_id)
            self._send_json({
                "status": "success",
                "used_preferences": "user_input" if prefs else "city_interest_default",
                "reference_interest_vector": prefs or city_int,
                "count": len(ranked_places),
                "data": ranked_places
            })
            return

        # 9. POST /voice/chat or /voice/message
        if norm_path in ("/voice/chat", "/voice/message"):
            from backend.services.voice_assistant import voice_assistant
            user_msg = body.get("message", "")
            history = body.get("conversation_history", [])
            context = body.get("context", {})
            res = voice_assistant.process_conversation_turn(user_msg, history, context)
            self._send_json(res)
            return

        # 10. POST /voice/session or /voice/reset
        if norm_path in ("/voice/session", "/voice/reset"):
            self._send_json({
                "status": "success",
                "session_id": f"dhruva_voice_{int(datetime.now(timezone.utc).timestamp())}",
                "greeting": "Namaste! I am DHRUVA, your cultural and spiritual journey assistant. How may I guide your travels across Odisha today?",
                "suggested_prompts": [
                    "Plan a 3-day spiritual trip to Puri",
                    "Explore ancient temples in Bhubaneswar",
                    "Tell me about the Sun Temple in Konark",
                    "Check festival dates for Rath Yatra"
                ]
            })
            return

        # 11. POST /users/inputs
        if norm_path == "/users/inputs":
            self._send_json({
                "status": "success",
                "id": int(datetime.now(timezone.utc).timestamp()),
                "message": "User planner inputs saved successfully"
            })
            return

        self._send_error_json(f"POST API endpoint not found: {path}", status_code=404)

    # -----------------------------------------------------------------
    # PATCH Dispatcher
    # -----------------------------------------------------------------
    def do_PATCH(self) -> None:
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        body = self._read_json_body()
        norm_path = path[4:] if path.startswith("/api") else path

        if norm_path.startswith("/trips/"):
            sub = norm_path[len("/trips/"):]
            if sub.isdigit():
                self._handle_patch_trip(int(sub), body)
                return

        self._send_error_json(f"PATCH API endpoint not found: {path}", status_code=404)

    # -----------------------------------------------------------------
    # DELETE Dispatcher
    # -----------------------------------------------------------------
    def do_DELETE(self) -> None:
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        norm_path = path[4:] if path.startswith("/api") else path

        if norm_path.startswith("/trips/"):
            for separator in ("/itinerary/places/", "/places/"):
                if separator in norm_path:
                    try:
                        prefix, place_part = norm_path.split(separator)
                        trip_id = int(prefix.split("/trips/")[1])
                        place_id = int(place_part)
                        self._handle_remove_place(trip_id, place_id)
                        return
                    except Exception as e:
                        self._send_error_json(f"Invalid delete URL structure: {e}", status_code=400)
                        return

        self._send_error_json(f"DELETE API endpoint not found: {path}", status_code=404)

    # -----------------------------------------------------------------
    # API Handler Implementations
    # -----------------------------------------------------------------
    def _handle_plan_itinerary(self, body: Dict[str, Any]) -> None:
        dest = body.get("destination") or body.get("city_name") or "Bhubaneswar"
        city_id = body.get("city_id")
        num_days = int(body.get("num_days", 2))
        start_date = body.get("start_date", "2026-10-15")
        start_time = body.get("start_time", "08:30 AM")
        end_time = body.get("end_time", "07:30 PM")
        age = int(body.get("age", 55))
        pacing = body.get("pacing", "balanced")
        interests = body.get("interests", {
            "spiritual": 4.5, "architecture": 4.5, "history": 4.0, "culture": 4.5, "nature": 3.0
        })
        mandatory_pids = body.get("mandatory_place_ids", [])

        prefs = UserPlannerPreferences(
            city_name=dest,
            city_id=city_id,
            start_date=start_date,
            num_days=num_days,
            start_time=start_time,
            end_time=end_time,
            age=age,
            pacing=pacing,
            interests=interests,
            mandatory_place_ids=mandatory_pids
        )

        plan = self.engine.generate_itinerary(prefs)
        if plan.get("status") == "conflict":
            self._send_json(plan, status_code=409)  # 409 Conflict with structured recommendation
        else:
            self._send_json(plan, status_code=200)

    def _handle_full_trip(self, body: Dict[str, Any]) -> None:
        city_id = int(body.get("city_id", 1))
        city = self.repo.get_city(city_id)
        if not city:
            self._send_error_json(f"City with ID {city_id} not found", status_code=404)
            return

        title = body.get("title", f"{city.name} Full Trip")
        raw_windows = body.get("time_windows", [])
        time_windows = []
        for w in raw_windows:
            tw = TripTimeWindow(
                id=w.get("id"),
                day_number=int(w.get("day_number", 1)),
                date_str=w.get("date_str") or w.get("date") or "2026-10-15",
                window_start=w.get("window_start", "08:30:00"),
                window_end=w.get("window_end", "19:00:00"),
                start_lat=float(w["start_lat"]) if w.get("start_lat") is not None else city.lat,
                start_long=float(w["start_long"]) if w.get("start_long") is not None else city.long,
                end_lat=float(w["end_lat"]) if w.get("end_lat") is not None else None,
                end_long=float(w["end_long"]) if w.get("end_long") is not None else None,
            )
            time_windows.append(tw)

        start_lat = float(body.get("start_lat", time_windows[0].start_lat if time_windows else city.lat))
        start_long = float(body.get("start_long", time_windows[0].start_long if time_windows else city.long))
        end_lat = float(body["end_lat"]) if "end_lat" in body and body["end_lat"] is not None else None
        end_long = float(body["end_long"]) if "end_long" in body and body["end_long"] is not None else None
        start_datetime = body.get("start_datetime", "")
        end_datetime = body.get("end_datetime", "")
        preferences = body.get("preferences", {})
        mandatory_place_ids = [int(pid) for pid in body.get("mandatory_place_ids", [])]

        trip = Trip(
            id=None,
            title=title,
            mode="full_trip",
            city_id=city_id,
            start_lat=start_lat,
            start_long=start_long,
            end_lat=end_lat,
            end_long=end_long,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            time_windows=time_windows,
            preferences=preferences,
            mandatory_place_ids=mandatory_place_ids,
        )

        gen_res = self.generator.generate(trip)
        if gen_res.status == "conflict":
            self._send_json(gen_res.to_dict(), status_code=409)
            return

        self.repo.save_trip(trip)
        trip_dict = self._serialize_trip(trip)
        self._send_json({
            "status": "success",
            "trip": trip_dict,
            "itinerary_items": trip_dict["itinerary_items"]
        }, status_code=200)

    def _handle_quick_visit(self, body: Dict[str, Any]) -> None:
        """Handle Quick Visit mode (single-day, constrained total minutes)."""
        city_id = body.get("city_id")
        dest_name = body.get("destination") or body.get("city_name")
        city_obj = None
        if city_id:
            city_obj = self.repo.get_city(int(city_id))
        elif dest_name:
            city_obj = self.repo.get_city_by_name(dest_name)

        if not city_obj:
            city_obj = self.repo.get_city(1)

        start_lat = float(body.get("start_lat", city_obj.lat))
        start_long = float(body.get("start_long", city_obj.long))
        end_lat = float(body["end_lat"]) if "end_lat" in body and body["end_lat"] is not None else None
        end_long = float(body["end_long"]) if "end_long" in body and body["end_long"] is not None else None

        total_minutes = int(body.get("total_minutes", 240))  # 4 hours default
        start_dt = body.get("start_datetime", datetime.now(timezone.utc).strftime("%Y-%m-%d 09:00:00"))
        prefs = body.get("preferences", {
            "spiritual": 4.5, "architecture": 4.5, "history": 4.0, "culture": 4.5, "nature": 3.0
        })
        mandatory_pids = [int(pid) for pid in body.get("mandatory_place_ids", [])]

        trip = Trip(
            id=None,
            title=body.get("title", f"{city_obj.name} Quick Visit Tour"),
            mode="quick_visit",
            city_id=city_obj.id,
            start_lat=start_lat,
            start_long=start_long,
            end_lat=end_lat,
            end_long=end_long,
            start_datetime=start_dt,
            total_minutes=total_minutes,
            preferences=prefs,
            mandatory_place_ids=mandatory_pids
        )

        gen_result = self.generator.generate(trip)
        if gen_result.status == "conflict":
            self._send_json(gen_result.to_dict(), status_code=409)
            return

        self.repo.save_trip(trip)
        trip_dict = self._serialize_trip(trip)
        self._send_json({
            "status": "success",
            "trip": trip_dict,
            "itinerary_items": trip_dict["itinerary_items"],
            "destination": city_obj.name,
            "trip_title": trip.title,
            "mode": trip.mode,
            "available_minutes": total_minutes
        }, status_code=200)

    def _handle_add_place(self, trip_id: int, body: Dict[str, Any]) -> None:
        trip = self.repo.get_trip(trip_id)
        if not trip:
            self._send_error_json(f"Trip #{trip_id} not found", status_code=404)
            return

        place_id = body.get("place_id")
        if not place_id:
            self._send_error_json("Missing place_id in payload", status_code=400)
            return

        day_number = int(body.get("day_number", 1))
        try:
            result = self.generator.add_place_to_itinerary(trip, int(place_id), day_number=day_number)
            if hasattr(result, "status") and result.status == "conflict":
                self._send_json(result.to_dict(), status_code=409)
                return
            self.repo.save_trip(trip)
            trip_dict = self._serialize_trip(trip)
            self._send_json({
                "status": "success",
                "message": f"Place #{place_id} added and itinerary rebalanced",
                "trip": trip_dict,
                "itinerary_items": trip_dict["itinerary_items"]
            })
        except Exception as e:
            self._send_error_json(f"Failed to add place: {e}", status_code=400)

    def _handle_remove_place(self, trip_id: int, place_id: int) -> None:
        trip = self.repo.get_trip(trip_id)
        if not trip:
            self._send_error_json(f"Trip #{trip_id} not found", status_code=404)
            return

        try:
            self.generator.remove_place_from_itinerary(trip, place_id)
            self.repo.save_trip(trip)
            trip_dict = self._serialize_trip(trip)
            self._send_json({
                "status": "success",
                "message": f"Place #{place_id} removed and itinerary rebalanced",
                "trip": trip_dict,
                "itinerary_items": trip_dict["itinerary_items"]
            })
        except Exception as e:
            self._send_error_json(f"Failed to remove place: {e}", status_code=400)

    def _handle_shuffle(self, trip_id: int) -> None:
        trip = self.repo.get_trip(trip_id)
        if not trip:
            self._send_error_json(f"Trip #{trip_id} not found", status_code=404)
            return

        try:
            result = self.generator.generate_shuffle(trip)
            self.repo.save_trip(trip)
            trip_dict = self._serialize_trip(trip)
            self._send_json({
                "status": "success",
                "shuffle_count": trip.shuffle_count,
                "shuffle_index": trip.shuffle_count,
                "remaining_shuffles": max(0, settings.max_shuffle_count - trip.shuffle_count),
                "trip": trip_dict,
                "itinerary_items": trip_dict["itinerary_items"]
            })
        except ValueError as ve:
            self._send_error_json(str(ve), status_code=429)  # Max shuffles reached
        except Exception as e:
            self._send_error_json(f"Shuffle failed: {e}", status_code=400)

    def _handle_generate_itinerary(self, trip_id: int) -> None:
        trip = self.repo.get_trip(trip_id)
        if not trip:
            self._send_error_json(f"Trip #{trip_id} not found", status_code=404)
            return

        gen_result = self.generator.generate(trip)
        if gen_result.status == "conflict":
            self._send_json(gen_result.to_dict(), status_code=409)
            return

        self.repo.save_trip(trip)
        trip_dict = self._serialize_trip(trip)
        self._send_json({
            "status": "success",
            "trip": trip_dict,
            "itinerary_items": trip_dict["itinerary_items"]
        }, status_code=200)

    def _handle_patch_trip(self, trip_id: int, body: Dict[str, Any]) -> None:
        trip = self.repo.get_trip(trip_id)
        if not trip:
            self._send_error_json(f"Trip #{trip_id} not found", status_code=404)
            return

        if "title" in body:
            trip.title = str(body["title"])
        if "preferences" in body and isinstance(body["preferences"], dict):
            trip.preferences = body["preferences"]
        if "mandatory_place_ids" in body and isinstance(body["mandatory_place_ids"], list):
            trip.mandatory_place_ids = [int(pid) for pid in body["mandatory_place_ids"]]
        if "total_minutes" in body:
            trip.total_minutes = int(body["total_minutes"])
        if "start_datetime" in body:
            trip.start_datetime = str(body["start_datetime"])
        if "end_datetime" in body:
            trip.end_datetime = str(body["end_datetime"])
        if "time_windows" in body and isinstance(body["time_windows"], list):
            new_windows = []
            for w in body["time_windows"]:
                tw = TripTimeWindow(
                    id=w.get("id"),
                    day_number=int(w.get("day_number", 1)),
                    date_str=w.get("date_str") or w.get("date") or "2026-10-15",
                    window_start=w.get("window_start", "08:30:00"),
                    window_end=w.get("window_end", "19:00:00"),
                    start_lat=float(w["start_lat"]) if w.get("start_lat") is not None else trip.start_lat,
                    start_long=float(w["start_long"]) if w.get("start_long") is not None else trip.start_long,
                    end_lat=float(w["end_lat"]) if w.get("end_lat") is not None else None,
                    end_long=float(w["end_long"]) if w.get("end_long") is not None else None,
                )
                new_windows.append(tw)
            trip.time_windows = new_windows

        gen_result = self.generator.generate(trip)
        if gen_result.status == "conflict":
            self._send_json(gen_result.to_dict(), status_code=409)
            return

        self.repo.save_trip(trip)
        trip_dict = self._serialize_trip(trip)
        self._send_json({
            "status": "success",
            "message": f"Trip #{trip_id} updated and itinerary regenerated",
            "trip": trip_dict,
            "itinerary_items": trip_dict["itinerary_items"]
        }, status_code=200)

    def _handle_scoring_breakdown(self, body: Dict[str, Any]) -> None:
        place_id = body.get("place_id")
        place = self.repo.get_place(place_id) if place_id else None
        if not place:
            self._send_error_json("Valid place_id required for scoring breakdown", status_code=400)
            return

        user_prefs = body.get("user_prefs", {
            "spiritual": 4.5, "architecture": 4.5, "history": 4.0, "culture": 4.5, "nature": 3.0
        })
        travel_time = float(body.get("travel_time_minutes", 15.0))
        travel_dist = float(body.get("travel_distance_km", 5.0))
        day_name = body.get("day_name", "Monday")
        arrival_min = int(body.get("arrival_minute_from_midnight", 540))

        breakdown = score_place_candidate(
            place=place,
            user_prefs=user_prefs,
            travel_time_minutes=travel_time,
            travel_distance_km=travel_dist,
            day_name=day_name,
            arrival_minute_from_midnight=arrival_min
        )

        self._send_json({
            "status": "success",
            "breakdown": {
                "place_id": breakdown.place_id,
                "place_name": breakdown.place_name,
                "interest_match": breakdown.interest_match,
                "popularity_score": breakdown.popularity_score,
                "cultural_score": breakdown.cultural_score,
                "raw_utility": breakdown.raw_utility,
                "travel_time_minutes": breakdown.travel_time_minutes,
                "travel_distance_km": breakdown.travel_distance_km,
                "visit_duration_minutes": breakdown.visit_duration_minutes,
                "total_time_cost_minutes": breakdown.total_time_cost_minutes,
                "efficiency_score": breakdown.efficiency_score,
                "is_open": breakdown.is_open,
                "notes": breakdown.notes,
            }
        })

    def _handle_routing_matrix(self, body: Dict[str, Any]) -> None:
        raw_coords = body.get("coordinates", [])
        profile = body.get("profile", settings.ors_profile)
        if not raw_coords or len(raw_coords) < 2:
            self._send_error_json("Matrix requires at least 2 coordinate pairs [[lat, lon], ...]", status_code=400)
            return

        coords = [(float(pt[0]), float(pt[1])) for pt in raw_coords]
        matrix_res = self.router.calculate_matrix(coords, profile=profile)

        self._send_json({
            "status": "success",
            "source": matrix_res.source,
            "locations_count": len(coords),
            "durations_minutes": matrix_res.durations_minutes,
            "distances_km": matrix_res.distances_km,
            "matrix": {
                "durations": matrix_res.durations_minutes,
                "distances": matrix_res.distances_km,
            }
        })

    # -----------------------------------------------------------------
    # Static File Dispatcher
    # -----------------------------------------------------------------
    def _serve_static_file(self, path: str) -> None:
        if path == "/" or not path:
            path = "/index.html"

        # Remove leading slash and decode
        rel_path = unquote(path.lstrip("/"))
        file_path = (FRONTEND_DIR / rel_path).resolve()

        # Security check: ensure path is within FRONTEND_DIR
        try:
            file_path.relative_to(FRONTEND_DIR)
        except ValueError:
            self._send_error_json("Access forbidden", status_code=403)
            return

        if not file_path.exists() or not file_path.is_file():
            self._send_error_json(f"File not found: {path}", status_code=404)
            return

        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "application/octet-stream"

        try:
            with open(file_path, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8" if "text" in mime_type or "json" in mime_type or "javascript" in mime_type else mime_type)
            self.send_header("Content-Length", str(len(content)))
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            logger.error(f"Error serving {file_path}: {e}")
            self._send_error_json("Internal server error", status_code=500)


def run_server(port: int = 8000, host: str = "0.0.0.0") -> None:
    """Start standalone DHRUVA backend server."""
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, DhruvaAPIRequestHandler)
    print(f"===============================================================")
    print(f"  DHRUVA Travel Planning Backend running at http://localhost:{port}/")
    print(f"  - Web Client: http://localhost:{port}/index.html")
    print(f"  - Explore:    http://localhost:{port}/pages/explore.html")
    print(f"  - Planner:    http://localhost:{port}/pages/trip.html")
    print(f"  - REST APIs:  http://localhost:{port}/api/health")
    print(f"===============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down DHRUVA server gracefully...")
        httpd.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8000
    run_server(port=port)
