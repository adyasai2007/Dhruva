"""
End-to-end verification of Dhruva integrated server.py.
Tests static asset dispatching and REST API endpoints over HTTP.
"""
import json
import threading
import time
import urllib.request
import urllib.parse
import sys
from http.server import HTTPServer
from pathlib import Path

# Add Dhruva root to sys.path
dhruva_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(dhruva_root))

from backend.server import DhruvaAPIRequestHandler

def run_tests():
    port = 8765
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, DhruvaAPIRequestHandler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)

    base_url = f"http://127.0.0.1:{port}"
    print(f"Testing server at {base_url}...")

    tests_passed = 0
    total_tests = 0

    def check(desc, condition):
        nonlocal tests_passed, total_tests
        total_tests += 1
        if condition:
            tests_passed += 1
            print(f"  [PASS] {desc}")
        else:
            print(f"  [FAIL] {desc}")

    # 1. Test Static Files
    static_routes = [
        "/index.html",
        "/pages/explore.html",
        "/pages/trip.html",
        "/pages/itinerary.html",
        "/pages/profile.html",
        "/css/variables.css",
        "/css/style.css",
        "/css/components.css",
        "/css/voice-orb.css",
        "/css/responsive.css",
        "/js/app.js",
        "/js/navigation.js",
        "/js/components.js",
        "/js/planner.js",
        "/js/voice-orb.js",
        "/mock/destinations.json",
        "/mock/places.json",
        "/mock/itineraries.json",
        "/mock/events.json",
        "/mock/users.json"
    ]

    print("\n--- 1. Testing Static Asset Serving from frontend/ ---")
    for route in static_routes:
        try:
            req = urllib.request.urlopen(f"{base_url}{route}")
            content = req.read()
            check(f"GET {route} (HTTP {req.status}, {len(content)} bytes)", req.status == 200 and len(content) > 0)
        except Exception as e:
            check(f"GET {route} - Exception: {e}", False)

    # 2. Test Root Route fallback to index.html
    try:
        req = urllib.request.urlopen(f"{base_url}/")
        content = req.read().decode('utf-8')
        check(f"GET / -> index.html fallback", req.status == 200 and "DHRUVA" in content)
    except Exception as e:
        check(f"GET / - Exception: {e}", False)

    # 3. Test REST APIs
    print("\n--- 2. Testing REST API Endpoints ---")

    # /api/health
    try:
        req = urllib.request.urlopen(f"{base_url}/api/health")
        data = json.loads(req.read().decode('utf-8'))
        check("/api/health returns healthy status & record counts", data.get("status") == "healthy" and data["records"]["cities_count"] == 3)
    except Exception as e:
        check(f"/api/health - Exception: {e}", False)

    # /api/cities
    try:
        req = urllib.request.urlopen(f"{base_url}/api/cities")
        data = json.loads(req.read().decode('utf-8'))
        check(f"/api/cities returns {data.get('count')} cities", data.get("status") == "success" and data.get("count") >= 3)
    except Exception as e:
        check(f"/api/cities - Exception: {e}", False)

    # /api/places
    try:
        req = urllib.request.urlopen(f"{base_url}/api/places?city=Puri")
        data = json.loads(req.read().decode('utf-8'))
        check(f"/api/places?city=Puri returns {data.get('count')} places", data.get("status") == "success" and data.get("count") >= 5)
    except Exception as e:
        check(f"/api/places - Exception: {e}", False)

    # /api/festivals
    try:
        req = urllib.request.urlopen(f"{base_url}/api/festivals")
        data = json.loads(req.read().decode('utf-8'))
        check(f"/api/festivals returns {data.get('count')} festivals", data.get("status") == "success" and data.get("count") >= 5)
    except Exception as e:
        check(f"/api/festivals - Exception: {e}", False)

    # POST /api/itinerary/plan
    try:
        payload = json.dumps({
            "destination": "Bhubaneswar",
            "num_days": 2,
            "age": 55,
            "pacing": "balanced",
            "interests": {"spiritual": 4.5, "architecture": 4.5, "history": 4.0, "culture": 4.5, "nature": 3.0}
        }).encode('utf-8')
        post_req = urllib.request.Request(
            f"{base_url}/api/itinerary/plan",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        res = urllib.request.urlopen(post_req)
        plan_data = json.loads(res.read().decode('utf-8'))
        check("POST /api/itinerary/plan generates multi-day itinerary", plan_data.get("status") == "success" and len(plan_data.get("days", [])) == 2)
    except Exception as e:
        check(f"POST /api/itinerary/plan - Exception: {e}", False)

    # POST /api/users/inputs
    try:
        user_payload = json.dumps({
            "gps_location": "20.2961,85.8245",
            "start_date": "2026-10-15",
            "start_time": "08:30 AM",
            "end_time": "07:30 PM",
            "age": 58
        }).encode('utf-8')
        user_req = urllib.request.Request(
            f"{base_url}/api/users/inputs",
            data=user_payload,
            headers={"Content-Type": "application/json"}
        )
        user_res = urllib.request.urlopen(user_req)
        user_res_data = json.loads(user_res.read().decode('utf-8'))
        check(f"POST /api/users/inputs saves record (id: {user_res_data.get('id')})", user_res_data.get("status") == "success" and user_res_data.get("id") is not None)
    except Exception as e:
        check(f"POST /api/users/inputs - Exception: {e}", False)

    print("\n=================================================================")
    print(f"SERVER VERIFICATION RESULT: {tests_passed}/{total_tests} TESTS PASSED")
    print("=================================================================")

    httpd.shutdown()
    httpd.server_close()

if __name__ == "__main__":
    run_tests()
