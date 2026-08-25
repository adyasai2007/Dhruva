# DHRUVA --- Product & Agent Specification

## 1. Product Overview

**Product:** DHRUVA\
**Tagline direction:** Your Journey, Guided.

DHRUVA is a culturally focused travel-planning web application that
helps travelers discover meaningful destinations and organize
personalized journeys around Indian cities and regions.

The product is inspired by the idea of **Dhruva, the guiding star**. The
application should guide users through travel planning instead of
presenting them with a dense collection of disconnected tourist
information.

The first implementation is **web-first**, with responsive architecture
so the same design system can later be adapted into a dedicated mobile
experience.

------------------------------------------------------------------------

## 2. Problem

Travel planning requires combining many separate pieces of information:

-   destinations and places
-   cultural and heritage interests
-   opening hours
-   available time
-   trip dates
-   travel duration
-   seasonal considerations
-   events
-   route practicality
-   personal preferences

Generic travel platforms often provide lists of attractions without
turning those inputs into a coherent cultural journey.

DHRUVA aims to reduce this planning burden by turning user preferences
and destination information into a clear, understandable travel plan.

------------------------------------------------------------------------

## 3. Target Users

### Primary audience

Adults approximately **40--65+** who want meaningful cultural travel
without an unnecessarily complicated planning interface.

This means the product must prioritize:

-   readable typography
-   strong visual hierarchy
-   comfortable spacing
-   obvious actions
-   clear navigation
-   accessible controls
-   restrained animation

### Secondary audience

Younger travelers, families, students, and other travelers interested in
Indian culture, heritage, history, food, architecture, local
experiences, and structured travel planning.

------------------------------------------------------------------------

## 4. Geographic Scope

The initial focus is on major cities and destinations across:

-   North India
-   South India
-   East India
-   West India

The frontend must be data-driven rather than hard-coded to a single
destination, so additional cities can be introduced later through data.

------------------------------------------------------------------------

## 5. Core User Journey

``` text
Home
  ↓
Choose / search destination
  ↓
Choose date
  ↓
Choose available time / duration
  ↓
Select interests
  ↓
Generate personalized plan
  ↓
Explore recommended places
  ↓
Adjust / refine plan
  ↓
View itinerary
  ↓
Save / manage My Plan
```

The experience should feel like guided planning, not a long technical
questionnaire.

------------------------------------------------------------------------

## 6. Core Features

### 6.1 Destination Discovery

Users can discover destinations and culturally relevant places.

Potential information:

-   destination/place name
-   location
-   description
-   cultural significance
-   category
-   image
-   recommended duration
-   opening/closing information
-   best time information

### 6.2 Personalized Trip Planning

The planner should collect information such as:

-   destination
-   date
-   available start/end time
-   number of days
-   interests
-   optional preferences

The frontend will initially demonstrate this using mock JSON data.

### 6.3 Cultural and Heritage Discovery

DHRUVA should emphasize meaningful cultural exploration.

Potential categories:

-   heritage
-   temples / spiritual places
-   architecture
-   museums
-   markets
-   food
-   local culture
-   festivals / events
-   nature
-   historical landmarks

### 6.4 Best Time

The application should help users understand when and how a place is
best experienced.

Potential information:

-   best visiting period
-   recommended time of day
-   opening hours
-   seasonal information
-   crowd considerations
-   event periods

### 6.5 Itinerary

Generated plans should be represented as understandable itineraries
containing:

-   day
-   time
-   place
-   activity
-   estimated duration
-   travel transition
-   notes
-   alternatives where applicable

### 6.6 Voice Assistance

Voice assistance is a planned product feature.

A **custom visual halo** will be designed separately. For this phase,
only treat voice as a product capability and reserve a sensible
interaction point for it.

Do not implement or specify the final halo yet, and do not assume a
particular speech or AI backend.

### 6.7 My Plan

Users should have a personal area for saved/current trips.

Potential content:

