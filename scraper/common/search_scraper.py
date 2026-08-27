"""
DHRUVA Multi-Provider Search Evidence Gatherer
---------------------------------------------
Scrapes web search results and extracts clean text evidence for LLM verification.
Supports:
1. DuckDuckGo (Zero API key required, HTML search parser)
2. Wikipedia / Wikimedia API (Zero API key required, authoritative heritage truth)
3. SerpAPI (Google Search API via SERPAPI_KEY)
4. Bing Web Search (via BING_SEARCH_KEY)
5. Stub (Zero-cost fallback)
"""

from __future__ import annotations
import logging
import re
import urllib.parse
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

import requests
from bs4 import BeautifulSoup

from scraper.common.config import ScraperConfig

logger = logging.getLogger("dhruva.search_scraper")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 DhruvaBot/1.0"
MAX_RESULTS = 3
MAX_CHARS_PER_PAGE = 3500


@dataclass
class Evidence:
    """Structured evidence retrieved from search results and organic pages."""
    query: str
    urls: List[str] = field(default_factory=list)
    combined_text: str = ""
    provider_used: str = "stub"
    snippets: List[Dict[str, str]] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not self.combined_text or len(self.combined_text.strip()) < 50


class SearchEvidenceScraper:
    """
    Decoupled search evidence gathering engine.
    Fetches real-time web context to ground LLM reasoning without hallucinations.
    """

    def __init__(self, config: Optional[ScraperConfig] = None, provider: Optional[str] = None):
        self.config = config or ScraperConfig()
        self.provider = (provider or self.config.search_provider or "duckduckgo").lower()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def gather_evidence(
        self,
        place_name: str,
        city: str,
        state: str = "Odisha",
        query_type: str = "general"
    ) -> Evidence:
        """
        Gather search evidence for a place in a given city.
        query_type: 'general' | 'timings_fee' | 'festival'
        """
        query = self._build_query(place_name, city, state, query_type)
        logger.info(f"Gathering evidence with provider '{self.provider}' for query: '{query}'")

        urls, snippets = self._search(query)
        texts: List[str] = []
        fetched_urls: List[str] = []

        # Include search snippets as high-density evidence
        for snip in snippets:
            texts.append(f"Search Snippet ({snip.get('url', '')}):\n{snip.get('title', '')} - {snip.get('snippet', '')}")

        # Fetch top organic result pages
        for url in urls[:MAX_RESULTS]:
            # Skip binary, social media, or noisy links
            if any(ext in url.lower() for ext in [".pdf", ".jpg", ".png", "facebook.com", "instagram.com", "twitter.com", "youtube.com"]):
                continue
            page_text = self._fetch_clean_page_text(url)
            if page_text:
                texts.append(f"Source: {url}\n{page_text}")
                fetched_urls.append(url)

        combined = "\n\n---\n\n".join(texts)
        return Evidence(
            query=query,
            urls=fetched_urls or urls,
            combined_text=combined,
            provider_used=self.provider,
            snippets=snippets
        )

    def _build_query(self, place_name: str, city: str, state: str, query_type: str) -> str:
        """Construct targeted, high-precision search query."""
        clean_name = re.sub(r"^\s*(discover|explore|visit|experience|plan\s+(a|your))\s+", "", place_name, flags=re.IGNORECASE).strip()
        if query_type == "timings_fee":
            return f"{clean_name} {city} {state} opening timings entry ticket fee hours"
        elif query_type == "festival":
            return f"{clean_name} {city} {state} annual festival dates celebrations"
        return f"{clean_name} {city} {state} tourism tourist attraction heritage"

    def _search(self, query: str) -> Tuple[List[str], List[Dict[str, str]]]:
        """Route to configured search provider with automatic graceful fallbacks."""
        if self.provider == "serpapi" and self.config.serpapi_key:
            try:
                return self._search_serpapi(query)
            except Exception as e:
                logger.warning(f"SerpAPI search failed ({e}), falling back to DuckDuckGo/Wikipedia")
        elif self.provider == "bing" and self.config.bing_search_key:
            try:
                return self._search_bing(query)
            except Exception as e:
                logger.warning(f"Bing search failed ({e}), falling back to DuckDuckGo/Wikipedia")

        if self.provider == "wikipedia":
            wiki_res = self._search_wikipedia(query)
            if wiki_res[0]:
                return wiki_res

        # Default zero-cost provider: DuckDuckGo HTML parser
        ddg_res = self._search_duckduckgo(query)
        if ddg_res[0]:
            return ddg_res

        # Wikipedia fallback
        wiki_res = self._search_wikipedia(query)
        if wiki_res[0]:
            return wiki_res

        return self._search_stub(query)

    def _search_duckduckgo(self, query: str) -> Tuple[List[str], List[Dict[str, str]]]:
        """Search DuckDuckGo HTML interface (zero API key needed)."""
        urls: List[str] = []
        snippets: List[Dict[str, str]] = []
        try:
            resp = self.session.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": USER_AGENT},
                timeout=self.config.timeout_seconds
            )
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for result in soup.select(".result"):
                    title_elem = result.select_one(".result__title a")
                    snippet_elem = result.select_one(".result__snippet")
                    if title_elem and title_elem.get("href"):
                        raw_href = title_elem["href"]
                        # DuckDuckGo redirect link parsing (/l/?uddg=...)
                        match = re.search(r"uddg=([^&]+)", raw_href)
                        final_url = urllib.parse.unquote(match.group(1)) if match else raw_href
                        if final_url.startswith("http"):
                            urls.append(final_url)
                            snippets.append({
                                "title": title_elem.get_text(strip=True),
                                "url": final_url,
                                "snippet": snippet_elem.get_text(strip=True) if snippet_elem else ""
                            })
                    if len(urls) >= MAX_RESULTS:
                        break
        except Exception as e:
            logger.debug(f"DuckDuckGo search encountered error: {e}")

        return urls, snippets

    def _search_wikipedia(self, query: str) -> Tuple[List[str], List[Dict[str, str]]]:
        """Query Wikimedia REST API for authoritative historical/cultural entries."""
        urls: List[str] = []
        snippets: List[Dict[str, str]] = []
        try:
            resp = self.session.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "format": "json",
                    "utf8": 1,
                    "srlimit": MAX_RESULTS
                },
                timeout=self.config.timeout_seconds
            )
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("query", {}).get("search", []):
                    title = item.get("title", "")
                    page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                    raw_snippet = item.get("snippet", "")
                    clean_snippet = BeautifulSoup(raw_snippet, "html.parser").get_text()
                    urls.append(page_url)
                    snippets.append({
                        "title": title,
                        "url": page_url,
                        "snippet": clean_snippet
                    })
        except Exception as e:
            logger.debug(f"Wikipedia search encountered error: {e}")

        return urls, snippets

    def _search_serpapi(self, query: str) -> Tuple[List[str], List[Dict[str, str]]]:
        """Query SerpAPI Google Search."""
        urls: List[str] = []
        snippets: List[Dict[str, str]] = []
        resp = self.session.get(
            "https://serpapi.com/search",
            params={"q": query, "api_key": self.config.serpapi_key, "num": MAX_RESULTS, "gl": "in"},
            timeout=self.config.timeout_seconds
        )
        resp.raise_for_status()
        data = resp.json()
        for r in data.get("organic_results", []):
            if "link" in r:
                urls.append(r["link"])
                snippets.append({
                    "title": r.get("title", ""),
                    "url": r["link"],
                    "snippet": r.get("snippet", "")
                })
        return urls, snippets

    def _search_bing(self, query: str) -> Tuple[List[str], List[Dict[str, str]]]:
        """Query Bing Web Search API."""
        urls: List[str] = []
        snippets: List[Dict[str, str]] = []
        resp = self.session.get(
            "https://api.bing.microsoft.com/v7.0/search",
            headers={"Ocp-Apim-Subscription-Key": self.config.bing_search_key},
            params={"q": query, "count": MAX_RESULTS, "mkt": "en-IN"},
            timeout=self.config.timeout_seconds
        )
        resp.raise_for_status()
        data = resp.json()
        for r in data.get("webPages", {}).get("value", []):
            if "url" in r:
                urls.append(r["url"])
                snippets.append({
                    "title": r.get("name", ""),
                    "url": r["url"],
                    "snippet": r.get("snippet", "")
                })
        return urls, snippets

    def _search_stub(self, query: str) -> Tuple[List[str], List[Dict[str, str]]]:
        """Stub search fallback when all network providers are inaccessible."""
        return [], []

    def _fetch_clean_page_text(self, url: str) -> Optional[str]:
        """Download URL content and extract clean text stripped of boilerplate."""
        try:
            resp = self.session.get(url, timeout=self.config.timeout_seconds)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, "html.parser")
            # Decompose ads, scripts, navigations, sidebars
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "noscript"]):
                tag.decompose()

            # Extract main article if present, or body
            main_content = soup.find("article") or soup.find("main") or soup.find("body") or soup
            text = main_content.get_text(separator=" ")
            clean_text = re.sub(r"\s+", " ", text).strip()
            return clean_text[:MAX_CHARS_PER_PAGE]
        except Exception as e:
            logger.debug(f"Failed fetching page text from {url}: {e}")
            return None
