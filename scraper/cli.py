"""
Command-line interface (CLI) for DHRUVA Cultural Scraper.
Provides configurable arguments for destination crawling, rate limiting,
export formatting, and execution auditing.
"""

from __future__ import annotations
import argparse
import logging
import sys
from pathlib import Path
from typing import List

from scraper import __version__
from scraper.common.config import ScraperConfig
from scraper.incredible_india.scraper import IncredibleIndiaScraper


def setup_logging(debug: bool = False) -> None:
    """Configure structured logging output with timestamps and log levels."""
    log_level = logging.DEBUG if debug else logging.INFO
    log_format = "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def parse_arguments(argv: List[str] = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        prog="dhruva-scraper",
        description="DHRUVA Cultural Scraper — Collects structured heritage and travel facts for India destinations."
    )

    parser.add_argument(
        "--city",
        type=str,
        default="bhubaneswar",
        help="Target city destination (default: 'bhubaneswar')"
    )
    parser.add_argument(
        "--state",
        type=str,
        default="odisha",
        help="Target state (default: 'odisha')"
    )
    parser.add_argument(
        "--start-url",
        type=str,
        default=None,
        help="Custom starting hub URL (overrides default state/city hierarchy)"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help="Maximum number of individual place pages to crawl (default: 5)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="Base politeness delay in seconds between HTTP requests (default: 1.5s)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/scraped",
        help="Directory to save scraped JSON, CSV, and audit reports (default: 'data/scraped')"
    )
    parser.add_argument(
        "--export-formats",
        type=str,
        default="json,csv",
        help="Comma-separated list of export formats: 'json', 'csv' (default: 'json,csv')"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume scraping session from existing checkpoint file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate link discovery and pipeline without firing live network requests"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable detailed debug logging"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    return parser.parse_args(argv)


def main(argv: List[str] = None) -> int:
    """CLI execution entrypoint."""
    args = parse_arguments(argv)
    setup_logging(debug=args.debug)

    logger = logging.getLogger("dhruva.scraper.cli")
    logger.info(f"--- DHRUVA Cultural Scraper v{__version__} ---")
    logger.info(f"Target Destination: {args.city.title()}, {args.state.title()}")
    logger.info(f"Page Limit: {args.max_pages} | Delay: {args.delay}s | Output: {args.output_dir}")

    config = ScraperConfig(
        default_city=args.city,
        default_state=args.state,
        delay_seconds=args.delay,
        output_dir=Path(args.output_dir),
        checkpoint_file=Path(args.output_dir) / ".checkpoint.json",
        max_pages=args.max_pages,
        export_formats=[f.strip().lower() for f in args.export_formats.split(",")],
        debug=args.debug,
        dry_run=args.dry_run
    )

    scraper = IncredibleIndiaScraper(config)

    if args.resume:
        logger.info("Checking for previous checkpoint...")
        scraper.crawler.load_checkpoint()

    try:
        cities = [c.strip() for c in args.city.split(",") if c.strip()]
        if len(cities) > 1:
            destinations = [{"city": c, "state": args.state} for c in cities]
            report = scraper.scrape_multiple_destinations(
                destinations=destinations,
                max_pages_per_destination=args.max_pages
            )
        else:
            report = scraper.scrape_destination(
                city=cities[0],
                state=args.state,
                start_url=args.start_url,
                max_pages=args.max_pages
            )

        print("\n" + "=" * 60)
        print("SCRAPING EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Target Source            : {report.target_source}")
        print(f"Destination              : {report.city}, {report.state}")
        print(f"Pages Discovered         : {report.total_pages_discovered}")
        print(f"Pages Crawled            : {report.total_pages_crawled}")
        print(f"Places Normalized        : {report.total_places_normalized}")
        print(f"Errors Encountered       : {report.errors_count}")
        print(f"Total Duration           : {report.duration_seconds} seconds")
        print(f"Average Completeness     : {report.average_completeness}%")
        print("-" * 60)
        print("Key Artifacts Generated in:", config.output_dir.resolve())
        print("  - raw_places.json")
        print("  - normalized_places.json")
        print("  - places.csv")
        print("  - missing_fields_report.json")
        print("  - missing_fields_report.md")
        print("  - scraping_report.json")
        print("=" * 60 + "\n")

        return 0 if report.total_places_normalized > 0 else 1

    except KeyboardInterrupt:
        logger.warning("\nScrape run interrupted by user. State saved to checkpoint.")
        return 130
    except Exception as e:
        logger.critical(f"Unhandled fatal error in scraper: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
