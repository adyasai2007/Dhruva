"""
DHRUVA Scraping and Data Ingestion Package.
Ensures .env is loaded before any module initialization.
"""

from pathlib import Path
import os

env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.is_file():
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path, override=True)
    except ImportError:
        pass
    # Zero-dependency fallback loader
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
