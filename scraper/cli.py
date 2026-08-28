"""
Command-line interface for running the DHRUVA Wikipedia MediaWiki Data Pipeline.
Usage:
    python -m scraper.cli --help
    python -m scraper.cli run
"""

import argparse
import os
import sys
from pathlib import Path

# Explicitly ensure .env is loaded before pipeline imports
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.is_file():
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path, override=True)
    except ImportError:
        pass
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k:
                    os.environ[k] = v
    except Exception:
        pass

from scraper.pipeline import pipeline


def main():
    parser = argparse.ArgumentParser(
        description="DHRUVA Cultural Travel Planner - Wikipedia & MediaWiki Data Extraction Pipeline"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    run_parser = subparsers.add_parser("run", help="Run the full extraction, classification, and CSV/SQL dump generation")

    args = parser.parse_args()

    if args.command == "run" or len(sys.argv) == 1:
        print("Executing DHRUVA Odisha Wikipedia & MediaWiki Pipeline...")
        summary = pipeline.run()
        print("\n--- Pipeline Summary ---")
        for k, v in summary.items():
            print(f"  {k}: {v}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
