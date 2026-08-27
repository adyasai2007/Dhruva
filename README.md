# DHRUVA

> **Your Journey, Guided.**

DHRUVA is an intelligent, culturally guided travel-planning platform designed to curate mindful journeys through India’s living heritage, sacred sanctums, architectural wonders, and regional traditions. Tailored with deep respect for accessibility and cultural depth, DHRUVA features readable typography, spacious layouts, accessibility controls, voice assistance, and algorithmic itinerary generation.

---

## 🏗️ Architecture & Project Structure

The project is modularized into distinct, decoupled subsystems:

```
Dhruva/
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
│   │   └── voice-orb.js       # Real-time pitch detection, STT/TTS & voice assistant
│   ├── mock/                  # Static mock datasets for standalone frontend operation
│   │   ├── destinations.json  # Destination highlights, regions & ideal seasons
│   │   ├── places.json        # Heritage places, temples & opening hours
│   │   ├── itineraries.json   # Sample structured daily itineraries
│   │   ├── events.json        # Regional festivals & cultural events
│   │   └── users.json         # Mock traveler profiles
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
│   ├── models.py              # Pydantic data models for places & destinations
│   ├── common/                # Crawler, geocoder, normalizer & exporter utilities
│   └── incredible_india/      # Incredible India portal scrapers & parsers
│
├── data/                      # 📊 Data Pipeline Storage
│   ├── processed/             # Cleaned relational CSV tables
│   └── scraped/               # Raw crawler payloads & normalization reports
│
├── scripts/                   # 🛠️ Database Maintenance & Inspection Utilities
│   ├── verify_db.py           # Database integrity and relation validation script
│   └── generate_postgres_files.py # PostgreSQL dump & migration script generator
│
└── [Documentation]            # agents.md, design.md, CLAUDE.md, README.md
```

---

## ✨ Implemented Features

### 1. Rich Cultural Frontend Experience
- **Hero & Cultural Discovery**: Conversational destination search with quick-filter pills.
- **Explore Directory (`pages/explore.html`)**: Filter by region (North, South, East, West, Central) and cultural categories (Spiritual, Royal Heritage, Craft, Architecture).
- **Interactive Trip Planner (`pages/trip.html`)**: 4-step wizard capturing dates, pacing, group size, and cultural interest affinities.
- **Dynamic Itinerary (`pages/itinerary.html`)**: Time-slotted daily plan showing visiting hours, transit times, and cultural etiquette tips.
- **Profile & Wishlist (`pages/profile.html`)**: Saved destinations, active itineraries, and custom accessibility toggles.

### 2. Audio-Reactive Voice Assistant ("Dhruva Voice Orb")
- **Pitch Detection Engine**: Real-time vocal fundamental frequency analysis using the autocorrelation algorithm.
- **HTML5 Canvas Visualizer**: Dynamic animated golden-brass halo that expands and reacts to speaking volume and pitch.
- **Speech Synthesis & Recognition**: Web Speech API (SpeechRecognition + SpeechSynthesis) with fallback cultural Q&A knowledge base.

### 3. PostgreSQL Database & Seed Data (`database/`)
- **Full Relational Schema**: 5 interconnected tables (`CITIES`, `PLACES`, `OPENING_HOURS`, `MIN_INTEREST`, `FESTIVALS`) with foreign keys and performance indexes.
- **Ready-to-Deploy SQL Dump**: `dhruva_postgres_dump.sql` for instant one-step initialization.

---

## 🚀 Quick Start Guide

### 1. Run Frontend Application
Serve static files using any HTTP server:

```bash
cd Dhruva/frontend
python -m http.server 8000
```
Open your browser at: **`http://localhost:8000/index.html`**

### 2. Initialize PostgreSQL Database
Load the schema and seed data into your PostgreSQL instance:

```bash
psql -U postgres -d dhruva_db -f Dhruva/database/dhruva_postgres_dump.sql
```

---

## 📚 Documentation Index

- **`CLAUDE.md`**: Project architecture, development guidelines, and CLI workflow.
- **`agents.md`**: Product requirements, feature roadmap, and agent specifications.
- **`design.md`**: Visual identity, design tokens, color palette, and UX specifications.
- **`frontend/README.md`**: Frontend client documentation, components, and module guide.
- **`database/README.md`**: PostgreSQL setup, schemas, and import guide.
