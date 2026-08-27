"""
DHRUVA Cultural Data Verification and LLM Fact-Checking Module.
--------------------------------------------------------------
Integrates:
1. Multi-Provider Search Evidence Retrieval (DuckDuckGo, Wikipedia API, SerpAPI, Bing)
2. Groq LLM Structured Triage (llama-3.3-70b-versatile, temperature=0, JSON mode)
3. Google Gemini 2.5/1.5 Flash Fallback
4. Offline Heuristic Fact-Checking, Categorization, and Sanitization
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

from scraper.common.config import ScraperConfig
from scraper.common.search_scraper import SearchEvidenceScraper, Evidence

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
    "chandaka-elephant-sanctuary": "https://s7ap1.scene7.com/is/image/incredibleindia/cuttack-odisha-bhitarkanika-national-park-cuttack-orissa-1-attr-hero?qlt=82&ts=1726674724638",
    "jajpur-heritage-sites": "https://s7ap1.scene7.com/is/image/incredibleindia/Explore-the-Rich-Heritage-of-Jajpur-City7-hero?qlt=82&ts=1726663567178",
    "ananta-vasudeva-temple": "https://s7ap1.scene7.com/is/image/incredibleindia/lingaraj-temple-bhubaneshwar-odisha-1-attr-hero?qlt=82"
}

_SUSPICIOUS_NAME_PATTERNS = [
    re.compile(r"^\s*discover\b", re.IGNORECASE),
    re.compile(r"^\s*explore\b", re.IGNORECASE),
    re.compile(r"^\s*plan\s+(a|your)\b", re.IGNORECASE),
    re.compile(r"^\s*experience\b", re.IGNORECASE),
    re.compile(r"^\s*visit\b", re.IGNORECASE),
]

KNOWN_NAME_CORRECTIONS = {
    "discover a symphony of wildlife": "Chandaka Elephant Sanctuary",
    "explore the rich heritage of jajpur": "Jajpur Heritage Sites",
    "experience the rich heritage of jajpur": "Jajpur Heritage Sites",
}

GROQ_SYSTEM_PROMPT = """You are an expert cultural heritage data verifier and fact-checker for India tourism.
You are given a candidate attraction/place record and retrieved web search evidence.
Compare the database record against the search evidence to determine factual accuracy.

Respond ONLY with a JSON object strictly matching this schema:
{
  "status": "correct" | "questionable" | "incorrect" | "insufficient_evidence",
  "confidence": <float 0.0-1.0>,
  "is_valid_place": <true if this is a genuine physical attraction, false if it is purely an annual festival or invalid blurb>,
  "verified_name": "<Canonical, clean entity name (e.g. 'Chandaka Elephant Sanctuary')>",
  "category": "<Temple & Sacred Sanctum | Heritage & Archaeological Site | Arts, Crafts & Museum | Nature & Scenic Sanctum | Monument & Fort | Cultural Quarter & Bazar>",
  "sub_category": "<Specific sub category>",
  "short_description": "<Concise, engaging 1-2 sentence description (100-180 characters)>",
  "opens_at": "<HH:MM AM/PM>",
  "closes_at": "<HH:MM AM/PM>",
  "duration": <float hours, e.g. 2.0>,
  "duration_label": "<e.g. '1.5 to 2.5 Hours'>",
  "popularity": <float 1.0-5.0>,
  "risk": "<Low | Moderate | Guarded>",
  "entry_fee": "<e.g. 'Free entry' or 'Rs. 40 per adult'>",
  "interest_scores": {
    "architecture": <float 0.0-5.0>,
    "history": <float 0.0-5.0>,
    "spiritual": <float 0.0-5.0>,
    "nature": <float 0.0-5.0>,
    "culture": <float 0.0-5.0>
  },
  "reasoning": "<1-2 sentence summary of evidence found>"
}

