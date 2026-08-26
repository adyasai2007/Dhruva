"""
Data normalizer for DHRUVA Cultural Scraper.
Transforms raw scraped content into structured, validated, and enriched models
aligned with DHRUVA's architectural specifications and database schemas.
"""

from __future__ import annotations
import re
import unicodedata
from typing import List, Dict, Tuple, Optional, Any
from scraper.models import RawScrapedPlace, NormalizedPlace, PlaceCompleteness


class PlaceNormalizer:
    """
    Standardizes raw scraped fields, classifies categories according to DHRUVA taxonomy,
    normalizes opening hours, and evaluates record completeness.
    """

    # Core DHRUVA Categories
    CAT_TEMPLE = "Temple & Sacred Sanctum"
    CAT_HERITAGE = "Heritage & Archaeological Site"
    CAT_ARTS_MUSEUM = "Arts, Crafts & Museum"
    CAT_NATURE = "Nature & Scenic Sanctum"
    CAT_BAZAR = "Cultural Quarter & Bazar"
    CAT_MONUMENT = "Monument & Fort"

    CATEGORY_KEYWORDS = {
        CAT_TEMPLE: [
            "temple", "mandir", "shrine", "sanctum", "deity", "shiva", "vishnu", "durga",
            "krishna", "jagannath", "shaivism", "vaishnavism", "aarti", "puja", "darshan",
            "ghat", "matha", "stupa", "monastery", "gurudwara", "mosque", "church", "yogini",
            "chausathi", "tantric", "tantra"
        ],
        CAT_HERITAGE: [
            "cave", "caves", "rock-cut", "ruins", "excavation", "archaeological", "inscription",
            "ancient", "historic site", "stone age", "stepwell", "heritage site", "gumpha"
        ],
        CAT_ARTS_MUSEUM: [
            "museum", "gallery", "craft", "crafts", "handloom", "textile", "pottery",
            "sculpture", "tribal art", "heritage village", "kala", "bhoomi", "exhibition"
        ],
        CAT_NATURE: [
            "lake", "sanctuary", "wildlife", "hill", "hills", "forest", "falls", "waterfall",
            "botanical", "park", "garden", "zoological", "river", "gorge", "wetland"
        ],
        CAT_BAZAR: [
            "bazar", "bazaar", "market", "shopping", "lane", "street", "haat", "crafts market"
        ],
        CAT_MONUMENT: [
            "palace", "fort", "memorial", "pillar", "gate", "tomb", "minar", "tower"
        ]
    }

    HISTORICAL_DYNASTIES = [
        "Somavamsi", "Ganga", "Kalinga", "Kharavela", "Maurya", "Ashoka", "Gupta",
        "Chola", "Pallava", "Chalukya", "Rashtrakuta", "Hoysala", "Vijayanagara",
        "Mughal", "Maratha", "Sultanate", "British Colonial", "Bhauma-Kara", "Sailodbhava"
    ]

    ARCHITECTURAL_STYLES = [
        "Kalinga Architecture", "Rekha Deula", "Pidha Deula", "Khakhara Deula",
        "Dravidian Architecture", "Nagara Style", "Vesara Style", "Rock-cut Cave",
        "Indo-Islamic", "Buddhist Architecture", "Jain Architecture", "Colonial"
    ]

    @staticmethod
    def clean_text(text: Optional[str]) -> str:
        """Sanitize text by removing HTML artifacts, zero-width chars, and normalizing whitespace."""
        if not text:
            return ""
        # Unicode normalization
        text = unicodedata.normalize("NFKC", text)
        # Replace non-breaking spaces and irregular whitespace
        text = text.replace("\xa0", " ").replace("​", "").replace("﻿", "")
        # Standardize quotes and dashes
        text = re.sub(r"[‘’‚‛]", "'", text)
        text = re.sub(r"[“”„‟]", '"', text)
        text = re.sub(r"[–—]", "-", text)
        # Collapse multiple spaces and trim
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        return text.strip()

    @classmethod
    def generate_slug(cls, name: str, city: str = "") -> str:
        """Create a clean, URL-safe and schema-compliant slug identifier."""
        cleaned = cls.clean_text(name).lower()
        cleaned = re.sub(r"[^a-z0-9\s-]", "", cleaned)
        slug = re.sub(r"[\s_]+", "-", cleaned).strip("-")
        return slug or "heritage-site"

    @classmethod
    def classify_category(cls, raw: RawScrapedPlace) -> Tuple[str, str]:
        """
        Determine core category and subcategory from headings, keywords, meta, and title.
        """
        combined_text = " ".join([
            raw.title,
            raw.place_name_raw,
            raw.meta_description,
            " ".join(raw.meta_keywords),
            " ".join(h.get("text", "") for h in raw.headings),
            " ".join(raw.paragraphs[:3])
        ]).lower()

        name_lower = raw.place_name_raw.lower()
        url_lower = raw.source_url.lower()

        scores: Dict[str, int] = {cat: 0 for cat in cls.CATEGORY_KEYWORDS}
        for cat, keywords in cls.CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw in name_lower:
                    scores[cat] += 15
                elif kw in url_lower:
                    scores[cat] += 10
                elif re.search(rf"\b{re.escape(kw)}\b", combined_text):
                    scores[cat] += 1

        primary_category = max(scores.items(), key=lambda x: x[1])[0]
        if scores[primary_category] == 0:
            primary_category = cls.CAT_HERITAGE

        # Subcategory determination
        sub_category = "Cultural Heritage"
        if primary_category == cls.CAT_TEMPLE:
            if "shiva" in combined_text or "shaiv" in combined_text:
                sub_category = "Shiva Temple & Sanctum"
            elif "vishnu" in combined_text or "vaishnav" in combined_text or "krishna" in combined_text:
                sub_category = "Vaishnava Temple"
            elif "shakti" in combined_text or "durga" in combined_text or "chandi" in combined_text or "yogini" in combined_text:
                sub_category = "Shakti Peetha / Devi Shrine"
            elif "kalinga" in combined_text:
                sub_category = "Kalinga Temple Architecture"
            else:
                sub_category = "Sacred Heritage Temple"
        elif primary_category == cls.CAT_HERITAGE:
            if "cave" in combined_text or "gumpha" in combined_text or "jain" in combined_text:
                sub_category = "Rock-cut Caves & Inscriptions"
            elif "archaeological" in combined_text or "ruins" in combined_text:
                sub_category = "Ancient Archaeological Monument"
            else:
                sub_category = "Historical Heritage Site"
        elif primary_category == cls.CAT_ARTS_MUSEUM:
            if "craft" in combined_text or "handloom" in combined_text:
                sub_category = "Traditional Craft & Artisan Heritage"
            elif "tribal" in combined_text:
                sub_category = "Tribal Art & Ethnographic Museum"
            else:
                sub_category = "State Cultural Museum"
        elif primary_category == cls.CAT_NATURE:
            if "wildlife" in combined_text or "sanctuary" in combined_text or "park" in combined_text:
                sub_category = "Wildlife Sanctum & Eco-Heritage"
            elif "lake" in combined_text or "river" in combined_text:
                sub_category = "Sacred Water Body & Wetlands"
            else:
                sub_category = "Scenic Landscape & Nature"

        return primary_category, sub_category

    @classmethod
    def normalize_opening_hours(cls, raw_timing: str, category: str) -> str:
        """Standardize opening hours string into readable format."""
        cleaned = cls.clean_text(raw_timing)
        if not cleaned:
            if category == cls.CAT_TEMPLE:
                return "06:00 AM - 08:00 PM (Daily; Aarti timings may vary)"
            elif category in (cls.CAT_HERITAGE, cls.CAT_NATURE):
                return "08:00 AM - 05:30 PM (Daily / Sunrise to Sunset)"
            elif category == cls.CAT_ARTS_MUSEUM:
                return "10:00 AM - 05:00 PM (Closed on Mondays and National Holidays)"
            return "09:00 AM - 06:00 PM (General Visiting Hours)"

        # Handle 'Opening time - 07:00 AM Closing time - 07:00 PM'
        open_match = re.search(r"opening\s*time\s*[-:]*\s*(\d{1,2}:\d{2}\s*[APMapm]*)", cleaned, re.IGNORECASE)
        close_match = re.search(r"closing\s*time\s*[-:]*\s*(\d{1,2}:\d{2}\s*[APMapm]*)", cleaned, re.IGNORECASE)

        if open_match and close_match:
            return f"{open_match.group(1).upper().strip()} - {close_match.group(1).upper().strip()}"

        # Standard range matches like '7:00 AM to 7:00 PM' or '06:00 - 18:00'
        range_match = re.search(r"(\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)\s*(?:to|-)\s*(\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)", cleaned)
        if range_match:
            return f"{range_match.group(1).upper().strip()} - {range_match.group(2).upper().strip()}"

        return cleaned

    @classmethod
    def infer_historical_period(cls, text: str) -> str:
        """Extract historical dynasty, architectural style, or century from narrative text."""
        findings: List[str] = []

        # Check for centuries
        century_match = re.search(r"(\d{1,2}(?:st|nd|rd|th))\s+century(?:\s+(CE|BCE|AD|BC))?", text, re.IGNORECASE)
        if century_match:
            c_num = century_match.group(1).lower()
            era = f" {century_match.group(2).upper()}" if century_match.group(2) else ""
            findings.append(f"{c_num} Century{era}")

        # Check for dynasties
        for dynasty in cls.HISTORICAL_DYNASTIES:
            if re.search(rf"\b{re.escape(dynasty)}\b", text, re.IGNORECASE):
                findings.append(f"{dynasty} Dynasty")
                break

        # Check for architectural styles
        for style in cls.ARCHITECTURAL_STYLES:
            if re.search(rf"\b{re.escape(style)}\b", text, re.IGNORECASE):
                findings.append(style)
                break

        if findings:
            return " • ".join(findings)
        return "Ancient Heritage Period"

    @classmethod
    def generate_accessibility_notes(cls, category: str, name: str) -> str:
        """Synthesize mindful accessibility guidance for senior travelers and adults."""
        if category == cls.CAT_TEMPLE:
            return (
                "Footwear removal mandatory at the temple entrance. Smooth stone flooring inside; "
                "surfaces may get warm under direct afternoon sun. Moderate step climbing required "
                "to access sanctum sanctorum. Wheelchair assistance available at main outer gates."
            )
        elif category == cls.CAT_HERITAGE:
            return (
                "Uneven natural stone pathways and rock-cut flight of stairs. Sturdy walking footwear "
                "and walking cane recommended for senior visitors. Shaded pavilions available for rest."
            )
        elif category == cls.CAT_ARTS_MUSEUM:
            return (
                "Level paved walkways and wheelchair ramps throughout exhibition galleries. "
                "Air-conditioned indoor halls with ample seated rest zones and accessible restrooms."
            )
        elif category == cls.CAT_NATURE:
            return (
                "Paved trails with occasional unpaved terrain. Battery-operated safari vehicles "
                "and shaded sit-outs available for comfortable elderly touring."
            )
        return (
            "Standard paved access. Early morning visits recommended to avoid crowds and heat."
        )

    @classmethod
    def generate_best_time_and_duration(cls, category: str) -> Tuple[str, str]:
        """Provide recommended visit timing and duration according to category."""
        if category == cls.CAT_TEMPLE:
            return (
                "Early Morning (06:30 AM - 09:00 AM) or Evening Aarti (06:00 PM - 07:30 PM)",
                "1.5 to 2 Hours"
            )
        elif category == cls.CAT_HERITAGE:
            return (
                "Morning (07:30 AM - 10:30 AM) or Late Afternoon (03:30 PM - 05:30 PM)",
                "2 to 3 Hours"
            )
        elif category == cls.CAT_ARTS_MUSEUM:
            return (
                "Mid-Morning (10:30 AM - 01:30 PM) or Afternoon (02:30 PM - 05:00 PM)",
                "2 to 2.5 Hours"
            )
        elif category == cls.CAT_NATURE:
            return (
                "Early Morning (07:00 AM - 10:00 AM)",
                "2.5 to 3.5 Hours"
            )
        return ("Morning (09:00 AM - 12:00 PM)", "1 to 2 Hours")

    @classmethod
    def extract_festivals(cls, celebrations_raw: str, narrative_text: str) -> List[str]:
        """Extract list of celebrated festivals from celebration section or narrative."""
        known_festivals = [
            "Mahashivaratri", "Ashokashtami", "Chandan Yatra", "Rath Yatra", "Durga Puja",
            "Makar Sankranti", "Kalinga Mahotsav", "Mukteswar Dance Festival",
            "Rajarani Music Festival", "Dhauli-Kalinga Mahotsav", "Tusu Festival",
            "Diwali", "Janmashtami", "Navratri", "Shravan Month Pilgrimage"
        ]

        combined = f"{celebrations_raw} {narrative_text}"
        found = []
        for fest in known_festivals:
            if re.search(rf"\b{re.escape(fest)}\b", combined, re.IGNORECASE):
                found.append(fest)

        if not found and celebrations_raw:
            # Clean and split raw string if comma-separated
            parts = [cls.clean_text(p) for p in re.split(r"[,;•\n]", celebrations_raw)]
            found = [p for p in parts if len(p) > 2 and len(p) < 40]

        return found[:5]

    @classmethod
    def normalize(cls, raw: RawScrapedPlace) -> NormalizedPlace:
        """
        Transform a RawScrapedPlace instance into a fully normalized, validated NormalizedPlace.
        """
        # Determine name
        name = cls.clean_text(raw.place_name_raw)
        if not name or name.lower() in ("create an account", "trending searches", "plan your trip", "share"):
            # Fall back to title cleaning
            name_candidate = raw.title.split("|")[0].strip()
            name_candidate = re.sub(r"^(?:Visit the|Experience the|Explore the|Discover)\s+", "", name_candidate, flags=re.IGNORECASE)
            name_candidate = re.sub(r"\s+in\s+.*$", "", name_candidate, flags=re.IGNORECASE)
            name = cls.clean_text(name_candidate)

        city = cls.clean_text(raw.city).title() or "Bhubaneswar"
        state = cls.clean_text(raw.state).title() or "Odisha"
        slug_id = cls.generate_slug(name, city)

        # Categorize
        category, sub_category = cls.classify_category(raw)

        # Descriptions & narratives
        short_desc = cls.clean_text(raw.meta_description)
        narrative_parts = [cls.clean_text(p) for p in raw.paragraphs if len(p) > 30]

        # Filter out noisy boilerplate paragraphs
        filtered_narrative = []
        boilerplate_keywords = ["cookie consent", "download app", "sign up", "user name", "my profile", "logout", "follow us", "all rights reserved"]
        for p in narrative_parts:
            if not any(bk in p.lower() for bk in boilerplate_keywords):
                filtered_narrative.append(p)

        full_description = "\n\n".join(filtered_narrative[:4]) if filtered_narrative else short_desc

        # Cultural significance
        significance_parts = []
        for h in raw.headings:
            htext = cls.clean_text(h.get("text", ""))
            if htext and not any(bk in htext.lower() for bk in ["nearest airport", "railway station", "timings", "follow us", "download app", "share"]):
                significance_parts.append(htext)

        cultural_significance = (
            " • ".join(significance_parts[:3]) + (". " + filtered_narrative[0] if filtered_narrative else "")
            if significance_parts else short_desc
        )

        # Historical period
        all_narrative_text = " ".join([raw.title, short_desc, full_description, cultural_significance])
        historical_period = cls.infer_historical_period(all_narrative_text)

        # Timings & Hours
        opening_hours = cls.normalize_opening_hours(raw.timing_raw, category)

        # Best time & Duration
        best_time, duration = cls.generate_best_time_and_duration(category)

        # Accessibility
        accessibility_notes = cls.generate_accessibility_notes(category, name)

        # Entry Fee
        entry_fee = "Free entry (Donations welcome; special darshan queue fees may apply)" if category == cls.CAT_TEMPLE else "Entry fee applicable; verify on-site"

        # Festivals
        festivals = cls.extract_festivals(raw.celebrations_raw, all_narrative_text)

        # Transit
        transit_info = {}
        if raw.transit_raw.get("airport"):
            transit_info["nearest_airport"] = cls.clean_text(raw.transit_raw["airport"])
        else:
            transit_info["nearest_airport"] = "Biju Patnaik International Airport (BBI), Bhubaneswar"

        if raw.transit_raw.get("railway"):
            transit_info["nearest_railway"] = cls.clean_text(raw.transit_raw["railway"])
        else:
            transit_info["nearest_railway"] = "Bhubaneswar Railway Station (BBS)"

        # Image URLs
        images = list(dict.fromkeys([img for img in raw.image_urls if img.startswith("http")]))
        if not images and raw.og_image:
            images.append(raw.og_image)

        return NormalizedPlace(
            id=slug_id,
            name=name,
            city=city,
            state=state,
            category=category,
            sub_category=sub_category,
            short_description=short_desc,
            full_description=full_description,
            cultural_significance=cultural_significance,
            historical_period=historical_period,
            opening_hours=opening_hours,
            entry_fee=entry_fee,
            best_time_of_day=best_time,
            recommended_duration=duration,
            accessibility_notes=accessibility_notes,
            festivals=festivals,
            nearest_transit=transit_info,
            image_urls=images[:5],
            latitude=None,
            longitude=None,
            source_url=raw.source_url,
            scraped_at_utc=raw.scraped_at_utc
        )

    @staticmethod
    def evaluate_completeness(place: NormalizedPlace) -> PlaceCompleteness:
        """
        Assess completeness across all critical fields for a normalized place record.
        """
        critical_fields = [
            ("name", bool(place.name and len(place.name) > 2)),
            ("city", bool(place.city)),
            ("state", bool(place.state)),
            ("category", bool(place.category)),
            ("sub_category", bool(place.sub_category)),
            ("short_description", bool(place.short_description and len(place.short_description) > 15)),
            ("full_description", bool(place.full_description and len(place.full_description) > 30)),
            ("cultural_significance", bool(place.cultural_significance and len(place.cultural_significance) > 15)),
            ("historical_period", bool(place.historical_period)),
            ("opening_hours", bool(place.opening_hours)),
            ("entry_fee", bool(place.entry_fee)),
            ("best_time_of_day", bool(place.best_time_of_day)),
            ("recommended_duration", bool(place.recommended_duration)),
            ("accessibility_notes", bool(place.accessibility_notes)),
            ("festivals", bool(len(place.festivals) > 0)),
            ("nearest_transit", bool(len(place.nearest_transit) > 0)),
            ("image_urls", bool(len(place.image_urls) > 0)),
            ("source_url", bool(place.source_url)),
        ]

        total = len(critical_fields)
        filled = sum(1 for _, is_filled in critical_fields if is_filled)
        missing = [fname for fname, is_filled in critical_fields if not is_filled]
        score = round((filled / total) * 100.0, 2)

        return PlaceCompleteness(
            place_id=place.id,
            place_name=place.name,
            total_fields=total,
            filled_fields=filled,
            missing_fields=missing,
            completeness_score=score
        )
