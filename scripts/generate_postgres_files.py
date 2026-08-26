"""
DHRUVA PostgreSQL & Relational Database Exporter
Generates PostgreSQL DDL schema (.schema, .sql), Full PostgreSQL data dump (.sql),
CSV COPY script (.sql), and updates the SQLite database (.db).
"""

import sqlite3
from pathlib import Path
import shutil

def generate():
    db_path = Path("backend/database/dhruva.db")
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. PostgreSQL Schema Definition
    postgres_schema = """-- =====================================================================
-- DHRUVA Cultural Travel Planner - PostgreSQL Relational Database Schema
-- =====================================================================

DROP TABLE IF EXISTS OPENING_HOURS CASCADE;
DROP TABLE IF EXISTS MIN_INTEREST CASCADE;
DROP TABLE IF EXISTS FESTIVALS CASCADE;
DROP TABLE IF EXISTS USERS_INPUT CASCADE;
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
-- Table 2: PLACES
-- ---------------------------------------------------------------------
CREATE TABLE PLACES (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    duration DOUBLE PRECISION NOT NULL,
    duration_label VARCHAR(50),
    popularity DOUBLE PRECISION NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    long DOUBLE PRECISION NOT NULL,
    risk VARCHAR(50) NOT NULL,
    city_id INTEGER NOT NULL,
    category VARCHAR(100),
    sub_category VARCHAR(100),
    description TEXT,
    image_url TEXT,
    entry_fee VARCHAR(255),
    CONSTRAINT fk_places_city FOREIGN KEY (city_id) REFERENCES CITIES(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Table 3: OPENING_HOURS
-- ---------------------------------------------------------------------
CREATE TABLE OPENING_HOURS (
    id SERIAL PRIMARY KEY,
    opens_at VARCHAR(20) NOT NULL,
    closes_at VARCHAR(20) NOT NULL,
    place_id INTEGER NOT NULL,
    day_of_week VARCHAR(50) NOT NULL,
    CONSTRAINT fk_hours_place FOREIGN KEY (place_id) REFERENCES PLACES(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Table 4: MIN_INTEREST
-- ---------------------------------------------------------------------
CREATE TABLE MIN_INTEREST (
    id SERIAL PRIMARY KEY,
    place_id INTEGER NOT NULL UNIQUE,
    architecture DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    history DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    spiritual DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    nature DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    culture DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    CONSTRAINT fk_interest_place FOREIGN KEY (place_id) REFERENCES PLACES(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Table 5: FESTIVALS
-- ---------------------------------------------------------------------
CREATE TABLE FESTIVALS (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    start_date VARCHAR(50) NOT NULL,
    end_date VARCHAR(50) NOT NULL,
    city_id INTEGER NOT NULL,
    description TEXT,
    CONSTRAINT fk_festivals_city FOREIGN KEY (city_id) REFERENCES CITIES(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Table 6: USERS_INPUT
-- ---------------------------------------------------------------------
CREATE TABLE USERS_INPUT (
    id SERIAL PRIMARY KEY,
    gps_location VARCHAR(100) NOT NULL,
    start_date VARCHAR(50) NOT NULL,
    start_time VARCHAR(20) NOT NULL,
    end_time VARCHAR(20) NOT NULL,
    age INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------
-- Performance Indexes
-- ---------------------------------------------------------------------
CREATE INDEX idx_places_city_id ON PLACES(city_id);
CREATE INDEX idx_places_popularity ON PLACES(popularity);
CREATE INDEX idx_opening_hours_place_id ON OPENING_HOURS(place_id);
CREATE INDEX idx_festivals_city_id ON FESTIVALS(city_id);
CREATE INDEX idx_min_interest_place_id ON MIN_INTEREST(place_id);
"""

    def escape_sql(val):
        if val is None:
            return "NULL"
        if isinstance(val, (int, float)):
            return str(val)
        s = str(val).replace("'", "''")
        return f"'{s}'"

    # 2. Build PostgreSQL SQL Dump with full INSERT statements
    dump_lines = [
        postgres_schema,
        "\n-- =====================================================================",
        "-- DATA POPULATION (INSERT STATEMENTS)",
        "-- =====================================================================\n"
    ]

    # CITIES
    cursor.execute("SELECT id, name, state, lat, long FROM CITIES ORDER BY id")
    cities = cursor.fetchall()
    dump_lines.append("-- 1. Populate CITIES")
    for c in cities:
        dump_lines.append(f"INSERT INTO CITIES (id, name, state, lat, long) VALUES ({c[0]}, {escape_sql(c[1])}, {escape_sql(c[2])}, {c[3]}, {c[4]});")

    # PLACES
    cursor.execute("SELECT id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee FROM PLACES ORDER BY id")
    places = cursor.fetchall()
    dump_lines.append("\n-- 2. Populate PLACES")
    for p in places:
        dump_lines.append(
            f"INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) "
            f"VALUES ({p[0]}, {escape_sql(p[1])}, {p[2]}, {escape_sql(p[3])}, {p[4]}, {p[5]}, {p[6]}, {escape_sql(p[7])}, {p[8]}, {escape_sql(p[9])}, {escape_sql(p[10])}, {escape_sql(p[11])}, {escape_sql(p[12])}, {escape_sql(p[13])});"
        )

    # OPENING_HOURS
    cursor.execute("SELECT id, opens_at, closes_at, place_id, day_of_week FROM OPENING_HOURS ORDER BY id")
    hours = cursor.fetchall()
    dump_lines.append("\n-- 3. Populate OPENING_HOURS")
    for h in hours:
        dump_lines.append(f"INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES ({h[0]}, {escape_sql(h[1])}, {escape_sql(h[2])}, {h[3]}, {escape_sql(h[4])});")

    # MIN_INTEREST
    cursor.execute("SELECT id, place_id, architecture, history, spiritual, nature, culture FROM MIN_INTEREST ORDER BY id")
    interests = cursor.fetchall()
    dump_lines.append("\n-- 4. Populate MIN_INTEREST")
    for mi in interests:
        dump_lines.append(f"INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES ({mi[0]}, {mi[1]}, {mi[2]}, {mi[3]}, {mi[4]}, {mi[5]}, {mi[6]});")

    # FESTIVALS
    cursor.execute("SELECT id, name, start_date, end_date, city_id, description FROM FESTIVALS ORDER BY id")
    festivals = cursor.fetchall()
    dump_lines.append("\n-- 5. Populate FESTIVALS")
    for f in festivals:
        dump_lines.append(f"INSERT INTO FESTIVALS (id, name, start_date, end_date, city_id, description) VALUES ({f[0]}, {escape_sql(f[1])}, {escape_sql(f[2])}, {escape_sql(f[3])}, {f[4]}, {escape_sql(f[5])});")

    # USERS_INPUT
    cursor.execute("SELECT id, gps_location, start_date, start_time, end_time, age FROM USERS_INPUT ORDER BY id")
    users = cursor.fetchall()
    dump_lines.append("\n-- 6. Populate USERS_INPUT")
    for u in users:
        dump_lines.append(f"INSERT INTO USERS_INPUT (id, gps_location, start_date, start_time, end_time, age) VALUES ({u[0]}, {escape_sql(u[1])}, {escape_sql(u[2])}, {escape_sql(u[3])}, {escape_sql(u[4])}, {u[5]});")

    # Reset PostgreSQL Serial Sequences
    dump_lines.append("\n-- =====================================================================")
    dump_lines.append("-- Reset Sequences in PostgreSQL for AUTO_INCREMENT")
    dump_lines.append("-- =====================================================================")
    dump_lines.append("SELECT setval('cities_id_seq', (SELECT COALESCE(MAX(id), 1) FROM CITIES));")
    dump_lines.append("SELECT setval('places_id_seq', (SELECT COALESCE(MAX(id), 1) FROM PLACES));")
    dump_lines.append("SELECT setval('opening_hours_id_seq', (SELECT COALESCE(MAX(id), 1) FROM OPENING_HOURS));")
    dump_lines.append("SELECT setval('min_interest_id_seq', (SELECT COALESCE(MAX(id), 1) FROM MIN_INTEREST));")
    dump_lines.append("SELECT setval('festivals_id_seq', (SELECT COALESCE(MAX(id), 1) FROM FESTIVALS));")
    dump_lines.append("SELECT setval('users_input_id_seq', (SELECT COALESCE(MAX(id), 1) FROM USERS_INPUT));")

    full_dump_sql = "\n".join(dump_lines)

    # 3. CSV Import SQL script (for \copy CLI command)
    csv_import_sql = """-- =====================================================================
-- DHRUVA PostgreSQL CSV Direct Import Script
-- Run via psql CLI in your terminal inside the folder containing the CSVs:
--   psql -U <username> -d <dbname> -f postgres_import_csv.sql
-- =====================================================================

\\copy CITIES(id, name, state, lat, long) FROM 'cities.csv' WITH (FORMAT csv, HEADER true);
\\copy PLACES(id, name, duration, popularity, lat, long, risk, city_id, category, sub_category, duration_label, image_url, entry_fee, description) FROM 'places.csv' WITH (FORMAT csv, HEADER true);
\\copy OPENING_HOURS(id, opens_at, closes_at, place_id, day_of_week) FROM 'opening_hours.csv' WITH (FORMAT csv, HEADER true);
\\copy MIN_INTEREST(id, place_id, architecture, history, spiritual, nature, culture) FROM 'min_interest.csv' WITH (FORMAT csv, HEADER true);
\\copy FESTIVALS(id, name, start_date, end_date, city_id, description) FROM 'festivals.csv' WITH (FORMAT csv, HEADER true);
\\copy USERS_INPUT(id, gps_location, start_date, start_time, end_time, age) FROM 'users_input.csv' WITH (FORMAT csv, HEADER true);

SELECT setval('cities_id_seq', (SELECT COALESCE(MAX(id), 1) FROM CITIES));
SELECT setval('places_id_seq', (SELECT COALESCE(MAX(id), 1) FROM PLACES));
SELECT setval('opening_hours_id_seq', (SELECT COALESCE(MAX(id), 1) FROM OPENING_HOURS));
SELECT setval('min_interest_id_seq', (SELECT COALESCE(MAX(id), 1) FROM MIN_INTEREST));
SELECT setval('festivals_id_seq', (SELECT COALESCE(MAX(id), 1) FROM FESTIVALS));
SELECT setval('users_input_id_seq', (SELECT COALESCE(MAX(id), 1) FROM USERS_INPUT));
"""

    # 4. Write to targets (backend/database and verified)
    targets = [Path("backend/database"), Path("verified")]
    for target in targets:
        target.mkdir(parents=True, exist_ok=True)

        # 1. postgres_schema.sql
        (target / "postgres_schema.sql").write_text(postgres_schema, encoding="utf-8")
        # 2. dhruva_postgres_dump.sql (Complete schema + data inserts)
        (target / "dhruva_postgres_dump.sql").write_text(full_dump_sql, encoding="utf-8")
        # 3. postgres_import_csv.sql
        (target / "postgres_import_csv.sql").write_text(csv_import_sql, encoding="utf-8")
        # 4. dhruva.schema
        (target / "dhruva.schema").write_text(postgres_schema, encoding="utf-8")
        # 5. dhruva.db
        if target != db_path.parent:
            shutil.copy(db_path, target / "dhruva.db")

    conn.close()
    print("SUCCESS: PostgreSQL files and database assets created in:")
    print("  1. backend/database/")
    print("  2. verified/")

if __name__ == "__main__":
    generate()
