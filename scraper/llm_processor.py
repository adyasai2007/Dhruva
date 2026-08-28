"""
LLM Preprocessing, Extraction & Cultural Classification Engine for DHRUVA.
Leverages Groq API (GPT-OSS-120B) combined with SerpApi Web Search Evidence
to extract grounded factual heritage data, evaluate tourist visitability, and classify 5D interest profiles.
"""

from __future__ import annotations
import json
import logging
import os
import re
import time
import urllib.parse
import urllib.request
from typing import Dict, Any, Optional, List

logger = logging.getLogger("dhruva.llm")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """You are an expert cultural heritage historian and data ingestion assistant for DHRUVA, an Indian cultural and heritage travel platform.

Your task is to analyze factual Wikipedia article content and authoritative Web Search Evidence (from official tourism/ASI sources) for an attraction in Odisha, India, and produce a clean, structured JSON object adhering to our strict schema.

CRITICAL RULES:
1. STRICT FACTUAL GROUNDING: Extract ONLY facts supported by the provided text and search evidence. Never hallucinate or invent timings, fees, or features.
2. RELEVANCE FILTER: Evaluate whether the entity is:
   a) Culturally or historically significant (temple, monument, sanctuary, museum, heritage site, craft village).
   b) Publicly visitable / relevant for cultural travelers (NOT a private administrative office, commercial mall, or generic neighborhood).
   If it is NOT visitable or NOT culturally significant, set "is_included": false.
3. OPENING HOURS & ENTRY FEES:
   - Extract factual opening and closing times from the Wikipedia text or Web Search Evidence (e.g. "06:00 AM" to "06:00 PM" for ASI sunrise-to-sunset monuments, or "10:00 AM" to "05:00 PM" with Monday closed for museums).
   - If the site is closed on certain days (e.g., museums closed on Mondays), list them in "closed_days": ["Monday"].
   - Extract verified ticket entry fees (e.g., "₹25 for Indians, ₹300 for Foreigners (ASI)", "Free entry").
4. CULTURAL INTEREST DIMENSIONS (Score each dimension realistically on a 0.0 to 5.0 scale):
   - architecture: Sculptural quality, Kalinga deula architecture, stone carvings, masonry, design.
   - history: Antiquity, dynasty origins (Ganga, Somavamshi, Gajapati, Mauryan/Ashokan), archaeological value.
   - spiritual: Active worship, deity darshan, pilgrimage sanctity (Sri Jagannath, Shaiva, Shakta, Buddhist, Jain).
   - nature: Eco-systems, sacred water bodies, ancient trees, landscape setting.
   - culture: Living festivals, rituals, classical arts, pattachitra crafts, culinary heritage.
5. TAXONOMY:
   - category: Choose one of ["Temple & Sacred Sanctum", "Heritage & Sacred Sanctum", "Heritage & Archaeological Site", "Arts, Crafts & Museum", "Monument & Fort", "Nature & Scenic Sanctum"]
   - risk: Exertion level ["Low", "Moderate", "High"]
   - duration: Realistic visit duration in hours (e.g., 1.5, 2.0, 2.5, 3.0, 3.5)
   - duration_label: e.g. "1.5 to 2.5 Hours", "2 to 3 Hours", "3 to 4 Hours"
6. JSON ONLY: Respond with a valid JSON object matching the target structure.

TARGET JSON STRUCTURE:
{
  "is_included": true,
  "rejection_reason": null,
  "name": "Exact Name",
  "category": "Temple & Sacred Sanctum",
  "sub_category": "Kalinga Architecture Shiva Temple",
  "description": "2-3 sentence culturally rich summary based only on article and search evidence.",
  "duration": 2.0,
  "duration_label": "1.5 to 2.5 Hours",
  "risk": "Low",
  "entry_fee": "Free entry (Donations welcome)",
  "opening_hours": {
    "opens_at": "06:00 AM",
    "closes_at": "08:30 PM",
    "closed_days": []
  },
  "interests": {
    "architecture": 4.9,
    "history": 4.8,
    "spiritual": 5.0,
    "nature": 2.5,
    "culture": 4.8
  }
}
"""


