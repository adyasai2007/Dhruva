"""
Unit tests for PlaceNormalizer.
Tests text sanitization, taxonomy classification, historical inference,
accessibility guidance generation, and completeness evaluation.
"""

from scraper.common.normalizer import PlaceNormalizer
from scraper.models import RawScrapedPlace, NormalizedPlace


def test_clean_text():
    dirty_text = "  Kalinga\xa0Architecture  with​ zero-width chars and  ‘smart quotes’ & “double quotes”–dashes.\n\n\nNew paragraph.  "
    cleaned = PlaceNormalizer.clean_text(dirty_text)
    assert "\xa0" not in cleaned
    assert "​" not in cleaned
    assert "Kalinga Architecture" in cleaned
    assert "'smart quotes'" in cleaned
    assert '"double quotes"' in cleaned
    assert "-dashes" in cleaned


def test_generate_slug():
    assert PlaceNormalizer.generate_slug("Lingaraj Temple", "Bhubaneswar") == "lingaraj-temple"
    assert PlaceNormalizer.generate_slug("Khandagiri & Udayagiri Caves!") == "khandagiri-udayagiri-caves"
    assert PlaceNormalizer.generate_slug("Kala Bhoomi - Odisha Crafts Museum") == "kala-bhoomi---odisha-crafts-museum" or "kala-bhoomi-odisha-crafts-museum"


def test_classify_category():
    # Test Temple classification
    raw_temple = RawScrapedPlace(
        source_url="https://example.com/lingaraj",
        title="Lingaraj Temple",
        meta_description="Ancient Shiva temple with sanctum and aarti darshan",
        meta_keywords=["temple", "shiva"],
        og_image="",
        state="Odisha",
        city="Bhubaneswar",
        place_name_raw="Lingaraj Temple",
        headings=[],
        paragraphs=["Dedicated to Lord Shiva in Kalinga architecture."],
        timing_raw="",
        celebrations_raw="",
        transit_raw={},
        nearby_attractions=[],
        image_urls=[],
        extracted_tags=[],
        scraped_at_utc=""
    )
    cat, subcat = PlaceNormalizer.classify_category(raw_temple)
    assert cat == PlaceNormalizer.CAT_TEMPLE
    assert "Shiva" in subcat

    # Test Heritage / Cave classification
    raw_caves = RawScrapedPlace(
        source_url="https://example.com/caves",
        title="Udayagiri Caves",
        meta_description="Rock-cut ancient Jain caves and inscriptions",
        meta_keywords=["caves", "heritage"],
        og_image="",
        state="Odisha",
        city="Bhubaneswar",
        place_name_raw="Udayagiri Caves",
        headings=[],
        paragraphs=["Ancient rock-cut gumpha from the 2nd century BCE."],
        timing_raw="",
        celebrations_raw="",
        transit_raw={},
        nearby_attractions=[],
        image_urls=[],
        extracted_tags=[],
        scraped_at_utc=""
    )
    cat, subcat = PlaceNormalizer.classify_category(raw_caves)
    assert cat == PlaceNormalizer.CAT_HERITAGE
    assert "Caves" in subcat

    # Test Museum classification
    raw_museum = RawScrapedPlace(
        source_url="https://example.com/museum",
        title="Kala Bhoomi Crafts Museum",
        meta_description="Handloom and traditional handicrafts exhibition",
        meta_keywords=["museum", "crafts"],
        og_image="",
        state="Odisha",
        city="Bhubaneswar",
        place_name_raw="Kala Bhoomi Crafts Museum",
        headings=[],
        paragraphs=["Displays exquisite silver filigree and tribal art."],
        timing_raw="",
        celebrations_raw="",
        transit_raw={},
        nearby_attractions=[],
        image_urls=[],
        extracted_tags=[],
        scraped_at_utc=""
    )
    cat, subcat = PlaceNormalizer.classify_category(raw_museum)
    assert cat == PlaceNormalizer.CAT_ARTS_MUSEUM


