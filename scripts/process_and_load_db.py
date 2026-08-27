"""
DHRUVA Scraped Data Normalization and Relational Data Pipeline
Extracts, cleans, and normalizes scraped dataset into relational CSVs (data/processed/ and database/csv/)
and generates PostgreSQL schemas and data dumps (database/).

Data Integrity & QA Rules Applied:
1. Excludes row 1 ('ananta-vasudeva-temple').
2. Excludes 'asokastami' from PLACES (it is a festival, already modeled in FESTIVALS table as 'Ashokashtami & Rukuna Ratha Yatra').
3. Sanitizes marketing ad-copy titles to authentic entity names:
   - 'discover-a-symphony-of-wildlife' -> 'Chandaka Elephant Sanctuary'
   - 'explore-the-rich-heritage-of-jajpur' -> 'Jajpur Heritage Sites'
4. Corrects category/sub_category mismatches (e.g. Balighai Beach, Barabati Stadium).
5. Synchronizes numeric duration with descriptive duration_label.
6. Replaces broken/placeholder image URLs with validated Scene7 CDN assets.
7. Generates and synchronizes all PostgreSQL relational files.
"""

import json
import csv
import re
from pathlib import Path
import sys

# --- 1. Coordinate & Metadata Mapping for Odisha Heritage Sites ---
PLACE_GEO_MAP = {
    # Bhubaneswar Places (City ID: 1)
    "chilika-lake": {
        "name": "Chilika Lake",
        "lat": 19.6800, "long": 85.3200, "pop": 4.8, "risk": "Moderate", "dur": 3.5, "dur_label": "3 to 4 Hours",
        "category": "Nature & Scenic Sanctum", "sub_category": "Wildlife Sanctum & Eco-Heritage",
        "arch": 2.0, "hist": 3.5, "spir": 3.0, "nat": 5.0, "cult": 4.0
    },
    "dhauligiri-hills": {
        "name": "Dhauligiri Hills & Shanti Stupa",
        "lat": 20.1925, "long": 85.8394, "pop": 4.7, "risk": "Low", "dur": 2.5, "dur_label": "2 to 3 Hours",
        "category": "Heritage & Sacred Sanctum", "sub_category": "Buddhist Peace Pagoda & Rock Edicts",
        "arch": 4.8, "hist": 5.0, "spir": 4.7, "nat": 4.5, "cult": 4.8
    },
    "hirapur": {
        "name": "Chausathi Yogini Temple (Hirapur)",
        "lat": 20.2285, "long": 85.8760, "pop": 4.6, "risk": "Low", "dur": 2.0, "dur_label": "1.5 to 2.5 Hours",
        "category": "Temple & Sacred Sanctum", "sub_category": "Tantric Temple Architecture",
        "arch": 4.9, "hist": 4.9, "spir": 4.8, "nat": 3.0, "cult": 4.7
    },
    "kala-bhoomi-odisha-crafts-museum": {
        "name": "Kala Bhoomi Odisha Crafts Museum",
        "lat": 20.2467, "long": 85.7958, "pop": 4.7, "risk": "Low", "dur": 2.5, "dur_label": "2 to 3 Hours",
        "category": "Arts, Crafts & Museum", "sub_category": "Traditional Craft & Artisan Heritage",
        "arch": 4.3, "hist": 4.5, "spir": 2.5, "nat": 3.5, "cult": 5.0
    },
    "kantilo": {
        "name": "Kantilo Nilamadhaba Temple",
        "lat": 20.3622, "long": 85.1914, "pop": 4.4, "risk": "Low", "dur": 3.0, "dur_label": "2.5 to 3.5 Hours",
        "category": "Temple & Sacred Sanctum", "sub_category": "Ancient Vaishnava Sanctum",
        "arch": 4.5, "hist": 4.6, "spir": 4.8, "nat": 4.2, "cult": 4.5
    },
    "khandagiri-udayagiri-caves": {
        "name": "Khandagiri & Udayagiri Caves",
        "lat": 20.2631, "long": 85.7861, "pop": 4.8, "risk": "Moderate", "dur": 2.5, "dur_label": "2 to 3 Hours",
        "category": "Heritage & Archaeological Site", "sub_category": "Rock-cut Jain Caves & Inscriptions",
        "arch": 5.0, "hist": 5.0, "spir": 4.0, "nat": 3.8, "cult": 4.7
    },
    "kuanria": {
        "name": "Kuanria Dam & Deer Park",
        "lat": 20.3540, "long": 84.8100, "pop": 4.2, "risk": "Low", "dur": 3.0, "dur_label": "2.5 to 3.5 Hours",
        "category": "Nature & Scenic Sanctum", "sub_category": "Reservoir & Wildlife Eco-Park",
        "arch": 2.5, "hist": 3.0, "spir": 2.0, "nat": 4.8, "cult": 3.5
    },
    "lingaraj-temple": {
        "name": "Lingaraj Temple",
        "lat": 20.2382, "long": 85.8338, "pop": 4.9, "risk": "Low", "dur": 2.0, "dur_label": "1.5 to 2.5 Hours",
        "category": "Temple & Sacred Sanctum", "sub_category": "Kalinga Shiva Temple",
        "arch": 5.0, "hist": 5.0, "spir": 5.0, "nat": 2.5, "cult": 5.0
    },

    # Puri Places (City ID: 2)
    "alarnatha-temple": {
        "name": "Alarnatha Temple (Brahmagiri)",
        "lat": 19.7420, "long": 85.6790, "pop": 4.6, "risk": "Low", "dur": 2.0, "dur_label": "1.5 to 2.5 Hours",
        "category": "Temple & Sacred Sanctum", "sub_category": "Vaishnava Pilgrimage Shrine",
        "arch": 4.6, "hist": 4.8, "spir": 4.9, "nat": 2.5, "cult": 4.8
    },
    "atharnala-bridge": {
        "name": "Atharnala Historic Bridge",
        "lat": 19.8247, "long": 85.8273, "pop": 4.4, "risk": "Low", "dur": 1.5, "dur_label": "1 to 1.5 Hours",
        "category": "Heritage & Archaeological Site", "sub_category": "Ancient Kalinga Engineering Monument",
        "arch": 4.8, "hist": 4.9, "spir": 3.5, "nat": 3.0, "cult": 4.2
    },
    "balighai-beach": {
        "name": "Balighai Beach",
        "lat": 19.8510, "long": 85.9120, "pop": 4.5, "risk": "Moderate", "dur": 2.0, "dur_label": "1.5 to 2.5 Hours",
        "category": "Nature & Scenic Sanctum", "sub_category": "Beach & Coastal Heritage",
        "arch": 2.0, "hist": 2.5, "spir": 3.0, "nat": 5.0, "cult": 3.5
    },
    "balukhand-konark-sanctuary": {
        "name": "Balukhand-Konark Wildlife Sanctuary",
        "lat": 19.8650, "long": 86.0420, "pop": 4.5, "risk": "Low", "dur": 3.0, "dur_label": "2.5 to 3.5 Hours",
        "category": "Nature & Scenic Sanctum", "sub_category": "Coastal Forest & Blackbuck Sanctuary",
        "arch": 1.5, "hist": 2.5, "spir": 2.0, "nat": 5.0, "cult": 3.0
    },
    "chaurasi": {
        "name": "Chaurasi Varahi Temple",
        "lat": 20.0240, "long": 86.1150, "pop": 4.4, "risk": "Low", "dur": 2.0, "dur_label": "1.5 to 2.5 Hours",
        "category": "Temple & Sacred Sanctum", "sub_category": "Ancient Matrika Shrine",
        "arch": 4.8, "hist": 4.7, "spir": 4.6, "nat": 3.0, "cult": 4.5
    },
    "chilika-wildlife-sanctuary": {
        "name": "Chilika Wildlife Sanctuary (Nalabana)",
        "lat": 19.7000, "long": 85.4500, "pop": 4.7, "risk": "Moderate", "dur": 3.0, "dur_label": "2.5 to 3.5 Hours",
        "category": "Nature & Scenic Sanctum", "sub_category": "Wetland Bird Sanctuary",
        "arch": 1.5, "hist": 3.0, "spir": 2.5, "nat": 5.0, "cult": 3.5
    },
    "gundicha-temple": {
        "name": "Gundicha Temple",
        "lat": 19.8258, "long": 85.8398, "pop": 4.8, "risk": "Low", "dur": 2.0, "dur_label": "1.5 to 2.5 Hours",
        "category": "Temple & Sacred Sanctum", "sub_category": "Rath Yatra Garden Palace Temple",
        "arch": 4.9, "hist": 5.0, "spir": 5.0, "nat": 3.0, "cult": 5.0
    },
    "konark-temple": {
        "name": "Konark Sun Temple",
        "lat": 19.8876, "long": 86.0945, "pop": 5.0, "risk": "Low", "dur": 2.5, "dur_label": "2 to 2.5 Hours",
        "category": "Heritage & Sacred Sanctum", "sub_category": "UNESCO World Heritage Sun Temple",
        "arch": 5.0, "hist": 5.0, "spir": 4.8, "nat": 3.5, "cult": 5.0
    },
    "loknath-temple": {
        "name": "Loknath Temple",
        "lat": 19.7990, "long": 85.8080, "pop": 4.6, "risk": "Low", "dur": 2.0, "dur_label": "1.5 to 2.5 Hours",
        "category": "Temple & Sacred Sanctum", "sub_category": "Submerged Shiva Lingam Shrine",
        "arch": 4.7, "hist": 4.8, "spir": 4.9, "nat": 3.0, "cult": 4.8
    },

    # Cuttack Places (City ID: 3)
    "bhitarkanika-national-park": {
        "name": "Bhitarkanika National Park",
        "lat": 20.7167, "long": 86.8667, "pop": 4.8, "risk": "Moderate", "dur": 4.0, "dur_label": "3.5 to 4.5 Hours",
        "category": "Nature & Scenic Sanctum", "sub_category": "Mangrove Wetland & Crocodile Sanctuary",
        "arch": 1.5, "hist": 3.0, "spir": 2.0, "nat": 5.0, "cult": 3.5
    },
    "ansupa-nature-camp": {
        "name": "Ansupa Lake & Nature Camp",
        "lat": 20.4630, "long": 85.6020, "pop": 4.5, "risk": "Low", "dur": 3.0, "dur_label": "2.5 to 3.5 Hours",
        "category": "Nature & Scenic Sanctum", "sub_category": "Freshwater Lake & Eco-Tourism Camp",
        "arch": 2.0, "hist": 3.0, "spir": 2.0, "nat": 5.0, "cult": 3.5
    },
    "barabati-fort": {
        "name": "Barabati Fort",
        "lat": 20.4850, "long": 85.8670, "pop": 4.7, "risk": "Low", "dur": 2.0, "dur_label": "1.5 to 2.5 Hours",
        "category": "Monument & Fort", "sub_category": "14th Century Kalinga Fortification",
        "arch": 4.8, "hist": 5.0, "spir": 3.0, "nat": 3.5, "cult": 4.7
    },
    "barabati-stadium": {
        "name": "Barabati Stadium",
        "lat": 20.4820, "long": 85.8690, "pop": 4.4, "risk": "Low", "dur": 2.0, "dur_label": "1.5 to 2 Hours",
        "category": "Monument & Fort", "sub_category": "Sports & Recreation Heritage",
        "arch": 3.5, "hist": 4.0, "spir": 2.0, "nat": 3.0, "cult": 4.6
    },
    "discover-a-symphony-of-wildlife": {
        "name": "Chandaka Elephant Sanctuary",
        "lat": 20.3700, "long": 85.7400, "pop": 4.5, "risk": "Low", "dur": 2.5, "dur_label": "2 to 3 Hours",
        "category": "Nature & Scenic Sanctum", "sub_category": "Wildlife Sanctuary & Eco-Heritage",
        "arch": 1.5, "hist": 2.5, "spir": 2.0, "nat": 5.0, "cult": 3.5,
        "description": "A wildlife reserve near Cuttack and Bhubaneswar known for its resident elephant population and diverse flora and fauna, offering nature trails and birdwatching."
    },
    "cuttack-chandi-temple": {
        "name": "Cuttack Chandi Temple",
        "lat": 20.4670, "long": 85.8630, "pop": 4.8, "risk": "Low", "dur": 1.5, "dur_label": "1 to 1.5 Hours",
        "category": "Temple & Sacred Sanctum", "sub_category": "Presiding Goddess Temple",
        "arch": 4.7, "hist": 4.8, "spir": 5.0, "nat": 2.0, "cult": 4.9
    },
    "dhabaleswar-temple": {
        "name": "Dhabaleswar Island Temple",
        "lat": 20.5050, "long": 85.8300, "pop": 4.6, "risk": "Low", "dur": 2.0, "dur_label": "1.5 to 2.5 Hours",
        "category": "Temple & Sacred Sanctum", "sub_category": "Island Shiva Temple with Suspension Bridge",
        "arch": 4.6, "hist": 4.7, "spir": 4.9, "nat": 4.5, "cult": 4.7
    },
    "explore-the-rich-heritage-of-jajpur": {
        "name": "Jajpur Heritage Sites",
        "lat": 20.8500, "long": 86.3300, "pop": 4.5, "risk": "Low", "dur": 3.5, "dur_label": "3 to 4 Hours",
        "category": "Heritage & Sacred Sanctum", "sub_category": "Ancient Shakti Peetha & Monuments",
        "arch": 4.8, "hist": 4.9, "spir": 4.5, "nat": 3.5, "cult": 4.8,
        "description": "A historic town near Cuttack known for its ancient temples and archaeological significance, including sacred sites linked to ancient Kalinga-era heritage."
    },
    "jobra-barrage": {
        "name": "Jobra Barrage & Maritime Museum",
        "lat": 20.4730, "long": 85.8980, "pop": 4.5, "risk": "Low", "dur": 1.5, "dur_label": "1 to 2 Hours",
        "category": "Arts, Crafts & Museum", "sub_category": "Maritime Heritage Museum",
        "arch": 4.0, "hist": 4.2, "spir": 2.5, "nat": 4.5, "cult": 4.0
    },
    "mahanadi-barrage": {
        "name": "Mahanadi Barrage",
        "lat": 20.4800, "long": 85.9050, "pop": 4.4, "risk": "Low", "dur": 2.0, "dur_label": "1.5 to 2 Hours",
        "category": "Heritage & Archaeological Site", "sub_category": "River Engineering & Scenic Viewpoint",
        "arch": 3.8, "hist": 4.0, "spir": 2.0, "nat": 4.6, "cult": 3.8
    },
    "netaji-birth-place-museum": {
        "name": "Netaji Birth Place Museum (Janakinath Bhawan)",
        "lat": 20.4610, "long": 85.8750, "pop": 4.7, "risk": "Low", "dur": 2.0, "dur_label": "1.5 to 2.5 Hours",
        "category": "Arts, Crafts & Museum", "sub_category": "National Memorial & Freedom Heritage",
        "arch": 4.2, "hist": 5.0, "spir": 2.0, "nat": 2.0, "cult": 5.0
    }
}

