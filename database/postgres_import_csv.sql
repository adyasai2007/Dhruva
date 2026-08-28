-- =====================================================================
-- DHRUVA PostgreSQL CSV Direct Import Script
-- Run via psql CLI in your terminal inside the folder containing the CSVs:
--   psql -U <username> -d <dbname> -f postgres_import_csv.sql
-- =====================================================================

\copy CITIES(id, name, state, lat, long) FROM 'cities.csv' WITH (FORMAT csv, HEADER true);
\copy CITY_INTEREST(id, city_id, architecture, history, spiritual, nature, culture) FROM 'city_interest.csv' WITH (FORMAT csv, HEADER true);
\copy PLACES(id, name, duration, duration_label, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee, source, source_url, last_updated) FROM 'places.csv' WITH (FORMAT csv, HEADER true);
\copy OPENING_HOURS(id, opens_at, closes_at, place_id, day_of_week) FROM 'opening_hours.csv' WITH (FORMAT csv, HEADER true);
\copy MIN_INTEREST(id, place_id, architecture, history, spiritual, nature, culture) FROM 'min_interest.csv' WITH (FORMAT csv, HEADER true);
\copy FESTIVALS(id, name, start_date, end_date, city_id, description) FROM 'festivals.csv' WITH (FORMAT csv, HEADER true);

SELECT setval('cities_id_seq', (SELECT COALESCE(MAX(id), 1) FROM CITIES));
SELECT setval('city_interest_id_seq', (SELECT COALESCE(MAX(id), 1) FROM CITY_INTEREST));
SELECT setval('places_id_seq', (SELECT COALESCE(MAX(id), 1) FROM PLACES));
SELECT setval('opening_hours_id_seq', (SELECT COALESCE(MAX(id), 1) FROM OPENING_HOURS));
SELECT setval('min_interest_id_seq', (SELECT COALESCE(MAX(id), 1) FROM MIN_INTEREST));
SELECT setval('festivals_id_seq', (SELECT COALESCE(MAX(id), 1) FROM FESTIVALS));
