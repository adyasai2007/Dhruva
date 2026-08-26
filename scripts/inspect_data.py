import json
import csv
from pathlib import Path

def inspect_all():
    normalized_path = Path("data/scraped/normalized_places.json")
    csv_path = Path("data/scraped/places.csv")
    raw_path = Path("data/scraped/raw_places.json")

    with open(normalized_path, "r", encoding="utf-8") as f:
        places_json = json.load(f)

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        places_csv = list(reader)

    print(f"Normalized JSON count: {len(places_json)}")
    print(f"Places CSV count: {len(places_csv)}")

    print("\n--- ALL PLACES IN JSON ---")
    for i, p in enumerate(places_json):
        img_count = len(p.get("image_urls", []))
        sec_images = [img for img in p.get("image_urls", []) if "incredible-india-og.png" not in img]
        festivals = p.get("festivals", [])
        timing = p.get("opening_hours", "")
        duration = p.get("recommended_duration", "")
        category = p.get("category", "")
        print(f"[{i}] id: '{p['id']}' | name: '{p['name']}' | city: '{p['city']}' | coords: ({p.get('latitude')}, {p.get('longitude')}) | sec_imgs: {len(sec_images)} | festivals: {len(festivals)} | timing: '{timing}' | dur: '{duration}' | cat: '{category}'")

    print("\n--- DETAIL OF ROW 0 & 1 ---")
    for i in [0, 1]:
        print(f"Row {i}:", json.dumps(places_json[i], indent=2))

if __name__ == "__main__":
    inspect_all()
