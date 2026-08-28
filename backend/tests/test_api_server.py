"""
Integration tests for the Zero-Dependency Dhruva REST API and Static File Server.
"""

import json
import threading
import urllib.request
import urllib.error
import urllib.parse
from http.server import ThreadingHTTPServer
import pytest

from backend.server import DhruvaAPIRequestHandler


@pytest.fixture(scope="module")
def server_url():
    """Start test server on an ephemeral port in a daemon thread."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), DhruvaAPIRequestHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"
    yield base_url
    server.shutdown()
    server.server_close()


def http_get(url: str):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
            status = resp.status
            content_type = resp.headers.get("Content-Type", "")
            return status, content_type, data
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", ""), e.read()


def http_post(url: str, body: dict):
    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
            status = resp.status
            return status, json.loads(data.decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def http_delete(url: str):
    req = urllib.request.Request(url, headers={"Accept": "application/json"}, method="DELETE")
    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
            status = resp.status
            return status, json.loads(data.decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


class TestStaticAndHealthEndpoints:
    def test_health_check(self, server_url):
        status, ctype, data = http_get(f"{server_url}/api/health")
        assert status == 200
        assert "application/json" in ctype
        res = json.loads(data.decode("utf-8"))
        assert res["status"] == "healthy"
        assert res["service"] == "dhruva-backend"

    def test_static_index_html(self, server_url):
        status, ctype, data = http_get(f"{server_url}/index.html")
        assert status == 200
        assert "text/html" in ctype
        assert b"DHRUVA" in data

    def test_static_css_variables(self, server_url):
        status, ctype, data = http_get(f"{server_url}/css/variables.css")
        assert status == 200
        assert "text/css" in ctype

    def test_static_mock_json(self, server_url):
        status, ctype, data = http_get(f"{server_url}/mock/destinations.json")
        assert status == 200
        assert "application/json" in ctype
        res = json.loads(data.decode("utf-8"))
        assert isinstance(res, list)

    def test_nonexistent_static_file(self, server_url):
        status, _, _ = http_get(f"{server_url}/nonexistent-file.xyz")
        assert status == 404


class TestDataQueryEndpoints:
    def test_get_cities(self, server_url):
        status, _, data = http_get(f"{server_url}/api/cities")
        assert status == 200
        cities = json.loads(data.decode("utf-8"))
        assert len(cities) == 3
        names = [c["name"] for c in cities]
        assert "Bhubaneswar" in names
        assert "Puri" in names

    def test_get_places_filtered(self, server_url):
        # Filter by city
        status, _, data = http_get(f"{server_url}/api/places?city_name=Bhubaneswar&limit=5")
        assert status == 200
        places = json.loads(data.decode("utf-8"))
        assert len(places) <= 5
        assert len(places) > 0
        assert places[0]["city_id"] == 1

    def test_get_festivals(self, server_url):
        status, _, data = http_get(f"{server_url}/api/festivals?city_name=Puri")
        assert status == 200
        festivals = json.loads(data.decode("utf-8"))
        assert len(festivals) > 0


class TestScoringAndRoutingEndpoints:
    def test_scoring_breakdown_endpoint(self, server_url):
        status, res = http_post(
            f"{server_url}/api/scoring/breakdown",
            {
                "place_id": 1,
                "preferences": {"spiritual": 5.0, "architecture": 4.5},
                "travel_time_minutes": 10.0,
                "travel_distance_km": 4.5,
                "day_name": "Monday",
                "arrival_minute": 540
            }
        )
        assert status == 200
        assert res["status"] == "success"
        breakdown = res["breakdown"]
        assert breakdown["place_id"] == 1
        assert breakdown["is_open"] is True
        assert breakdown["efficiency_score"] > 0

    def test_routing_matrix_endpoint(self, server_url):
        status, res = http_post(
            f"{server_url}/api/routing/matrix",
            {
                "coordinates": [
                    [85.8245, 20.2961],
                    [85.8338, 20.2382]
                ]
            }
        )
        assert status == 200
        assert res["status"] == "success"
        matrix = res["matrix"]
        assert len(matrix["durations"]) == 2
        assert len(matrix["distances"]) == 2
        assert matrix["durations"][0][0] == 0.0


class TestTripPlanningAndLifecycle:
    def test_cultural_plan_generation(self, server_url):
        status, res = http_post(
            f"{server_url}/api/itinerary/plan",
            {
                "city_name": "Bhubaneswar",
                "start_date": "2026-10-15",
                "num_days": 2,
                "start_time": "08:30 AM",
                "end_time": "06:30 PM",
                "age": 58,
                "pacing": "balanced",
                "interests": {"spiritual": 4.5, "architecture": 4.5, "history": 4.0}
            }
        )
        assert status == 200
        assert res["status"] == "success"
        assert res["senior_friendly"] is True
        assert len(res["days"]) == 2
        assert res["trip_id"] is not None

    def test_full_trip_crud_and_shuffle(self, server_url):
        # 1. Create Trip via /api/trips/full-trip
        status, res = http_post(
            f"{server_url}/api/trips/full-trip",
            {
                "title": "API Full Trip Test",
                "city_id": 1,
                "time_windows": [
                    {
                        "day_number": 1,
                        "date_str": "2026-10-15",
                        "window_start": "08:30:00",
                        "window_end": "19:00:00",
                        "start_lat": 20.2961,
                        "start_long": 85.8245
                    }
                ],
                "preferences": {"spiritual": 5.0, "architecture": 4.5}
            }
        )
        assert status == 200
        assert res["status"] == "success"
        trip_id = res["trip"]["id"]
        assert trip_id is not None
        initial_items = res["trip"]["itinerary_items"]
        assert len(initial_items) > 0

        # 2. Get Trip via GET /api/trips/<id>
        get_status, _, get_data = http_get(f"{server_url}/api/trips/{trip_id}")
        assert get_status == 200
        trip_obj = json.loads(get_data.decode("utf-8"))
        assert trip_obj["id"] == trip_id

        # 3. Dynamic Add Place via POST /api/trips/<id>/itinerary/places
        scheduled_pids = {it["place_id"] for it in initial_items}
        # Find candidate place
        _, _, pdata = http_get(f"{server_url}/api/places?city_name=Bhubaneswar")
        all_places = json.loads(pdata.decode("utf-8"))
        candidate = next((p for p in all_places if p["id"] not in scheduled_pids), None)
        assert candidate is not None

        add_status, add_res = http_post(
            f"{server_url}/api/trips/{trip_id}/itinerary/places",
            {"place_id": candidate["id"], "day_number": 1}
        )
        assert add_status == 200
        assert add_res["status"] == "success"
        assert len(add_res["itinerary_items"]) == len(initial_items) + 1

        # 4. Dynamic Remove Place via DELETE /api/trips/<id>/itinerary/places/<pid>
        del_status, del_res = http_delete(
            f"{server_url}/api/trips/{trip_id}/itinerary/places/{candidate['id']}"
        )
        assert del_status == 200
        assert del_res["status"] == "success"
        assert len(del_res["itinerary_items"]) == len(initial_items)

        # 5. Shuffle Variations (1, 2, 3 succeed; 4th returns 429)
        s1_status, s1_res = http_post(f"{server_url}/api/trips/{trip_id}/itinerary/shuffle", {})
        assert s1_status == 200
        assert s1_res["shuffle_count"] == 1

        s2_status, s2_res = http_post(f"{server_url}/api/trips/{trip_id}/itinerary/shuffle", {})
        assert s2_status == 200
        assert s2_res["shuffle_count"] == 2

        s3_status, s3_res = http_post(f"{server_url}/api/trips/{trip_id}/itinerary/shuffle", {})
        assert s3_status == 200
        assert s3_res["shuffle_count"] == 3

        s4_status, s4_res = http_post(f"{server_url}/api/trips/{trip_id}/itinerary/shuffle", {})
        assert s4_status == 429
        assert "limit" in s4_res["error"].lower()

    def test_quick_visit_endpoint(self, server_url):
        status, res = http_post(
            f"{server_url}/api/trips/quick-visit",
            {
                "city_id": 1,
                "total_minutes": 240,
                "start_datetime": "2026-10-15 09:00:00",
                "preferences": {"spiritual": 5.0, "architecture": 4.5}
            }
        )
        assert status == 200
        assert res["status"] == "success"
        assert len(res["trip"]["itinerary_items"]) >= 1
