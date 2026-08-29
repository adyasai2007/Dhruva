"""
Synchronizes database CSV tables to frontend/mock JSON datasets for standalone client mode.
"""

import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_DIR = BASE_DIR / "database" / "csv"
MOCK_DIR = BASE_DIR / "frontend" / "mock"
MOCK_DIR.mkdir(parents=True, exist_ok=True)

def sync():
    # 1. Read cities & city_interest
    cities = {}
    city_images = {
        1: {
            "hero": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Lingaraj_Temple_%2C_Bhubaneswar.jpg/960px-Lingaraj_Temple_%2C_Bhubaneswar.jpg",
            "tagline": "Temple City of India & Kalinga Heritage",
            "desc": "Explore iconic 11th-century sandstone shrines, Mukteshvara toranas, and ancient rock edicts across Bhubaneswar."
        },
        2: {
            "hero": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/Konarka_Temple.jpg/960px-Konarka_Temple.jpg",
            "tagline": "Spiritual Sanctum of Lord Jagannath & Sun Temple",
            "desc": "Experience the sacred Jagannath Dham, Konark Sun Temple chariot architecture, and living heritage crafts of Raghurajpur."
        },
        3: {
            "hero": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/Entrance_of_Barabati_fort.jpg/960px-Entrance_of_Barabati_fort.jpg",
            "tagline": "Millennium City of Silver Filigree & Barabati Legacy",
            "desc": "Discover the 14th-century Barabati Fort, maritime Bali Yatra traditions, and delicate Tarakasi silver craft quarters."
        }
    }

    with open(CSV_DIR / "cities.csv", "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = int(row["id"])
            c_meta = city_images.get(cid, {
                "hero": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Lingaraj_Temple_%2C_Bhubaneswar.jpg/960px-Lingaraj_Temple_%2C_Bhubaneswar.jpg",
                "tagline": f"Sacred heritage & cultural heart of {row['name']}",
                "desc": f"Explore ancient Kalinga architecture and living traditions in {row['name']}."
            })
            cities[cid] = {
                "id": row["name"].lower(),
                "cityId": cid,
                "name": row["name"],
                "state": row["state"],
                "lat": float(row["lat"]),
                "long": float(row["long"]),
                "region": "East India",
                "tagline": c_meta["tagline"],
                "description": c_meta["desc"],
                "heroImage": c_meta["hero"],
                "thumbnailImage": c_meta["hero"],
                "bestTime": {"idealMonths": "October to March", "temperature": "20°C – 30°C"},
                "placeCount": 0,
                "city_interest": {}
            }

    with open(CSV_DIR / "city_interest.csv", "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = int(row["city_id"])
            if cid in cities:
                cities[cid]["city_interest"] = {
                    "architecture": float(row["architecture"]),
                    "history": float(row["history"]),
                    "spiritual": float(row["spiritual"]),
                    "nature": float(row["nature"]),
                    "culture": float(row["culture"]),
                }

    # 2. Read min_interest
    interests = {}
    with open(CSV_DIR / "min_interest.csv", "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            interests[int(row["place_id"])] = {
                "architecture": float(row["architecture"]),
                "history": float(row["history"]),
                "spiritual": float(row["spiritual"]),
                "nature": float(row["nature"]),
                "culture": float(row["culture"]),
            }

    # 3. Read places
    places = []
    with open(CSV_DIR / "places.csv", "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pid = int(row["id"])
            cid = int(row["city_id"])
            if cid in cities:
                cities[cid]["placeCount"] += 1

            p_int = interests.get(pid, {"architecture": 4.5, "history": 4.5, "spiritual": 4.5, "nature": 2.0, "culture": 4.5})
            places.append({
                "id": str(pid),
                "name": row["name"],
                "cityId": cid,
                "destinationId": cities.get(cid, {}).get("id", "bhubaneswar"),
                "category": row["category"],
                "sub_category": row["sub_category"],
                "shortDescription": row["description"][:160] + "..." if len(row["description"]) > 160 else row["description"],
                "fullDescription": row["description"],
                "culturalSignificance": f"{row['name']} exemplifies the profound living cultural and architectural legacy of Odisha, preserved through centuries.",
                "duration": float(row["duration"]),
                "duration_label": row["duration_label"],
                "recommendedDuration": row["duration_label"],
                "bestTimeOfDay": "Morning Darshan (06:30 AM - 10:30 AM) or Sunset",
                "entry_fee": row["entry_fee"],
                "entryFee": row["entry_fee"],
                "lat": float(row["lat"]),
                "long": float(row["long"]),
                "risk": row["risk"],
                "image": row["image_url"] or "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Lingaraj_Temple_%2C_Bhubaneswar.jpg/960px-Lingaraj_Temple_%2C_Bhubaneswar.jpg",
                "image_url": row["image_url"],
                "source": row["source"],
                "source_url": row["source_url"],
                "interests": p_int,
                "tips": "Wear respectful traditional attire. Mindful pacing recommended."
            })

    # Save destinations.json
    dest_list = list(cities.values())
    with open(MOCK_DIR / "destinations.json", "w", encoding="utf-8") as f:
        json.dump(dest_list, f, indent=2)
    print(f"Wrote {len(dest_list)} destinations to frontend/mock/destinations.json")

    # Save places.json
    with open(MOCK_DIR / "places.json", "w", encoding="utf-8") as f:
        json.dump(places, f, indent=2)
    print(f"Wrote {len(places)} places to frontend/mock/places.json")

if __name__ == "__main__":
    sync()
