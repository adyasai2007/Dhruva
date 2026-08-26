"""
DHRUVA Cultural Travel Planner - FastAPI Backend Application.
Provides high-performance ASGI REST APIs for relational cultural destination data,
spatial proximity search, and algorithmic itinerary generation.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException, Query, status
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
except ImportError:
    # Allow fallback if FastAPI is not installed in current environment
    FastAPI = None

from backend.database.db_service import DhruvaDBService
from backend.services.itinerary_engine import CulturalItineraryEngine, UserPlannerPreferences


# Pydantic Request & Response Schemas
class CulturalInterests(BaseModel):
    spiritual: float = Field(default=4.5, ge=0.0, le=5.0)
    architecture: float = Field(default=4.5, ge=0.0, le=5.0)
    history: float = Field(default=4.0, ge=0.0, le=5.0)
    nature: float = Field(default=3.0, ge=0.0, le=5.0)
    culture: float = Field(default=4.5, ge=0.0, le=5.0)


class ItineraryPlanRequest(BaseModel):
    city_id: Optional[int] = None
    city_name: Optional[str] = "Bhubaneswar"
    gps_location: Optional[str] = "20.2961,85.8245"
    start_date: str = "2026-10-15"
    num_days: int = Field(default=3, ge=1, le=14)
    start_time: str = "08:30 AM"
    end_time: str = "07:30 PM"
    age: int = Field(default=58, ge=1, le=120)
    pacing: str = Field(default="balanced", description="relaxed, balanced, or immersive")
    interests: Optional[CulturalInterests] = Field(default_factory=CulturalInterests)


class UserInputCreateRequest(BaseModel):
    gps_location: str = "20.2961,85.8245"
    start_date: str = "2026-10-15"
    start_time: str = "08:00 AM"
    end_time: str = "08:00 PM"
    age: int = 58


def create_app() -> Any:
    """Factory creating configured FastAPI instance."""
    if FastAPI is None:
        raise RuntimeError("FastAPI is not installed. Please install requirements via `pip install -r backend/requirements.txt` or run `python -m backend.server 8000`.")

    app = FastAPI(
        title="DHRUVA Cultural Travel Planner API",
        description="Backend API powering heritage, temple sanctum, and regional tradition itineraries across India.",
        version="1.0.0"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    db_service = DhruvaDBService()
    itinerary_engine = CulturalItineraryEngine(db_service)

    @app.get("/api/health", tags=["System"])
    def health_check():
        cities = db_service.get_cities()
        places = db_service.get_places(limit=500)
        festivals = db_service.get_festivals()
        return {
            "status": "healthy",
            "version": "1.0.0",
            "database": str(db_service.db_path.resolve()),
            "records": {
                "cities_count": len(cities),
                "places_count": len(places),
                "festivals_count": len(festivals)
            }
        }

    @app.get("/api/cities", tags=["Destinations"])
    def list_cities():
        cities = db_service.get_cities()
        return {"status": "success", "count": len(cities), "data": cities}

    @app.get("/api/cities/{city_id}", tags=["Destinations"])
    def get_city(city_id: int):
        city = db_service.get_city_by_id(city_id)
        if not city:
            raise HTTPException(status_code=404, detail="City not found")
        return {"status": "success", "data": city}

    @app.get("/api/places", tags=["Places"])
    def list_places(
        city_id: Optional[int] = None,
        city: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        min_popularity: float = 0.0,
        spiritual: float = 0.0,
        architecture: float = 0.0,
        history: float = 0.0,
        nature: float = 0.0,
        culture: float = 0.0,
        sort_by: str = "popularity",
        limit: int = 50,
        offset: int = 0
    ):
        places = db_service.get_places(
            city_id=city_id,
            city_name=city,
            category=category,
            search=search,
            min_popularity=min_popularity,
            min_spiritual=spiritual,
            min_architecture=architecture,
            min_history=history,
            min_nature=nature,
            min_culture=culture,
            sort_by=sort_by,
            limit=limit,
            offset=offset
        )
        return {"status": "success", "count": len(places), "data": places}

    @app.get("/api/places/nearby", tags=["Places"])
    def get_nearby(
        lat: float = Query(..., description="Latitude"),
        lon: float = Query(..., description="Longitude"),
        max_distance_km: float = Query(40.0, description="Search radius in kilometers"),
        limit: int = Query(10, description="Max results")
    ):
        nearby = db_service.get_nearby_places(lat, lon, max_distance_km, limit)
        return {"status": "success", "count": len(nearby), "data": nearby}

    @app.get("/api/places/{place_id}", tags=["Places"])
    def get_place(place_id: int):
        place = db_service.get_place_by_id(place_id)
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")
        return {"status": "success", "data": place}

    @app.get("/api/festivals", tags=["Cultural Events"])
    def list_festivals(city_id: Optional[int] = None):
        festivals = db_service.get_festivals(city_id=city_id)
        return {"status": "success", "count": len(festivals), "data": festivals}

    @app.get("/api/users/inputs", tags=["User Profiles"])
    def get_user_inputs():
        inputs = db_service.get_user_inputs()
        return {"status": "success", "count": len(inputs), "data": inputs}

    @app.post("/api/users/inputs", status_code=status.HTTP_201_CREATED, tags=["User Profiles"])
    def create_user_input(req: UserInputCreateRequest):
        new_id = db_service.save_user_input(
            req.gps_location, req.start_date, req.start_time, req.end_time, req.age
        )
        return {"status": "success", "message": "User input saved successfully", "id": new_id}

    @app.post("/api/itinerary/plan", tags=["Planner"])
    def plan_itinerary(req: ItineraryPlanRequest):
        interests_dict = req.interests.dict() if req.interests else {
            "spiritual": 4.5, "architecture": 4.5, "history": 4.0, "nature": 3.0, "culture": 4.5
        }
        prefs = UserPlannerPreferences(
            city_id=req.city_id,
            city_name=req.city_name,
            gps_location=req.gps_location,
            start_date=req.start_date,
            num_days=req.num_days,
            start_time=req.start_time,
            end_time=req.end_time,
            age=req.age,
            pacing=req.pacing,
            interests=interests_dict
        )
        return itinerary_engine.generate_itinerary(prefs)

    return app


# Module-level ASGI app instance for Uvicorn
if FastAPI is not None:
    app = create_app()
else:
    app = None
