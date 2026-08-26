"""
DHRUVA PostgreSQL Database File Generator
Generates PostgreSQL DDL schema (.schema, .sql), Full PostgreSQL data dump (.sql),
and CSV COPY script (.sql) directly from processed relational CSVs in data/processed/.
Zero SQLite dependencies.
"""

import csv
from pathlib import Path

def get_base_dirs():
    candidates = [
        Path("."),
        Path(__file__).parent.parent,
        Path("Dhruva"),
    ]
    for c in candidates:
        if (c / "data" / "processed").exists() and (c / "database").exists():
            return c / "data" / "processed", c / "database"
        if (c / "database" / "csv").exists() and (c / "database").exists():
            return c / "database" / "csv", c / "database"
    # Default fallback
    base = Path(__file__).parent.parent
    return base / "database" / "csv", base / "database"

def escape_sql(val):
    if val is None or val == "":
        return "NULL"
    try:
        if isinstance(val, (int, float)):
            return str(val)
        # Check if numeric string
        if val.isdigit():
            return str(int(val))
        val_float = float(val)
        return str(val_float)
    except ValueError:
        pass
    s = str(val).replace("'", "''")
    return f"'{s}'"

def generate():
    csv_dir, db_dir = get_base_dirs()
    if not csv_dir.exists():
        raise FileNotFoundError(f"Processed CSV directory not found at {csv_dir}")
    db_dir.mkdir(parents=True, exist_ok=True)

    # 1. PostgreSQL Schema DDL Definition
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

    def read_csv_rows(filename):
        fpath = csv_dir / filename
        if not fpath.exists():
            raise FileNotFoundError(f"Missing CSV file: {fpath}")
        with open(fpath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    # 2. Build PostgreSQL SQL Dump with full INSERT statements from CSVs
    dump_lines = [
        postgres_schema,
        "\n-- =====================================================================",
        "-- DATA POPULATION (INSERT STATEMENTS)",
        "-- =====================================================================\n"
    ]

    # CITIES
    cities = read_csv_rows("cities.csv")
    dump_lines.append("-- 1. Populate CITIES")
    for c in cities:
        dump_lines.append(f"INSERT INTO CITIES (id, name, state, lat, long) VALUES ({c['id']}, {escape_sql(c['name'])}, {escape_sql(c['state'])}, {c['lat']}, {c['long']});")

    # PLACES
    places = read_csv_rows("places.csv")
    dump_lines.append("\n-- 2. Populate PLACES")
    for p in places:
        dump_lines.append(
            f"INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) "
            f"VALUES ({p['id']}, {escape_sql(p['name'])}, {p['duration']}, {escape_sql(p.get('duration_label', ''))}, {p['popularity']}, {p['lat']}, {p['long']}, {escape_sql(p['risk'])}, {p['city_id']}, {escape_sql(p.get('category', ''))}, {escape_sql(p.get('sub_category', ''))}, {escape_sql(p.get('description', ''))}, {escape_sql(p.get('image_url', ''))}, {escape_sql(p.get('entry_fee', ''))});"
        )

    # OPENING_HOURS
    hours = read_csv_rows("opening_hours.csv")
    dump_lines.append("\n-- 3. Populate OPENING_HOURS")
    for h in hours:
        dump_lines.append(f"INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES ({h['id']}, {escape_sql(h['opens_at'])}, {escape_sql(h['closes_at'])}, {h['place_id']}, {escape_sql(h['day_of_week'])});")

    # MIN_INTEREST
    interests = read_csv_rows("min_interest.csv")
    dump_lines.append("\n-- 4. Populate MIN_INTEREST")
    for mi in interests:
        dump_lines.append(f"INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES ({mi['id']}, {mi['place_id']}, {mi['architecture']}, {mi['history']}, {mi['spiritual']}, {mi['nature']}, {mi['culture']});")

    # FESTIVALS
    festivals = read_csv_rows("festivals.csv")
    dump_lines.append("\n-- 5. Populate FESTIVALS")
    for f in festivals:
        dump_lines.append(f"INSERT INTO FESTIVALS (id, name, start_date, end_date, city_id, description) VALUES ({f['id']}, {escape_sql(f['name'])}, {escape_sql(f['start_date'])}, {escape_sql(f['end_date'])}, {f['city_id']}, {escape_sql(f.get('description', ''))});")

    # USERS_INPUT
    users = read_csv_rows("users_input.csv")
    dump_lines.append("\n-- 6. Populate USERS_INPUT")
    for u in users:
        dump_lines.append(f"INSERT INTO USERS_INPUT (id, gps_location, start_date, start_time, end_time, age) VALUES ({u['id']}, {escape_sql(u['gps_location'])}, {escape_sql(u['start_date'])}, {escape_sql(u['start_time'])}, {escape_sql(u['end_time'])}, {u['age']});")

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

    # 4. Write to backend/database
    (db_dir / "postgres_schema.sql").write_text(postgres_schema, encoding="utf-8")
    (db_dir / "dhruva_postgres_dump.sql").write_text(full_dump_sql, encoding="utf-8")
    (db_dir / "postgres_import_csv.sql").write_text(csv_import_sql, encoding="utf-8")
    (db_dir / "dhruva.schema").write_text(postgres_schema, encoding="utf-8")

    print("SUCCESS: PostgreSQL files generated directly from CSVs in:")
    print(f"  - {db_dir.resolve()}/")
    print(f"    * postgres_schema.sql")
    print(f"    * dhruva_postgres_dump.sql ({len(dump_lines)} SQL lines)")
    print(f"    * postgres_import_csv.sql")
    print(f"    * dhruva.schema")

if __name__ == "__main__":
    generate()
