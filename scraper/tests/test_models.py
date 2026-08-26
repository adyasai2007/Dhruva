"""
Unit tests for Scraper Data Models.
Verifies dataclass construction, default factories, dictionary serialization,
and JSON round-tripping.
"""

import json
from scraper.models import (
    RawScrapedPlace,
    NormalizedPlace,
    PlaceCompleteness,
    ScrapingReport
)


def test_raw_scraped_place_dict_serialization():
    raw = RawScrapedPlace(
        source_url="https://www.incredibleindia.gov.in/en/odisha/bhubaneswar/lingaraj-temple",
        title="Lingaraj Temple | Incredible India",
        meta_description="11th century temple in Bhubaneswar.",
        meta_keywords=["temple", "shiva"],
        og_image="https://example.com/lingaraj.jpg",
        state="Odisha",
        city="Bhubaneswar",
        place_name_raw="Lingaraj Temple",
        headings=[{"tag": "h2", "text": "History"}],
        paragraphs=["Built by Somavamsi rulers."],
        timing_raw="06:00 AM - 09:00 PM",
        celebrations_raw="Mahashivaratri",
        transit_raw={"airport": "BBI Airport"},
        nearby_attractions=["Mukteswara Temple"],
        image_urls=["https://example.com/img1.jpg"],
        extracted_tags=["heritage", "kalinga"],
        scraped_at_utc="2026-08-26T12:00:00Z"
    )

    d = raw.to_dict()
    assert d["source_url"] == "https://www.incredibleindia.gov.in/en/odisha/bhubaneswar/lingaraj-temple"
    assert d["place_name_raw"] == "Lingaraj Temple"
    assert len(d["paragraphs"]) == 1
    assert d["transit_raw"]["airport"] == "BBI Airport"

    # Verify JSON serializability
    json_str = json.dumps(d)
    assert "Lingaraj Temple" in json_str


def test_normalized_place_dict_serialization():
    norm = NormalizedPlace(
        id="lingaraj-temple",
        name="Lingaraj Temple",
        city="Bhubaneswar",
        state="Odisha",
        category="Temple & Sacred Sanctum",
        sub_category="Shiva Temple & Sanctum",
        short_description="An ancient temple.",
        full_description="Detailed historical description of the sanctum.",
        cultural_significance="Epicenter of Shaivism in Odisha.",
        historical_period="11th Century CE • Somavamsi Dynasty",
        opening_hours="06:00 AM - 09:00 PM",
        entry_fee="Free entry",
        best_time_of_day="Early Morning (06:30 AM - 09:00 AM)",
        recommended_duration="1.5 to 2 Hours",
        accessibility_notes="Footwear removal mandatory.",
        festivals=["Mahashivaratri", "Ashokashtami"],
        nearest_transit={"nearest_airport": "Biju Patnaik Airport"},
        image_urls=["https://example.com/lingaraj.jpg"],
        source_url="https://www.incredibleindia.gov.in/en/odisha/bhubaneswar/lingaraj-temple",
        scraped_at_utc="2026-08-26T12:00:00Z"
    )

    d = norm.to_dict()
    assert d["id"] == "lingaraj-temple"
    assert d["category"] == "Temple & Sacred Sanctum"
    assert len(d["festivals"]) == 2
    assert d["nearest_transit"]["nearest_airport"] == "Biju Patnaik Airport"


def test_place_completeness_model():
    comp = PlaceCompleteness(
        place_id="mukteswara-temple",
        place_name="Mukteswara Temple",
        total_fields=18,
        filled_fields=17,
        missing_fields=["festivals"],
        completeness_score=94.44
    )

    d = comp.to_dict()
    assert d["place_id"] == "mukteswara-temple"
    assert d["completeness_score"] == 94.44
    assert d["missing_fields"] == ["festivals"]


def test_scraping_report_model():
    report = ScrapingReport(
        target_source="Incredible India Tourism Portal",
        start_url="https://www.incredibleindia.gov.in/en/odisha/bhubaneswar",
        city="Bhubaneswar",
        state="Odisha",
        total_pages_discovered=10,
        total_pages_crawled=5,
        total_places_normalized=5,
        errors_count=0,
        error_details=[],
        start_time_utc="2026-08-26T12:00:00Z",
        end_time_utc="2026-08-26T12:01:00Z",
        duration_seconds=60.0,
        average_completeness=96.5,
        field_completeness_summary={"name": 100.0, "category": 100.0},
        completeness_per_place=[]
    )

    d = report.to_dict()
    assert d["total_places_normalized"] == 5
    assert d["average_completeness"] == 96.5
    assert d["errors_count"] == 0
