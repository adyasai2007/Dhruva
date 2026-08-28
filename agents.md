# DHRUVA — Product & Agent Architecture Specification

## 1. Project Identity

**DHRUVA** is a culturally grounded, intelligent travel-planning platform designed to guide travelers through the spiritual sanctums, living heritage, and regional traditions of India.

**Tagline:** *DHRUVA — Your Journey, Guided.*

```text
       Warm Parchment + Deep Temple Green + Brass Gold
                     Cultural Depth
              Accessible for Generations (40–65+)
                   Audio-Reactive Voice Orb
                 Algorithmic Itinerary Engine
                 Real-Time Gemini Live Audio
```

---

## 2. Target Audience & Core Principles

The primary audience includes adults aged **40–65+**, spiritual seekers, family journey planners, and heritage enthusiasts.

### Key Experience Principles
1. **Legibility & Comfort:** Generous typography scale (`Cormorant Garamond` serifs for editorial elegance, `Plus Jakarta Sans` for UI readability), high-contrast ratios, and responsive spacing.
2. **Mindful Pacing:** Respects physical stamina and temple rest hours; avoids overcrowded itineraries.
3. **Cultural Context:** Provides historical background, behavioral etiquette, dress codes, and festive timing for sacred sites.
4. **Multi-Modal Interaction:** Text, visual step-by-step wizard, and real-time audio-reactive Gemini Live voice guidance.

---

## 3. Decoupled Monorepo Architecture

The repository is modularized into distinct, decoupled subsystems:

```text
Dhruva/
├── backend/                   # ⚡ Core Python Backend & Engine Services
│   ├── server.py              # HTTP REST API & static asset server (Port 8000)
│   ├── live_websocket_server.py # Bidirectional Gemini Live WebSocket audio server (Port 8001)
│   ├── config.py              # Environment configuration
│   ├── database/              # SQLite/Postgres repository and models
│   ├── algorithm/             # 5D Scoring and itinerary generation
│   ├── routing/               # Matrix routing with OpenRouteService
│   ├── services/              # High-level business logic & Gemini Live tool orchestration
│   └── tests/                 # Full test suite (76 tests)
│
├── frontend/                  # Modular Vanilla Client (HTML5, CSS3, ES6+ IIFE)
│   ├── index.html             # Landing & discovery search
│   ├── pages/                 # Multi-page application views (explore, trip, itinerary, profile)
│   ├── css/                   # Tokenized stylesheets (variables, style, components, voice-orb, responsive)
│   ├── js/                    # Client application modules (app, navigation, components, planner, voice-orb)
│   ├── mock/                  # Static mock JSON datasets for standalone client mode
│   └── assets/                # Static images, vectors & icons
│
├── database/                  # PostgreSQL Database Dumps, Schemas & Relational CSVs
│   ├── dhruva_postgres_dump.sql # Full PostgreSQL dump (schema + all seed data)
│   ├── postgres_schema.sql    # PostgreSQL DDL schema definition
│   └── csv/                   # Normalized relational CSV tables (CITIES, PLACES, etc.)
│
├── scraper/                   # Web Scraping & Data Extraction Pipeline
│   ├── pipeline.py            # Crawler, geocoder & normalizer pipeline
│   ├── cli.py                 # CLI interface for scraper suites
│   ├── llm_processor.py       # LLM enrichment helper
│   ├── mediawiki_client.py    # MediaWiki / Wikipedia crawler
│   └── search_client.py       # Search & retrieval client
│
└── scripts/                   # Standalone scripts & developer tools
    ├── live_audio_stream.py   # Standalone PyAudio Gemini Live streaming test script
    ├── run_live_assistant.py  # Local terminal assistant with tool calling
    └── sync_frontend_mock.py  # Synchronize database rows to mock JSON
```

---

## 4. Frontend Client Architecture (`Dhruva/frontend/`)

Built as a lightweight, zero-build vanilla web application using the IIFE module pattern.

### JavaScript Modules (`frontend/js/`)
1. **`DhruvaApp` (`js/app.js`):**
   - Central application state in `localStorage` (`dhruva_app_state_v1`).
   - Mock data loader with dynamic relative path resolution (`fetchMockData`).
   - Global toast notification manager.
   - Theme management (`initTheme`, `toggleTheme` for "Sacred Night" dark mode).
   - Accessibility settings (`text-scale-large`, `high-contrast`).
   - Destination bookmarking & plan persistence.

