"""
Incredible India Tourism Scraper Orchestrator.
Coordinates respectful crawling, link discovery, parsing, normalization,
data export, and analytical auditing for destination cultural places.
"""

from __future__ import annotations
import logging
import time
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin

from scraper.common.config import ScraperConfig
from scraper.common.crawler import PoliteCrawler
from scraper.common.normalizer import PlaceNormalizer
from scraper.common.exporter import DataExporter
from scraper.incredible_india.parser import IncredibleIndiaParser
from scraper.models import RawScrapedPlace, NormalizedPlace, ScrapingReport, PlaceCompleteness

logger = logging.getLogger("dhruva.scraper.incredible_india.scraper")


class IncredibleIndiaScraper:
    """
    High-level orchestrator for scraping cultural place data from Incredible India.
    """

    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig()
        self.crawler = PoliteCrawler(self.config)
        self.exporter = DataExporter(self.config.output_dir)

    def scrape_destination(
        self,
        city: str = "bhubaneswar",
        state: str = "odisha",
        start_url: Optional[str] = None,
        max_pages: Optional[int] = None
    ) -> ScrapingReport:
        """
        Execute an end-to-end scrape for a designated city destination.
        """
        start_time = time.time()
        start_time_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        limit = max_pages if max_pages is not None else self.config.max_pages

        city_slug = city.lower().replace(" ", "-")
        state_slug = state.lower().replace(" ", "-")

        if not start_url:
            start_url = f"{self.config.base_url}/en/{state_slug}/{city_slug}"

        logger.info(f"Starting scrape for {city.title()}, {state.title()} (max_pages={limit})")
        logger.info(f"Hub URL: {start_url}")

        raw_places: List[RawScrapedPlace] = []
        normalized_places: List[NormalizedPlace] = []
        completeness_records: List[PlaceCompleteness] = []
        error_details: List[Dict[str, str]] = []

        # 1. Fetch Hub Page
        hub_html = self.crawler.fetch_page(start_url)
        discovered_urls: List[str] = []

        if hub_html:
            discovered_urls = IncredibleIndiaParser.extract_attraction_links(
                html_content=hub_html,
                base_url=self.config.base_url,
                city=city,
                state=state
            )
        else:
            logger.warning(f"Could not fetch hub page: {start_url}")
            error_details.append({
                "url": start_url,
                "error": self.crawler.failed_urls.get(start_url, "Failed to load hub page")
            })

        # Fallback discovery seeds if hub page yields few links
        if len(discovered_urls) < limit:
            seed_attractions = [
                f"{self.config.base_url}/en/{state_slug}/{city_slug}/lingaraj-temple",
                f"{self.config.base_url}/en/{state_slug}/{city_slug}/mukteswara-temple",
                f"{self.config.base_url}/en/{state_slug}/{city_slug}/rajarani-temple",
                f"{self.config.base_url}/en/{state_slug}/{city_slug}/khandagiri-and-udayagiri-caves",
                f"{self.config.base_url}/en/{state_slug}/{city_slug}/kala-bhoomi-odisha-crafts-museum",
                f"{self.config.base_url}/en/{state_slug}/{city_slug}/ananta-vasudeva-temple",
                f"{self.config.base_url}/en/{state_slug}/{city_slug}/museum-of-tribal-arts-and-artifacts",
                f"{self.config.base_url}/en/{state_slug}/{city_slug}/dhauligiri-hills",
                f"{self.config.base_url}/en/{state_slug}/{city_slug}/nandankanan",
                f"{self.config.base_url}/en/{state_slug}/{city_slug}/pathani-samanta-planetarium"
            ]
            for seed in seed_attractions:
                if seed not in discovered_urls:
                    discovered_urls.append(seed)

        logger.info(f"Targeting {min(len(discovered_urls), limit)} place URLs out of {len(discovered_urls)} discovered.")

        # 2. Sequential crawl of place pages
        pages_crawled = 0
        for place_url in discovered_urls:
            if pages_crawled >= limit:
                logger.info(f"Reached page limit ({limit}). Concluding crawl.")
                break

            logger.info(f"Processing place [{pages_crawled + 1}/{limit}]: {place_url}")
            page_html = self.crawler.fetch_page(place_url)

            if not page_html:
                err_reason = self.crawler.failed_urls.get(place_url, "Unknown network or robots failure")
                logger.warning(f"Failed to fetch {place_url}: {err_reason}")
                error_details.append({"url": place_url, "error": err_reason})
                continue

            try:
                # Parse raw place facts
                raw_place = IncredibleIndiaParser.parse_place_page(page_html, place_url)
                raw_places.append(raw_place)

                # Normalize place model
                norm_place = PlaceNormalizer.normalize(raw_place)
                normalized_places.append(norm_place)

                # Evaluate field completeness
                completeness = PlaceNormalizer.evaluate_completeness(norm_place)
                completeness_records.append(completeness)

                pages_crawled += 1
                logger.info(
                    f"✓ Parsed & normalized '{norm_place.name}' (Category: {norm_place.category}, "
                    f"Completeness: {completeness.completeness_score}%)"
                )

                # Checkpoint progress
                self.crawler.save_checkpoint({
                    "city": city,
                    "pages_crawled": pages_crawled,
                    "places_count": len(normalized_places)
                })

            except Exception as e:
                logger.error(f"Error parsing place from {place_url}: {e}", exc_info=True)
                error_details.append({"url": place_url, "error": str(e)})

        end_time = time.time()
        end_time_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        duration = round(end_time - start_time, 2)

        # 3. Compute aggregate summary metrics
        total_normalized = len(normalized_places)
        avg_score = (
            sum(c.completeness_score for c in completeness_records) / total_normalized
            if total_normalized > 0 else 0.0
        )

        # Compute field-by-field completeness rates
        field_names = [
            "name", "city", "state", "category", "sub_category",
            "short_description", "full_description", "cultural_significance",
            "historical_period", "opening_hours", "entry_fee", "best_time_of_day",
            "recommended_duration", "accessibility_notes", "festivals",
            "nearest_transit", "image_urls", "source_url"
        ]
        field_summary: Dict[str, float] = {}
        for fname in field_names:
            present_count = sum(1 for c in completeness_records if fname not in c.missing_fields)
            field_summary[fname] = round((present_count / total_normalized * 100.0) if total_normalized > 0 else 0.0, 1)

        report = ScrapingReport(
            target_source="Incredible India Tourism Portal",
            start_url=start_url,
            city=city.title(),
            state=state.title(),
            total_pages_discovered=len(discovered_urls),
            total_pages_crawled=pages_crawled,
            total_places_normalized=total_normalized,
            errors_count=len(error_details),
            error_details=error_details,
            start_time_utc=start_time_utc,
            end_time_utc=end_time_utc,
            duration_seconds=duration,
            average_completeness=round(avg_score, 2),
            field_completeness_summary=field_summary,
            completeness_per_place=completeness_records
        )

        # 4. Export all artifacts
        self.exporter.export_raw_json(raw_places)
        self.exporter.export_normalized_json(normalized_places)
        self.exporter.export_csv(normalized_places)
        self.exporter.export_missing_fields_report(completeness_records)
        self.exporter.export_scrape_report(report)

        logger.info(
            f"Scraping run completed in {duration}s. "
            f"Successfully normalized {total_normalized} places (Avg completeness: {avg_score:.2f}%)."
        )
        return report

    def scrape_multiple_destinations(
        self,
        destinations: List[Dict[str, str]],
        max_pages_per_destination: Optional[int] = None
    ) -> ScrapingReport:
        """
        Execute an aggregated multi-city crawl across multiple destinations.
        """
        start_time = time.time()
        start_time_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        limit = max_pages_per_destination if max_pages_per_destination is not None else self.config.max_pages

        all_raw_places: List[RawScrapedPlace] = []
        all_normalized_places: List[NormalizedPlace] = []
        all_completeness: List[PlaceCompleteness] = []
        all_errors: List[Dict[str, str]] = []
        total_discovered = 0
        total_crawled = 0
        visited_ids: Set[str] = set()

        for dest in destinations:
            city = dest.get("city", "bhubaneswar")
            state = dest.get("state", "odisha")
            city_slug = city.lower().replace(" ", "-")
            state_slug = state.lower().replace(" ", "-")
            hub_url = dest.get("start_url") or f"{self.config.base_url}/en/{state_slug}/{city_slug}"

            logger.info(f"=== Crawling Destination: {city.title()}, {state.title()} ===")
            hub_html = self.crawler.fetch_page(hub_url)
            discovered_urls: List[str] = []

            if hub_html:
                discovered_urls = IncredibleIndiaParser.extract_attraction_links(
                    html_content=hub_html,
                    base_url=self.config.base_url,
                    city=city,
                    state=state
                )
            else:
                logger.warning(f"Could not fetch hub page: {hub_url}")
                all_errors.append({
                    "url": hub_url,
                    "error": self.crawler.failed_urls.get(hub_url, "Failed to load hub page")
                })

            total_discovered += len(discovered_urls)
            logger.info(f"Discovered {len(discovered_urls)} places for {city.title()}. Crawling up to {limit}.")

            pages_crawled_dest = 0
            for place_url in discovered_urls:
                if pages_crawled_dest >= limit:
                    break

                page_html = self.crawler.fetch_page(place_url)
                if not page_html:
                    err_reason = self.crawler.failed_urls.get(place_url, "Unknown network or robots failure")
                    all_errors.append({"url": place_url, "error": err_reason})
                    continue

                try:
                    raw_place = IncredibleIndiaParser.parse_place_page(page_html, place_url)
                    norm_place = PlaceNormalizer.normalize(raw_place)

                    # Deduplicate by slug ID
                    if norm_place.id in visited_ids:
                        logger.debug(f"Skipping duplicate place ID: {norm_place.id}")
                        continue
                    visited_ids.add(norm_place.id)

                    completeness = PlaceNormalizer.evaluate_completeness(norm_place)

                    all_raw_places.append(raw_place)
                    all_normalized_places.append(norm_place)
                    all_completeness.append(completeness)
                    pages_crawled_dest += 1
                    total_crawled += 1

                    logger.info(
                        f"✓ [{city.title()}] '{norm_place.name}' ({norm_place.category}) - {completeness.completeness_score}% complete"
                    )

                except Exception as e:
                    logger.error(f"Error parsing place from {place_url}: {e}", exc_info=True)
                    all_errors.append({"url": place_url, "error": str(e)})

        end_time = time.time()
        end_time_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        duration = round(end_time - start_time, 2)

        total_normalized = len(all_normalized_places)
        avg_score = (
            sum(c.completeness_score for c in all_completeness) / total_normalized
            if total_normalized > 0 else 0.0
        )

        field_names = [
            "name", "city", "state", "category", "sub_category",
            "short_description", "full_description", "cultural_significance",
            "historical_period", "opening_hours", "entry_fee", "best_time_of_day",
            "recommended_duration", "accessibility_notes", "festivals",
            "nearest_transit", "image_urls", "source_url"
        ]
        field_summary: Dict[str, float] = {}
        for fname in field_names:
            present_count = sum(1 for c in all_completeness if fname not in c.missing_fields)
            field_summary[fname] = round((present_count / total_normalized * 100.0) if total_normalized > 0 else 0.0, 1)

        city_names = ", ".join(d.get("city", "").title() for d in destinations)
        report = ScrapingReport(
            target_source="Incredible India Tourism Portal",
            start_url=", ".join(d.get("start_url", f"{self.config.base_url}/en/{d.get('state', 'odisha')}/{d.get('city', '')}") for d in destinations),
            city=city_names,
            state="Odisha",
            total_pages_discovered=total_discovered,
            total_pages_crawled=total_crawled,
            total_places_normalized=total_normalized,
            errors_count=len(all_errors),
            error_details=all_errors,
            start_time_utc=start_time_utc,
            end_time_utc=end_time_utc,
            duration_seconds=duration,
            average_completeness=round(avg_score, 2),
            field_completeness_summary=field_summary,
            completeness_per_place=all_completeness
        )

        # Export consolidated artifacts
        self.exporter.export_raw_json(all_raw_places)
        self.exporter.export_normalized_json(all_normalized_places)
        self.exporter.export_csv(all_normalized_places)
        self.exporter.export_missing_fields_report(all_completeness)
        self.exporter.export_scrape_report(report)

        logger.info(
            f"Multi-city scrape finished in {duration}s. Total normalized places: {total_normalized} (Avg completeness: {avg_score:.2f}%)."
        )
        return report
