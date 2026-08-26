"""
DHRUVA Integrated HTTP REST API & Static Web Server.
Zero-external-dependency server built using Python's standard library `http.server`.
Serves both the frontend web application and REST API endpoints connected to dhruva.db.
"""

from __future__ import annotations
import argparse
import json
import logging
import mimetypes
import os
import sys
import urllib.parse
from http import HTTPStatus
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.database.db_service import DhruvaDBService
from backend.services.itinerary_engine import CulturalItineraryEngine, UserPlannerPreferences

logger = logging.getLogger("dhruva.server")


class DhruvaAPIRequestHandler(SimpleHTTPRequestHandler):
    """
    HTTP Request Handler combining REST API routing (/api/*) and static asset serving.
    """

    db_service: DhruvaDBService = DhruvaDBService()
    itinerary_engine: CulturalItineraryEngine = CulturalItineraryEngine(db_service)

    def _send_json_response(self, data: Any, status: int = 200) -> None:
        """Helper to serialize and transmit JSON payload with CORS headers."""
        try:
            body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            logger.error(f"Error transmitting JSON response: {e}")

    def do_OPTIONS(self) -> None:
        """Handle CORS preflight requests."""
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self) -> None:
        """Route GET requests to API handlers or static file dispatcher."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # -------------------------------------------------------------
        # REST API Routes
        # -------------------------------------------------------------
        if path.startswith("/api/"):
            # 1. Health & Statistics
            if path == "/api/health":
                cities = self.db_service.get_cities()
                places = self.db_service.get_places(limit=500)
                festivals = self.db_service.get_festivals()
                return self._send_json_response({
                    "status": "healthy",
                    "version": "1.0.0",
                    "database": str(self.db_service.db_path.resolve()),
                    "records": {
                        "cities_count": len(cities),
                        "places_count": len(places),
                        "festivals_count": len(festivals)
                    }
                })

            # 2. Cities API
            if path == "/api/cities":
                cities = self.db_service.get_cities()
                return self._send_json_response({"status": "success", "count": len(cities), "data": cities})

            if path.startswith("/api/cities/"):
                city_id_str = path.replace("/api/cities/", "").strip("/")
                if city_id_str.isdigit():
                    city = self.db_service.get_city_by_id(int(city_id_str))
                    if city:
                        return self._send_json_response({"status": "success", "data": city})
                    return self._send_json_response({"status": "error", "message": "City not found"}, 404)

            # 3. Places API
            if path == "/api/places":
                city_id = int(query_params["city_id"][0]) if "city_id" in query_params else None
                city_name = query_params["city"][0] if "city" in query_params else None
                category = query_params["category"][0] if "category" in query_params else None
                search = query_params["search"][0] if "search" in query_params else None
                min_popularity = float(query_params["min_popularity"][0]) if "min_popularity" in query_params else 0.0
                min_spir = float(query_params["spiritual"][0]) if "spiritual" in query_params else 0.0
                min_arch = float(query_params["architecture"][0]) if "architecture" in query_params else 0.0
                min_hist = float(query_params["history"][0]) if "history" in query_params else 0.0
                min_nat = float(query_params["nature"][0]) if "nature" in query_params else 0.0
                min_cult = float(query_params["culture"][0]) if "culture" in query_params else 0.0
                sort_by = query_params["sort_by"][0] if "sort_by" in query_params else "popularity"
                limit = int(query_params["limit"][0]) if "limit" in query_params else 50
                offset = int(query_params["offset"][0]) if "offset" in query_params else 0

                places = self.db_service.get_places(
                    city_id=city_id,
                    city_name=city_name,
                    category=category,
                    search=search,
                    min_popularity=min_popularity,
                    min_spiritual=min_spir,
                    min_architecture=min_arch,
                    min_history=min_hist,
                    min_nature=min_nat,
                    min_culture=min_cult,
                    sort_by=sort_by,
                    limit=limit,
                    offset=offset
                )
                return self._send_json_response({"status": "success", "count": len(places), "data": places})

            # 4. Nearby Places API
            if path == "/api/places/nearby":
                if "lat" in query_params and "lon" in query_params:
                    lat = float(query_params["lat"][0])
                    lon = float(query_params["lon"][0])
                    max_dist = float(query_params.get("max_distance_km", [40.0])[0])
                    limit = int(query_params.get("limit", [10])[0])
                    nearby = self.db_service.get_nearby_places(lat, lon, max_dist, limit)
                    return self._send_json_response({"status": "success", "count": len(nearby), "data": nearby})
                return self._send_json_response({"status": "error", "message": "Missing lat/lon parameters"}, 400)

            # 5. Place by ID (Full Detail with Opening Hours & Interest Scores)
            if path.startswith("/api/places/"):
                place_id_str = path.replace("/api/places/", "").strip("/")
                if place_id_str.isdigit():
                    place = self.db_service.get_place_by_id(int(place_id_str))
                    if place:
                        return self._send_json_response({"status": "success", "data": place})
                    return self._send_json_response({"status": "error", "message": "Place not found"}, 404)

            # 6. Festivals API
            if path == "/api/festivals":
                city_id = int(query_params["city_id"][0]) if "city_id" in query_params else None
                festivals = self.db_service.get_festivals(city_id=city_id)
                return self._send_json_response({"status": "success", "count": len(festivals), "data": festivals})

            # 7. User Inputs API
            if path == "/api/users/inputs":
                inputs = self.db_service.get_user_inputs()
                return self._send_json_response({"status": "success", "count": len(inputs), "data": inputs})

            return self._send_json_response({"status": "error", "message": f"Endpoint not found: {path}"}, 404)

        # -------------------------------------------------------------
        # Static Asset Serving (Frontend HTML/CSS/JS)
        # -------------------------------------------------------------
        return super().do_GET()

    def do_POST(self) -> None:
        """Handle POST requests for trip planning and user input saving."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        # Read JSON body
        content_length = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        try:
            payload = json.loads(post_body) if post_body else {}
        except json.JSONDecodeError:
            return self._send_json_response({"status": "error", "message": "Invalid JSON in request body"}, 400)

        # 1. Dynamic Itinerary Generation
        if path == "/api/itinerary/plan":
            prefs = UserPlannerPreferences(
                city_id=payload.get("city_id"),
                city_name=payload.get("city_name") or payload.get("destination"),
                gps_location=payload.get("gps_location"),
                start_date=payload.get("start_date", "2026-10-15"),
                num_days=int(payload.get("num_days", payload.get("days", 3))),
                start_time=payload.get("start_time", "08:30 AM"),
                end_time=payload.get("end_time", "07:30 PM"),
                age=int(payload.get("age", 58)),
                pacing=payload.get("pacing", "balanced"),
                interests=payload.get("interests", {
                    "spiritual": 4.5,
                    "architecture": 4.5,
                    "history": 4.0,
                    "culture": 4.5,
                    "nature": 3.0
                })
            )
            result = self.itinerary_engine.generate_itinerary(prefs)
            return self._send_json_response(result)

        # 2. Save User Input Record
        if path == "/api/users/inputs":
            gps = payload.get("gps_location", "20.2961,85.8245")
            sdate = payload.get("start_date", "2026-10-15")
            stime = payload.get("start_time", "08:00 AM")
            etime = payload.get("end_time", "08:00 PM")
            age = int(payload.get("age", 50))
            new_id = self.db_service.save_user_input(gps, sdate, stime, etime, age)
            return self._send_json_response({
                "status": "success",
                "message": "User input saved successfully",
                "id": new_id
            }, 201)

        return self._send_json_response({"status": "error", "message": f"POST endpoint not found: {path}"}, 404)


