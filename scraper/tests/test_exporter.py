"""
Unit tests for DataExporter.
Tests JSON export, CSV tabular export, missing fields analysis, and scraping reports.
"""

import json
import csv
from pathlib import Path
import pytest

from scraper.common.exporter import DataExporter
from scraper.models import (
    RawScrapedPlace,
    NormalizedPlace,
    PlaceCompleteness,
    ScrapingReport
)


@pytest.fixture
def sample_raw_place() -> RawScrapedPlace:
    return RawScrapedPlace(
        source_url="https://example.com/lingaraj",
        title="Lingaraj Temple",
        meta_description="Ancient temple in Bhubaneswar",
        meta_keywords=["temple", "shiva"],
        og_image="https://example.com/img.jpg",
        state="Odisha",
        city="Bhubaneswar",
        place_name_raw="Lingaraj Temple",
        headings=[{"tag": "h2", "text": "History"}],
        paragraphs=["Sample narrative paragraph."],
        timing_raw="06:00 AM - 09:00 PM",
        celebrations_raw="Mahashivaratri",
        transit_raw={"airport": "BBI Airport", "railway": "BBS Station"},
        nearby_attractions=["Mukteswara Temple"],
        image_urls=["https://example.com/img.jpg"],
        extracted_tags=["heritage"],
        scraped_at_utc="2026-08-26T12:00:00Z"
    )


@pytest.fixture
def sample_normalized_place() -> NormalizedPlace:
    return NormalizedPlace(
        id="lingaraj-temple",
        name="Lingaraj Temple",
        city="Bhubaneswar",
        state="Odisha",
        category="Temple & Sacred Sanctum",
        sub_category="Shiva Temple & Sanctum",
        short_description="An ancient temple in Bhubaneswar.",
        full_description="Detailed historical description of the sanctum.",
        cultural_significance="Epicenter of Shaivism in Odisha.",
        historical_period="11th Century CE • Somavamsi Dynasty",
        opening_hours="06:00 AM - 09:00 PM",
        entry_fee="Free entry",
        best_time_of_day="Early Morning",
        recommended_duration="1.5 to 2 Hours",
        accessibility_notes="Footwear removal mandatory.",
        festivals=["Mahashivaratri", "Ashokashtami"],
        nearest_transit={
            "nearest_airport": "Biju Patnaik International Airport (BBI)",
            "nearest_railway": "Bhubaneswar Railway Station (BBS)"
        },
        image_urls=["https://example.com/lingaraj.jpg"],
        source_url="https://example.com/lingaraj",
        scraped_at_utc="2026-08-26T12:00:00Z"
    )


def test_export_raw_json(tmp_path: Path, sample_raw_place: RawScrapedPlace):
    exporter = DataExporter(tmp_path)
    file_path = exporter.export_raw_json([sample_raw_place])

    assert file_path.exists()
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["place_name_raw"] == "Lingaraj Temple"


def test_export_normalized_json(tmp_path: Path, sample_normalized_place: NormalizedPlace):
    exporter = DataExporter(tmp_path)
    file_path = exporter.export_normalized_json([sample_normalized_place])

    assert file_path.exists()
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["id"] == "lingaraj-temple"
    assert data[0]["category"] == "Temple & Sacred Sanctum"


def test_export_csv(tmp_path: Path, sample_normalized_place: NormalizedPlace):
    exporter = DataExporter(tmp_path)
    file_path = exporter.export_csv([sample_normalized_place])

    assert file_path.exists()
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["name"] == "Lingaraj Temple"
    assert rows[0]["category"] == "Temple & Sacred Sanctum"
    assert "Mahashivaratri" in rows[0]["festivals"]
    assert "BBI" in rows[0]["nearest_airport"]


def test_export_missing_fields_report(tmp_path: Path):
    exporter = DataExporter(tmp_path)
    completeness = [
        PlaceCompleteness("lingaraj-temple", "Lingaraj Temple", 18, 18, [], 100.0),
        PlaceCompleteness("caves", "Udayagiri Caves", 18, 16, ["festivals", "entry_fee"], 88.89)
    ]
    json_path, md_path = exporter.export_missing_fields_report(completeness)

    assert json_path.exists()
    assert md_path.exists()

    with open(json_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    assert len(json_data) == 2

    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()
    assert "DHRUVA Cultural Data Completeness" in md_content
    assert "Lingaraj Temple" in md_content
    assert "Udayagiri Caves" in md_content
    assert "88.89%" in md_content


def test_export_scrape_report(tmp_path: Path):
    exporter = DataExporter(tmp_path)
    report = ScrapingReport(
        target_source="Incredible India Tourism Portal",
        start_url="https://example.com/bhubaneswar",
        city="Bhubaneswar",
        state="Odisha",
        total_pages_discovered=5,
        total_pages_crawled=5,
        total_places_normalized=5,
        errors_count=0,
        error_details=[],
        start_time_utc="2026-08-26T12:00:00Z",
        end_time_utc="2026-08-26T12:01:00Z",
        duration_seconds=60.0,
        average_completeness=95.0,
        field_completeness_summary={"name": 100.0},
        completeness_per_place=[]
    )
    file_path = exporter.export_scrape_report(report)

    assert file_path.exists()
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["city"] == "Bhubaneswar"
    assert data["total_places_normalized"] == 5