2. **`DhruvaNavigation` (`js/navigation.js`):**
   - Active route highlighting across root and nested `pages/` routes.
   - Header scroll-elevation effect.
   - Mobile navigation drawer toggle.
   - Global keyboard shortcuts (Escape dismissals).

3. **`DhruvaPlanner` (`js/planner.js`):**
   - 4-step wizard state machine (`Step 1: Destination`, `Step 2: Dates & Group`, `Step 3: Pacing & Age`, `Step 4: Cultural Interests`).
   - Live planning summary sidebar.
   - Destination-aware recommendation filtering.
   - Dynamic itinerary generation & persistence handoff.

4. **`DhruvaComponents` (`js/components.js`):**
   - Modular HTML renderers: Destination Cards, Place Cards, Event Cards, Timeline Rows.
   - Accessible Place Detail Modals with opening hours and cultural etiquette tips.

5. **`DhruvaVoiceOrb` (`js/voice-orb.js`):**
   - Real-time vocal fundamental frequency pitch detection (autocorrelation algorithm).
   - Dynamic audio-reactive HTML5 Canvas visualizer rendering golden-brass halo rings.
   - Bidirectional PCM audio streaming to Gemini Live via WebSocket (`ws://localhost:8001`).
   - Real-time tool execution notifications & UI navigation handoffs.

---

## 5. Backend & Algorithmic Services (`Dhruva/backend/`)

### Serving Subsystems
1. **Integrated Server (`backend/server.py`):**
   - Thread-safe HTTP server serving static frontend assets and REST API endpoints.
   - Endpoints for full itinerary planning, place filtering, utility breakdowns, and quick visits.
2. **Gemini Live WebSocket Server (`backend/live_websocket_server.py`):**
   - Low-latency bidirectional audio streaming using Google GenAI Live SDK (`gemini-3.1-flash-live-preview`).
   - Live function calling integration with local database tools (`search_places`, `get_place_details`, `create_itinerary`, `navigate_ui`).

### Database Access Layer (`backend/database/db_service.py`)
- Encapsulates queries across 5 normalized relational tables: `CITIES`, `PLACES`, `OPENING_HOURS`, `MIN_INTEREST`, `FESTIVALS`.
- Implements Haversine distance spatial calculations and 5D cultural cosine interest vector matching.

### Algorithmic Itinerary Engine (`backend/services/itinerary_engine.py`)
- **Spatial Clustering:** Minimizes inter-place travel transit using coordinates.
- **Interest Scoring Matrix:** Computes affinity vectors across Spiritual, Architecture, History, Culture, and Nature.
- **Pacing & Fatigue Limits:** Modulates daily activity counts based on traveler age and pacing preference (*Relaxed*, *Balanced*, *Intensive*).
- **Sanctum Scheduling:** Validates visits against recorded opening hours and midday temple rest closures.

---

## 6. REST API Endpoint Specification

| Endpoint | Method | Parameters / Body | Description |
| :--- | :--- | :--- | :--- |
| `/api/health` | `GET` | — | System health status, database path & record counts |
| `/api/cities` | `GET` | — | List all destination cities with place counts |
| `/api/cities/{id}` | `GET` | `id` (int) | Retrieve detailed city metadata |
| `/api/places` | `GET` | `city_id`, `category`, `search`, `min_rating`, `spiritual`, `architecture`, etc. | Dynamic multi-criteria place filtering |
| `/api/places/nearby`| `GET` | `lat`, `lon`, `max_distance_km`, `limit` | Proximity radius search |
| `/api/places/{id}` | `GET` | `id` (int) | Full place details with opening hours |
| `/api/festivals` | `GET` | `city_id` (optional) | Cultural festivals and dates |
| `/api/itinerary/plan`| `POST`| `city_name`, `num_days`, `age`, `pacing`, `interests` | Algorithmic multi-day itinerary generation |
| `/api/itinerary/rebalance` | `POST` | `trip_id`, `action`, `place_id`, `day_index` | Dynamic insertion/removal rebalancer |
| `/api/itinerary/variations`| `POST` | `trip_id` | 3-shuffle alternative itinerary variation generator |

---

## 7. Development & Operational Commands

```bash
# 1. Start HTTP Backend & REST API Server (Port 8000)
python backend/server.py 8000

# 2. Start Gemini Live WebSocket Audio Server (Port 8001)
python backend/live_websocket_server.py

# 3. Run Backend Test Suite (76 unit & integration tests)
python -m pytest backend/tests
```
