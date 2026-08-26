-- =====================================================================
-- DHRUVA Cultural Travel Planner - Relational Database Schema
-- Compatible with SQLite3 & PostgreSQL
-- =====================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------
-- Table 1: CITIES
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS OPENING_HOURS;
DROP TABLE IF EXISTS MIN_INTEREST;
DROP TABLE IF EXISTS FESTIVALS;
DROP TABLE IF EXISTS USERS_INPUT;
DROP TABLE IF EXISTS PLACES;
DROP TABLE IF EXISTS CITIES;

CREATE TABLE CITIES (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    state VARCHAR(100) NOT NULL,
    lat REAL NOT NULL,
    long REAL NOT NULL
);

-- ---------------------------------------------------------------------
-- Table 2: PLACES
-- ---------------------------------------------------------------------
CREATE TABLE PLACES (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    duration REAL NOT NULL,                    -- Duration in hours (e.g. 1.5, 2.0, 3.0)
    duration_label VARCHAR(50),                -- Human readable (e.g. '1.5 to 2 Hours')
    popularity REAL NOT NULL,                  -- Popularity rating (1.0 to 5.0 scale)
    lat REAL NOT NULL,
    long REAL NOT NULL,
    risk VARCHAR(50) NOT NULL,                 -- Risk level ('Low', 'Moderate', 'Guarded')
    city_id INTEGER NOT NULL,
    category VARCHAR(100),
    sub_category VARCHAR(100),
    description TEXT,
    image_url TEXT,                            -- Clean, working Scene7 CDN asset URL
    entry_fee VARCHAR(255),
    FOREIGN KEY (city_id) REFERENCES CITIES(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Table 3: OPENING_HOURS
-- ---------------------------------------------------------------------
CREATE TABLE OPENING_HOURS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opens_at VARCHAR(20) NOT NULL,             -- e.g. '06:00 AM' or '06:00:00'
    closes_at VARCHAR(20) NOT NULL,            -- e.g. '07:00 PM' or '19:00:00'
    place_id INTEGER NOT NULL,
    day_of_week VARCHAR(50) NOT NULL,          -- e.g. 'Monday', 'Tuesday', ... or 'All Days'
    FOREIGN KEY (place_id) REFERENCES PLACES(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Table 4: MIN_INTEREST (Interest Scores & Feature Weights)
-- ---------------------------------------------------------------------
CREATE TABLE MIN_INTEREST (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    place_id INTEGER NOT NULL UNIQUE,
    architecture REAL NOT NULL DEFAULT 0.0,    -- Score 0.0 - 5.0
    history REAL NOT NULL DEFAULT 0.0,         -- Score 0.0 - 5.0
    spiritual REAL NOT NULL DEFAULT 0.0,       -- Score 0.0 - 5.0
    nature REAL NOT NULL DEFAULT 0.0,          -- Score 0.0 - 5.0
    culture REAL NOT NULL DEFAULT 0.0,         -- Score 0.0 - 5.0
    FOREIGN KEY (place_id) REFERENCES PLACES(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Table 5: FESTIVALS
-- ---------------------------------------------------------------------
CREATE TABLE FESTIVALS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    start_date VARCHAR(50) NOT NULL,           -- e.g. '2026-06-27' or 'June'
    end_date VARCHAR(50) NOT NULL,             -- e.g. '2026-07-06' or 'July'
    city_id INTEGER NOT NULL,
    description TEXT,
    FOREIGN KEY (city_id) REFERENCES CITIES(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Table 6: USERS - INPUT (Itinerary Generation Request Log & Parameters)
-- ---------------------------------------------------------------------
CREATE TABLE USERS_INPUT (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gps_location VARCHAR(100) NOT NULL,        -- 'lat,long' or city name
    start_date VARCHAR(50) NOT NULL,           -- 'YYYY-MM-DD'
    start_time VARCHAR(20) NOT NULL,           -- 'HH:MM:SS' or '08:00 AM'
    end_time VARCHAR(20) NOT NULL,             -- 'HH:MM:SS' or '20:00 PM'
    age INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------
-- Indexes for Fast Querying
-- ---------------------------------------------------------------------
CREATE INDEX idx_places_city_id ON PLACES(city_id);
CREATE INDEX idx_places_popularity ON PLACES(popularity);
CREATE INDEX idx_opening_hours_place_id ON OPENING_HOURS(place_id);
CREATE INDEX idx_festivals_city_id ON FESTIVALS(city_id);
CREATE INDEX idx_min_interest_place_id ON MIN_INTEREST(place_id);
