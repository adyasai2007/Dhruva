# DHRUVA

> **Your Journey, Guided.**

DHRUVA is an intelligent, culturally guided travel-planning platform designed to curate mindful journeys through India’s living heritage, sacred sanctums, architectural wonders, and regional traditions. Tailored with deep respect for accessibility and cultural depth, DHRUVA features readable typography, spacious layouts, accessibility controls, real-time Gemini Live voice assistance, and algorithmic multi-day itinerary generation.

---

## 🏗️ Architecture & Project Structure

The project is modularized into distinct, decoupled subsystems:

```
Dhruva/
├── backend/                   # ⚡ Core Python Backend & Engine Services
│   ├── server.py              # High-performance HTTP REST API & static file server
│   ├── live_websocket_server.py # Bidirectional Gemini Live WebSocket audio streaming server
│   ├── config.py              # Application settings & environment configuration
│   ├── database/              # SQLite/PostgreSQL data repository & DB service layer
│   │   ├── db.py              # Thread-safe in-memory/disk data repository
│   │   ├── db_service.py      # High-level database access & query methods
│   │   └── models.py          # Data models (City, Place, OpeningHour, MinInterest, Trip)
│   ├── algorithm/             # 5D Scoring & Itinerary Generation Algorithms
│   │   ├── scoring.py         # 5D cosine similarity & multi-factor utility scoring
│   │   └── itinerary_generator.py # Multi-day time-window & fatigue-pacing generator
│   ├── routing/               # Matrix Routing & Transit Calculation
│   │   └── ors_client.py      # OpenRouteService matrix client with Haversine fallback
│   ├── services/              # High-level Business Logic Services
│   │   ├── itinerary_engine.py # Cultural itinerary engine with fatigue & schedule validation
│   │   └── voice_assistant.py  # Gemini Live function calling & NLP fallback service
│   └── tests/                 # Comprehensive test suite (76 unit & integration tests)
│
├── frontend/                  # ✨ Pure Modular Frontend Client (HTML5, CSS3, ES6+)
│   ├── index.html             # Main discovery & landing page
│   ├── pages/                 # Multi-page application views
│   │   ├── explore.html       # Destination directory & place catalog
│   │   ├── trip.html          # 4-Step conversational trip planner wizard
│   │   ├── itinerary.html     # Dynamic day-by-day itinerary & cultural guide
│   │   └── profile.html       # Traveler profile, saved wishlists & preferences
│   ├── css/                   # Tokenized stylesheets
│   │   ├── variables.css      # Design tokens (colors, typography, spacing, dark mode)
│   │   ├── style.css          # Base typography, header, search bar, footer
│   │   ├── components.css     # Reusable UI cards, chips, modals, buttons, toasts
│   │   ├── voice-orb.css      # Floating voice orb, microphone ripple & canvas visualizer
│   │   └── responsive.css     # Breakpoints & mobile drawer navigation
│   ├── js/                    # Client application logic (IIFE namespaces)
│   │   ├── app.js             # State management (localStorage), theme & accessibility
│   │   ├── navigation.js      # Route highlighting, sticky header & mobile drawer
│   │   ├── components.js      # Dynamic HTML card & modal renderers
│   │   ├── planner.js         # Step wizard state machine & recommendation filters
│   │   └── voice-orb.js       # Real-time Web Audio streaming to Gemini Live WebSocket
│   ├── mock/                  # Static mock datasets for standalone frontend operation
│   └── assets/                # Static assets, images & icons
│
├── database/                  # 🐘 PostgreSQL Database Dumps, Schemas & Relational CSVs
│   ├── README.md              # Database documentation & setup instructions
│   ├── dhruva_postgres_dump.sql # Full PostgreSQL dump (schema + all seed data)
│   ├── postgres_schema.sql    # PostgreSQL DDL schema definition
│   ├── postgres_import_csv.sql # PostgreSQL CSV bulk copy script
│   ├── dhruva.schema          # PostgreSQL DDL schema
│   ├── database.sql           # Relational schema reference
│   └── csv/                   # Normalized relational CSV tables (CITIES, PLACES, etc.)
│
├── scraper/                   # 🌐 Web Scraping & Data Pipeline Suite
│   ├── pipeline.py            # End-to-end extraction, normalization & geocoding
│   ├── cli.py                 # Command-line interface for scrapers
│   ├── llm_processor.py       # LLM extraction & enrichment helper
│   ├── mediawiki_client.py    # Wikipedia & MediaWiki API crawler
│   ├── search_client.py       # Web search & information retriever
│   └── odisha_data.py         # Seed dataset definitions
│
├── scripts/                   # 🛠️ Utilities & Standalone Tools
│   ├── live_audio_stream.py   # Standalone PyAudio client for Gemini Live API
│   ├── run_live_assistant.py  # Local terminal voice assistant with DB tool execution
│   └── sync_frontend_mock.py  # Database to mock JSON synchronization script
│
└── [Documentation]            # agents.md, design.md, CLAUDE.md, README.md
```

