"""
Polite and resilient web crawler for DHRUVA.
Enforces robots.txt compliance, polite rate limiting with jitter, exponential backoff,
canonical URL tracking, and checkpoint persistence.
"""

from __future__ import annotations
import json
import logging
import random
import time
from pathlib import Path
from typing import Optional, Set, Dict, Any, List
import urllib.parse
import urllib.robotparser
import requests

from scraper.common.config import ScraperConfig

logger = logging.getLogger("dhruva.scraper.crawler")


class PoliteCrawler:
    """
    HTTP client orchestrator adhering to ethical web scraping best practices.
    """

    def __init__(self, config: ScraperConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.config.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        })

        self.visited_urls: Set[str] = set()
        self.failed_urls: Dict[str, str] = {}
        self.robot_parsers: Dict[str, urllib.robotparser.RobotFileParser] = {}
        self.last_request_time: float = 0.0

    @staticmethod
    def canonicalize_url(url: str) -> str:
        """
        Normalize a URL by removing trailing fragments, query tracking parameters,
        and standardizing scheme/host casing.
        """
        parsed = urllib.parse.urlparse(url)
        # Filter out common tracking query params
        query_params = urllib.parse.parse_qsl(parsed.query)
        cleaned_params = [
            (k, v) for k, v in query_params
            if not k.startswith("utm_") and k not in ("fbclid", "gclid", "_ga")
        ]
        new_query = urllib.parse.urlencode(cleaned_params)

        path = parsed.path
        if path != "/" and path.endswith("/"):
            path = path[:-1]

        canonical = urllib.parse.urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            "",  # params
            new_query,
            ""   # fragment stripped
        ))
        return canonical

    def get_robot_parser(self, base_url: str) -> urllib.robotparser.RobotFileParser:
        """Fetch and cache robots.txt for a given origin."""
        parsed = urllib.parse.urlparse(base_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"

        if origin in self.robot_parsers:
            return self.robot_parsers[origin]

        rp = urllib.robotparser.RobotFileParser()
        robots_url = f"{origin}/robots.txt"
        logger.info(f"Fetching robots.txt from {robots_url}")

        try:
            resp = self.session.get(
                robots_url,
                timeout=self.config.timeout_seconds,
                headers={"User-Agent": self.config.user_agent}
            )
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
                logger.info(f"Successfully loaded robots.txt for {origin}")
            else:
                logger.warning(
                    f"robots.txt at {robots_url} returned status {resp.status_code}. Defaulting to allow all."
                )
                rp.allow_all = True
        except Exception as e:
            logger.warning(f"Failed to fetch robots.txt ({e}). Defaulting to allow all.")
            rp.allow_all = True

        self.robot_parsers[origin] = rp
        return rp

    def is_allowed_by_robots(self, url: str) -> bool:
        """Check if URL access is permitted by site's robots.txt."""
        if not self.config.respect_robots_txt:
            return True

        parsed = urllib.parse.urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        rp = self.get_robot_parser(origin)
        return rp.can_fetch(self.config.user_agent, url)

    def _apply_rate_limit(self) -> None:
        """Enforce polite pause between consecutive requests with random jitter."""
        if self.last_request_time > 0:
            elapsed = time.time() - self.last_request_time
            jitter = random.uniform(-self.config.delay_jitter, self.config.delay_jitter)
            target_delay = max(0.5, self.config.delay_seconds + jitter)

            if elapsed < target_delay:
                sleep_duration = target_delay - elapsed
                logger.debug(f"Polite delay: sleeping {sleep_duration:.2f}s")
                time.sleep(sleep_duration)

    def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch HTML content from a URL with retries, exponential backoff,
        and robots.txt verification.
        """
        canonical_url = self.canonicalize_url(url)

        if canonical_url in self.visited_urls:
            logger.debug(f"Skipping already visited URL: {canonical_url}")
            return None

        if not self.is_allowed_by_robots(canonical_url):
            logger.warning(f"URL disallowed by robots.txt: {canonical_url}")
            self.failed_urls[canonical_url] = "Disallowed by robots.txt"
            return None

        if self.config.dry_run:
            logger.info(f"[DRY RUN] Would fetch: {canonical_url}")
            self.visited_urls.add(canonical_url)
            return "<html><body><h1>Dry Run</h1></body></html>"

        for attempt in range(1, self.config.max_retries + 1):
            self._apply_rate_limit()
            try:
                logger.info(f"Fetching (attempt {attempt}/{self.config.max_retries}): {canonical_url}")
                response = self.session.get(
                    canonical_url,
                    timeout=self.config.timeout_seconds,
                    allow_redirects=True
                )
                self.last_request_time = time.time()

                if response.status_code == 200:
                    self.visited_urls.add(canonical_url)
                    # Verify content type is HTML
                    ctype = response.headers.get("Content-Type", "")
                    if "text/html" not in ctype and "application/xhtml" not in ctype:
                        logger.warning(f"Non-HTML response type '{ctype}' for {canonical_url}")
                    return response.text

                elif response.status_code == 404:
                    logger.warning(f"HTTP 404 Not Found: {canonical_url}")
                    self.failed_urls[canonical_url] = "HTTP 404 Not Found"
                    self.visited_urls.add(canonical_url)
                    return None

                elif response.status_code in (429, 500, 502, 503, 504):
                    backoff = self.config.retry_backoff_factor ** attempt
                    logger.warning(
                        f"HTTP {response.status_code} for {canonical_url}. "
                        f"Retrying in {backoff:.1f}s..."
                    )
                    time.sleep(backoff)
                else:
                    logger.error(f"HTTP {response.status_code} for {canonical_url}")
                    self.failed_urls[canonical_url] = f"HTTP {response.status_code}"
                    self.visited_urls.add(canonical_url)
                    return None

            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                backoff = self.config.retry_backoff_factor ** attempt
                logger.warning(f"Network error on {canonical_url}: {e}. Retrying in {backoff:.1f}s...")
                time.sleep(backoff)
            except Exception as e:
                logger.error(f"Unexpected error fetching {canonical_url}: {e}")
                self.failed_urls[canonical_url] = str(e)
                self.visited_urls.add(canonical_url)
                return None

        self.failed_urls[canonical_url] = f"Exceeded max retries ({self.config.max_retries})"
        return None

    def save_checkpoint(self, data: Dict[str, Any]) -> None:
        """Persist crawler state to disk for resumption."""
        self.config.ensure_directories()
        checkpoint_data = {
            "visited_urls": list(self.visited_urls),
            "failed_urls": self.failed_urls,
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "extra_data": data,
        }
        try:
            with open(self.config.checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(checkpoint_data, f, indent=2)
            logger.debug(f"Saved checkpoint to {self.config.checkpoint_file}")
        except Exception as e:
            logger.error(f"Failed to write checkpoint: {e}")

    def load_checkpoint(self) -> Optional[Dict[str, Any]]:
        """Load state from previous run checkpoint if present."""
        if not self.config.checkpoint_file.exists():
            return None
        try:
            with open(self.config.checkpoint_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.visited_urls = set(data.get("visited_urls", []))
            self.failed_urls = data.get("failed_urls", {})
            logger.info(
                f"Resumed from checkpoint: {len(self.visited_urls)} visited URLs restored."
            )
            return data.get("extra_data")
        except Exception as e:
            logger.error(f"Failed to read checkpoint file: {e}")
            return None
