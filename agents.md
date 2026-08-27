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
```

---

## 2. Target Audience & Core Principles

The primary audience includes adults aged **40–65+**, spiritual seekers, family journey planners, and heritage enthusiasts.

### Key Experience Principles
1. **Legibility & Comfort:** Generous typography scale (`Cormorant Garamond` serifs for editorial elegance, `Plus Jakarta Sans` for UI readability), high-contrast ratios, and responsive spacing.
2. **Mindful Pacing:** Respects physical stamina and temple rest hours; avoids overcrowded itineraries.
3. **Cultural Context:** Provides historical background, behavioral etiquette, dress codes, and festive timing for sacred sites.
4. **Multi-Modal Interaction:** Text, visual step-by-step wizard, and real-time audio-reactive voice guidance.

---

## 3. Decoupled Monorepo Architecture

The repository is modularized into distinct, decoupled subsystems:

```text
Dhruva/
├── frontend/                  # Modular Vanilla Client (HTML5, CSS3, ES6+ IIFE)
│   ├── index.html             # Landing & discovery search
│   ├── pages/                 # Multi-page application views
│   │   ├── explore.html       # Destination directory & place catalog
│   │   ├── trip.html          # 4-step conversational trip planner wizard
│   │   ├── itinerary.html     # Dynamic day-by-day timeline & cultural guide
│   │   └── profile.html       # "My Plan", saved destinations & preferences
│   ├── css/                   # Tokenized stylesheets (variables, style, components, voice-orb, responsive)
│   ├── js/                    # Client application modules (app, navigation, components, planner, voice-orb)
│   ├── mock/                  # Static mock JSON datasets for standalone client mode
│   └── assets/                # Static images, vectors & icons
│
├── database/                  # PostgreSQL Database Dumps, Schemas & Relational CSVs
│   ├── README.md              # Database documentation & setup instructions
│   ├── dhruva_postgres_dump.sql # Full PostgreSQL dump (schema + all seed data)
│   ├── postgres_schema.sql    # PostgreSQL DDL schema definition
│   ├── postgres_import_csv.sql # PostgreSQL CSV bulk copy script
│   ├── dhruva.schema          # PostgreSQL DDL schema
│   ├── database.sql           # Relational schema reference
│   └── csv/                   # Normalized relational CSV tables (CITIES, PLACES, etc.)
│
├── scraper/                   # Web Scraping & Data Extraction Pipeline
│   ├── pipeline.py            # Crawler, geocoder & normalizer pipeline
│   ├── cli.py                 # CLI interface for scraper suites
│   ├── models.py              # Pydantic data schemas
│   ├── common/                # Shared utilities
│   └── incredible_india/      # Incredible India scrapers
│
├── data/                      # Data Pipeline Artifacts
│   ├── processed/             # Cleaned relational CSVs
│   └── scraped/               # Raw payloads & reports
│
├── scripts/                   # Database Utilities
│   ├── verify_db.py           # Database validation script
│   └── generate_postgres_files.py # PostgreSQL dump generator
│
└── database/                  # Master Operational Database & Relational Assets (Postgres DDL & Dumps)
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
   - Web Speech API integration (SpeechRecognition & SpeechSynthesis).
   - Offline cultural Q&A fallback knowledge base.

---

## 5. Backend & Algorithmic Services (`Dhruva/backend/`)

### Dual Serving Modes
1. **Integrated Server (`backend/server.py`):**
   - Pure Python standard library (`http.server.HTTPServer`).
   - Translates static filesystem requests directly from `Dhruva/frontend/`.
   - Routes `/api/*` requests to relational database queries and itinerary generation.
2. **FastAPI ASGI Server (`backend/app/main.py`):**
   - High-throughput production API with Pydantic validation and interactive Swagger documentation at `/docs`.

### Database Access Layer (`backend/database/db_service.py`)
- Encapsulates queries across 5 normalized relational tables: `CITIES`, `PLACES`, `OPENING_HOURS`, `MIN_INTEREST`, `FESTIVALS`.
- Implements Haversine distance spatial calculations for radius searches and proximity clustering.

### Algorithmic Itinerary Engine (`backend/services/itinerary_engine.py`)
- **Spatial Clustering:** Minimizes inter-place travel transit using coordinates.
- **Interest Scoring Matrix:** Computes affinity vectors across Spiritual, Architecture, History, Culture, and Nature.
- **Pacing & Fatigue Limits:** Modulates daily activity counts based on traveler age and pacing preference (*Relaxed*, *Comfortable*, *Immersive*).
- **Sanctum Scheduling:** Validates visits against recorded opening hours and noon temple rest closures.

---

## 6. REST API Endpoint Specification

| Endpoint | Method | Parameters / Body | Description |
| :--- | :--- | :--- | :--- |
| `/api/health` | `GET` | — | System health status, database path & record counts |
| `/api/cities` | `GET` | — | List all destination cities with place counts |
| `/api/cities/{id}` | `GET` | `id` (int) | Retrieve detailed city metadata |
| `/api/places` | `GET` | `city_id`, `category`, `search`, `min_popularity`, `spiritual`, `architecture`, etc. | Dynamic multi-criteria place filtering |
| `/api/places/nearby`| `GET` | `lat`, `lon`, `max_distance_km`, `limit` | Proximity radius search |
| `/api/places/{id}` | `GET` | `id` (int) | Full place details with opening hours |
| `/api/festivals` | `GET` | `city_id` (optional) | Cultural festivals and dates |
| `/api/itinerary/plan`| `POST`| `city_name`, `num_days`, `age`, `pacing`, `interests` | Algorithmic multi-day itinerary generation |

---

## 7. Development & Operational Commands

```bash
# 1. Integrated Full-Stack Server (Recommended)
python -m backend.server 8000
# Accessible at http://localhost:8000/index.html

# 2. Standalone Frontend Serving
cd frontend && python -m http.server 8000

# 3. FastAPI Production ASGI Server
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```