---

## ✨ Implemented Features

### 1. Real-Time Gemini Live Audio Assistant ("Dhruva Voice Orb")
- **Bidirectional Streaming**: Low-latency PCM audio streaming between the browser and Google Gemini Live API (`gemini-3.1-flash-live-preview`) over WebSockets (`ws://localhost:8001`).
- **Live Tool Execution**: Gemini triggers real-time function calls (`search_places`, `get_place_details`, `create_itinerary`, `navigate_ui`), which are executed against the local database and returned to the model for conversational speech delivery.
- **Audio-Reactive Visualizer**: Fluid multi-layer golden-brass canvas orb with real-time vocal pitch autocorrelation and audio energy reactive ripples.
- **Dynamic Frontend Navigation**: Seamless voice commands that open place modals or navigate directly to generated itineraries.

### 2. Algorithmic Itinerary & Recommendation Engine
- **5D MIN_INTEREST Cosine Ranking**: Ranks cultural places across Spiritual, Architecture, History, Nature, and Living Culture dimensions.
- **Mindful Fatigue Pacing**: Custom pace profiles (`relaxed`, `balanced`, `intensive`) with midday sanctum rest buffers and senior-friendly travel scheduling.
- **Matrix Routing**: OpenRouteService transit calculation with road-winding Haversine fallback.

### 3. Rich Cultural Frontend Experience
- **Explore Directory (`pages/explore.html`)**: Filter by region and cultural categories with verified opening hours and etiquette.
- **Interactive Trip Planner (`pages/trip.html`)**: 4-step wizard capturing dates, pacing, group size, and cultural interest affinities.
- **Dynamic Itinerary (`pages/itinerary.html`)**: Time-slotted daily plan showing visiting hours, transit times, and cultural etiquette tips.
- **Profile & Wishlist (`pages/profile.html`)**: Saved destinations, active itineraries, and custom accessibility toggles.

---

## 🚀 Quick Start Guide

### 1. Start the HTTP Backend & REST API Server
```bash
python Dhruva/backend/server.py 8000
```
Open your browser at: **`http://localhost:8000/index.html`**

### 2. Start the Gemini Live WebSocket Server
In a separate terminal:
```bash
python Dhruva/backend/live_websocket_server.py
```

### 3. Run Backend Test Suite
```bash
python -m pytest Dhruva/backend/tests
```

### 4. Initialize PostgreSQL Database (Optional)
```bash
psql -U postgres -d dhruva_db -f Dhruva/database/dhruva_postgres_dump.sql
```

---

## 📚 Documentation Index

- **`CLAUDE.md`**: Project architecture, development guidelines, and CLI workflow.
- **`agents.md`**: Product requirements, feature roadmap, and agent specifications.
- **`design.md`**: Visual identity, design tokens, color palette, and UX specifications.
- **`database/README.md`**: PostgreSQL setup, schemas, and import guide.
