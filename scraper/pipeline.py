"""
DHRUVA End-to-End Automated Pipeline Orchestrator.

Integrates:
1. Live Scraping (Incredible India Tourism Portal)
2. LLM Verification & Google Search Grounding (Gemini 2.0 / 1.5 Flash + Heuristic Fallback)
3. Automated Spatial Geocoding (OpenStreetMap Nominatim + Local Disk Cache)
4. Master Verified Dataset Generation
5. Automated Relational Table Dissection (6 Normalized Entities)
6. SQLite Database Schema Creation (dhruva.db) & Processed CSV Exports
"""

from __future__ import annotations
import argparse
import csv
import json
import logging
import sqlite3
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from scraper.common.config import ScraperConfig
from scraper.common.geocoder import DhruvaGeocoder
from scraper.common.verifier import PlaceVerifier, VerifiedPlaceData
from scraper.incredible_india.scraper import IncredibleIndiaScraper

logger = logging.getLogger("dhruva.pipeline")


class DhruvaEndToEndPipeline:
    """
    Automated pipeline orchestrating Scraping -> LLM Verification -> Geocoding -> Table Dissection -> DB Population.
    """

    DEFAULT_FESTIVALS = [
        {"name": "Rath Yatra (Grand Chariot Festival)", "start_date": "2026-06-27", "end_date": "2026-07-06", "city": "Puri", "description": "World-renowned annual procession of Lord Jagannath, Balabhadra, and Subhadra in majestic chariots along the Bada Danda in Puri."},
        {"name": "Ashokashtami & Rukuna Ratha Yatra", "start_date": "2026-04-14", "end_date": "2026-04-18", "city": "Bhubaneswar", "description": "Car festival of Lord Lingaraj celebrated in Bhubaneswar's ancient Ekamra Kshetra with ancient Kalinga rituals."},
        {"name": "Maha Shivaratri & Jagara", "start_date": "2026-02-15", "end_date": "2026-02-16", "city": "Bhubaneswar", "description": "Grand nocturnal vigil at Lingaraj Temple and Dhabaleswar Temple culminating with the Mahadipa offering at midnight."},
        {"name": "Chandan Yatra", "start_date": "2026-05-09", "end_date": "2026-05-29", "city": "Puri", "description": "21-day summer water festival celebrated with divine boat rides in the Narendra Tirtha lake in Puri."},
        {"name": "Durga Puja & Silver Filigree (Chandi Medha)", "start_date": "2026-10-18", "end_date": "2026-10-23", "city": "Cuttack", "description": "Historic autumnal celebration in Cuttack featuring exquisite Tarakasi (silver filigree) tableaus and divine energy."},
        {"name": "Bali Yatra (Maritime Trade Festival)", "start_date": "2026-11-23", "end_date": "2026-11-30", "city": "Cuttack", "description": "Asia's largest open-air trade fair on the banks of Mahanadi commemorating ancient maritime trade voyages to Bali and Java."},
        {"name": "Konark Dance & Music Festival", "start_date": "2026-12-01", "end_date": "2026-12-05", "city": "Puri", "description": "Spectacular classical Indian dance performances set against the illuminated backdrop of the UNESCO World Heritage Sun Temple."}
    ]

    DEFAULT_USERS_INPUT = [
        {"id": 1, "gps_location": "20.2961,85.8245", "start_date": "2026-10-15", "start_time": "08:00 AM", "end_time": "08:00 PM", "age": 58},
        {"id": 2, "gps_location": "19.8135,85.8312", "start_date": "2026-11-01", "start_time": "07:30 AM", "end_time": "07:00 PM", "age": 62},
        {"id": 3, "gps_location": "20.4625,85.8830", "start_date": "2026-11-24", "start_time": "09:00 AM", "end_time": "09:30 PM", "age": 45}
    ]

    def __init__(
        self,
        config: Optional[ScraperConfig] = None,
        gemini_api_key: Optional[str] = None,
        db_path: Path = Path("backend/database/dhruva.db"),
        schema_path: Path = Path("backend/database/schema.sql"),
        processed_dir: Path = Path("data/processed")
    ):
        self.config = config or ScraperConfig()
        self.db_path = db_path
        self.schema_path = schema_path
        self.processed_dir = processed_dir
        self.geocoder = DhruvaGeocoder()
        self.verifier = PlaceVerifier(gemini_api_key=gemini_api_key)

    def run_pipeline(
        self,
        cities: List[str],
        state: str = "odisha",
        max_pages: int = 15,
        from_scraped_file: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Execute the full pipeline end-to-end.
        """
        start_time = time.time()
        print("\n" + "=" * 70)
        print("  DHRUVA AUTOMATED DATA PIPELINE & DATABASE GENERATOR")
        print("=" * 70)

        # -------------------------------------------------------------
        # STAGE 1: Data Ingestion (Scraping or Loading Existing Scraped)
        # -------------------------------------------------------------
        print(f"\n[STAGE 1/6] Ingesting scraped destination data for {', '.join(cities).title()}...")
        raw_places_dicts: List[Dict[str, Any]] = []

        if from_scraped_file and from_scraped_file.exists():
            print(f"-> Ingesting from existing scraped dataset: {from_scraped_file}")
            with open(from_scraped_file, "r", encoding="utf-8") as f:
                raw_places_dicts = json.load(f)
        else:
            scraper = IncredibleIndiaScraper(self.config)
            destinations = [{"city": c, "state": state} for c in cities]
            report = scraper.scrape_multiple_destinations(destinations, max_pages_per_destination=max_pages)
            normalized_json_path = self.config.output_dir / "normalized_places.json"
            if normalized_json_path.exists():
                with open(normalized_json_path, "r", encoding="utf-8") as f:
                    raw_places_dicts = json.load(f)

        print(f"-> Total ingested candidate places: {len(raw_places_dicts)}")

        # -------------------------------------------------------------
        # STAGE 2: Verification, Fact-Checking & LLM Grounding
        # -------------------------------------------------------------
        print(f"\n[STAGE 2/6] Verifying and fact-checking places (Gemini Grounding / Heuristic)...")
        verified_places: List[VerifiedPlaceData] = []
        rejected_count = 0

        for place in raw_places_dicts:
            res = self.verifier.verify_place(place)
            if res and res.is_valid:
                verified_places.append(res)
            else:
                rejected_count += 1
                logger.info(f"Filtered out invalid/corrupted entry: {place.get('id')}")

        print(f"-> Verified: {len(verified_places)} valid places | Excluded: {rejected_count} corrupted/invalid")

        # -------------------------------------------------------------
        # STAGE 3: Automated Spatial Geocoding (OpenStreetMap / Cache)
        # -------------------------------------------------------------
        print(f"\n[STAGE 3/6] Automatically resolving spatial GPS coordinates (DhruvaGeocoder)...")
        for p in verified_places:
            lat, lon = self.geocoder.get_coordinates(p.name, p.city, p.state)
            p.lat = lat
            p.long = lon

        # -------------------------------------------------------------
        # STAGE 4: Master Dataset Generation
        # -------------------------------------------------------------
        print(f"\n[STAGE 4/6] Exporting Master Verified Dataset...")
        master_json_path = self.config.output_dir / "verified_places.json"
        master_csv_path = self.config.output_dir / "verified_places.csv"
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        verified_dicts = [p.to_dict() for p in verified_places]
        with open(master_json_path, "w", encoding="utf-8") as f:
            json.dump(verified_dicts, f, indent=2, ensure_ascii=False)

        if verified_dicts:
            fieldnames = list(verified_dicts[0].keys())
            with open(master_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(verified_dicts)

        print(f"-> Saved master verified dataset to {master_json_path}")

        # -------------------------------------------------------------
        # STAGE 5: Automated Table Dissection (6 Relational Entities)
        # -------------------------------------------------------------
        print(f"\n[STAGE 5/6] Dissecting master dataset into 6 Relational Tables...")

        # 1. CITIES table
        unique_cities = list({p.city.title() for p in verified_places})
        cities_rows = []
        city_name_to_id = {}
        for idx, cname in enumerate(sorted(unique_cities), start=1):
            city_lat, city_lon = self.geocoder.get_coordinates(cname, cname, state.title())
            city_name_to_id[cname.lower()] = idx
            cities_rows.append({
                "id": idx,
                "name": cname,
                "state": state.title(),
                "lat": city_lat,
                "long": city_lon
            })

        # 2. PLACES table
        places_rows = []
        opening_hours_rows = []
        min_interest_rows = []
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        for idx, p in enumerate(verified_places, start=1):
            cid = city_name_to_id.get(p.city.lower(), 1)
            places_rows.append({
                "id": idx,
                "name": p.name,
                "duration": p.duration,
                "duration_label": p.duration_label,
                "popularity": p.popularity,
                "lat": p.lat,
                "long": p.long,
                "risk": p.risk,
                "city_id": cid,
                "category": p.category,
                "sub_category": p.sub_category,
                "description": p.short_description,
                "image_url": p.image_url,
                "entry_fee": p.entry_fee
            })

            # 3. OPENING_HOURS table
            for day in days_of_week:
                opening_hours_rows.append({
                    "opens_at": p.opens_at,
                    "closes_at": p.closes_at,
                    "place_id": idx,
                    "day_of_week": day
                })

            # 4. MIN_INTEREST table
            min_interest_rows.append({
                "place_id": idx,
                "architecture": p.architecture,
                "history": p.history,
                "spiritual": p.spiritual,
                "nature": p.nature,
                "culture": p.culture
            })

        # 5. FESTIVALS table
        festivals_rows = []
        for idx, f in enumerate(self.DEFAULT_FESTIVALS, start=1):
            cid = city_name_to_id.get(f["city"].lower(), 1)
            festivals_rows.append({
                "id": idx,
                "name": f["name"],
                "start_date": f["start_date"],
                "end_date": f["end_date"],
                "city_id": cid,
                "description": f["description"]
            })

        # 6. USERS_INPUT table
        users_input_rows = self.DEFAULT_USERS_INPUT

        print(f"   * CITIES: {len(cities_rows)} records")
        print(f"   * PLACES: {len(places_rows)} records")
        print(f"   * OPENING_HOURS: {len(opening_hours_rows)} records")
        print(f"   * MIN_INTEREST: {len(min_interest_rows)} records")
        print(f"   * FESTIVALS: {len(festivals_rows)} records")
        print(f"   * USERS_INPUT: {len(users_input_rows)} records")

        # -------------------------------------------------------------
        # STAGE 6: Database Schema Execution & CSV Export
        # -------------------------------------------------------------
        print(f"\n[STAGE 6/6] Provisioning SQLite Database & Exporting Relational CSVs...")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Run DDL schema
        with open(self.schema_path, "r", encoding="utf-8") as sf:
            cursor.executescript(sf.read())

        # Populate tables
        cursor.executemany("INSERT INTO CITIES VALUES (:id, :name, :state, :lat, :long)", cities_rows)
        cursor.executemany("""
            INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee)
            VALUES (:id, :name, :duration, :duration_label, :popularity, :lat, :long, :risk, :city_id, :category, :sub_category, :description, :image_url, :entry_fee)
        """, places_rows)
        cursor.executemany("INSERT INTO OPENING_HOURS (opens_at, closes_at, place_id, day_of_week) VALUES (:opens_at, :closes_at, :place_id, :day_of_week)", opening_hours_rows)
        cursor.executemany("INSERT INTO MIN_INTEREST (place_id, architecture, history, spiritual, nature, culture) VALUES (:place_id, :architecture, :history, :spiritual, :nature, :culture)", min_interest_rows)
        cursor.executemany("INSERT INTO FESTIVALS VALUES (:id, :name, :start_date, :end_date, :city_id, :description)", festivals_rows)
        cursor.executemany("INSERT INTO USERS_INPUT (id, gps_location, start_date, start_time, end_time, age) VALUES (:id, :gps_location, :start_date, :start_time, :end_time, :age)", users_input_rows)

        conn.commit()
        conn.close()
        print(f"[OK] SQLite database successfully written to: {self.db_path.resolve()}")

        # Export relational CSVs
        def write_relational_csv(filename: str, fieldnames: List[str], rows: List[Dict[str, Any]]) -> None:
            fpath = self.processed_dir / filename
            with open(fpath, "w", newline="", encoding="utf-8") as cf:
                writer = csv.DictWriter(cf, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            print(f"[OK] Exported CSV: {fpath} ({len(rows)} records)")

        write_relational_csv("cities.csv", ["id", "name", "state", "lat", "long"], cities_rows)
        write_relational_csv("places.csv", ["id", "name", "duration", "popularity", "lat", "long", "risk", "city_id", "category", "sub_category", "duration_label", "image_url", "entry_fee", "description"], places_rows)
        opening_hours_csv = [{"id": i+1, **r} for i, r in enumerate(opening_hours_rows)]
        write_relational_csv("opening_hours.csv", ["id", "opens_at", "closes_at", "place_id", "day_of_week"], opening_hours_csv)
        min_interest_csv = [{"id": i+1, **r} for i, r in enumerate(min_interest_rows)]
        write_relational_csv("min_interest.csv", ["id", "place_id", "architecture", "history", "spiritual", "nature", "culture"], min_interest_csv)
        write_relational_csv("festivals.csv", ["id", "name", "start_date", "end_date", "city_id", "description"], festivals_rows)
        write_relational_csv("users_input.csv", ["id", "gps_location", "start_date", "start_time", "end_time", "age"], users_input_rows)

        duration = round(time.time() - start_time, 2)
        print("\n" + "=" * 70)
        print(f"PIPELINE COMPLETED SUCCESSFULLY IN {duration} SECONDS")
        print(f"Database: {self.db_path.resolve()}")
        print(f"Processed CSV Directory: {self.processed_dir.resolve()}")
        print("=" * 70 + "\n")

        return {
            "duration": duration,
            "places_count": len(places_rows),
            "cities_count": len(cities_rows),
            "db_path": str(self.db_path),
            "processed_dir": str(self.processed_dir)
        }


def main():
    parser = argparse.ArgumentParser(description="DHRUVA Automated Data Pipeline & Database Generator")
    parser.add_argument("--cities", type=str, default="bhubaneswar,puri,cuttack", help="Comma-separated list of target cities")
    parser.add_argument("--state", type=str, default="odisha", help="Target state name")
    parser.add_argument("--max-pages", type=int, default=15, help="Max pages to crawl per destination")
    parser.add_argument("--from-file", type=str, default="data/scraped/normalized_places.json", help="Path to existing scraped JSON to run verification & DB generation directly")
    parser.add_argument("--gemini-key", type=str, default=None, help="Google Gemini API key for search grounding verification")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s]: %(message)s")

    city_list = [c.strip() for c in args.cities.split(",") if c.strip()]
    input_file = Path(args.from_file) if args.from_file else None

    pipeline = DhruvaEndToEndPipeline(gemini_api_key=args.gemini_key)
    pipeline.run_pipeline(
        cities=city_list,
        state=args.state,
        max_pages=args.max_pages,
        from_scraped_file=input_file
    )


if __name__ == "__main__":
    main()