-   current trip
-   upcoming trip
-   saved itinerary
-   destination
-   dates
-   plan status
-   quick access to itinerary

------------------------------------------------------------------------

## 7. Frontend Scope

The current phase is **frontend/UI only**.

Use:

-   HTML
-   CSS
-   JavaScript
-   static/mock JSON

The Python backend will be developed separately by other team members.

Do not make assumptions about:

-   Python framework
-   database
-   AI/recommendation implementation
-   API architecture
-   authentication implementation
-   external services

The frontend should simply remain modular enough to integrate with a
future backend.

### Future boundary

``` text
DHRUVA FRONTEND
HTML
CSS
JavaScript
UI state
Reusable components
Mock JSON
        │
        │ Future API integration
        ▼
DHRUVA BACKEND
Python
Business logic
Recommendation / AI logic
Database
External services
APIs
```

------------------------------------------------------------------------

## 8. Mock Data

Use static JSON during UI development.

Recommended structure:

``` text
data/
└── mock/
    ├── destinations.json
    ├── places.json
    ├── itineraries.json
    ├── events.json
    └── users.json
```

Do not put large datasets directly inside HTML.

Mock data should resemble realistic backend response structures so the
frontend can later replace local JSON with API responses without
requiring a major UI rewrite.

------------------------------------------------------------------------

## 9. Modular Folder Structure

``` text
DHRUVA/
│
├── agents.md
├── design.md
├── README.md
│
├── index.html
│
├── pages/
│   ├── explore.html
│   ├── trip.html
│   ├── itinerary.html
│   └── profile.html
│
├── css/
│   ├── style.css
│   ├── responsive.css
│   ├── components.css
│   └── variables.css
│
├── js/
│   ├── app.js
│   ├── navigation.js
│   ├── planner.js
│   └── components.js
│
├── data/
│   └── mock/
│       ├── destinations.json
│       ├── places.json
│       ├── itineraries.json
│       ├── events.json
│       └── users.json
│
└── assets/
    ├── images/
    ├── icons/
    └── fonts/
```

------------------------------------------------------------------------

## 10. File Responsibilities

-   `index.html`: DHRUVA home/landing experience.
-   `pages/explore.html`: destination and place discovery.
-   `pages/trip.html`: trip planning flow.
-   `pages/itinerary.html`: detailed generated itinerary.
-   `pages/profile.html`: profile and saved-plan area.
-   `css/variables.css`: global design tokens.
-   `css/style.css`: global/page styles.
-   `css/components.css`: reusable component styles.
-   `css/responsive.css`: responsive behavior.
-   `js/app.js`: application initialization/shared behavior.
-   `js/navigation.js`: navigation and page transitions/state.
-   `js/planner.js`: planner interactions using mock data.
-   `js/components.js`: reusable component behavior.
-   `data/mock/`: temporary frontend data.
-   `assets/`: imagery, icons, and fonts.

------------------------------------------------------------------------

## 11. Design-to-Backend Handoff

The intended future replacement is:

``` text
mock JSON → API responses
```

Therefore:

-   keep UI rendering separate from data
-   avoid destination-specific business logic in HTML/CSS
-   use reusable components
-   keep data fields meaningful
-   do not couple the frontend to an assumed Python implementation

The exact backend architecture is intentionally outside this document.

------------------------------------------------------------------------

## 12. Non-Goals for Current Phase

Do not implement:

-   Python backend
-   database
-   production authentication
-   real recommendation engine
-   real weather integration
-   real event integration
-   production voice recognition
-   custom voice halo
-   payment systems
-   deployment infrastructure

These are future integration concerns.

------------------------------------------------------------------------

## 13. Development Priority

``` text
1. Design system
2. Global layout
3. Navigation
4. Home
5. Explore
6. Trip planner
7. Itinerary
8. My Plan / Profile
9. Responsive behavior
10. Interaction polish
11. Mock-data integration
12. Backend handoff preparation
```

The UI should be stabilized before introducing backend assumptions.
