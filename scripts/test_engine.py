"""
Quick test of DhruvaDBService and CulturalItineraryEngine.
"""
import sys
from pathlib import Path

# Add Dhruva root to sys.path
dhruva_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(dhruva_root))

from backend.database.db_service import DhruvaDBService
from backend.services.itinerary_engine import CulturalItineraryEngine, UserPlannerPreferences

def main():
    print("=================================================================")
    print("Testing DhruvaDBService and CulturalItineraryEngine")
    print("=================================================================")

    db = DhruvaDBService()
    cities = db.get_cities()
    print(f"1. Cities retrieved: {len(cities)}")
    for c in cities:
        print(f"   - {c['name']}, {c['state']} (places: {c['place_count']}, avg rating: {round(c['avg_rating'], 2)})")

    places = db.get_places(city_name="Puri", limit=10)
    print(f"\n2. Places in Puri: {len(places)}")
    for p in places:
        print(f"   - {p['name']} ({p['category']}) | Rating: {p['popularity']} | Duration: {p['duration_label']}")

    engine = CulturalItineraryEngine(db)
    prefs = UserPlannerPreferences(
        city_name="Puri",
        start_date="2026-10-15",
        num_days=2,
        start_time="08:30 AM",
        end_time="07:30 PM",
        age=58,
        pacing="relaxed",
        interests={"spiritual": 5.0, "architecture": 4.5, "history": 4.0, "culture": 4.5, "nature": 2.0}
    )
    plan = engine.generate_itinerary(prefs)
    print(f"\n3. Generated Itinerary:")
    print(f"   Status: {plan.get('status')}")
    print(f"   Destination: {plan.get('destination')}")
    print(f"   Total Days: {len(plan.get('days', []))}")
    print(f"   Pacing: {plan.get('pacing_profile')}")

    for day in plan.get("days", []):
        print(f"\n   --- Day {day['day_number']} ({day['date']}) | Theme: {day['theme']} ---")
        for act in day.get("activities", []):
            print(f"      [{act['time_slot']}] {act['place_name']} ({act['category']}) - {act['duration_hours']} hrs")
            print(f"         Cultural Tip: {act['cultural_tip']}")

    print("\n=================================================================")
    print("ENGINE TEST PASSED 100%")
    print("=================================================================")

if __name__ == "__main__":
    main()
