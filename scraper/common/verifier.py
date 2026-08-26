"""
DHRUVA Cultural Data Verification and LLM Fact-Checking Module.
Verifies scraped heritage places against live web knowledge via Google Gemini API
with Google Search Grounding, or utilizes rule-based heuristic validation when offline.
"""

from __future__ import annotations
import json
import logging
import os
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import requests

logger = logging.getLogger("dhruva.scraper.verifier")

# High-resolution Scene7 fallback images for Odisha cultural landmarks
IMAGE_FALLBACKS = {
    "asokastami": "https://s7ap1.scene7.com/is/image/incredibleindia/lingaraj-temple-bhubaneshwar-odisha-1-attr-hero?qlt=82&ts=1742165306173",
    "chilika-lake": "https://s7ap1.scene7.com/is/image/incredibleindia/chilika-wildlife-sanctuary-puri-odisha-1-attr-hero?qlt=82&ts=1726663755053",
    "kala-bhoomi-odisha-crafts-museum": "https://s7ap1.scene7.com/is/image/incredibleindia/1-khandagiri-udaigiri-caves-attr-hero?qlt=82&ts=1742172787783",
    "kantilo": "https://s7ap1.scene7.com/is/image/incredibleindia/Explore-the-Rich-Heritage-of-Jajpur-City7-hero?qlt=82&ts=1726663567178",
    "kuanria": "https://s7ap1.scene7.com/is/image/incredibleindia/ansupa-lake-cuttack-odisha-1-attr-hero?qlt=82&ts=1726674675128",
    "balukhand-konark-sanctuary": "https://s7ap1.scene7.com/is/image/incredibleindia/chilika-wildlife-sanctuary-puri-odisha-2-attr-hero?qlt=82&ts=1726663783800",
    "discover-a-symphony-of-wildlife": "https://s7ap1.scene7.com/is/image/incredibleindia/cuttack-odisha-bhitarkanika-national-park-cuttack-orissa-1-attr-hero?qlt=82&ts=1726674724638",
    "ananta-vasudeva-temple": "https://s7ap1.scene7.com/is/image/incredibleindia/lingaraj-temple-bhubaneshwar-odisha-1-attr-hero?qlt=82"
}


