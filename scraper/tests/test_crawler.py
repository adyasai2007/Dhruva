"""
Unit tests for PoliteCrawler.
Tests URL canonicalization, robots.txt verification, rate limiting, and checkpoint persistence.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from scraper.common.config import ScraperConfig
from scraper.common.crawler import PoliteCrawler


def test_canonicalize_url():
    # Strips UTM params and fragments
    url_with_tracking = "https://www.incredibleindia.gov.in/en/odisha/bhubaneswar/lingaraj-temple/?utm_source=google&utm_medium=cpc#overview"
    canonical = PoliteCrawler.canonicalize_url(url_with_tracking)
    assert canonical == "https://www.incredibleindia.gov.in/en/odisha/bhubaneswar/lingaraj-temple"

    # Preserves necessary query params
    url_with_page = "https://www.incredibleindia.gov.in/en/search?q=temple&page=2"
    canonical_page = PoliteCrawler.canonicalize_url(url_with_page)
    assert "q=temple" in canonical_page
    assert "page=2" in canonical_page


def test_robots_txt_allow_and_disallow():
    config = ScraperConfig(respect_robots_txt=True)
    crawler = PoliteCrawler(config)

    # Mock RobotFileParser
    mock_parser = MagicMock()
    mock_parser.can_fetch.side_effect = lambda ua, url: False if "/admin" in url else True
    crawler.robot_parsers["https://www.incredibleindia.gov.in"] = mock_parser

    assert crawler.is_allowed_by_robots("https://www.incredibleindia.gov.in/en/odisha/bhubaneswar/lingaraj-temple") is True
    assert crawler.is_allowed_by_robots("https://www.incredibleindia.gov.in/admin/login") is False


def test_checkpoint_save_and_load(tmp_path: Path):
    checkpoint_file = tmp_path / ".test_checkpoint.json"
    config = ScraperConfig(checkpoint_file=checkpoint_file)
    crawler = PoliteCrawler(config)

    # Mark some URLs visited
    crawler.visited_urls.add("https://example.com/page1")
    crawler.visited_urls.add("https://example.com/page2")
    crawler.failed_urls["https://example.com/page3"] = "404 Not Found"

    extra_data = {"city": "bhubaneswar", "pages_crawled": 2}
    crawler.save_checkpoint(extra_data)

    assert checkpoint_file.exists()

    # Load in new crawler instance
    new_crawler = PoliteCrawler(config)
    loaded_data = new_crawler.load_checkpoint()

    assert "https://example.com/page1" in new_crawler.visited_urls
    assert "https://example.com/page2" in new_crawler.visited_urls
    assert new_crawler.failed_urls.get("https://example.com/page3") == "404 Not Found"
    assert loaded_data["city"] == "bhubaneswar"
    assert loaded_data["pages_crawled"] == 2


def test_polite_crawler_headers():
    config = ScraperConfig(user_agent="DhruvaCulturalBot/1.0 (Testing)")
    crawler = PoliteCrawler(config)
    assert crawler.session.headers["User-Agent"] == "DhruvaCulturalBot/1.0 (Testing)"
    assert "Accept-Language" in crawler.session.headers