Rules:
1. Never hallucinate facts not grounded in evidence or well-known cultural history.
2. If place name starts with marketing slogans (e.g. 'Discover a symphony of wildlife'), resolve to the true POI name ('Chandaka Elephant Sanctuary').
3. If the record is purely an annual festival (e.g. 'Asokastami'), set is_valid_place: false because festivals belong in the FESTIVALS table.
4. If evidence is empty, use 'insufficient_evidence'.
"""


@dataclass
class VerifiedPlaceData:
    """Structured, verified entity ready for relational table dissection."""
    id: str
    name: str
    city: str
    state: str
    is_valid: bool = True
    validation_source: str = "heuristic"  # 'groq_llama70b', 'gemini_grounded', or 'heuristic'
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


class GroqVerifier:
    """
    Sub-second fact-checker using Groq Cloud LLM (llama-3.3-70b-versatile).
    Uses standard REST API over HTTPS for zero-dependency portability.
    """

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.model = model

    def verify(self, place_dict: Dict[str, Any], evidence: Evidence) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            return None

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        user_content = (
            f"Candidate Record:\n"
            f"- ID: {place_dict.get('id')}\n"
            f"- Name: {place_dict.get('name')}\n"
            f"- City: {place_dict.get('city')}\n"
            f"- State: {place_dict.get('state')}\n"
            f"- Current Category: {place_dict.get('category')}\n"
            f"- Scraped Description: {place_dict.get('short_description') or place_dict.get('full_description', '')[:300]}\n"
            f"- Scraped Hours: {place_dict.get('opening_hours')}\n\n"
            f"Search Query: {evidence.query}\n"
            f"Search Evidence Text:\n{evidence.combined_text[:4000]}"
        )

        payload = {
            "model": self.model,
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": GROQ_SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ]
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=20)
            if resp.status_code == 200:
                result = resp.json()
                raw_text = result["choices"][0]["message"]["content"]
                return json.loads(raw_text)
            else:
                logger.warning(f"Groq API returned HTTP {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.warning(f"Groq verification request failed: {e}")

        return None


class PlaceVerifier:
    """
    Unified fact-checker and enricher for scraped travel data.
    1. Search Evidence Retrieval (DuckDuckGo, Wikipedia, SerpAPI, Bing)
    2. Groq Llama 3.3 70B Verification
    3. Gemini Grounded / Flash Fallback
    4. Heuristic Rule-Based Verification
    """

    def __init__(self, config: Optional[ScraperConfig] = None, gemini_api_key: Optional[str] = None):
        self.config = config or ScraperConfig()
        self.groq_api_key = self.config.groq_api_key or os.environ.get("GROQ_API_KEY", "")
        self.gemini_api_key = gemini_api_key or self.config.gemini_api_key or os.environ.get("GEMINI_API_KEY") or self._find_env_key()
        self.search_scraper = SearchEvidenceScraper(self.config)
        self.groq_verifier = GroqVerifier(api_key=self.groq_api_key, model=self.config.groq_model) if self.groq_api_key else None

    def _find_env_key(self) -> Optional[str]:
        """Look for GEMINI_API_KEY or GROQ_API_KEY in local .env files."""
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
                            if line.startswith("GEMINI_API_KEY"):
                                parts = line.split("=", 1)
                                if len(parts) == 2 and parts[1].strip():
                                    return parts[1].strip().strip("\"'")
                except Exception as e:
                    logger.debug(f"Could not read env file {p}: {e}")
        return None

    def is_suspicious_name(self, name: str) -> bool:
        """Check if place name looks like marketing slogan / CTA rather than genuine entity name."""
        if not name:
            return False
        clean = name.strip()
        return any(pat.match(clean) for pat in _SUSPICIOUS_NAME_PATTERNS)

    def sanitize_place_name(self, raw_name: str) -> str:
        """Sanitize ad-copy headlines into true POI names."""
        norm = raw_name.strip().lower()
        if norm in KNOWN_NAME_CORRECTIONS:
            return KNOWN_NAME_CORRECTIONS[norm]
        for pattern in _SUSPICIOUS_NAME_PATTERNS:
            if pattern.match(raw_name.strip()):
                cleaned = pattern.sub("", raw_name.strip()).strip()
                return cleaned.title() if cleaned else raw_name
        return raw_name

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

        clean_id = place_id.lower().replace("_", "-")
        return IMAGE_FALLBACKS.get(
            clean_id,
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

        def _fmt(t: str) -> str:
            t = t.strip().upper().replace(".", ":")
            parts = t.split(":")
            if len(parts) == 2:
                hr = parts[0].strip()
                rest = parts[1].strip()
                if len(hr) == 1:
                    hr = f"0{hr}"
                return f"{hr}:{rest}"
            return t

        match = re.search(r'(\d{1,2}[:.]\d{2}\s*(?:AM|PM))\s*(?:-|to)\s*(\d{1,2}[:.]\d{2}\s*(?:AM|PM))', timing_str, re.IGNORECASE)
        if match:
            return (_fmt(match.group(1)), _fmt(match.group(2)))

        open_match = re.search(r'Opening time\s*-\s*(\d{1,2}[:.]\d{2}\s*(?:AM|PM))', timing_str, re.IGNORECASE)
        close_match = re.search(r'Closing time\s*-\s*(\d{1,2}[:.]\d{2}\s*(?:AM|PM))', timing_str, re.IGNORECASE)
        if open_match and close_match:
            return (
                _fmt(open_match.group(1)),
                _fmt(close_match.group(1))
            )

        return ("06:00 AM", "07:00 PM")

    def synchronize_duration_label(self, duration: float, custom_label: Optional[str] = None) -> str:
        """Ensure duration_label accurately represents numeric duration."""
        if custom_label and "-" in custom_label:
            return custom_label
        if duration <= 1.0:
            return "45 Min to 1.0 Hour"
        elif duration <= 1.5:
            return "1 to 1.5 Hours"
        elif duration <= 2.0:
            return "1.5 to 2 Hours"
        elif duration <= 2.5:
            return "2 to 2.5 Hours"
        elif duration <= 3.0:
            return "2.5 to 3.5 Hours"
        elif duration <= 4.0:
            return "3.5 to 4.5 Hours"
        else:
            return f"{duration} to {duration + 1.0} Hours"

    def verify_with_groq(self, place_dict: Dict[str, Any]) -> Optional[VerifiedPlaceData]:
        """Verify candidate place with Groq LLM + Search Evidence."""
        if not self.groq_verifier:
            return None

        evidence = self.search_scraper.gather_evidence(
            place_name=place_dict.get("name", ""),
            city=place_dict.get("city", "Bhubaneswar"),
            state=place_dict.get("state", "Odisha")
        )

        groq_res = self.groq_verifier.verify(place_dict, evidence)
        if not groq_res:
            return None

        if not groq_res.get("is_valid_place", True):
            logger.info(f"Groq marked '{place_dict.get('name')}' as NOT a physical place entity.")
            return None

        scores = groq_res.get("interest_scores", {})
        working_img = self.clean_image_url(place_dict.get("id", ""), place_dict.get("image_urls", []))
        verified_name = groq_res.get("verified_name") or self.sanitize_place_name(place_dict.get("name", ""))
        dur = float(groq_res.get("duration", 2.0))
        dur_label = self.synchronize_duration_label(dur, groq_res.get("duration_label"))

        return VerifiedPlaceData(
            id=place_dict.get("id"),
            name=verified_name,
            city=place_dict.get("city", "Bhubaneswar"),
            state=place_dict.get("state", "Odisha"),
            is_valid=True,
            validation_source="groq_llama70b",
            category=groq_res.get("category", place_dict.get("category", "Heritage & Archaeological Site")),
            sub_category=groq_res.get("sub_category", place_dict.get("sub_category", "Cultural Heritage")),
            short_description=groq_res.get("short_description") or place_dict.get("short_description", ""),
            full_description=place_dict.get("full_description", ""),
            opens_at=groq_res.get("opens_at", "06:00 AM"),
            closes_at=groq_res.get("closes_at", "07:00 PM"),
            duration=dur,
            duration_label=dur_label,
            popularity=float(groq_res.get("popularity", 4.5)),
            risk=groq_res.get("risk", "Low"),
            image_url=working_img,
            entry_fee=groq_res.get("entry_fee", "Free entry"),
            architecture=float(scores.get("architecture", 4.0)),
            history=float(scores.get("history", 4.0)),
            spiritual=float(scores.get("spiritual", 4.0)),
            nature=float(scores.get("nature", 3.0)),
            culture=float(scores.get("culture", 4.5)),
            festivals=[]
        )

    def verify_with_gemini(self, place_dict: Dict[str, Any]) -> Optional[VerifiedPlaceData]:
        """Verify scraped place using Google Gemini API."""
        if not self.gemini_api_key:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.gemini_model}:generateContent?key={self.gemini_api_key}"
        prompt = f"""
