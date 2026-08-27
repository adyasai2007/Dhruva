"""
Unit tests for DHRUVA Cultural Data Verification and LLM Fact-Checking Module.
Tests SearchEvidenceScraper, timing parser, duration label synchronizer,
Scene7 image resolution, and PlaceVerifier heuristic validation.
"""

import pytest
from scraper.common.config import ScraperConfig
from scraper.common.search_scraper import SearchEvidenceScraper, Evidence
from scraper.common.verifier import (
    PlaceVerifier,
    GroqVerifier,
    VerifiedPlaceData,
    IMAGE_FALLBACKS,
    KNOWN_NAME_CORRECTIONS
)


@pytest.fixture
def verifier():
    config = ScraperConfig(search_provider="stub")
    return PlaceVerifier(config=config)


def test_sanitize_place_name(verifier):
    assert verifier.sanitize_place_name("Discover a symphony of wildlife") == "Chandaka Elephant Sanctuary"
    assert verifier.sanitize_place_name("Explore the rich heritage of jajpur") == "Jajpur Heritage Sites"
    assert verifier.sanitize_place_name("Experience the rich heritage of jajpur") == "Jajpur Heritage Sites"
    assert verifier.sanitize_place_name("Visit Lingaraj Temple") == "Lingaraj Temple"
    assert verifier.sanitize_place_name("Mukteswara Temple") == "Mukteswara Temple"


def test_parse_timing_regex(verifier):
    opens, closes = verifier.parse_timing_regex("06:00 AM - 09:00 PM")
    assert opens == "06:00 AM"
    assert closes == "09:00 PM"

    opens, closes = verifier.parse_timing_regex("8:00 am to 5:30 pm")
    assert opens == "08:00 AM"
    assert closes == "05:30 PM"

    # 24 hours timing
    opens, closes = verifier.parse_timing_regex("Open 24 hours")
    assert opens == "12:00 AM"
    assert closes == "11:59 PM"

    # Default fallback for unparseable timings
    opens, closes = verifier.parse_timing_regex("Unparseable text")
    assert opens == "06:00 AM"
    assert closes == "07:00 PM"


def test_synchronize_duration_label(verifier):
    assert verifier.synchronize_duration_label(2.0) == "1.5 to 2 Hours"
    assert verifier.synchronize_duration_label(1.5) == "1 to 1.5 Hours"
    assert verifier.synchronize_duration_label(3.5) == "3.5 to 4.5 Hours"
    assert verifier.synchronize_duration_label(2.0, "1.5-2.5 Hours") == "1.5-2.5 Hours"


def test_clean_image_url(verifier):
    # Fallback lookup
    img = verifier.clean_image_url("chandaka-elephant-sanctuary", [])
    assert "incredibleindia" in img
    assert img == IMAGE_FALLBACKS["chandaka-elephant-sanctuary"]

    # OG image fallback
    img_broken = verifier.clean_image_url(
        "custom-place",
        ["https://www.incredibleindia.gov.in/content/dam/incredible-india-v2/incredible-india-og.png"]
    )
    assert "incredible-india-og.png" not in img_broken

    # Valid working image
    valid_url = "https://s7ap1.scene7.com/is/image/incredibleindia/lingaraj-temple-hero"
    img_valid = verifier.clean_image_url("custom-place", [valid_url])
    assert img_valid == valid_url


def test_verify_heuristic_temple(verifier):
    sample_temple = {
        "id": "lingaraj-temple",
        "name": "Lingaraj Temple",
        "city": "Bhubaneswar",
        "state": "Odisha",
        "category": "Temple & Sacred Sanctum",
        "sub_category": "Hindu Temple",
        "short_description": "Prominent 11th-century Kalinga architecture temple dedicated to Lord Shiva.",
        "full_description": "Built by the Somavamsi dynasty, the temple complex houses over 50 shrines.",
        "opening_hours": "06:00 AM - 09:00 PM",
        "duration": 2.0,
        "popularity": 4.9,
        "risk": "Low",
        "image_urls": ["https://s7ap1.scene7.com/is/image/incredibleindia/lingaraj-temple-hero"]
    }

    res = verifier.verify_heuristic(sample_temple)
    assert res is not None
    assert isinstance(res, VerifiedPlaceData)
    assert res.id == "lingaraj-temple"
    assert res.name == "Lingaraj Temple"
    assert res.spiritual >= 4.5
    assert res.architecture >= 4.5
    assert res.opens_at == "06:00 AM"
    assert res.closes_at == "09:00 PM"


def test_verify_heuristic_corrupted_exclusion(verifier):
    # Ananta Vasudeva Temple (row 1 duplicate/corrupt) and Asokastami (festival) must be filtered out
    assert verifier.verify_heuristic({"id": "ananta-vasudeva-temple", "name": "Ananta Vasudeva Temple"}) is None
    assert verifier.verify_heuristic({"id": "asokastami", "name": "Asokastami Festival"}) is None


def test_search_evidence_scraper_stub():
    scraper = SearchEvidenceScraper(provider="stub")
    ev = scraper.gather_evidence("Lingaraj Temple", "Bhubaneswar")
    assert isinstance(ev, Evidence)
    assert ev.provider_used == "stub"
    assert "Lingaraj Temple" in ev.query


def test_groq_verifier_no_key():
    gv = GroqVerifier(api_key="")
    res = gv.verify({"id": "test", "name": "Test"}, Evidence(query="test"))
    assert res is None