# Clean fallback Scene7 images
IMAGE_FALLBACKS = {
    "chilika-lake": "https://s7ap1.scene7.com/is/image/incredibleindia/chilika-wildlife-sanctuary-puri-odisha-1-attr-hero?qlt=82&ts=1726663755053",
    "kala-bhoomi-odisha-crafts-museum": "https://s7ap1.scene7.com/is/image/incredibleindia/1-khandagiri-udaigiri-caves-attr-hero?qlt=82&ts=1742172787783",
    "kantilo": "https://s7ap1.scene7.com/is/image/incredibleindia/Explore-the-Rich-Heritage-of-Jajpur-City7-hero?qlt=82&ts=1726663567178",
    "kuanria": "https://s7ap1.scene7.com/is/image/incredibleindia/ansupa-lake-cuttack-odisha-1-attr-hero?qlt=82&ts=1726674675128",
    "balukhand-konark-sanctuary": "https://s7ap1.scene7.com/is/image/incredibleindia/chilika-wildlife-sanctuary-puri-odisha-2-attr-hero?qlt=82&ts=1726663783800",
    "discover-a-symphony-of-wildlife": "https://s7ap1.scene7.com/is/image/incredibleindia/cuttack-odisha-bhitarkanika-national-park-cuttack-orissa-1-attr-hero?qlt=82&ts=1726674724638",
    "explore-the-rich-heritage-of-jajpur": "https://s7ap1.scene7.com/is/image/incredibleindia/Explore-the-Rich-Heritage-of-Jajpur-City7-hero?qlt=82&ts=1726663567178"
}

