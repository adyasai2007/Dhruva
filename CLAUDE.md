# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**DHRUVA** ("Your Journey, Guided") is a culturally focused travel-planning platform designed to guide travelers through heritage, spiritual sanctums, and regional traditions of India. The primary target audience includes adults aged 40–65+, requiring readable typography, strong contrast, spacious layouts, accessibility controls, Gemini Live real-time voice assistance, and mindful itinerary pacing.

The repository is modularized into decoupled frontend (`frontend/`), high-performance Python backend (`backend/`), PostgreSQL relational database storage (`database/`), web scraper (`scraper/`), and utility scripts (`scripts/`).

## Development & Serving Commands

### 1. HTTP Server & REST API
```bash
# Start backend HTTP server (serves frontend static assets + REST APIs on port 8000)
python backend/server.py 8000
```
Navigate to `http://localhost:8000/index.html`.

### 2. Gemini Live WebSocket Audio Server
```bash
# Start bidirectional audio streaming bridge on ws://localhost:8001
python backend/live_websocket_server.py
```

### 3. Run Backend Test Suite
```bash
python -m pytest backend/tests
```

### 4. PostgreSQL Database Setup (Optional)
```bash
# Load schema and seed data into PostgreSQL
psql -U postgres -d dhruva_db -f database/dhruva_postgres_dump.sql
```

## Architecture & Code Structure

### 1. Backend Engine (`backend/`)
- `server.py`: Zero-dependency `ThreadingHTTPServer` exposing REST API endpoints for recommendations, routing, dynamic itinerary editing, and static frontend assets.
- `live_websocket_server.py`: Asynchronous WebSocket server (`ws://localhost:8001`) that bridges browser Web Audio (16kHz PCM) with Google Gemini Live API (`gemini-3.1-flash-live-preview`), handling real-time function calling and returning 24kHz synthesized audio.
- `config.py`: Environment configuration and fallback defaults.
- `database/`:
  - `models.py`: Data classes (`City`, `Place`, `MinInterest`, `OpeningHour`, `Festival`, `Trip`).
  - `db.py`: `DataRepository` managing thread-safe in-memory collections and query indices.
  - `db_service.py`: `DhruvaDBService` providing high-level business queries and 5D interest calculations.
- `algorithm/`:
  - `scoring.py`: 5D cosine similarity matching, utility breakdown, and cultural relevance ranking.
  - `itinerary_generator.py`: Algorithmic multi-day schedule generator with time-window validation and fatigue pacing.
- `routing/`:
  - `ors_client.py`: OpenRouteService matrix routing client with road-winding Haversine fallback.
- `services/`:
  - `itinerary_engine.py`: `CulturalItineraryEngine` managing user preferences, conflict resolution, and alternative variations.
  - `voice_assistant.py`: `VoiceAssistantService` defining Gemini tool declarations and tool execution logic.
- `tests/`: 76 unit and integration test cases covering scoring, itinerary generation, routing, REST APIs, and tool execution.

### 2. Frontend Client (`frontend/`)
The frontend is a vanilla web application built without external framework dependencies or bundlers.
- `index.html`: Home page featuring conversational hero search, featured cultural destinations, and seasonal highlights.
- `pages/explore.html`: Discovery directory with region filters, cultural categories, place cards, and best-time guide.
- `pages/trip.html`: Multi-step conversational trip planner wizard (destination, dates, pacing, interests).
- `pages/itinerary.html`: Generated itinerary view displaying day-by-day timelines, activities, transit notes, and cultural tips.
- `pages/profile.html`: "My Plan" and traveler profile managing saved destinations, active journeys, and accessibility preferences.

#### JavaScript Modules (IIFE Pattern in `frontend/js/`)
- `DhruvaApp` (`js/app.js`): Core application controller. Manages state in `localStorage` (`dhruva_app_state_v1`), toast notifications, bookmarking, theme switching, and accessibility classes.
- `DhruvaNavigation` (`js/navigation.js`): Controls header scroll effects, active route highlighting, mobile drawer navigation, and keyboard accessibility.
- `DhruvaPlanner` (`js/planner.js`): Step-by-step wizard logic for `pages/trip.html`.
- `DhruvaComponents` (`js/components.js`): Dynamic HTML template renderers for destination cards, place cards, cultural events, and place detail modals.
- `DhruvaVoiceOrb` (`js/voice-orb.js`): Real-time audio assistant connecting to `live_websocket_server.py` with pitch autocorrelation, audio-reactive canvas orb visualizer, and UI navigation dispatch.

#### Styling & Design System (`frontend/css/`)
- `css/variables.css`: Design tokens (*Warm Parchment* `#F7F2E8`, *Temple Green* `#234A35`, *Brass Gold* `#B99A5B`), typography (`Cormorant Garamond` serif, `Plus Jakarta Sans`), and dark mode tokens.
- `css/style.css`: Base layout, typography scale, header, hero, search bar, and footer.
- `css/components.css`: Reusable UI components (cards, pills, chips, modals, buttons, toasts, timeline).
- `css/voice-orb.css`: Floating voice trigger button, overlay modal, animated canvas halo, and microphone states.
- `css/responsive.css`: Media queries managing mobile drawers and responsive layouts.

### 3. PostgreSQL Relational Database (`database/`)
- `dhruva_postgres_dump.sql`: Complete PostgreSQL schema + data dump.
- `postgres_schema.sql` / `dhruva.schema`: PostgreSQL DDL schema definition.
- `postgres_import_csv.sql`: `\copy` bulk data import script.
- `csv/`: Normalized relational CSV files for `CITIES`, `PLACES`, `OPENING_HOURS`, `MIN_INTEREST`, and `FESTIVALS`.

### 4. Data Scraper & Pipeline (`scraper/`)
- `pipeline.py`: Comprehensive extraction and normalization pipeline for cultural heritage sites.
- `cli.py`: Command-line interface for scrapers.
- `mediawiki_client.py` & `search_client.py`: Wikipedia and web retrieval tools.
- `llm_processor.py`: LLM-assisted cultural place metadata enrichment.

### 5. Utility Scripts (`scripts/`)
- `live_audio_stream.py`: Standalone PyAudio Gemini Live streaming test script.
- `run_live_assistant.py`: Standalone terminal assistant with tool calling.
- `sync_frontend_mock.py`: Utility to synchronize database rows into frontend mock JSON files.

## Key Development Conventions

- **Frontend Isolation**: All frontend assets (HTML, CSS, JS, mock JSON) reside in `frontend/`.
- **State Management**: Client state is kept in `localStorage` under `dhruva_app_state_v1`.
- **Visual Palette**: Dominant palette consists of warm parchment/cream surfaces (`#F7F2E8`, `#FFFDF8`), deep temple green brand color (`#234A35`), and brass/gold accents (`#B99A5B`).
- **Testing**: Always run `python -m pytest backend/tests` before submitting code changes.
