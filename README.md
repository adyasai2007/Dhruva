# DHRUVA

> **Your Journey, Guided.**

DHRUVA is a culturally focused travel-planning web application designed
to help travelers discover destinations and create meaningful,
personalized journeys.

## Current Phase

This repository is currently focused on the **frontend/UI design**.

The backend will be developed separately in Python by other team
members.

### Current stack

-   HTML
-   CSS
-   JavaScript
-   Static/mock JSON data

## Documentation

  -----------------------------------------------------------------------
  File                                Purpose
  ----------------------------------- -----------------------------------
  `agents.md`                         Product requirements, feature
                                      scope, architecture boundaries, and
                                      development guidance

  `design.md`                         Visual identity, design system, UI
                                      rules, and reference direction

  `README.md`                         Project overview and development
                                      orientation
  -----------------------------------------------------------------------

## Project Structure

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

## Development Principles

1.  Keep UI and data separate.
2.  Use reusable components and design tokens.
3.  Keep mock data in JSON.
4.  Avoid assumptions about the future Python backend.
5.  Build web/desktop first while keeping responsive adaptation
    possible.
6.  Prioritize readability and accessibility.
7.  Maintain one consistent DHRUVA visual language across all pages.

## Planned Screens

-   Home
-   Explore
-   Trip Planner
-   Itinerary
-   My Plan / Profile

## Future Integration

The frontend should eventually consume backend/API data instead of mock
JSON.

The Python backend architecture, database, AI/recommendation system, and
external service integrations are intentionally outside the current
frontend specification.
