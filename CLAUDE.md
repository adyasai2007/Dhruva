# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**DHRUVA** ("Your Journey, Guided") is a culturally focused travel-planning web application designed to guide travelers through heritage, spiritual sanctums, and regional traditions of India. The primary target audience includes adults aged 40–65+, requiring readable typography, strong contrast, spacious layouts, and accessible UI controls.

The repository is currently a **pure frontend prototype** (HTML5, CSS3, ES6+ JavaScript, mock JSON) built without external framework dependencies or bundlers. A Python backend is planned for future integration to replace mock data with APIs.

## Development & Serving Commands

Because the app uses JavaScript `fetch()` to load static JSON from `data/mock/`, pages must be served via an HTTP server rather than opened directly via `file://`.

```bash
python -m http.server 8000
```

Once running, navigate to `http://localhost:8000/index.html`.

## Architecture & Code Structure

### 1. Multi-Page Application Layout
- `index.html`: Home page featuring hero search, featured cultural destinations, and seasonal highlights.
- `pages/explore.html`: Discovery directory with region filters, cultural categories, place cards, and best-time guide.
- `pages/trip.html`: Multi-step conversational trip planner wizard (destination, dates, pacing, interests).
- `pages/itinerary.html`: Generated itinerary view displaying day-by-day timelines, activities, transit notes, and cultural tips.
- `pages/profile.html`: "My Plan" and traveler profile managing saved destinations, active journeys, and accessibility preferences.

### 2. JavaScript Modules (IIFE Pattern)
JavaScript code is organized into decoupled global namespaces:
- `DhruvaApp` (`js/app.js`): Core application controller. Manages state in `localStorage` (`dhruva_app_state_v1`), mock data fetching with relative path resolution (`fetchMockData`), toast notifications, bookmarking (`toggleSaveDestination`), plan saving, dark/light theme switching (`toggleTheme`), and accessibility classes (`text-scale-large`, `high-contrast`).
- `DhruvaNavigation` (`js/navigation.js`): Controls header scroll effects, active route highlighting, mobile drawer navigation, keyboard accessibility (Escape to dismiss modals), and delegated theme/font toggle events.
- `DhruvaPlanner` (`js/planner.js`): Step-by-step wizard logic for `pages/trip.html`. Computes live summary, filters recommendations based on destination and interest criteria, and synthesizes dynamic itineraries.
- `DhruvaComponents` (`js/components.js`): Dynamic HTML template renderers for destination cards, place cards, cultural events, and place detail modals.
- `DhruvaVoiceOrb` (`js/voice-orb.js`): Interactive voice assistant featuring real-time vocal pitch detection (autocorrelation algorithm), an audio-reactive HTML5 Canvas visualizer, Web Speech API (STT/TTS), and a local cultural query knowledge base.

### 3. Styling & Design System
Styles are strictly tokenized via CSS custom properties:
- `css/variables.css`: Defines colors, typography (`Cormorant Garamond` serif for editorial titles, `Plus Jakarta Sans` for functional UI), spacing scale, radii, shadows, and dark theme tokens under `:root.dark-theme` / `body.dark-theme`.
- `css/style.css`: Base layout, typography scale, header, hero, search bar, and footer.
- `css/components.css`: Reusable UI components (cards, pills, chips, modals, buttons, toasts, timeline).
- `css/voice-orb.css`: Floating voice trigger button, overlay modal, animated canvas halo, and microphone states.
- `css/responsive.css`: Media queries managing mobile drawers, grid collapses, and responsive padding.

### 4. Mock Data Layer
Located in `data/mock/`:
- `destinations.json`: Destination entries with descriptions, regions, ideal visiting months, highlights, and images.
- `places.json`: Heritage places, temples, and craft quarters with opening hours, category, and recommended duration.
- `itineraries.json`: Structured day-by-day sample itineraries with activity sequencing.
- `events.json`: Regional festivals and cultural events with travel tips.
- `users.json`: Mock user profiles and saved trip data.

## Key Development Conventions

- **Path Resolution**: When writing scripts or links, note the root vs `pages/` directory hierarchy. In `js/app.js`, `fetchMockData` dynamically checks `window.location.pathname` to resolve `data/mock/` vs `../data/mock/`.
- **State Management**: State is kept in `localStorage` under `dhruva_app_state_v1`. Changes to user preferences or saved plans should go through `DhruvaApp.getState()` and `DhruvaApp.saveState()`.
- **Visual Palette**: Dominant palette consists of warm parchment/cream surfaces (`#F7F2E8`, `#FFFDF8`), deep temple green brand color (`#234A35`), and brass/gold accents (`#B99A5B`). Dark mode uses deep forest/night tones (`#101713`, `#16211A`).
- **Separation of Concerns**: Keep business/data structures in JSON and UI rendering in `js/components.js` or dedicated page scripts to allow seamless transition to a future Python REST API.

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