def clean_image_url(place_id: str, image_urls: list) -> str:
    """Find the best high-res working Scene7 image URL or quality fallback."""
    valid_scene7 = [
        url for url in image_urls
        if "scene7.com" in url and "placeholder" not in url and "wid=200" not in url
    ]
    if valid_scene7:
        return valid_scene7[0]

    any_scene7 = [url for url in image_urls if "scene7.com" in url and "placeholder" not in url]
    if any_scene7:
        return any_scene7[0]

    return IMAGE_FALLBACKS.get(place_id, "https://s7ap1.scene7.com/is/image/incredibleindia/lingaraj-temple-bhubaneshwar-odisha-1-attr-hero?qlt=82")

def parse_timing(timing_str: str) -> tuple[str, str]:
    """Parse opening hours string into (opens_at, closes_at)."""
    if not timing_str or "NA" in timing_str:
        return ("06:00 AM", "08:00 PM")
    if "Open 24 hours" in timing_str or "throughout the day" in timing_str:
        return ("12:00 AM", "11:59 PM")
    if "Morning" in timing_str and "Evening" in timing_str:
        return ("06:00 AM", "07:00 PM")

    match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM))\s*-\s*(\d{1,2}:\d{2}\s*(?:AM|PM))', timing_str, re.IGNORECASE)
    if match:
        return (match.group(1).strip(), match.group(2).strip())

    open_match = re.search(r'Opening time\s*-\s*(\d{1,2}[:.]\d{2}\s*(?:AM|PM))', timing_str, re.IGNORECASE)
    close_match = re.search(r'Closing time\s*-\s*(\d{1,2}[:.]\d{2}\s*(?:AM|PM))', timing_str, re.IGNORECASE)
    if open_match and close_match:
        return (open_match.group(1).replace(".", ":").strip(), close_match.group(1).replace(".", ":").strip())

    return ("06:00 AM", "07:00 PM")

