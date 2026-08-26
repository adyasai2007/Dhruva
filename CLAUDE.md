# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**DHRUVA** ("Your Journey, Guided") is a culturally focused travel-planning platform designed to guide travelers through heritage, spiritual sanctums, and regional traditions of India. The primary target audience includes adults aged 40–65+, requiring readable typography, strong contrast, spacious layouts, accessibility controls, voice assistance, and mindful itinerary pacing.

The repository is modularized into decoupled frontend (`frontend/`), PostgreSQL relational database storage (`database/`), web scraper (`scraper/`), ETL scripts (`scripts/`), and raw/processed data storage (`data/`).

## Development & Serving Commands

### Standalone Frontend Serving
Serve the frontend independently using Python's static HTTP server or any static file server:

```bash
cd frontend
python -m http.server 8000
```
Navigate to `http://localhost:8000/index.html`.

### PostgreSQL Database Setup
```bash
# Load schema and seed data into PostgreSQL
psql -U postgres -d dhruva_db -f database/dhruva_postgres_dump.sql
```

## Architecture & Code Structure

### 1. Frontend Client (`frontend/`)
The frontend is a vanilla web application built without external framework dependencies or bundlers.
- `index.html`: Home page featuring conversational hero search, featured cultural destinations, and seasonal highlights.
- `pages/explore.html`: Discovery directory with region filters, cultural categories, place cards, and best-time guide.
- `pages/trip.html`: Multi-step conversational trip planner wizard (destination, dates, pacing, interests).
- `pages/itinerary.html`: Generated itinerary view displaying day-by-day timelines, activities, transit notes, and cultural tips.
- `pages/profile.html`: "My Plan" and traveler profile managing saved destinations, active journeys, and accessibility preferences.

#### JavaScript Modules (IIFE Pattern in `frontend/js/`)
- `DhruvaApp` (`js/app.js`): Core application controller. Manages state in `localStorage` (`dhruva_app_state_v1`), mock data fetching with relative path resolution (`fetchMockData`), toast notifications, bookmarking (`toggleSaveDestination`), plan saving, dark/light theme switching (`toggleTheme`), and accessibility classes (`text-scale-large`, `high-contrast`).
- `DhruvaNavigation` (`js/navigation.js`): Controls header scroll effects, active route highlighting, mobile drawer navigation, keyboard accessibility (Escape to dismiss modals), and delegated theme/font toggle events.
- `DhruvaPlanner` (`js/planner.js`): Step-by-step wizard logic for `pages/trip.html`. Computes live summary, filters recommendations based on destination and interest criteria, and synthesizes dynamic itineraries.
- `DhruvaComponents` (`js/components.js`): Dynamic HTML template renderers for destination cards, place cards, cultural events, and place detail modals.
- `DhruvaVoiceOrb` (`js/voice-orb.js`): Interactive voice assistant featuring real-time vocal pitch detection (autocorrelation algorithm), an audio-reactive HTML5 Canvas visualizer, Web Speech API (STT/TTS), and a local cultural query knowledge base.

#### Styling & Design System (`frontend/css/`)
- `css/variables.css`: Defines colors (*Warm Parchment* `#F7F2E8`, *Temple Green* `#234A35`, *Brass Gold* `#B99A5B`), typography (`Cormorant Garamond` serif for editorial titles, `Plus Jakarta Sans` for functional UI), spacing scale, radii, shadows, and dark theme tokens under `:root.dark-theme` / `body.dark-theme`.
- `css/style.css`: Base layout, typography scale, header, hero, search bar, and footer.
- `css/components.css`: Reusable UI components (cards, pills, chips, modals, buttons, toasts, timeline).
- `css/voice-orb.css`: Floating voice trigger button, overlay modal, animated canvas halo, and microphone states.
- `css/responsive.css`: Media queries managing mobile drawers, grid collapses, and responsive padding.

#### Mock Data Layer (`frontend/mock/`)
- `destinations.json`: Destination entries with descriptions, regions, ideal visiting months, highlights, and images.
- `places.json`: Heritage places, temples, and craft quarters with opening hours, category, and recommended duration.
- `itineraries.json`: Structured day-by-day sample itineraries with activity sequencing.
- `events.json`: Regional festivals and cultural events with travel tips.
- `users.json`: Mock user profiles and saved trip data.

### 2. PostgreSQL Relational Database (`database/`)
- `dhruva_postgres_dump.sql`: Complete PostgreSQL schema + data dump.
- `postgres_schema.sql` / `dhruva.schema`: PostgreSQL DDL schema definition.
- `postgres_import_csv.sql`: `\copy` bulk data import script.
- `database.sql`: Relational schema reference.
- `csv/`: Normalized relational CSV files for `CITIES`, `PLACES`, `OPENING_HOURS`, `MIN_INTEREST`, `FESTIVALS`, and `USERS_INPUT`.

### 3. Data Scraper & Pipeline (`scraper/`)
- `pipeline.py`: Comprehensive crawler and extraction pipeline for Indian cultural heritage sites.
- `incredible_india/`: Parsers for destination portals.
- `models.py`: Pydantic data schemas for scraped places and attractions.

## Key Development Conventions

- **Frontend Isolation**: All frontend assets (HTML, CSS, JS, mock JSON) reside in `frontend/`.
- **Path Resolution**: When writing scripts or links, note the root vs `pages/` directory hierarchy. In `js/app.js`, `fetchMockData` resolves `mock/` vs `../mock/`.
- **State Management**: Client state is kept in `localStorage` under `dhruva_app_state_v1`. Changes to user preferences or saved plans should go through `DhruvaApp.getState()` and `DhruvaApp.saveState()`.
- **Visual Palette**: Dominant palette consists of warm parchment/cream surfaces (`#F7F2E8`, `#FFFDF8`), deep temple green brand color (`#234A35`), and brass/gold accents (`#B99A5B`). Dark mode uses deep forest/night tones (`#101713`, `#16211A`).
- **Separation of Concerns**: Keep business/data structures in JSON or SQLite and UI rendering in `js/components.js` or dedicated page scripts to allow seamless transition between mock data and the Python REST API.

## gstack

Use the `/browse` skill from gstack for all web browsing. Never use `mcp__claude-in-chrome__*` tools.

Available gstack skills:
- `/office-hours`
- `/plan-ceo-review`
- `/plan-eng-review`
- `/plan-design-review`
- `/design-consultation`
- `/design-shotgun`
- `/design-html`
- `/review`
- `/ship`
- `/land-and-deploy`
- `/canary`
- `/benchmark`
- `/browse`
- `/connect-chrome`
- `/qa`
- `/qa-only`
- `/design-review`
- `/setup-browser-cookies`
- `/setup-deploy`
- `/setup-gbrain`
- `/retro`
- `/investigate`
- `/document-release`
- `/document-generate`
- `/codex`
- `/cso`
- `/autoplan`
- `/plan-devex-review`
- `/devex-review`
- `/careful`
- `/freeze`
- `/guard`
- `/unfreeze`
- `/gstack-upgrade`
- `/learn`