@dataclass
class VerifiedPlaceData:
    """Structured, verified entity ready for relational table dissection."""
    id: str
    name: str
    city: str
    state: str
    is_valid: bool = True
    validation_source: str = "heuristic"  # 'gemini_grounded' or 'heuristic'
    category: str = "Heritage & Archaeological Site"
    sub_category: str = "Cultural Heritage"
    short_description: str = ""
    full_description: str = ""
    opens_at: str = "06:00 AM"
    closes_at: str = "07:00 PM"
    duration: float = 2.0
    duration_label: str = "2.0 Hours"
    popularity: float = 4.5
    risk: str = "Low"
    image_url: str = ""
    entry_fee: str = "Free entry"
    # 5 Interest Scores (0.0 to 5.0)
    architecture: float = 4.0
    history: float = 4.0
    spiritual: float = 4.0
    nature: float = 3.0
    culture: float = 4.5
    # Festivals list
    festivals: List[Dict[str, str]] = field(default_factory=list)
    # Coordinates (resolved via geocoder)
    lat: Optional[float] = None
    long: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PlaceVerifier:
    """
    Intelligent fact-checker and enricher for scraped travel data.
    Supports Google Gemini API with Google Search Grounding and rule-based validation.
    """

    def __init__(self, gemini_api_key: Optional[str] = None, model_name: str = "gemini-3.5-flash-lite"):
        self.api_key = gemini_api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or self._find_env_key()
        self.model_name = model_name

    def _find_env_key(self) -> Optional[str]:
        """Look for GEMINI_API_KEY or GOOGLE_API_KEY in local .env files."""
        possible_paths = [
            Path("scraper/incredible_india/.env"),
            Path(".env"),
            Path(__file__).parent.parent / "incredible_india" / ".env",
            Path(__file__).parent.parent.parent / ".env"
        ]
        for p in possible_paths:
            if p.exists():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("GEMINI_API_KEY") or line.startswith("GOOGLE_API_KEY"):
                                parts = line.split("=", 1)
                                if len(parts) == 2:
                                    val = parts[1].strip().strip("\"'")
                                    if val:
                                        return val
                except Exception as e:
                    logger.debug(f"Could not read env file {p}: {e}")
        return None

    def clean_image_url(self, place_id: str, image_urls: List[str]) -> str:
        """Find the best high-res working Scene7 image URL or reliable fallback."""
        valid_scene7 = [
            url for url in image_urls
            if "scene7.com" in url and "placeholder" not in url and "wid=200" not in url and "og.png" not in url
        ]
        if valid_scene7:
            return valid_scene7[0]

        any_scene7 = [
            url for url in image_urls
            if "scene7.com" in url and "placeholder" not in url and "og.png" not in url
        ]
        if any_scene7:
            return any_scene7[0]

        return IMAGE_FALLBACKS.get(
            place_id,
            "https://s7ap1.scene7.com/is/image/incredibleindia/lingaraj-temple-bhubaneshwar-odisha-1-attr-hero?qlt=82"
        )

    def parse_timing_regex(self, timing_str: str) -> Tuple[str, str]:
        """Regex-based parser for opening hours."""
        if not timing_str or "NA" in timing_str:
            return ("06:00 AM", "08:00 PM")
        if "Open 24 hours" in timing_str or "throughout the day" in timing_str:
            return ("12:00 AM", "11:59 PM")
        if "Morning" in timing_str and "Evening" in timing_str:
            return ("06:00 AM", "07:00 PM")

        match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM))\s*-\s*(\d{1,2}:\d{2}\s*(?:AM|PM))', timing_str, re.IGNORECASE)
        if match:
            return (match.group(1).strip().upper(), match.group(2).strip().upper())

        open_match = re.search(r'Opening time\s*-\s*(\d{1,2}[:.]\d{2}\s*(?:AM|PM))', timing_str, re.IGNORECASE)
        close_match = re.search(r'Closing time\s*-\s*(\d{1,2}[:.]\d{2}\s*(?:AM|PM))', timing_str, re.IGNORECASE)
        if open_match and close_match:
            return (
                open_match.group(1).replace(".", ":").strip().upper(),
                close_match.group(1).replace(".", ":").strip().upper()
            )

        return ("06:00 AM", "07:00 PM")

    def verify_with_gemini(self, place_dict: Dict[str, Any]) -> Optional[VerifiedPlaceData]:
        """
        Verify scraped place using Google Gemini API with Google Search Grounding.
        """
        if not self.api_key:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"

        prompt = f"""
You are a cultural heritage and travel data verification expert for India tourism.
Analyze the following scraped place data and verify its factual accuracy using Google Search:

Place Data:
- ID: {place_dict.get('id')}
- Name: {place_dict.get('name')}
- City: {place_dict.get('city')}
- State: {place_dict.get('state')}
- Scraped Description: {place_dict.get('short_description') or place_dict.get('full_description', '')[:300]}
- Scraped Hours: {place_dict.get('opening_hours')}
- Scraped Festivals: {place_dict.get('festivals')}

Respond ONLY with a valid JSON object strictly matching this schema:
{{
    "is_valid": true,
    "verified_name": "Accurate Name of Place",
    "category": "Temple & Sacred Sanctum / Heritage & Archaeological Site / Arts, Crafts & Museum / Nature & Scenic Sanctum / Cultural Quarter & Bazar",
    "sub_category": "Specific sub category",
    "short_description": "Clean, engaging 1-2 sentence description (100-180 chars)",
    "opens_at": "HH:MM AM/PM",
    "closes_at": "HH:MM AM/PM",
    "duration": 2.0,
    "duration_label": "2.0 Hours",
    "popularity": 4.8,
    "risk": "Low / Moderate / Guarded",
    "entry_fee": "Free entry / Rs. 50 per person / etc.",
    "interest_scores": {{
        "architecture": 4.5,
        "history": 4.8,
        "spiritual": 5.0,
        "nature": 2.0,
        "culture": 4.9
    }},
    "festivals": [
        {{
            "name": "Festival Name",
            "start_date": "YYYY-MM-DD or Month",
            "end_date": "YYYY-MM-DD or Month",
            "description": "Brief description of the festival celebration"
        }}
    ]
}}

Note: If the place is corrupted, a duplicate, or not a genuine attraction (e.g. ananta-vasudeva-temple with corrupted description), set "is_valid": false.
"""

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "tools": [{"google_search": {}}],  # Enable Google Search Grounding
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }

        try:
            # 1. Attempt with Google Search Grounding (with 8s timeout)
            validation_source = "gemini_grounded"
            response = None
            try:
                response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=8)
            except Exception as e:
                logger.debug(f"Search grounding query timed out/errored: {e}")
                response = None

            # 2. Fallback to direct Gemini Flash JSON if search grounding quota or tool is restricted
            if response is None or response.status_code != 200:
                payload_direct = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.1,
                        "responseMimeType": "application/json"
                    }
                }
                response = requests.post(url, json=payload_direct, headers={"Content-Type": "application/json"}, timeout=15)
                validation_source = "gemini_flash"

            if response.status_code == 200:
                result_json = response.json()
                candidates = result_json.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    raw_text = candidates[0]["content"]["parts"][0]["text"]
                    data = json.loads(raw_text)

                    if not data.get("is_valid", True):
                        logger.warning(f"❌ Gemini marked '{place_dict.get('name')}' as INVALID/CORRUPTED.")
                        return None

                    scores = data.get("interest_scores", {})
                    working_img = self.clean_image_url(place_dict.get("id", ""), place_dict.get("image_urls", []))

                    return VerifiedPlaceData(
                        id=place_dict.get("id"),
                        name=data.get("verified_name") or place_dict.get("name"),
                        city=place_dict.get("city", "Bhubaneswar"),
                        state=place_dict.get("state", "Odisha"),
                        is_valid=True,
                        validation_source=validation_source,
                        category=data.get("category", place_dict.get("category")),
                        sub_category=data.get("sub_category", place_dict.get("sub_category")),
                        short_description=data.get("short_description") or place_dict.get("short_description"),
                        full_description=place_dict.get("full_description", ""),
                        opens_at=data.get("opens_at", "06:00 AM"),
                        closes_at=data.get("closes_at", "07:00 PM"),
                        duration=float(data.get("duration", 2.0)),
                        duration_label=data.get("duration_label", f"{data.get('duration', 2.0)} Hours"),
                        popularity=float(data.get("popularity", 4.5)),
                        risk=data.get("risk", "Low"),
                        image_url=working_img,
                        entry_fee=data.get("entry_fee", "Free entry"),
                        architecture=float(scores.get("architecture", 4.0)),
                        history=float(scores.get("history", 4.0)),
                        spiritual=float(scores.get("spiritual", 4.0)),
                        nature=float(scores.get("nature", 3.0)),
                        culture=float(scores.get("culture", 4.5)),
                        festivals=data.get("festivals", [])
                    )
            else:
                logger.warning(f"Gemini API returned HTTP {response.status_code}: {response.text[:200]}")
        except Exception as e:
            logger.warning(f"Gemini verification failed for '{place_dict.get('name')}': {e}")

        return None

    def verify_heuristic(self, place_dict: Dict[str, Any]) -> Optional[VerifiedPlaceData]:
        """
        Rule-based offline verification and enrichment fallback.
        """
        place_id = place_dict.get("id", "")
        name = place_dict.get("name", "")

        # 1. Filter out known corrupted records (e.g. ananta-vasudeva-temple scraped error)
        if place_id == "ananta-vasudeva-temple" or "ananta vasudeva" in name.lower():
            logger.info(f"Filtered out corrupted place record: {place_id}")
            return None

        # 2. Timing parsing
        opens_at, closes_at = self.parse_timing_regex(place_dict.get("opening_hours", ""))

        # 3. Clean Scene7 Image URL
        image_url = self.clean_image_url(place_id, place_dict.get("image_urls", []))

        # 4. Interest scoring heuristics
        category = place_dict.get("category", "")
        desc_full = (place_dict.get("short_description", "") + " " + place_dict.get("full_description", "")).lower()

        # Defaults
        arch, hist, spir, nat, cult = 4.0, 4.0, 3.5, 2.5, 4.5
        dur = 2.0
        pop = 4.6
        risk = "Low"

        if "temple" in category.lower() or "sacred" in category.lower() or "shrine" in desc_full:
            spir = 5.0
            arch = 4.8
            hist = 4.8
            cult = 4.9
            nat = 2.0
            dur = 2.0
            pop = 4.8
        elif "nature" in category.lower() or "sanctuary" in desc_full or "lake" in desc_full:
            nat = 5.0
            spir = 2.5
            arch = 2.0
            hist = 3.0
            cult = 3.5
            dur = 3.5
            pop = 4.7
            risk = "Moderate" if ("lake" in desc_full or "wildlife" in desc_full) else "Low"
        elif "museum" in category.lower() or "craft" in desc_full:
            cult = 5.0
            arch = 4.2
            hist = 4.7
            spir = 2.0
            nat = 2.5
            dur = 2.5
            pop = 4.6
        elif "cave" in desc_full or "heritage" in category.lower():
            arch = 4.9
            hist = 5.0
            spir = 4.0
            nat = 3.5
            cult = 4.7
            dur = 2.5
            pop = 4.8
            risk = "Moderate" if "cave" in desc_full else "Low"

        short_desc = place_dict.get("short_description") or (place_dict.get("full_description", "")[:180] + "...")

        return VerifiedPlaceData(
            id=place_id,
            name=name,
            city=place_dict.get("city", "Bhubaneswar"),
            state=place_dict.get("state", "Odisha"),
            is_valid=True,
            validation_source="heuristic",
            category=place_dict.get("category", "Heritage & Archaeological Site"),
            sub_category=place_dict.get("sub_category", "Cultural Heritage"),
            short_description=short_desc,
            full_description=place_dict.get("full_description", ""),
            opens_at=opens_at,
            closes_at=closes_at,
            duration=dur,
            duration_label=place_dict.get("recommended_duration", f"{dur} Hours"),
            popularity=pop,
            risk=risk,
            image_url=image_url,
            entry_fee=place_dict.get("entry_fee", "Free entry"),
            architecture=arch,
            history=hist,
            spiritual=spir,
            nature=nat,
            culture=cult,
            festivals=[]
        )

    def verify_place(self, place_dict: Dict[str, Any]) -> Optional[VerifiedPlaceData]:
        """
        Main verification entrypoint: attempts Gemini Search Grounding first,
        falling back to heuristic validation.
        """
        # Try Gemini API if key is configured
        if self.api_key:
            logger.info(f"Verifying '{place_dict.get('name')}' with Gemini Google Search Grounding...")
            verified = self.verify_with_gemini(place_dict)
            if verified:
                return verified
            logger.info("Falling back to heuristic validation...")

        return self.verify_heuristic(place_dict)
