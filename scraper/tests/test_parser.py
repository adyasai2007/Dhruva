"""
Unit tests for IncredibleIndiaParser.
Validates extraction of attraction links from hub pages and structured facts
from place detail HTML fixtures (complete, partial, malformed).
"""

from pathlib import Path
from scraper.incredible_india.parser import IncredibleIndiaParser

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(filename: str) -> str:
    with open(FIXTURES_DIR / filename, "r", encoding="utf-8") as f:
        return f.read()


def test_extract_attraction_links_from_hub():
    hub_html = load_fixture("hub_bhubaneswar.html")
    base_url = "https://www.incredibleindia.gov.in"
    links = IncredibleIndiaParser.extract_attraction_links(
        html_content=hub_html,
        base_url=base_url,
        city="bhubaneswar",
        state="odisha"
    )

    assert len(links) >= 5
    assert any("lingaraj-temple" in link for link in links)
    assert any("mukteswara-temple" in link for link in links)
    assert any("rajarani-temple" in link for link in links)
    assert any("khandagiri-and-udayagiri-caves" in link for link in links)
    assert any("kala-bhoomi-odisha-crafts-museum" in link for link in links)

    # Verify excluded articles are not in place links
    assert not any("must-visit-places-in-bhubaneswar" in link for link in links)


def test_parse_complete_place_page():
    html = load_fixture("place_lingaraj_complete.html")
    url = "https://www.incredibleindia.gov.in/en/odisha/bhubaneswar/lingaraj-temple"

    raw = IncredibleIndiaParser.parse_place_page(html, url)

    assert raw.source_url == url
    assert "Lingaraj Temple" in raw.place_name_raw
    assert raw.state == "Odisha"
    assert raw.city == "Bhubaneswar"
    assert "Somavamsi" in raw.meta_keywords or "Somavamsi" in " ".join(raw.paragraphs)
    assert "06:00 AM" in raw.timing_raw
    assert "09:00 PM" in raw.timing_raw
    assert "Mahashivaratri" in raw.celebrations_raw
    assert "Ashokashtami" in raw.celebrations_raw
    assert "Biju Patnaik International Airport" in raw.transit_raw.get("airport", "")
    assert "Bhubaneswar Railway Station" in raw.transit_raw.get("railway", "")
    assert len(raw.paragraphs) >= 3
    assert len(raw.image_urls) >= 1
    assert "Mukteswara Temple" in raw.nearby_attractions


def test_parse_partial_place_page():
    html = load_fixture("place_partial.html")
    url = "https://www.incredibleindia.gov.in/en/odisha/bhubaneswar/khandagiri-and-udayagiri-caves"

    raw = IncredibleIndiaParser.parse_place_page(html, url)

    assert raw.source_url == url
    assert "Khandagiri" in raw.place_name_raw
    assert len(raw.paragraphs) >= 1
    assert raw.timing_raw == ""  # Missing in partial fixture
    assert raw.celebrations_raw == ""  # Missing in partial fixture
    assert raw.transit_raw == {}  # Missing in partial fixture


def test_parse_malformed_html():
    html = load_fixture("place_malformed.html")
    url = "https://www.incredibleindia.gov.in/en/odisha/bhubaneswar/unknown-place"

    # Must parse without throwing unhandled exceptions
    raw = IncredibleIndiaParser.parse_place_page(html, url)
    assert raw.source_url == url
    assert raw.state == "Odisha"
    assert raw.city == "Bhubaneswar"
