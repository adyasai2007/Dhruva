-- =====================================================================
-- DHRUVA Cultural Travel Planner - PostgreSQL Relational Database Schema
-- =====================================================================

DROP TABLE IF EXISTS ITINERARY_ITEMS CASCADE;
DROP TABLE IF EXISTS TRIP_TIME_WINDOWS CASCADE;
DROP TABLE IF EXISTS TRIPS CASCADE;
DROP TABLE IF EXISTS OPENING_HOURS CASCADE;
DROP TABLE IF EXISTS MIN_INTEREST CASCADE;
DROP TABLE IF EXISTS CITY_INTEREST CASCADE;
DROP TABLE IF EXISTS FESTIVALS CASCADE;
DROP TABLE IF EXISTS PLACES CASCADE;
DROP TABLE IF EXISTS CITIES CASCADE;

-- ---------------------------------------------------------------------
-- Table 1: CITIES
-- ---------------------------------------------------------------------
CREATE TABLE CITIES (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    state VARCHAR(100) NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    long DOUBLE PRECISION NOT NULL
);

-- ---------------------------------------------------------------------
-- Table 2: CITY_INTEREST (Default City Cultural Profile)
-- ---------------------------------------------------------------------
CREATE TABLE CITY_INTEREST (
    id SERIAL PRIMARY KEY,
    city_id INTEGER NOT NULL UNIQUE,
    architecture DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    history DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    spiritual DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    nature DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    culture DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    CONSTRAINT fk_city_interest_city
        FOREIGN KEY (city_id) REFERENCES CITIES(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Table 3: PLACES (Factual Cultural/Heritage Catalog)
-- ---------------------------------------------------------------------
CREATE TABLE PLACES (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    duration DOUBLE PRECISION NOT NULL,
    duration_label VARCHAR(50),
    lat DOUBLE PRECISION NOT NULL,
    long DOUBLE PRECISION NOT NULL,
    risk VARCHAR(50) NOT NULL,
    city_id INTEGER NOT NULL,
    category VARCHAR(100),
    sub_category VARCHAR(100),
    description TEXT,
    image_url TEXT,
    entry_fee VARCHAR(255),
    source VARCHAR(100),
    source_url TEXT,
    last_updated TIMESTAMP,
    CONSTRAINT fk_places_city
        FOREIGN KEY (city_id) REFERENCES CITIES(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Table 4: OPENING_HOURS
-- ---------------------------------------------------------------------
CREATE TABLE OPENING_HOURS (
    id SERIAL PRIMARY KEY,
    opens_at VARCHAR(20) NOT NULL,
    closes_at VARCHAR(20) NOT NULL,
    place_id INTEGER NOT NULL,
    day_of_week VARCHAR(50) NOT NULL,
    CONSTRAINT fk_hours_place
        FOREIGN KEY (place_id) REFERENCES PLACES(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Table 5: MIN_INTEREST (5D Cultural Affinity Vector)
-- ---------------------------------------------------------------------
CREATE TABLE MIN_INTEREST (
    id SERIAL PRIMARY KEY,
    place_id INTEGER NOT NULL UNIQUE,
    architecture DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    history DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    spiritual DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    nature DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    culture DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    CONSTRAINT fk_interest_place
        FOREIGN KEY (place_id) REFERENCES PLACES(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Table 6: FESTIVALS
-- ---------------------------------------------------------------------
CREATE TABLE FESTIVALS (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    start_date VARCHAR(50) NOT NULL,
    end_date VARCHAR(50) NOT NULL,
    city_id INTEGER NOT NULL,
    description TEXT,
    CONSTRAINT fk_festivals_city
        FOREIGN KEY (city_id) REFERENCES CITIES(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Table 7: TRIPS
-- ---------------------------------------------------------------------
CREATE TABLE TRIPS (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    mode VARCHAR(50) NOT NULL,
    city_id INTEGER NOT NULL,
    start_lat DOUBLE PRECISION NOT NULL,
    start_long DOUBLE PRECISION NOT NULL,
    end_lat DOUBLE PRECISION,
    end_long DOUBLE PRECISION,
    start_datetime TIMESTAMP NOT NULL,
    end_datetime TIMESTAMP NOT NULL,
    total_minutes INTEGER,
    preferences JSONB DEFAULT '{}'::jsonb,
    mandatory_place_ids JSONB DEFAULT '[]'::jsonb,
    shuffle_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_trips_city
        FOREIGN KEY (city_id) REFERENCES CITIES(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Table 8: TRIP_TIME_WINDOWS
-- ---------------------------------------------------------------------
CREATE TABLE TRIP_TIME_WINDOWS (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL,
    day_number INTEGER NOT NULL,
    date DATE NOT NULL,
    window_start TIME NOT NULL,
    window_end TIME NOT NULL,
    start_lat DOUBLE PRECISION,
    start_long DOUBLE PRECISION,
    end_lat DOUBLE PRECISION,
    end_long DOUBLE PRECISION,
    CONSTRAINT fk_time_windows_trip
        FOREIGN KEY (trip_id) REFERENCES TRIPS(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Table 9: ITINERARY_ITEMS
-- ---------------------------------------------------------------------
CREATE TABLE ITINERARY_ITEMS (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL,
    day_number INTEGER NOT NULL,
    sequence_order INTEGER NOT NULL,
    place_id INTEGER NOT NULL,
    arrival_time TIMESTAMP NOT NULL,
    departure_time TIMESTAMP NOT NULL,
    visit_duration_minutes INTEGER NOT NULL,
    travel_time_from_prev_minutes INTEGER NOT NULL,
    travel_distance_km DOUBLE PRECISION NOT NULL,
    is_mandatory BOOLEAN DEFAULT FALSE,
    notes TEXT,
    CONSTRAINT fk_itinerary_items_trip
        FOREIGN KEY (trip_id) REFERENCES TRIPS(id) ON DELETE CASCADE,
    CONSTRAINT fk_itinerary_items_place
        FOREIGN KEY (place_id) REFERENCES PLACES(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Performance Indexes
-- ---------------------------------------------------------------------
CREATE INDEX idx_places_city_id ON PLACES(city_id);
CREATE INDEX idx_opening_hours_place_id ON OPENING_HOURS(place_id);
CREATE INDEX idx_festivals_city_id ON FESTIVALS(city_id);
CREATE INDEX idx_city_interest_city_id ON CITY_INTEREST(city_id);
CREATE INDEX idx_min_interest_place_id ON MIN_INTEREST(place_id);
CREATE INDEX idx_trips_city_id ON TRIPS(city_id);
CREATE INDEX idx_trip_time_windows_trip_id ON TRIP_TIME_WINDOWS(trip_id);
CREATE INDEX idx_itinerary_items_trip_id ON ITINERARY_ITEMS(trip_id);
CREATE INDEX idx_itinerary_items_place_id ON ITINERARY_ITEMS(place_id);
