"""
Database service abstraction layer for DHRUVA backend.
Provides high-level relational query APIs, filtering, and summary statistics
leveraging the core DataRepository and CSV/PostgreSQL storage.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Any
from backend.database.db import db_repo
from backend.database.models import City, CityInterest, Place, Festival, MinInterest, OpeningHour


class DhruvaDBService:
    """Service layer for querying cultural data and trip entities."""

    def __init__(self, repo=db_repo):
        self.repo = repo

    def get_cities(self) -> List[Dict[str, Any]]:
        """Retrieve all cities with aggregated statistics and default cultural interest profiles."""
        cities = self.repo.get_cities()
        results = []
        for c in cities:
            city_places = self.repo.get_places_by_city(c.id)
            avg_pop = (
                sum(p.popularity for p in city_places) / len(city_places)
                if city_places else 0.0
            )
            ci = self.repo.get_city_interest(c.id) or c.interest
            results.append({
                "id": c.id,
                "name": c.name,
                "state": c.state,
                "lat": c.lat,
                "long": c.long,
                "place_count": len(city_places),
                "avg_rating": round(avg_pop, 2),
                "city_interest": ci.as_dict() if ci else {},
            })
        return sorted(results, key=lambda x: x["name"])

    def get_city_by_id(self, city_id: int) -> Optional[Dict[str, Any]]:
        c = self.repo.get_city(city_id)
        if not c:
            return None
        places = self.repo.get_places_by_city(c.id)
        ci = self.repo.get_city_interest(c.id) or c.interest
        return {
            "id": c.id,
            "name": c.name,
            "state": c.state,
            "lat": c.lat,
            "long": c.long,
            "place_count": len(places),
            "city_interest": ci.as_dict() if ci else {},
        }

    def get_city_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        c = self.repo.get_city_by_name(name)
        if not c:
            return None
        return self.get_city_by_id(c.id)

    def get_city_interest(self, city_id: int) -> Optional[Dict[str, float]]:
        ci = self.repo.get_city_interest(city_id)
        return ci.as_dict() if ci else None

    def get_places(
        self,
        city_id: Optional[int] = None,
        city_name: Optional[str] = None,
        category: Optional[str] = None,
        min_rating: Optional[float] = None,
        user_interests: Optional[Dict[str, float]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query places with dynamic interest-based scoring, filtering by city, category, rating, and limit.
        When user_interests is not supplied, falls back to the city's default CITY_INTEREST vector.
        """
        target_city = None
        if city_name and not city_id:
            target_city = self.repo.get_city_by_name(city_name)
            if target_city:
                city_id = target_city.id
        elif city_id:
            target_city = self.repo.get_city(city_id)

        if city_id is not None:
            places = self.repo.get_places_by_city(city_id)
        else:
            places = self.repo.get_all_places()

        # Determine effective interest vector: User preferences -> CITY_INTEREST fallback
        effective_prefs = user_interests
        if not effective_prefs:
            ref_city_id = city_id or (target_city.id if target_city else 1)
            ci = self.repo.get_city_interest(ref_city_id)
            if ci:
                effective_prefs = ci.as_dict()

        from backend.algorithm.scoring import calculate_interest_similarity

        results = []
        for p in places:
            if category and p.category and category.lower() not in p.category.lower():
                continue

            # Calculate dynamic popularity / match score
            if effective_prefs and p.interests:
                sim = calculate_interest_similarity(effective_prefs, p.interests)
                dyn_popularity = round(sim * 5.0, 2)
                match_pct = int(round(sim * 100))
            else:
                sim = 0.9
                dyn_popularity = p.popularity or 4.5
                match_pct = int(round(dyn_popularity * 20))

            if min_rating is not None and dyn_popularity < min_rating:
                continue

            # Serialize place
            interests_dict = p.interests.as_dict() if p.interests else {}
            hours_list = [
                {
                    "day_of_week": oh.day_of_week,
                    "opens_at": oh.opens_at,
                    "closes_at": oh.closes_at,
                }
                for oh in p.opening_hours
            ]

            results.append({
                "id": p.id,
                "name": p.name,
                "city_id": p.city_id,
                "duration": p.duration,
                "duration_label": p.duration_label or f"{p.duration} hrs",
                "popularity": dyn_popularity,
                "match_score": round(sim, 4),
                "match_percentage": match_pct,
                "lat": p.lat,
                "long": p.long,
                "risk": p.risk,
                "category": p.category,
                "sub_category": p.sub_category,
                "image_url": p.image_url,
                "entry_fee": p.entry_fee,
                "description": p.description,
                "source": p.source,
                "source_url": p.source_url,
                "interests": interests_dict,
                "opening_hours": hours_list,
            })

        results.sort(key=lambda x: (x["popularity"], x.get("match_score", 0)), reverse=True)
        if limit is not None and limit > 0:
            results = results[:limit]

        return results

    def get_place_by_id(self, place_id: int) -> Optional[Dict[str, Any]]:
        p = self.repo.get_place(place_id)
        if not p:
            return None
        res = self.get_places(city_id=p.city_id)
        for item in res:
            if item["id"] == place_id:
                return item
        return None

    def get_festivals(self, city_id: Optional[int] = None, city_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve regional festivals and cultural events."""
        if city_name and not city_id:
            c = self.repo.get_city_by_name(city_name)
            if c:
                city_id = c.id

        festivals = self.repo.festivals
        if city_id is not None:
            festivals = [f for f in festivals if f.city_id == city_id]

        results = []
        for f in festivals:
            city = self.repo.get_city(f.city_id)
            results.append({
                "id": f.id,
                "name": f.name,
                "start_date": f.start_date,
                "end_date": f.end_date,
                "city_id": f.city_id,
                "city_name": city.name if city else "",
                "description": f.description,
            })
        return results


# Global singleton instance
dhruva_db = DhruvaDBService()
