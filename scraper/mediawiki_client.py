"""
MediaWiki Action API Client for DHRUVA Cultural Travel Planner.
Provides structured, machine-readable extraction of Wikipedia articles,
coordinates, images, sections, and candidate attraction links without parsing HTML.
"""

from __future__ import annotations
import json
import logging
import time
import urllib.parse
import urllib.request
from typing import Dict, Any, List, Optional

logger = logging.getLogger("dhruva.mediawiki")


class MediaWikiClient:
    """
    Client for Wikipedia's MediaWiki Action API.
    Adheres to Wikimedia User-Agent and rate-limiting policies.
    """

    BASE_URL = "https://en.wikipedia.org/w/api.php"
    DEFAULT_USER_AGENT = "DhruvaCulturalTravelPlanner/1.0 (https://github.com/adyasai2007/Dhruva; travel-research@dhruva.org)"

    def __init__(self, user_agent: Optional[str] = None, request_delay: float = 0.5):
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self.request_delay = request_delay

    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a GET request to MediaWiki API with rate limiting and retry handling."""
        params["format"] = "json"
        query_string = urllib.parse.urlencode(params)
        url = f"{self.BASE_URL}?{query_string}"

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/json",
            }
        )

        # Politeness delay
        if self.request_delay > 0:
            time.sleep(self.request_delay)

        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=15) as response:
                    if response.status == 200:
                        raw_data = response.read().decode("utf-8")
                        return json.loads(raw_data)
                    else:
                        logger.warning(f"MediaWiki API HTTP {response.status} for {url}")
            except Exception as e:
                logger.warning(f"MediaWiki API attempt {attempt + 1} failed for {url}: {e}")
                time.sleep(1.0 * (attempt + 1))

        return {}

    def get_article_details(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Fetch rich structured content for an individual Wikipedia article:
        - Plain text extract (cleaned of wikitext/HTML)
        - Geographic coordinates (lat, lon)
        - High-resolution / thumbnail image URL
        - Page URL & last revision timestamp
        """
        params = {
            "action": "query",
            "titles": title,
            "prop": "extracts|coordinates|pageimages|info",
            "inprop": "url",
            "explaintext": "1",
            "piprop": "original|thumbnail",
            "pithumbsize": "800",
            "redirects": "1",
        }

        data = self._make_request(params)
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return None

        # Page response is keyed by page ID
        for page_id, page_data in pages.items():
            if page_id == "-1" or "missing" in page_data:
                logger.warning(f"Page '{title}' not found on Wikipedia.")
                return None

            # Coordinates
            coords = page_data.get("coordinates", [])
            lat, lon = None, None
            if coords:
                lat = coords[0].get("lat")
                lon = coords[0].get("lon")

            # Image
            thumb_info = page_data.get("thumbnail", {})
            orig_info = page_data.get("original", {})
            image_url = thumb_info.get("source") or orig_info.get("source")

            # Text extract
            extract = page_data.get("extract", "").strip()

            return {
                "page_id": page_data.get("pageid"),
                "title": page_data.get("title", title),
                "full_url": page_data.get("fullurl"),
                "last_updated": page_data.get("touched"),
                "lat": lat,
                "lon": lon,
                "image_url": image_url,
                "extract": extract,
                "length": page_data.get("length", 0),
            }

        return None

    def get_page_links(self, title: str, namespace: int = 0) -> List[str]:
        """Retrieve all internal article links on a given page."""
        params = {
            "action": "parse",
            "page": title,
            "prop": "links",
            "redirects": "1",
        }
        data = self._make_request(params)
        links = data.get("parse", {}).get("links", [])
        return [
            link.get("*") for link in links
            if link.get("ns") == namespace and link.get("exists") is not False
        ]

    def search_articles(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Search Wikipedia for articles matching a tourist/cultural query."""
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srnamespace": "0",
            "srlimit": str(limit),
        }
        data = self._make_request(params)
        return data.get("query", {}).get("search", [])


# Singleton client
mediawiki_client = MediaWikiClient()
