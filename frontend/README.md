# DHRUVA Frontend Module

> **Pure Modular Vanilla Web Client (HTML5, CSS3, ES6+ IIFE)**

The `Dhruva/frontend/` module contains the complete client-side application for DHRUVA. It is engineered with zero external build dependencies or bundlers, maximizing accessibility, speed, and maintainability.

---

## 📂 Directory Structure

```text
frontend/
├── index.html                 # Main discovery & landing page
├── pages/                     # Multi-page application views
│   ├── explore.html           # Destination directory & place catalog
│   ├── trip.html              # 4-step conversational trip planner wizard
│   ├── itinerary.html         # Dynamic day-by-day itinerary & cultural guide
│   └── profile.html           # Traveler profile, saved wishlists & preferences
├── css/                       # Tokenized stylesheets
│   ├── variables.css          # Design tokens (colors, typography, spacing, dark mode)
│   ├── style.css              # Base typography, header, search bar, footer
│   ├── components.css         # Reusable UI cards, chips, modals, buttons, toasts
│   ├── voice-orb.css          # Floating voice orb, microphone ripple & canvas visualizer
│   └── responsive.css         # Breakpoints & mobile drawer navigation
├── js/                        # Client application logic (IIFE namespaces)
│   ├── app.js                 # State management (localStorage), theme & accessibility
│   ├── navigation.js          # Route highlighting, sticky header & mobile drawer
│   ├── components.js          # Dynamic HTML card & modal renderers
│   ├── planner.js             # Step wizard state machine & recommendation filters
│   └── voice-orb.js           # Real-time pitch detection, STT/TTS & voice assistant
├── mock/                      # Static mock datasets for standalone frontend operation
│   ├── destinations.json      # Destination highlights, regions & ideal seasons
│   ├── places.json            # Heritage places, temples & opening hours
│   ├── itineraries.json       # Sample structured daily itineraries
│   ├── events.json            # Regional festivals & cultural events
│   └── users.json             # Mock traveler profiles
└── assets/                    # Static assets, images & icons
```

---

## 🚀 Running the Frontend

### Method 1: Integrated Full-Stack Server (Recommended)
Runs both the frontend assets and REST API endpoints from a single command:
```bash
cd Dhruva
python -m backend.server 8000
```
Open **`http://localhost:8000/index.html`** in your browser.

### Method 2: Standalone Static Server
```bash
cd Dhruva/frontend
python -m http.server 8000
```
Open **`http://localhost:8000/index.html`** in your browser.

---

## 🧩 JavaScript Architecture (IIFE Modules)

All frontend scripts use the Immediately Invoked Function Expression (IIFE) pattern exposing modular namespaces:

1. **`DhruvaApp` (`js/app.js`)**:
   - Manages persistent state in `localStorage` under `dhruva_app_state_v1`.
   - Dynamic mock data fetching (`fetchMockData`) with automatic relative path resolution (`mock/` vs `../mock/`).
   - Global toast notification dispatcher (`DhruvaApp.showToast`).
   - Theme manager supporting Light Mode (*Warm Parchment*) and Dark Mode (*Sacred Night*).
   - Accessibility settings (`.text-scale-large`, `.high-contrast`).

2. **`DhruvaNavigation` (`js/navigation.js`)**:
   - Dynamic navigation bar route highlighting for active pages.
   - Header scroll elevation and mobile hamburger drawer.
   - Global keyboard shortcuts (Escape key dismissal of overlays).

3. **`DhruvaPlanner` (`js/planner.js`)**:
   - 4-step trip planning wizard state machine.
   - Live planning summary calculation.
   - Algorithmic filtering of places and dynamic itinerary generation.

4. **`DhruvaComponents` (`js/components.js`)**:
   - Reusable template renderers for Destination Cards, Place Cards, and Itinerary Timelines.
   - Accessible Place Detail Modals with opening schedules and cultural etiquette notes.

5. **`DhruvaVoiceOrb` (`js/voice-orb.js`)**:
   - Real-time vocal pitch detection using autocorrelation algorithm.
   - Audio-reactive HTML5 Canvas golden halo visualizer.
   - Web Speech API integration (SpeechRecognition & SpeechSynthesis).
   - Offline cultural Q&A fallback knowledge base.

---

## 🎨 Styling System & Theme Tokens

Tokens are defined in `css/variables.css`:
- **Light Theme**: Warm Parchment (`#F7F2E8`), Deep Temple Green (`#234A35`), Burnished Brass Gold (`#B99A5B`).
- **Dark Theme (`.dark-theme`)**: Midnight Forest (`#101713`), Dark Sanctum Green (`#16211A`), Radiant Gold (`#D4B26F`).
- **Editorial Typography**: `Cormorant Garamond` (Serif) for headings and `Plus Jakarta Sans` (Sans-serif) for functional UI.