class LLMProcessor:
    """LLM extractor and classifier using Groq API with SerpApi web search evidence."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.model = model or os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    def process_article(
        self,
        place_title: str,
        city_name: str,
        article_text: str,
        metadata: Optional[Dict[str, Any]] = None,
        search_evidence: Optional[List[Dict[str, str]]] = None
    ) -> Optional[Dict[str, Any]]:
        """Process Wikipedia article & SerpApi search evidence through Groq LLM to generate structured schema record."""
        api_key = os.getenv("GROQ_API_KEY", "") or self.api_key
        if not api_key or api_key.startswith("your_"):
            logger.warning("No valid GROQ_API_KEY found. Using heuristic fallback processor.")
            return self._heuristic_fallback(place_title, city_name, article_text, metadata, search_evidence)

        # Format SerpApi search evidence
        search_block = ""
        if search_evidence:
            search_block = "\nAuthoritative Web Search Evidence (SerpApi):\n"
            for i, item in enumerate(search_evidence[:4], 1):
                search_block += f"{i}. {item.get('title')} ({item.get('link')})\n   {item.get('snippet')}\n"

        prompt = f"""Target City: {city_name}, Odisha
Place Title: {place_title}

Wikipedia Article Content:
{article_text[:5000]}
{search_block}
"""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }

        req = urllib.request.Request(
            GROQ_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "DhruvaCulturalTravelPlanner/1.0"
            }
        )

        max_retries = 3
        for attempt in range(max_retries):
            try:
                time.sleep(1.0)  # Safe request pacing
                with urllib.request.urlopen(req, timeout=30) as response:
                    if response.status == 200:
                        res_body = json.loads(response.read().decode("utf-8"))
                        content = res_body["choices"][0]["message"]["content"]
                        parsed = json.loads(content)
                        return parsed
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    wait_time = (attempt + 1) * 3.0
                    logger.warning(f"Groq API rate limit (429) on {place_title}. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Groq API HTTP error {e.code} for {place_title}: {e}")
                    break
            except Exception as e:
                logger.error(f"Groq API error for {place_title}: {e}")
                break

        return self._heuristic_fallback(place_title, city_name, article_text, metadata, search_evidence)

    def _heuristic_fallback(
        self,
        place_title: str,
        city_name: str,
        article_text: str,
        metadata: Optional[Dict[str, Any]] = None,
        search_evidence: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Deterministic domain-accurate fallback when Groq API key is rate-limited."""
        t_low = place_title.lower()
        text_clean = re.sub(r"==+[^=]+==+", " ", article_text or "")
        text_clean = re.sub(r"\s+", " ", text_clean).strip()
        body_low = text_clean.lower()

        # Archaeology & Monuments
        if "rajarani" in t_low:
            cat = "Heritage & Archaeological Site"
            sub_cat = "11th-Century Non-Functioning Sandstone Temple Monument (ASI)"
            scores = {"architecture": 4.9, "history": 4.8, "spiritual": 2.5, "nature": 2.5, "culture": 4.8}
            dur, dur_label = 2.0, "1.5 to 2.5 Hours"
            fee = "₹25 for Indians, ₹300 for Foreigners (ASI ticketed)"
            hours = {"opens_at": "06:00 AM", "closes_at": "06:00 PM", "closed_days": []}
            risk = "Low"
        elif "konark" in t_low or "sun temple" in t_low:
            cat = "Heritage & Sacred Sanctum"
            sub_cat = "UNESCO World Heritage Sun Temple"
            scores = {"architecture": 5.0, "history": 5.0, "spiritual": 4.8, "nature": 3.0, "culture": 5.0}
            dur, dur_label = 2.5, "2 to 2.5 Hours"
            fee = "₹40 for Indians, ₹600 for Foreigners (ASI ticketed)"
            hours = {"opens_at": "06:00 AM", "closes_at": "06:00 PM", "closed_days": []}
            risk = "Low"
        elif "dhauli" in t_low:
            cat = "Heritage & Sacred Sanctum"
            sub_cat = "Ashokan Rock Edicts & Buddhist Peace Pagoda"
            scores = {"architecture": 4.8, "history": 5.0, "spiritual": 4.7, "nature": 4.0, "culture": 4.8}
            dur, dur_label = 2.0, "1.5 to 2.5 Hours"
            fee = "Free entry (Parking/light-and-sound show fees separate)"
            hours = {"opens_at": "06:00 AM", "closes_at": "07:00 PM", "closed_days": []}
            risk = "Low"
        elif any(w in t_low for w in ["cave", "khandagiri", "udayagiri", "sisupalgarh", "atharnala"]):
            cat = "Heritage & Archaeological Site"
            sub_cat = "2nd-Century BCE Rock-Cut Jain Caves" if "cave" in t_low else "Ancient Kalinga Monument"
            scores = {"architecture": 4.8, "history": 5.0, "spiritual": 3.8, "nature": 3.5, "culture": 4.7}
            dur, dur_label = 2.5, "2 to 3 Hours"
            fee = "₹25 for Indians, ₹300 for Foreigners (ASI)" if "cave" in t_low else "Free entry (Open monument)"
            hours = {"opens_at": "08:00 AM", "closes_at": "05:00 PM", "closed_days": []}
            risk = "Moderate"
        elif any(w in t_low for w in ["museum", "craft", "raghurajpur", "maritime", "netaji"]):
            cat = "Arts, Crafts & Museum"
            sub_cat = "Traditional Handloom & Crafts Village" if "raghurajpur" in t_low else "Heritage & Archaeology Museum"
            scores = {"architecture": 4.3, "history": 4.7, "spiritual": 2.5, "nature": 2.5, "culture": 5.0}
            dur, dur_label = 2.5, "2 to 3 Hours"
            fee = "₹10 to ₹50 for Indian Visitors" if "museum" in t_low else "Free entry to artisan workshops"
            hours = {"opens_at": "10:00 AM", "closes_at": "05:00 PM", "closed_days": ["Monday"]} if "museum" in t_low else {"opens_at": "08:00 AM", "closes_at": "07:00 PM", "closed_days": []}
            risk = "Low"
        elif "fort" in t_low:
            cat = "Monument & Fort"
            sub_cat = "10th-Century Somavamshi Fortification Ruins"
            scores = {"architecture": 4.7, "history": 4.9, "spiritual": 2.5, "nature": 3.0, "culture": 4.6}
            dur, dur_label = 2.0, "1.5 to 2.5 Hours"
            fee = "Free entry (ASI protected monument)"
            hours = {"opens_at": "06:00 AM", "closes_at": "06:00 PM", "closed_days": []}
            risk = "Low"
        else:
            cat = "Temple & Sacred Sanctum"
            sub_cat = "Kalinga Architecture Sacred Sanctum"
            scores = {"architecture": 4.9, "history": 4.9, "spiritual": 5.0, "nature": 2.5, "culture": 4.9}
            dur, dur_label = 2.0, "1.5 to 2.5 Hours"
            fee = "Free entry (Donations welcome; special darshan queue fees may apply)"
            hours = {"opens_at": "06:00 AM", "closes_at": "08:30 PM", "closed_days": []}
            risk = "Low"

        sentences = [s.strip() for s in text_clean.split(". ") if len(s.strip()) > 20]
        desc = ". ".join(sentences[:2]) + ("." if sentences and not sentences[0].endswith(".") else "")
        if not desc:
            desc = f"{place_title} is an esteemed cultural and heritage landmark located in {city_name}, Odisha."

        return {
            "is_included": True,
            "rejection_reason": None,
            "name": place_title,
            "category": cat,
            "sub_category": sub_cat,
            "description": desc,
            "duration": dur,
            "duration_label": dur_label,
            "risk": risk,
            "entry_fee": fee,
            "opening_hours": hours,
            "interests": scores,
        }


llm_processor = LLMProcessor()
