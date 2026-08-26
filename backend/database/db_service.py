"""
DHRUVA Database Access and Query Service Layer.
Encapsulates all relational queries, spatial calculations, and data retrieval
from the normalized SQLite database (dhruva.db).
"""

from __future__ import annotations
import math
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class DhruvaDBService:
    """
    Data Access Object (DAO) providing high-performance query methods
    for CITIES, PLACES, OPENING_HOURS, MIN_INTEREST, FESTIVALS, and USERS_INPUT.
    """

    DEFAULT_DB_PATH = Path("backend/database/dhruva.db")

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or self.DEFAULT_DB_PATH

    def _get_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection with row factory enabled."""
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Database file not found at {self.db_path.resolve()}. "
                "Please run `python -m scraper.pipeline` to generate the database."
            )
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    # -------------------------------------------------------------
    # Spatial Calculation Helpers
    # -------------------------------------------------------------
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great-circle distance between two points on the Earth (in kilometers).
        """
        R = 6371.0  # Earth's radius in kilometers
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (
            math.sin(d_lat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(d_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 2)

    # -------------------------------------------------------------
    # CITIES Queries
    # -------------------------------------------------------------
    def get_cities(self) -> List[Dict[str, Any]]:
        """Retrieve all cultural destination cities with place counts."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    c.id, c.name, c.state, c.lat, c.long,
                    COUNT(p.id) AS place_count,
                    COALESCE(AVG(p.popularity), 0) AS avg_rating
                FROM CITIES c
                LEFT JOIN PLACES p ON c.id = p.city_id
                GROUP BY c.id
                ORDER BY c.id ASC;
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_city_by_id(self, city_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a single city by its Primary Key."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, state, lat, long FROM CITIES WHERE id = ?", (city_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # -------------------------------------------------------------
    # PLACES Queries & Relational Filters
    # -------------------------------------------------------------
    def get_places(
        self,
        city_id: Optional[int] = None,
        city_name: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        min_popularity: float = 0.0,
        max_risk: Optional[str] = None,
        min_spiritual: float = 0.0,
        min_architecture: float = 0.0,
        min_history: float = 0.0,
        min_nature: float = 0.0,
        min_culture: float = 0.0,
        sort_by: str = "popularity",
        order: str = "DESC",
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Query places with dynamic multi-criteria filtering, joins on CITIES and MIN_INTEREST.
        """
        query = """
            SELECT
                p.id, p.name, p.duration, p.duration_label, p.popularity,
                p.lat, p.long, p.risk, p.category, p.sub_category,
                p.description, p.image_url, p.entry_fee,
                c.id AS city_id, c.name AS city_name, c.state AS state_name,
                mi.architecture, mi.history, mi.spiritual, mi.nature, mi.culture
            FROM PLACES p
            JOIN CITIES c ON p.city_id = c.id
            JOIN MIN_INTEREST mi ON p.id = mi.place_id
            WHERE 1=1
        """
        params: List[Any] = []

        if city_id is not None:
            query += " AND p.city_id = ?"
            params.append(city_id)

        if city_name:
            query += " AND LOWER(c.name) = LOWER(?)"
            params.append(city_name.strip())

        if category:
            query += " AND (LOWER(p.category) LIKE ? OR LOWER(p.sub_category) LIKE ?)"
            params.append(f"%{category.lower()}%")
            params.append(f"%{category.lower()}%")

        if search:
            query += " AND (LOWER(p.name) LIKE ? OR LOWER(p.description) LIKE ?)"
            search_param = f"%{search.lower().strip()}%"
            params.append(search_param)
            params.append(search_param)

        if min_popularity > 0:
            query += " AND p.popularity >= ?"
            params.append(min_popularity)

        if max_risk:
            if max_risk.lower() == "low":
                query += " AND LOWER(p.risk) = 'low'"
            elif max_risk.lower() == "moderate":
                query += " AND LOWER(p.risk) IN ('low', 'moderate')"

        # Cultural Interest Filters
        if min_spiritual > 0:
            query += " AND mi.spiritual >= ?"
            params.append(min_spiritual)
        if min_architecture > 0:
            query += " AND mi.architecture >= ?"
            params.append(min_architecture)
        if min_history > 0:
            query += " AND mi.history >= ?"
            params.append(min_history)
        if min_nature > 0:
            query += " AND mi.nature >= ?"
            params.append(min_nature)
        if min_culture > 0:
            query += " AND mi.culture >= ?"
            params.append(min_culture)

        # Ordering
        valid_sort_columns = {
            "popularity": "p.popularity",
            "duration": "p.duration",
            "name": "p.name",
            "architecture": "mi.architecture",
            "history": "mi.history",
            "spiritual": "mi.spiritual",
            "nature": "mi.nature",
            "culture": "mi.culture"
        }
        sort_col = valid_sort_columns.get(sort_by.lower(), "p.popularity")
        order_dir = "ASC" if order.upper() == "ASC" else "DESC"
        query += f" ORDER BY {sort_col} {order_dir} LIMIT ? OFFSET ?"
        params.append(limit)
        params.append(offset)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_place_by_id(self, place_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single place with its full opening hours schedule,
        minimum cultural interest scores, and city details.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    p.id, p.name, p.duration, p.duration_label, p.popularity,
                    p.lat, p.long, p.risk, p.category, p.sub_category,
                    p.description, p.image_url, p.entry_fee,
                    c.id AS city_id, c.name AS city_name, c.state AS state_name,
                    c.lat AS city_lat, c.long AS city_long,
                    mi.architecture, mi.history, mi.spiritual, mi.nature, mi.culture
                FROM PLACES p
                JOIN CITIES c ON p.city_id = c.id
                JOIN MIN_INTEREST mi ON p.id = mi.place_id
                WHERE p.id = ?;
            """, (place_id,))
            place_row = cursor.fetchone()
            if not place_row:
                return None

            place_dict = dict(place_row)

            # Fetch opening hours
            cursor.execute("""
                SELECT id, day_of_week, opens_at, closes_at
                FROM OPENING_HOURS
                WHERE place_id = ?
                ORDER BY CASE day_of_week
                    WHEN 'Monday' THEN 1
                    WHEN 'Tuesday' THEN 2
                    WHEN 'Wednesday' THEN 3
                    WHEN 'Thursday' THEN 4
                    WHEN 'Friday' THEN 5
                    WHEN 'Saturday' THEN 6
                    WHEN 'Sunday' THEN 7
                END;
            """, (place_id,))
            place_dict["opening_hours"] = [dict(h) for h in cursor.fetchall()]

            return place_dict

    def get_nearby_places(
        self,
        lat: float,
        lon: float,
        max_distance_km: float = 40.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find places sorted by proximity to a given GPS coordinate.
        """
        all_places = self.get_places(limit=200)
        places_with_dist = []
        for p in all_places:
            if p.get("lat") and p.get("long"):
                d = self.haversine_distance(lat, lon, p["lat"], p["long"])
                if d <= max_distance_km:
                    p["distance_km"] = d
                    places_with_dist.append(p)

        places_with_dist.sort(key=lambda x: x["distance_km"])
        return places_with_dist[:limit]

    # -------------------------------------------------------------
    # FESTIVALS Queries
    # -------------------------------------------------------------
    def get_festivals(self, city_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve cultural festivals with city information."""
        query = """
            SELECT
                f.id, f.name, f.start_date, f.end_date, f.description,
                c.id AS city_id, c.name AS city_name, c.state AS state_name
            FROM FESTIVALS f
            JOIN CITIES c ON f.city_id = c.id
            WHERE 1=1
        """
        params = []
        if city_id is not None:
            query += " AND f.city_id = ?"
            params.append(city_id)
        query += " ORDER BY f.start_date ASC;"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    # -------------------------------------------------------------
    # USERS_INPUT Queries & Storage
    # -------------------------------------------------------------
    def get_user_inputs(self) -> List[Dict[str, Any]]:
        """Retrieve all stored user inputs."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, gps_location, start_date, start_time, end_time, age FROM USERS_INPUT ORDER BY id ASC;")
            return [dict(row) for row in cursor.fetchall()]

    def save_user_input(
        self,
        gps_location: str,
        start_date: str,
        start_time: str,
        end_time: str,
        age: int
    ) -> int:
        """Insert a new user trip planner input record and return generated ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO USERS_INPUT (gps_location, start_date, start_time, end_time, age)
                VALUES (?, ?, ?, ?, ?);
            """, (gps_location, start_date, start_time, end_time, age))
            conn.commit()
            return cursor.lastrowid
