"""
Data exporter for DHRUVA Cultural Scraper.
Outputs scraped facts to JSON, CSV, missing field audit reports, and execution summaries.
"""

from __future__ import annotations
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from scraper.models import RawScrapedPlace, NormalizedPlace, ScrapingReport, PlaceCompleteness

logger = logging.getLogger("dhruva.scraper.exporter")


class DataExporter:
    """Handles structured persistence of raw, normalized, and analytical datasets."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_raw_json(self, raw_places: List[RawScrapedPlace], filename: str = "raw_places.json") -> Path:
        """Write raw scraped places to JSON."""
        file_path = self.output_dir / filename
        data = [p.to_dict() for p in raw_places]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Exported {len(raw_places)} raw records to {file_path}")
        return file_path

    def export_normalized_json(self, places: List[NormalizedPlace], filename: str = "normalized_places.json") -> Path:
        """Write normalized places to JSON matching DHRUVA schema."""
        file_path = self.output_dir / filename
        data = [p.to_dict() for p in places]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Exported {len(places)} normalized records to {file_path}")
        return file_path

    def export_csv(self, places: List[NormalizedPlace], filename: str = "places.csv") -> Path:
        """Export normalized places to clean tabular CSV."""
        file_path = self.output_dir / filename
        if not places:
            logger.warning("No places to export to CSV.")
            return file_path

        fieldnames = [
            "id", "name", "city", "state", "category", "sub_category",
            "short_description", "cultural_significance", "historical_period",
            "opening_hours", "entry_fee", "best_time_of_day", "recommended_duration",
            "accessibility_notes", "festivals", "nearest_airport", "nearest_railway",
            "image_url_primary", "source_url", "scraped_at_utc"
        ]

        with open(file_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for p in places:
                row = {
                    "id": p.id,
                    "name": p.name,
                    "city": p.city,
                    "state": p.state,
                    "category": p.category,
                    "sub_category": p.sub_category,
                    "short_description": p.short_description,
                    "cultural_significance": p.cultural_significance,
                    "historical_period": p.historical_period,
                    "opening_hours": p.opening_hours,
                    "entry_fee": p.entry_fee,
                    "best_time_of_day": p.best_time_of_day,
                    "recommended_duration": p.recommended_duration,
                    "accessibility_notes": p.accessibility_notes,
                    "festivals": "; ".join(p.festivals),
                    "nearest_airport": p.nearest_transit.get("nearest_airport", ""),
                    "nearest_railway": p.nearest_transit.get("nearest_railway", ""),
                    "image_url_primary": p.image_urls[0] if p.image_urls else "",
                    "source_url": p.source_url,
                    "scraped_at_utc": p.scraped_at_utc
                }
                writer.writerow(row)

        logger.info(f"Exported CSV table to {file_path}")
        return file_path

    def export_missing_fields_report(
        self,
        completeness_list: List[PlaceCompleteness],
        json_filename: str = "missing_fields_report.json",
        md_filename: str = "missing_fields_report.md"
    ) -> Tuple[Path, Path]:
        """Generate JSON and Markdown report analyzing missing fields and completeness."""
        json_path = self.output_dir / json_filename
        md_path = self.output_dir / md_filename

        # JSON export
        data = [c.to_dict() for c in completeness_list]
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Markdown report generation
        total_records = len(completeness_list)
        avg_score = (
            sum(c.completeness_score for c in completeness_list) / total_records
            if total_records > 0 else 0.0
        )

        # Aggregate missing field frequencies
        field_miss_count: Dict[str, int] = {}
        for c in completeness_list:
            for field in c.missing_fields:
                field_miss_count[field] = field_miss_count.get(field, 0) + 1

        md_lines = [
            "# DHRUVA Cultural Data Completeness & Missing Fields Audit",
            "",
            f"**Total Records Analyzed:** {total_records}",
            f"**Average Completeness Score:** {avg_score:.2f}%",
            "",
            "## Field Completeness Breakdown",
            "",
            "| Field Name | Present Count | Missing Count | Completeness Rate |",
            "| :--- | :--- | :--- | :--- |"
        ]

        # Standard field list
        standard_fields = [
            "name", "city", "state", "category", "sub_category",
            "short_description", "full_description", "cultural_significance",
            "historical_period", "opening_hours", "entry_fee", "best_time_of_day",
            "recommended_duration", "accessibility_notes", "festivals",
            "nearest_transit", "image_urls", "source_url"
        ]

        for fname in standard_fields:
            miss = field_miss_count.get(fname, 0)
            pres = total_records - miss
            rate = (pres / total_records * 100.0) if total_records > 0 else 0.0
            md_lines.append(f"| `{fname}` | {pres}/{total_records} | {miss} | {rate:.1f}% |")

        md_lines.extend([
            "",
            "## Per-Place Completeness Summary",
            "",
            "| Place ID | Place Name | Score | Missing Fields |",
            "| :--- | :--- | :--- | :--- |"
        ])

        for c in completeness_list:
            missing_str = ", ".join(f"`{m}`" for m in c.missing_fields) if c.missing_fields else "None (100% complete)"
            md_lines.append(f"| `{c.place_id}` | {c.place_name} | {c.completeness_score}% | {missing_str} |")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines) + "\n")

        logger.info(f"Exported missing fields audit to {json_path} and {md_path}")
        return json_path, md_path

    def export_scrape_report(self, report: ScrapingReport, filename: str = "scraping_report.json") -> Path:
        """Write execution run report with timestamp and metrics."""
        file_path = self.output_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info(f"Exported scrape execution report to {file_path}")
        return file_path
