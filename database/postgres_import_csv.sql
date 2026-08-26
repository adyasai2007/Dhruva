-- =====================================================================
-- DHRUVA PostgreSQL CSV Direct Import Script
-- Run via psql CLI in your terminal inside the folder containing the CSVs:
--   psql -U <username> -d <dbname> -f postgres_import_csv.sql
-- =====================================================================

\copy CITIES(id, name, state, lat, long) FROM 'cities.csv' WITH (FORMAT csv, HEADER true);
\copy PLACES(id, name, duration, popularity, lat, long, risk, city_id, category, sub_category, duration_label, image_url, entry_fee, description) FROM 'places.csv' WITH (FORMAT csv, HEADER true);
\copy OPENING_HOURS(id, opens_at, closes_at, place_id, day_of_week) FROM 'opening_hours.csv' WITH (FORMAT csv, HEADER true);
\copy MIN_INTEREST(id, place_id, architecture, history, spiritual, nature, culture) FROM 'min_interest.csv' WITH (FORMAT csv, HEADER true);
\copy FESTIVALS(id, name, start_date, end_date, city_id, description) FROM 'festivals.csv' WITH (FORMAT csv, HEADER true);
\copy USERS_INPUT(id, gps_location, start_date, start_time, end_time, age) FROM 'users_input.csv' WITH (FORMAT csv, HEADER true);

SELECT setval('cities_id_seq', (SELECT COALESCE(MAX(id), 1) FROM CITIES));
SELECT setval('places_id_seq', (SELECT COALESCE(MAX(id), 1) FROM PLACES));
SELECT setval('opening_hours_id_seq', (SELECT COALESCE(MAX(id), 1) FROM OPENING_HOURS));
SELECT setval('min_interest_id_seq', (SELECT COALESCE(MAX(id), 1) FROM MIN_INTEREST));
SELECT setval('festivals_id_seq', (SELECT COALESCE(MAX(id), 1) FROM FESTIVALS));
SELECT setval('users_input_id_seq', (SELECT COALESCE(MAX(id), 1) FROM USERS_INPUT));
