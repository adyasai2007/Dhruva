-- =========================
-- CITIES
-- =========================
CREATE TABLE cities (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    state TEXT NOT NULL,
    lat REAL NOT NULL,
    long REAL NOT NULL
);

-- =========================
-- PLACES
-- =========================
CREATE TABLE places (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    duration INTEGER NOT NULL,          -- Duration in minutes
    popularity REAL,
    lat REAL NOT NULL,
    long REAL NOT NULL,
    risk REAL
);

-- =========================
-- OPENING HOURS
-- =========================
CREATE TABLE opening_hours (
    id INTEGER PRIMARY KEY,
    opens_at TEXT NOT NULL,             -- Format: HH:MM:SS
    closes_at TEXT NOT NULL,            -- Format: HH:MM:SS
    place_id INTEGER NOT NULL,
    day_of_week TEXT NOT NULL,

    FOREIGN KEY (place_id)
        REFERENCES places(id)
);

-- =========================
-- MINIMUM INTEREST
-- =========================
CREATE TABLE min_interest (
    id INTEGER PRIMARY KEY,
    pre BOOLEAN,
    architecture BOOLEAN,
    history BOOLEAN
);

-- =========================
-- FESTIVALS
-- =========================
CREATE TABLE festivals (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    start_date TEXT NOT NULL,           -- Format: YYYY-MM-DD
    end_date TEXT NOT NULL,             -- Format: YYYY-MM-DD
    city_id INTEGER NOT NULL,

    FOREIGN KEY (city_id)
        REFERENCES cities(id)
);