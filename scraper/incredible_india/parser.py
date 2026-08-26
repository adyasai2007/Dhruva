"""
Parser for Incredible India website pages.
Extracts structured heritage facts, cultural narratives, timing specifications,
transit info, festivals, and imagery using BeautifulSoup.
"""

from __future__ import annotations
import logging
import re
import time
from typing import List, Dict, Set, Optional, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from scraper.models import RawScrapedPlace

logger = logging.getLogger("dhruva.scraper.incredible_india.parser")


class IncredibleIndiaParser:
    """
    Parses HTML content from Incredible India tourism portal.
    """

    BASE_URL = "https://www.incredibleindia.gov.in"

    INDIAN_STATES_AND_UTS = {
        "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh", "goa",
        "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka", "kerala",
        "madhya pradesh", "maharashtra", "manipur", "meghalaya", "mizoram", "nagaland",
        "odisha", "punjab", "rajasthan", "sikkim", "tamil nadu", "telangana", "tripura",
        "uttar pradesh", "uttarakhand", "west bengal", "andaman and nicobar islands",
        "chandigarh", "dadra and nagar haveli and daman and diu", "delhi",
        "jammu and kashmir", "ladakh", "lakshadweep", "puducherry", "india"
    }

    NAV_EXCLUDED_HEADINGS = {
        "create an account", "plan your trip", "trending searches", "share", "login",
        "sign in", "popular destinations", "explore india", "state/ut :", "states & union territories",
        "destinations", "experiences", "themes", "festivals & events", "follow us",
        "download mobile app", "newsletter", "copyright"
    }

    @classmethod
    def is_hub_page(cls, url: str) -> bool:
        """Check if URL represents a destination/city overview hub page."""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.strip("/").split("/") if p]
        # Example: /en/odisha/bhubaneswar (3 parts: lang, state, city)
        return len(path_parts) == 3 and path_parts[0] in ("en", "hi")

    @classmethod
    def is_article_or_guide(cls, slug: str) -> bool:
        """Check if slug corresponds to a generic blog article, itinerary, food listicle, or thematic essay."""
        slug_lower = slug.lower()
        article_patterns = [
            r"^\d+-famous-",
            r"-dishes-",
            r"-cuisine-",
            r"-itinerary-",
            r"^adventure-awaits-",
            r"^discover-",
            r"^exploring-",
            r"^savour-",
            r"^find-an-",
            r"^when-you-",
            r"^must-visit-",
            r"^a-tourists-guide-",
            r"^a-thrilling-",
            r"^experience-",
            r"-delight$",
            r"-entertained$",
            r"^odisha-the-land-",
            r"^jagannath-consciousness$",
            r"^chhenapoda$"
        ]
        return any(re.search(pat, slug_lower) for pat in article_patterns)

    @classmethod
    def extract_attraction_links(cls, html_content: str, base_url: str, city: str, state: str) -> List[str]:
        """
        Extract links to child attraction/place detail pages from a city hub page.
        """
        soup = BeautifulSoup(html_content, "html.parser")
        discovered_urls: Set[str] = set()
        city_slug = city.lower().replace(" ", "-")
        state_slug = state.lower().replace(" ", "-")

        # 1. Search all anchor tags
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            path = parsed.path.rstrip("/")
            parts = [p for p in path.strip("/").split("/") if p]

            # We are looking for: /en/<state>/<city>/<attraction-slug>
            if len(parts) == 4 and parts[0] in ("en", "hi"):
                url_state = parts[1].lower()
                url_city = parts[2].lower()
                url_slug = parts[3].lower()

                if (url_city == city_slug or url_state == state_slug) and not cls.is_article_or_guide(url_slug):
                    discovered_urls.add(full_url)

        # 2. Check nearby attraction cards if present
        for card in soup.find_all(class_=lambda c: c and ("card" in c.lower() or "attraction" in c.lower())):
            a_tag = card.find("a", href=True)
            if a_tag:
                full_url = urljoin(base_url, a_tag["href"].strip())
                parsed = urlparse(full_url)
                parts = [p for p in parsed.path.strip("/").split("/") if p]
                if len(parts) == 4 and parts[0] in ("en", "hi") and not cls.is_article_or_guide(parts[3].lower()):
                    discovered_urls.add(full_url)

        logger.info(f"Discovered {len(discovered_urls)} attraction URLs for city '{city}'")
        return sorted(list(discovered_urls))

    @classmethod
    def parse_place_page(cls, html_content: str, url: str) -> RawScrapedPlace:
        """
        Extract raw structured facts from an attraction place page.
        """
        soup = BeautifulSoup(html_content, "html.parser")
        now_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # 1. Page Title & Meta tags
        title = soup.title.get_text(strip=True) if soup.title else ""
        meta_desc = ""
        meta_keywords: List[str] = []
        og_image = ""

        for meta in soup.find_all("meta"):
            name = (meta.get("name") or meta.get("property") or "").lower()
            content = meta.get("content", "").strip()
            if not content:
                continue
            if name in ("description", "og:description"):
                if not meta_desc or len(content) > len(meta_desc):
                    meta_desc = content
            elif name in ("keywords", "news_keywords"):
                meta_keywords = [k.strip() for k in content.split(",") if k.strip()]
            elif name in ("og:image", "twitter:image"):
                if not og_image:
                    og_image = urljoin(url, content)

        # 2. State and City from URL hierarchy
        parsed = urlparse(url)
        parts = [p for p in parsed.path.strip("/").split("/") if p]
        state = parts[1].replace("-", " ").title() if len(parts) >= 2 else ""
        city = parts[2].replace("-", " ").title() if len(parts) >= 3 else ""

        # Remove header, nav, and footer to prevent mega-menu pollution
        for tag_name in ("header", "nav", "footer", "script", "style", "noscript"):
            for tag in soup.find_all(tag_name):
                tag.extract()

        # 3. Place Name
        place_name_raw = ""
        slug_name = parts[3].replace("-", " ").title() if len(parts) >= 4 else ""

        # Priority 1: <h1> in content
        h1 = soup.find("h1")
        if h1:
            h1_text = h1.get_text(strip=True)
            if h1_text and h1_text.lower() not in cls.INDIAN_STATES_AND_UTS and h1_text.lower() not in cls.NAV_EXCLUDED_HEADINGS:
                place_name_raw = h1_text

        # Priority 2: <h2> in content if not a state name or navigation header
        if not place_name_raw:
            for h in soup.find_all("h2"):
                htext = h.get_text(strip=True)
                if htext and htext.lower() not in cls.INDIAN_STATES_AND_UTS and htext.lower() not in cls.NAV_EXCLUDED_HEADINGS:
                    if htext.lower() not in (state.lower(), city.lower(), f"visit {city.lower()}", f"experience {city.lower()}"):
                        place_name_raw = htext
                        break

        # Priority 3: Title tag (e.g. "Ananta Vasudeva Temple | Incredible India")
        if not place_name_raw and title:
            title_candidate = title.split("|")[0].split("-")[0].strip()
            title_candidate = re.sub(r"^(?:Visit\s+(?:the\s+)?|Experience\s+(?:the\s+)?|Explore\s+(?:the\s+)?|Discover\s+)", "", title_candidate, flags=re.IGNORECASE)
            title_candidate = re.sub(r"\s+in\s+.*$", "", title_candidate, flags=re.IGNORECASE).strip()
            if title_candidate and title_candidate.lower() not in cls.INDIAN_STATES_AND_UTS:
                place_name_raw = title_candidate

        # Check if place_name_raw is a poetic subtitle (like "The living lake") while slug has the actual entity name
        if slug_name:
            if not place_name_raw or place_name_raw.lower() in ("the living lake", "overview", "about", "history"):
                place_name_raw = slug_name
            # If slug contains key identifiers (like "temple", "lake", "hills", "caves", "museum") and place_name does not
            elif any(k in slug_name.lower() for k in ("temple", "lake", "caves", "museum", "hills", "waterfall")) and not any(k in place_name_raw.lower() for k in ("temple", "lake", "caves", "museum", "hills", "waterfall")):
                # E.g. "Ananta Vasudeva" vs "Ananta Vasudeva Temple" -> prefer "Ananta Vasudeva Temple"
                if slug_name.lower().startswith(place_name_raw.lower()):
                    place_name_raw = slug_name

        # 4. Headings & Paragraphs
        headings: List[Dict[str, str]] = []
        for h in soup.find_all(["h2", "h3", "h4", "h5"]):
            htext = h.get_text(strip=True)
            if htext and len(htext) > 3:
                if htext.lower() not in cls.INDIAN_STATES_AND_UTS and htext.lower() not in cls.NAV_EXCLUDED_HEADINGS:
                    if not any(k in htext.lower() for k in ["airport", "railway", "weather", "video description", "°c", "°f"]):
                        headings.append({"tag": h.name, "text": htext})

        paragraphs: List[str] = []
        for p in soup.find_all("p"):
            ptext = p.get_text(" ", strip=True)
            if ptext and len(ptext) > 25:
                # Exclude transit and boilerplate snippets from general paragraphs
                if not any(k in ptext.lower() for k in ["international airport", "railway station", "weather", "video description", "°c", "°f", "cookie"]):
                    paragraphs.append(ptext)

        # 5. Timings / Opening Hours
        timing_raw = ""
        # Search for headings or elements containing 'Timings' or 'Timing' or 'Hours'
        timing_header = soup.find(lambda tag: tag.name in ("h2", "h3", "h4", "h5", "strong", "span") and "timing" in tag.get_text().lower())
        if timing_header:
            parent = timing_header.find_parent(["div", "section", "li"])
            if parent:
                timing_raw = parent.get_text(" ", strip=True)
            else:
                timing_raw = timing_header.get_text(" ", strip=True)

        if not timing_raw:
            # Look for regex pattern in all text
            all_text = soup.get_text(" ")
            timing_match = re.search(r"(?:Opening\s*time|Visiting\s*hours|Timings?)[^\n.]{1,100}", all_text, re.IGNORECASE)
            if timing_match:
                timing_raw = timing_match.group(0).strip()

        # 6. Celebrations / Festivals
        celebrations_raw = ""
        celebration_header = soup.find(lambda tag: tag.name in ("h2", "h3", "h4", "h5") and any(k in tag.get_text().lower() for k in ["celebration", "festival", "fair", "mahotsav"]))
        if celebration_header:
            parent = celebration_header.find_parent(["div", "section"])
            if parent:
                celebrations_raw = parent.get_text(" ", strip=True)
            else:
                celebrations_raw = celebration_header.get_text(" ", strip=True)

        # 7. Transit / Connectivity (Airport, Railway Station)
        transit_raw: Dict[str, str] = {}
        for tag in soup.find_all(["div", "p", "li", "span"]):
            text = tag.get_text(" ", strip=True)
            if "nearest airport" in text.lower() and "airport" not in transit_raw:
                airport_clean = re.sub(r"^.*?nearest\s*airport\s*[:\-]*\s*", "", text, flags=re.IGNORECASE).strip()
                if airport_clean and len(airport_clean) < 120:
                    transit_raw["airport"] = airport_clean.split("Nearest")[0].split("Share")[0].strip()

            if "nearest railway" in text.lower() and "railway" not in transit_raw:
                railway_clean = re.sub(r"^.*?nearest\s*railway(?:\s*station)?\s*[:\-]*\s*", "", text, flags=re.IGNORECASE).strip()
                if railway_clean and len(railway_clean) < 120:
                    transit_raw["railway"] = railway_clean.split("Nearest")[0].split("Share")[0].strip()

        # 8. Nearby Attractions
        nearby_attractions: List[str] = []
        for card in soup.find_all(class_=lambda c: c and "card-title" in c.lower()):
            ctext = card.get_text(strip=True)
            if ctext and ctext not in nearby_attractions and ctext.lower() != place_name_raw.lower():
                nearby_attractions.append(ctext)

        # 9. Image URLs
        image_urls: List[str] = []
        if og_image:
            image_urls.append(og_image)

        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src") or ""
            if src and not any(k in src.lower() for k in ["logo", "icon", "arrow", "social", "share", "avatar", "blank", "app-store"]):
                full_img_url = urljoin(url, src)
                if full_img_url not in image_urls:
                    image_urls.append(full_img_url)

        return RawScrapedPlace(
            source_url=url,
            title=title,
            meta_description=meta_desc,
            meta_keywords=meta_keywords,
            og_image=og_image,
            state=state,
            city=city,
            place_name_raw=place_name_raw,
            headings=headings,
            paragraphs=paragraphs,
            timing_raw=timing_raw,
            celebrations_raw=celebrations_raw,
            transit_raw=transit_raw,
            nearby_attractions=nearby_attractions[:8],
            image_urls=image_urls[:6],
            extracted_tags=meta_keywords,
            scraped_at_utc=now_utc
        )