def test_normalize_opening_hours():
    # Raw with explicit open/close labels
    raw_timing = "Opening time - 06:30 AM Closing time - 08:30 PM"
    norm = PlaceNormalizer.normalize_opening_hours(raw_timing, PlaceNormalizer.CAT_TEMPLE)
    assert norm == "06:30 AM - 08:30 PM"

    # Fallback for empty temple timing
    empty_temple = PlaceNormalizer.normalize_opening_hours("", PlaceNormalizer.CAT_TEMPLE)
    assert "06:00 AM" in empty_temple
    assert "Daily" in empty_temple

    # Fallback for empty museum timing
    empty_museum = PlaceNormalizer.normalize_opening_hours("", PlaceNormalizer.CAT_ARTS_MUSEUM)
    assert "Mondays" in empty_museum


def test_infer_historical_period():
    text = "Built in the 11th century CE by Somavamsi dynasty rulers in classical Rekha Deula architecture."
    period = PlaceNormalizer.infer_historical_period(text)
    assert "11th Century" in period
    assert "Somavamsi Dynasty" in period
    assert "Rekha Deula" in period


def test_generate_accessibility_notes():
    temple_notes = PlaceNormalizer.generate_accessibility_notes(PlaceNormalizer.CAT_TEMPLE, "Lingaraj Temple")
    assert "Footwear removal" in temple_notes
    assert "Wheelchair" in temple_notes

    museum_notes = PlaceNormalizer.generate_accessibility_notes(PlaceNormalizer.CAT_ARTS_MUSEUM, "Kala Bhoomi")
    assert "wheelchair ramps" in museum_notes.lower()
    assert "restrooms" in museum_notes.lower()


def test_extract_festivals():
    celebrations_raw = "Mahashivaratri and Ashokashtami car festival"
    narrative = "Devotees celebrate Chandan Yatra and Mukteswar Dance Festival annually."
    festivals = PlaceNormalizer.extract_festivals(celebrations_raw, narrative)
    assert "Mahashivaratri" in festivals
    assert "Ashokashtami" in festivals
    assert "Chandan Yatra" in festivals


def test_evaluate_completeness():
    complete_place = NormalizedPlace(
        id="lingaraj-temple",
        name="Lingaraj Temple",
        city="Bhubaneswar",
        state="Odisha",
        category="Temple & Sacred Sanctum",
        sub_category="Shiva Temple & Sanctum",
        short_description="An ancient temple in Bhubaneswar, Odisha.",
        full_description="Detailed historical description of the sanctum with Kalinga architecture.",
        cultural_significance="Epicenter of Shaivism in Odisha.",
        historical_period="11th Century CE • Somavamsi Dynasty",
        opening_hours="06:00 AM - 09:00 PM",
        entry_fee="Free entry",
        best_time_of_day="Early Morning (06:30 AM - 09:00 AM)",
        recommended_duration="1.5 to 2 Hours",
        accessibility_notes="Footwear removal mandatory. Wheelchair assistance available at main outer gates.",
        festivals=["Mahashivaratri", "Ashokashtami"],
        nearest_transit={"nearest_airport": "Biju Patnaik Airport"},
        image_urls=["https://example.com/lingaraj.jpg"],
        source_url="https://www.incredibleindia.gov.in/en/odisha/bhubaneswar/lingaraj-temple",
        scraped_at_utc="2026-08-26T12:00:00Z"
    )

    metrics = PlaceNormalizer.evaluate_completeness(complete_place)
    assert metrics.completeness_score == 100.0
    assert len(metrics.missing_fields) == 0

    # Test with partial place missing festivals and transit
    partial_place = NormalizedPlace(
        id="caves",
        name="Caves",
        city="Bhubaneswar",
        state="Odisha",
        category="Heritage & Archaeological Site",
        sub_category="Rock-cut Caves",
        short_description="Rock cut caves in Odisha.",
        full_description="Detailed description of the caves.",
        cultural_significance="Historic significance of rock cut art.",
        historical_period="2nd Century BCE",
        opening_hours="08:00 AM - 05:30 PM",
        entry_fee="Free entry",
        best_time_of_day="Morning",
        recommended_duration="2 Hours",
        accessibility_notes="Steps present.",
        festivals=[],  # missing
        nearest_transit={},  # missing
        image_urls=[],  # missing
        source_url="https://example.com/caves",
        scraped_at_utc="2026-08-26T12:00:00Z"
    )
    partial_metrics = PlaceNormalizer.evaluate_completeness(partial_place)
    assert partial_metrics.completeness_score < 100.0
    assert "festivals" in partial_metrics.missing_fields
    assert "nearest_transit" in partial_metrics.missing_fields
    assert "image_urls" in partial_metrics.missing_fields