You are a cultural heritage and travel data verification expert for India tourism.
Analyze the following scraped place data and verify its factual accuracy:

Place Data:
- ID: {place_dict.get('id')}
- Name: {place_dict.get('name')}
- City: {place_dict.get('city')}
- State: {place_dict.get('state')}
- Scraped Description: {place_dict.get('short_description') or place_dict.get('full_description', '')[:300]}
- Scraped Hours: {place_dict.get('opening_hours')}

Respond ONLY with a valid JSON object strictly matching this schema:
{{
    "is_valid": true,
    "verified_name": "Accurate Name of Place",
    "category": "Temple & Sacred Sanctum / Heritage & Archaeological Site / Arts, Crafts & Museum / Nature & Scenic Sanctum / Monument & Fort",
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
    }}
}}

Note: If the place is a festival (e.g. Asokastami) or corrupted, set "is_valid": false.
"""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }

        try:
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=12)
            if resp.status_code == 200:
                result_json = resp.json()
                candidates = result_json.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    raw_text = candidates[0]["content"]["parts"][0]["text"]
                    data = json.loads(raw_text)

                    if not data.get("is_valid", True):
                        logger.warning(f"Gemini marked '{place_dict.get('name')}' as INVALID.")
                        return None

                    scores = data.get("interest_scores", {})
                    working_img = self.clean_image_url(place_dict.get("id", ""), place_dict.get("image_urls", []))
                    verified_name = data.get("verified_name") or self.sanitize_place_name(place_dict.get("name", ""))
                    dur = float(data.get("duration", 2.0))
                    dur_label = self.synchronize_duration_label(dur, data.get("duration_label"))

                    return VerifiedPlaceData(
                        id=place_dict.get("id"),
                        name=verified_name,
                        city=place_dict.get("city", "Bhubaneswar"),
                        state=place_dict.get("state", "Odisha"),
                        is_valid=True,
                        validation_source="gemini_flash",
                        category=data.get("category", place_dict.get("category")),
                        sub_category=data.get("sub_category", place_dict.get("sub_category")),
                        short_description=data.get("short_description") or place_dict.get("short_description"),
                        full_description=place_dict.get("full_description", ""),
                        opens_at=data.get("opens_at", "06:00 AM"),
                        closes_at=data.get("closes_at", "07:00 PM"),
                        duration=dur,
                        duration_label=dur_label,
                        popularity=float(data.get("popularity", 4.5)),
                        risk=data.get("risk", "Low"),
                        image_url=working_img,
                        entry_fee=data.get("entry_fee", "Free entry"),
                        architecture=float(scores.get("architecture", 4.0)),
                        history=float(scores.get("history", 4.0)),
                        spiritual=float(scores.get("spiritual", 4.0)),
                        nature=float(scores.get("nature", 3.0)),
                        culture=float(scores.get("culture", 4.5)),
                        festivals=[]
                    )
        except Exception as e:
            logger.warning(f"Gemini verification failed for '{place_dict.get('name')}': {e}")

        return None

    def verify_heuristic(self, place_dict: Dict[str, Any]) -> Optional[VerifiedPlaceData]:
        """
        Rule-based offline verification and enrichment fallback.
        Includes QA cleanup rules, ad copy sanitization, category fixes, and duration syncing.
        """
        place_id = place_dict.get("id", "")
        raw_name = place_dict.get("name", "")

        # 1. Filter out known corrupted records or festival-only records in places
        if place_id in ("asokastami", "ananta-vasudeva-temple") or "asokastami" in raw_name.lower():
            logger.info(f"Filtered out festival/corrupted record from places: {place_id} ({raw_name})")
            return None

        # 2. Sanitize place name
        clean_name = self.sanitize_place_name(raw_name)

        # 3. Timing parsing
        opens_at, closes_at = self.parse_timing_regex(place_dict.get("opening_hours", ""))

        # 4. Clean Scene7 Image URL
        image_url = self.clean_image_url(place_id, place_dict.get("image_urls", []))

        # 5. Determine category & interest scoring
        category = place_dict.get("category", "Heritage & Archaeological Site")
        sub_category = place_dict.get("sub_category", "Cultural Heritage")
        desc_full = (place_dict.get("short_description", "") + " " + place_dict.get("full_description", "")).lower()

        # Category Corrections for QA anomalies
        if "balighai" in clean_name.lower():
            category = "Nature & Scenic Sanctum"
            sub_category = "Beach & Coastal Heritage"
        elif "barabati stadium" in clean_name.lower():
            category = "Monument & Fort"
            sub_category = "Sports & Recreation Heritage"
        elif "chandaka" in clean_name.lower():
            category = "Nature & Scenic Sanctum"
            sub_category = "Wildlife Sanctuary & Reserve"
        elif "jajpur" in clean_name.lower():
            category = "Heritage & Archaeological Site"
            sub_category = "Ancient Kalinga Heritage"

        # Defaults
        arch, hist, spir, nat, cult = 4.0, 4.0, 3.5, 2.5, 4.5
        dur = float(place_dict.get("duration", 2.0))
        pop = 4.6
        risk = "Low"

        if "temple" in category.lower() or "sacred" in category.lower() or "shrine" in desc_full:
            spir, arch, hist, cult, nat = 5.0, 4.8, 4.8, 4.9, 2.0
            dur, pop = 2.0, 4.8
        elif "nature" in category.lower() or "sanctuary" in desc_full or "lake" in desc_full or "beach" in sub_category.lower():
            nat, spir, arch, hist, cult = 5.0, 2.5, 2.0, 3.0, 3.5
            dur = 3.5 if ("sanctuary" in desc_full or "lake" in desc_full) else 2.0
            pop = 4.7
            risk = "Moderate" if ("lake" in desc_full or "wildlife" in desc_full) else "Low"
        elif "museum" in category.lower() or "craft" in desc_full:
            cult, arch, hist, spir, nat = 5.0, 4.2, 4.7, 2.0, 2.5
            dur, pop = 2.5, 4.6
        elif "cave" in desc_full or "heritage" in category.lower() or "monument" in category.lower():
            arch, hist, spir, nat, cult = 4.9, 5.0, 4.0, 3.5, 4.7
            dur, pop = 2.5, 4.8
            risk = "Moderate" if "cave" in desc_full else "Low"

        # Explicit Duration Overrides from QA
        if "bhitarkanika" in clean_name.lower():
            dur = 4.0
        elif "atharnala" in clean_name.lower():
            dur = 1.5
        elif "konark" in clean_name.lower():
            dur = 2.5
        elif "barabati" in clean_name.lower() or "mahanadi barrage" in clean_name.lower():
            dur = 2.0

        dur_label = self.synchronize_duration_label(dur, place_dict.get("duration_label"))

        # Descriptions
        if "chandaka" in clean_name.lower():
            short_desc = "A wildlife reserve near Cuttack and Bhubaneswar known for resident elephant populations, nature trails, and rich biodiversity."
        elif "jajpur" in clean_name.lower():
            short_desc = "A historic heritage region known for ancient Kalinga temples, Buddhist archaeological complexes, and sacred ghats."
        else:
            short_desc = place_dict.get("short_description") or (place_dict.get("full_description", "")[:180] + "...")

        return VerifiedPlaceData(
            id=place_id,
            name=clean_name,
            city=place_dict.get("city", "Bhubaneswar"),
            state=place_dict.get("state", "Odisha"),
            is_valid=True,
            validation_source="heuristic",
            category=category,
            sub_category=sub_category,
            short_description=short_desc,
            full_description=place_dict.get("full_description", ""),
            opens_at=opens_at,
            closes_at=closes_at,
            duration=dur,
            duration_label=dur_label,
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
        Main multi-tier verification entrypoint:
        1. Groq LLM + Search Evidence (if GROQ_API_KEY configured)
        2. Gemini API (if GEMINI_API_KEY configured)
        3. Heuristic validation
        """
        # Tier 1: Groq LLM Fact-Checking
        if self.groq_verifier:
            logger.info(f"Verifying '{place_dict.get('name')}' with Groq Llama 3.3 70B & Web Evidence...")
            res = self.verify_with_groq(place_dict)
            if res:
                return res

        # Tier 2: Gemini API Fallback
        if self.gemini_api_key:
            logger.info(f"Verifying '{place_dict.get('name')}' with Gemini Flash...")
            res = self.verify_with_gemini(place_dict)
            if res:
                return res

        # Tier 3: Heuristic Rule-Based Verification
        return self.verify_heuristic(place_dict)
