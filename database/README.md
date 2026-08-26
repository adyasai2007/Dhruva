# DHRUVA PostgreSQL Database

This directory contains the complete PostgreSQL database files, schema definitions, SQL data dumps, and relational CSV files for the DHRUVA project.

---

## 📁 Directory Structure

- **`dhruva_postgres_dump.sql`**: Complete standalone PostgreSQL dump containing table creation DDL (`DROP` + `CREATE TABLE`), constraints, foreign keys, performance indexes, and seed `INSERT` statements for all Indian cultural places, cities, opening hours, interest profiles, and festivals.
- **`postgres_schema.sql` / `dhruva.schema`**: PostgreSQL DDL schema definition only (tables, foreign keys, sequence reset, indexes).
- **`postgres_import_csv.sql`**: Script to bulk copy data into PostgreSQL directly from the CSV files using `\copy`.
- **`database.sql`**: Relational table reference schema.
- **`csv/`**: Directory containing normalized relational CSV tables:
  - `cities.csv` (Indian cultural hubs: Bhubaneswar, Puri, Konark, etc.)
  - `places.csv` (Monuments, temples, craft villages, coordinates, popularity, duration)
  - `opening_hours.csv` (Daily operating schedules)
  - `min_interest.csv` (5-dimensional interest vectors: Architecture, History, Spiritual, Nature, Culture)
  - `festivals.csv` (Regional celebrations and dates)
  - `users_input.csv` (User trip query schema)

---

## 🚀 Quick Setup Instructions

### Option A: Restore from Complete SQL Dump (Recommended & Fastest)

Create your PostgreSQL database (if not already created) and run:

```bash
# Create database (optional)
createdb -U postgres dhruva_db

# Load schema and all seed data in one step
psql -U postgres -d dhruva_db -f dhruva_postgres_dump.sql
```

---

### Option B: Create Schema + Import via CSVs

1. Apply schema:
   ```bash
   psql -U postgres -d dhruva_db -f postgres_schema.sql
   ```

2. Import CSVs:
   ```bash
   cd csv
   psql -U postgres -d dhruva_db -f ../postgres_import_csv.sql
   ```

---

## 📊 Relational Database Schema Overview

```
                      +-------------------+
                      |      CITIES       |
                      +-------------------+
                      | id (PK)           |
                      | name              |
                      | state             |
                      | lat, long         |
                      +---------+---------+
                                |
             +------------------+------------------+
             | 1:N                                 | 1:N
             v                                     v
   +-------------------+                 +-------------------+
   |      PLACES       |                 |     FESTIVALS     |
   +-------------------+                 +-------------------+
   | id (PK)           |                 | id (PK)           |
   | city_id (FK)      |                 | city_id (FK)      |
   | name              |                 | name              |
   | duration          |                 | start_date        |
   | popularity        |                 | end_date          |
   | lat, long         |                 | description       |
   | risk              |                 +-------------------+
   | category          |
   | description       |
   | image_url         |
   | entry_fee         |
   +---------+---------+
             |
             +------------------+
             | 1:N              | 1:1
             v                  v
   +-------------------+  +-------------------+
   |   OPENING_HOURS   |  |   MIN_INTEREST    |
   +-------------------+  +-------------------+
   | id (PK)           |  | id (PK)           |
   | place_id (FK)     |  | place_id (FK)     |
   | opens_at          |  | architecture      |
   | closes_at         |  | history           |
   | day_of_week       |  | spiritual         |
   +-------------------+  | nature            |
                          | culture           |
                          +-------------------+
```
