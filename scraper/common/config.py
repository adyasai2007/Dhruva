"""
Configuration management for DHRUVA Cultural Scraper.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class ScraperConfig:
    """Settings controlling crawler behavior, politeness, and persistence."""
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

    def ensure_directories(self) -> None:
        """Create necessary output and artifact directories if they do not exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if self.checkpoint_file.parent:
            self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