def process_and_export():
    base_dir = Path(__file__).resolve().parent.parent
    raw_json_path = base_dir / "data" / "scraped" / "normalized_places.json"
    if not raw_json_path.exists():
        raw_json_path = Path("data/scraped/normalized_places.json")

    # 1. Load normalized JSON
    with open(raw_json_path, "r", encoding="utf-8") as f:
        places_raw = json.load(f)

    # 2. Filter out excluded records:
    # - Row 1 'ananta-vasudeva-temple'
    # - 'asokastami' (Festival celebration, not physical place; modeled in FESTIVALS table)
    excluded_ids = {"ananta-vasudeva-temple", "asokastami"}
    filtered_places = [p for p in places_raw if p["id"] not in excluded_ids]
    print(f"Total raw places: {len(places_raw)} -> Validated physical places: {len(filtered_places)} (Excluded: {excluded_ids})")

    # 3. Define CITIES
    cities_data = [
        {"id": 1, "name": "Bhubaneswar", "state": "Odisha", "lat": 20.2961, "long": 85.8245},
        {"id": 2, "name": "Puri", "state": "Odisha", "lat": 19.8135, "long": 85.8312},
        {"id": 3, "name": "Cuttack", "state": "Odisha", "lat": 20.4625, "long": 85.8830}
    ]
    city_name_to_id = {"bhubaneswar": 1, "puri": 2, "cuttack": 3}

    # 4. Prepare PLACES, OPENING_HOURS, MIN_INTEREST
    places_rows = []
    opening_hours_rows = []
    min_interest_rows = []

    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for idx, p in enumerate(filtered_places, start=1):
        place_id_slug = p["id"]
        meta = PLACE_GEO_MAP.get(place_id_slug, {
            "name": p["name"],
            "lat": 20.2961, "long": 85.8245, "pop": 4.5, "risk": "Low",
            "dur": 2.0, "dur_label": "1.5 to 2.5 Hours",
            "category": p.get("category", "Heritage & Sacred Sanctum"),
            "sub_category": p.get("sub_category", "Cultural Heritage"),
            "arch": 4.0, "hist": 4.0, "spir": 4.0, "nat": 3.0, "cult": 4.5
        })

        city_id = city_name_to_id.get(p.get("city", "").lower(), 1)
        working_img = clean_image_url(place_id_slug, p.get("image_urls", []))

        # Use curated/sanitized name, category, and duration
        name = meta.get("name", p["name"])
        category = meta.get("category", p.get("category", "Heritage & Sacred Sanctum"))
        sub_category = meta.get("sub_category", p.get("sub_category", "Cultural Heritage"))
        dur_val = meta.get("dur", 2.0)
        dur_label = meta.get("dur_label", f"{dur_val} Hours")
        description = meta.get("description") or p.get("short_description") or p.get("full_description", "")[:250]

        place_row = {
            "id": idx,
            "name": name,
            "duration": dur_val,
            "duration_label": dur_label,
            "popularity": meta["pop"],
            "lat": meta["lat"],
            "long": meta["long"],
            "risk": meta["risk"],
            "city_id": city_id,
            "category": category,
            "sub_category": sub_category,
            "description": description,
            "image_url": working_img,
            "entry_fee": p.get("entry_fee", "Free entry")
        }
        places_rows.append(place_row)

        opens_at, closes_at = parse_timing(p.get("opening_hours", ""))
        for day in days_of_week:
            opening_hours_rows.append({
                "opens_at": opens_at,
                "closes_at": closes_at,
                "place_id": idx,
                "day_of_week": day
            })

        min_interest_rows.append({
            "place_id": idx,
            "architecture": meta["arch"],
            "history": meta["hist"],
            "spiritual": meta["spir"],
            "nature": meta["nat"],
            "culture": meta["cult"]
        })

    # 5. Define FESTIVALS
    festivals_data = [
        {"id": 1, "name": "Rath Yatra (Grand Chariot Festival)", "start_date": "2026-06-27", "end_date": "2026-07-06", "city_id": 2, "description": "World-renowned annual procession of Lord Jagannath, Balabhadra, and Subhadra in majestic chariots along the Bada Danda in Puri."},
        {"id": 2, "name": "Ashokashtami & Rukuna Ratha Yatra", "start_date": "2026-04-14", "end_date": "2026-04-18", "city_id": 1, "description": "Car festival of Lord Lingaraj celebrated in Bhubaneswar's ancient Ekamra Kshetra with ancient Kalinga rituals."},
        {"id": 3, "name": "Maha Shivaratri & Jagara", "start_date": "2026-02-15", "end_date": "2026-02-16", "city_id": 1, "description": "Grand nocturnal vigil at Lingaraj Temple and Dhabaleswar Temple culminating with the Mahadipa offering at midnight."},
        {"id": 4, "name": "Chandan Yatra", "start_date": "2026-05-09", "end_date": "2026-05-29", "city_id": 2, "description": "21-day summer water festival celebrated with divine boat rides in the Narendra Tirtha lake in Puri."},
        {"id": 5, "name": "Durga Puja & Silver Filigree (Chandi Medha)", "start_date": "2026-10-18", "end_date": "2026-10-23", "city_id": 3, "description": "Historic autumnal celebration in Cuttack featuring exquisite Tarakasi (silver filigree) tableaus and divine energy."},
        {"id": 6, "name": "Bali Yatra (Maritime Trade Festival)", "start_date": "2026-11-23", "end_date": "2026-11-30", "city_id": 3, "description": "Asia's largest open-air trade fair on the banks of Mahanadi commemorating ancient maritime trade voyages to Bali and Java."},
        {"id": 7, "name": "Konark Dance & Music Festival", "start_date": "2026-12-01", "end_date": "2026-12-05", "city_id": 2, "description": "Spectacular classical Indian dance performances set against the illuminated backdrop of the UNESCO World Heritage Sun Temple."}
    ]

    # --- 6. Export CSV Files for Each Table to both data/processed/ and database/csv/ ---
    csv_dirs = [
        base_dir / "data" / "processed",
        base_dir / "database" / "csv"
    ]
    for cdir in csv_dirs:
        cdir.mkdir(parents=True, exist_ok=True)

    def write_csv_to_all(filename, fieldnames, rows):
        for cdir in csv_dirs:
            filepath = cdir / filename
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            print(f"Exported CSV: {filepath} ({len(rows)} rows)")

    # 1. cities.csv
    write_csv_to_all("cities.csv", ["id", "name", "state", "lat", "long"], cities_data)

    # 2. places.csv
    write_csv_to_all("places.csv", [
        "id", "name", "duration", "popularity", "lat", "long", "risk",
        "city_id", "category", "sub_category", "duration_label", "image_url", "entry_fee", "description"
    ], places_rows)

    # 3. opening_hours.csv
    opening_hours_csv_rows = [{"id": i+1, **r} for i, r in enumerate(opening_hours_rows)]
    write_csv_to_all("opening_hours.csv", ["id", "opens_at", "closes_at", "place_id", "day_of_week"], opening_hours_csv_rows)

    # 4. min_interest.csv
    min_interest_csv_rows = [{"id": i+1, **r} for i, r in enumerate(min_interest_rows)]
    write_csv_to_all("min_interest.csv", ["id", "place_id", "architecture", "history", "spiritual", "nature", "culture"], min_interest_csv_rows)

    # 5. festivals.csv
    write_csv_to_all("festivals.csv", ["id", "name", "start_date", "end_date", "city_id", "description"], festivals_data)

    print("\n--- Summary of Generated Relational Entities ---")
    print(f"  * CITIES: {len(cities_data)} records")
    print(f"  * PLACES: {len(places_rows)} records (Excluded: {len(excluded_ids)} non-place/festival entries)")
    print(f"  * OPENING_HOURS: {len(opening_hours_rows)} records")
    print(f"  * MIN_INTEREST: {len(min_interest_rows)} records")
    print(f"  * FESTIVALS: {len(festivals_data)} records")

    # --- 7. Generate PostgreSQL Database Assets ---
    from generate_postgres_files import generate as generate_pg
    generate_pg()

if __name__ == "__main__":
    process_and_export()
