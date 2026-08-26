"""
Data models for the DHRUVA Cultural Scraper.
Defines typed structures for raw scraped facts, normalized heritage places,
completeness metrics, and run summaries.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any


@dataclass
class RawScrapedPlace:
    """Raw extracted content from a source web page before normalization."""
    source_url: str
    title: str = ""
    meta_description: str = ""
    meta_keywords: List[str] = field(default_factory=list)
    og_image: str = ""
    state: str = ""
    city: str = ""
    place_name_raw: str = ""
    headings: List[Dict[str, str]] = field(default_factory=list)
    paragraphs: List[str] = field(default_factory=list)
    timing_raw: str = ""
    celebrations_raw: str = ""
    transit_raw: Dict[str, str] = field(default_factory=dict)
    nearby_attractions: List[str] = field(default_factory=list)
    image_urls: List[str] = field(default_factory=list)
    extracted_tags: List[str] = field(default_factory=list)
    scraped_at_utc: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NormalizedPlace:
    """
    Clean, normalized place entity matching DHRUVA schema expectations
    and downstream PostgreSQL table columns.
    """
    id: str
    name: str
    city: str
    state: str
    category: str
    sub_category: str
    short_description: str
    full_description: str
    cultural_significance: str
    historical_period: str
    opening_hours: str
    entry_fee: str
    best_time_of_day: str
    recommended_duration: str
    accessibility_notes: str
    festivals: List[str] = field(default_factory=list)
    nearest_transit: Dict[str, str] = field(default_factory=dict)
    image_urls: List[str] = field(default_factory=list)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_url: str = ""
    scraped_at_utc: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PlaceCompleteness:
    """Completeness metrics for an individual normalized place."""
    place_id: str
    place_name: str
    total_fields: int
    filled_fields: int
    missing_fields: List[str]
    completeness_score: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScrapingReport:
    """Summary and audit log of a scraper execution run."""
    target_source: str
    start_url: str
    city: str
    state: str
    total_pages_discovered: int = 0
    total_pages_crawled: int = 0
    total_places_normalized: int = 0
    errors_count: int = 0
    error_details: List[Dict[str, str]] = field(default_factory=list)
    start_time_utc: str = ""
    end_time_utc: str = ""
    duration_seconds: float = 0.0
    average_completeness: float = 0.0
    field_completeness_summary: Dict[str, float] = field(default_factory=dict)
    completeness_per_place: List[PlaceCompleteness] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
