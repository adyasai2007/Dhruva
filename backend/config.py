"""
Configuration management for DHRUVA backend.
Loads settings from environment variables with safe defaults.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

def _load_env_file(path: Path) -> None:
    """Zero-dependency .env loader to ensure environment variables load reliably."""
    if not path.is_file():
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
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

# Load .env from project root
env_file_path = Path(__file__).resolve().parent.parent / ".env"
_load_env_file(env_file_path)

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_file_path, override=True)
except ImportError:
    pass


@dataclass
class Settings:
    # Environment
    app_name: str = "DHRUVA Travel Planning Backend"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

    # Routing & ORS
    ors_api_key: str = os.getenv("ORS_API_KEY", "")
    ors_base_url: str = os.getenv("ORS_BASE_URL", "https://api.openrouteservice.org")
    ors_profile: str = os.getenv("ORS_PROFILE", "driving-car")
    ors_timeout_seconds: float = float(os.getenv("ORS_TIMEOUT_SECONDS", "10.0"))

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/dhruva_db"
    )

    # Supabase (optional direct credentials)
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # Default speeds & routing parameters (for fallback and routing calculations)
    default_driving_speed_kmh: float = 30.0
    default_walking_speed_kmh: float = 4.5
    road_winding_factor: float = 1.3  # Road winding / detour multiplier for Euclidean distances

    # Scoring Weights
    weight_interest: float = 0.50
    weight_popularity: float = 0.30
    weight_cultural: float = 0.20

    # Max shuffle attempts per trip
    max_shuffle_count: int = 3


settings = Settings()