def run_server(port: int = 8000, host: str = "0.0.0.0") -> None:
    """Start the integrated DHRUVA REST API & Frontend Server."""
    server_address = (host, port)
    httpd = HTTPServer(server_address, DhruvaAPIRequestHandler)
    print("\n" + "=" * 70)
    print(f"  DHRUVA INTEGRATED BACKEND & FRONTEND SERVER RUNNING")
    print("=" * 70)
    print(f"  * Web Application URL : http://localhost:{port}/index.html")
    print(f"  * Explore Directory   : http://localhost:{port}/pages/explore.html")
    print(f"  * Trip Planner Wizard : http://localhost:{port}/pages/trip.html")
    print(f"  * REST API Health     : http://localhost:{port}/api/health")
    print(f"  * REST API Cities     : http://localhost:{port}/api/cities")
    print(f"  * REST API Places     : http://localhost:{port}/api/places")
    print(f"  * REST API Festivals  : http://localhost:{port}/api/festivals")
    print(f"  * Itinerary Generator : POST http://localhost:{port}/api/itinerary/plan")
    print("=" * 70 + "\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping DHRUVA server...")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DHRUVA Integrated HTTP Server")
    parser.add_argument("port", nargs="?", type=int, default=8000, help="Port to bind server (default: 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface to bind")
    args = parser.parse_args()
    run_server(port=args.port, host=args.host)
