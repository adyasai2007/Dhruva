"""
Configuration management for DHRUVA Cultural Scraper.
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _float(name: str, default: float) -> float:
    val = os.getenv(name)
    return float(val) if val else default


def _int(name: str, default: int) -> int:
    val = os.getenv(name)
    return int(val) if val else default


@dataclass
class ScraperConfig:
    """Settings controlling crawler behavior, politeness, persistence, and verification."""
    # Identification
    user_agent: str = (
        "DhruvaCulturalBot/1.0 (Educational & Heritage Research; "
        "+https://github.com/dhruva-heritage/bot-policy; contact: dev@dhruva.app)"
    )

    # Target Site defaults
    base_url: str = "https://www.incredibleindia.gov.in"
    default_city: str = "bhubaneswar"
    default_state: str = "odisha"

    # Politeness & Rate Limits
    delay_seconds: float = 1.5
    delay_jitter: float = 0.5  # Random variance +/- jitter
    respect_robots_txt: bool = True

    # Network & Retries
    timeout_seconds: int = 15
    max_retries: int = 3
    retry_backoff_factor: float = 1.5

    # Output & Persistence
    output_dir: Path = field(default_factory=lambda: Path("data/scraped"))
    checkpoint_file: Path = field(default_factory=lambda: Path("data/scraped/.checkpoint.json"))
    max_pages: int = 10

    # Export formats
    export_formats: List[str] = field(default_factory=lambda: ["json", "csv"])

    # Debug / Logging
    debug: bool = False
    dry_run: bool = False

    # LLM Verification & Triage (Groq primary, Gemini fallback)
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    groq_model: str = field(default_factory=lambda: os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"))
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))

    # Search & Grounding Evidence Provider (duckduckgo | wikipedia | serpapi | bing | stub)
    search_provider: str = field(default_factory=lambda: os.getenv("SEARCH_PROVIDER", "duckduckgo"))
    serpapi_key: str = field(default_factory=lambda: os.getenv("SERPAPI_KEY", ""))
    bing_search_key: str = field(default_factory=lambda: os.getenv("BING_SEARCH_KEY", ""))

    # Verification Policy & Thresholds
    min_auto_confirm_confidence: float = field(default_factory=lambda: _float("MIN_AUTO_CONFIRM_CONFIDENCE", 0.85))
    default_staleness_days: int = field(default_factory=lambda: _int("DEFAULT_STALENESS_DAYS", 30))

    def ensure_directories(self) -> None:
        """Create necessary output and artifact directories if they do not exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if self.checkpoint_file.parent:
            self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
