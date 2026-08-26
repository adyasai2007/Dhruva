-- =====================================================================
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


-- =====================================================================
-- DATA POPULATION (INSERT STATEMENTS)
-- =====================================================================

-- 1. Populate CITIES
INSERT INTO CITIES (id, name, state, lat, long) VALUES (1, 'Bhubaneswar', 'Odisha', 20.2961, 85.8245);
INSERT INTO CITIES (id, name, state, lat, long) VALUES (2, 'Puri', 'Odisha', 19.8135, 85.8312);
INSERT INTO CITIES (id, name, state, lat, long) VALUES (3, 'Cuttack', 'Odisha', 20.4625, 85.883);

-- 2. Populate PLACES
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (1, 'Asokastami', 2.0, '2 to 2.5 Hours', 4.5, 20.2405, 85.834, 'Low', 1, 'Arts, Crafts & Museum', 'Traditional Craft & Artisan Heritage', 'Bhubaneswar''s Festival of Triumph', 'https://s7ap1.scene7.com/is/image/incredibleindia/lingaraj-temple-bhubaneshwar-odisha-1-attr-hero?qlt=82&ts=1742165306173', 'Entry fee applicable; verify on-site');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (2, 'Chilika Lake', 3.5, '2.5 to 3.5 Hours', 4.8, 19.68, 85.32, 'Moderate', 1, 'Nature & Scenic Sanctum', 'Wildlife Sanctum & Eco-Heritage', 'Dive into the avian paradise of Chilika Lake, where wetlands echo with the calls of migratory birds. Witness the majestic spectacle of nature as flamingos and pelicans grace the waters.', 'https://s7ap1.scene7.com/is/image/incredibleindia/chilika-wildlife-sanctuary-puri-odisha-1-attr-hero?qlt=82&ts=1726663755053', 'Entry fee applicable; verify on-site');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (3, 'Dhauligiri Hills', 2.5, '2.5 to 3.5 Hours', 4.7, 20.1925, 85.8394, 'Low', 1, 'Nature & Scenic Sanctum', 'Wildlife Sanctum & Eco-Heritage', 'Explore the serene Dhauli Giri Hills in Bhubaneswar, known for its historical significance and panoramic views, making it a place for reflection and tranquility.', 'https://s7ap1.scene7.com/is/image/incredibleindia/dhauligiri-hills-bubhaneshwar-odisha-1-attr-hero?qlt=82&ts=1742172014321', 'Entry fee applicable; verify on-site');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (4, 'Hirapur', 2.0, '1.5 to 2 Hours', 4.6, 20.2285, 85.876, 'Low', 1, 'Temple & Sacred Sanctum', 'Shakti Peetha / Devi Shrine', 'Hirapur, a village near Bhubaneswar, is famous for its 11th-century Hypaethral temple dedicated to Goddess Mahamaya, which is a must-visit for tourists.', 'https://s7ap1.scene7.com/is/image/incredibleindia/hirapur-bhubaneshwar1-odisha-attr-hero?qlt=82&ts=1742176593109', 'Free entry (Donations welcome; special darshan queue fees may apply)');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (5, 'Kala Bhoomi Odisha Crafts Museum', 2.5, '2 to 2.5 Hours', 4.7, 20.2467, 85.7958, 'Low', 1, 'Arts, Crafts & Museum', 'Traditional Craft & Artisan Heritage', 'Explore Kala Bhoomi Odisha Crafts Museum in Bhubhaneshwar: See more about Kala Bhoomi Odisha Crafts Museum photos, timings, ticket prices and know the Kala Bhoomi Odisha Crafts Museum location.', 'https://s7ap1.scene7.com/is/image/incredibleindia/1-khandagiri-udaigiri-caves-attr-hero?qlt=82&ts=1742172787783', 'Entry fee applicable; verify on-site');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (6, 'Kantilo', 3.0, '2.5 to 3.5 Hours', 4.4, 20.3622, 85.1914, 'Low', 1, 'Nature & Scenic Sanctum', 'Wildlife Sanctum & Eco-Heritage', 'Explore the historic town of Kantilo, on the banks of river Mahanadi, near Bhubaneswar with its beautiful temples and serene natural surroundings. Plan your visit today.', 'https://s7ap1.scene7.com/is/image/incredibleindia/Explore-the-Rich-Heritage-of-Jajpur-City7-hero?qlt=82&ts=1726663567178', 'Entry fee applicable; verify on-site');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (7, 'Khandagiri & Udayagiri Caves', 2.5, '2 to 3 Hours', 4.8, 20.2631, 85.7861, 'Moderate', 1, 'Heritage & Archaeological Site', 'Rock-cut Caves & Inscriptions', 'Experience the ancient rock-cut caves of Udayagiri and Khandagiri in Bhubaneswar, featuring stunning sculptures, inscriptions, and panoramic views of the city.', 'https://s7ap1.scene7.com/is/image/incredibleindia/1-khandagiri-udaigiri-caves-attr-hero?qlt=82&ts=1742172787783', 'Entry fee applicable; verify on-site');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (8, 'Kuanria', 3.0, '2.5 to 3.5 Hours', 4.2, 20.354, 84.81, 'Low', 1, 'Nature & Scenic Sanctum', 'Wildlife Sanctum & Eco-Heritage', 'A peaceful dam to seek solitude in the temple city', 'https://s7ap1.scene7.com/is/image/incredibleindia/ansupa-lake-cuttack-odisha-1-attr-hero?qlt=82&ts=1726674675128', 'Entry fee applicable; verify on-site');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (9, 'Lingaraj Temple', 2.0, '1.5 to 2 Hours', 4.9, 20.2382, 85.8338, 'Low', 1, 'Temple & Sacred Sanctum', 'Shiva Temple & Sanctum', 'Embark on a spiritual journey and marvel at the ancient architecture of Lingaraj Temple in Bhubaneswar, a must-visit for Hindu devotees and history enthusiasts.', 'https://s7ap1.scene7.com/is/image/incredibleindia/lingaraj-temple-bhubaneshwar-odisha-1-attr-hero?qlt=82&ts=1742165306173', 'Free entry (Donations welcome; special darshan queue fees may apply)');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (10, 'Bhitarkanika National Park', 4.0, '2.5 to 3.5 Hours', 4.8, 20.7167, 86.8667, 'Moderate', 3, 'Nature & Scenic Sanctum', 'Wildlife Sanctum & Eco-Heritage', 'Explore Bhitarkanika National Park in Cuttack - Where Wildlife and Pristine Ecosystems Converge.', 'https://s7ap1.scene7.com/is/image/incredibleindia/cuttack-odisha-bhitarkanika-national-park-cuttack-orissa-1-attr-hero?qlt=82&ts=1726674724638', 'Entry fee applicable; verify on-site');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (11, 'Alarnatha Temple', 2.0, '1.5 to 2 Hours', 4.6, 19.742, 85.679, 'Low', 2, 'Temple & Sacred Sanctum', 'Vaishnava Temple', 'Alarnatha Temple A Hindu shrine located in Brahmagiri, Puri, dedicated to Lord Vishnu. Celebrated for its annual Rath Yatra festival, drawing many devotees and visitors.', 'https://s7ap1.scene7.com/is/image/incredibleindia/alarnatha-temple-or-alvarnaatha-puri-odisha-1-attr-hero?qlt=82&ts=1726674737792', 'Free entry (Donations welcome; special darshan queue fees may apply)');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (12, 'Atharnala Bridge', 1.5, '2.5 to 3.5 Hours', 4.4, 19.8247, 85.8273, 'Low', 2, 'Nature & Scenic Sanctum', 'Wildlife Sanctum & Eco-Heritage', 'Atharnala Bridge is an ancient stone bridge in Puri, Odisha. Visit to witness its impressive architecture and learn about its historical significance.', 'https://s7ap1.scene7.com/is/image/incredibleindia/atharnala-stone-bridge-puri-odisha-1-attr-hero?qlt=82&ts=1726663682500', 'Entry fee applicable; verify on-site');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (13, 'Balighai Beach', 2.0, '1.5 to 2 Hours', 4.5, 19.851, 85.912, 'Moderate', 2, 'Temple & Sacred Sanctum', 'Sacred Heritage Temple', 'Enjoy the beauty of nature along the coast at Balighai Beach in Puri. It''s a peaceful spot for relaxation and serene views.', 'https://s7ap1.scene7.com/is/image/incredibleindia/balighai-beach-puri-odisha-1-attr-hero?qlt=82&ts=1726674743727', 'Free entry (Donations welcome; special darshan queue fees may apply)');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (14, 'Balukhand-Konark Sanctuary', 3.0, '2.5 to 3.5 Hours', 4.5, 19.865, 86.042, 'Low', 2, 'Nature & Scenic Sanctum', 'Wildlife Sanctum & Eco-Heritage', 'Immerse in the natural wonders of Balukhand Konark Wildlife Sanctuary in Puri, home to rich biodiversity and pristine coastal landscapes.', 'https://s7ap1.scene7.com/is/image/incredibleindia/chilika-wildlife-sanctuary-puri-odisha-2-attr-hero?qlt=82&ts=1726663783800', 'Entry fee applicable; verify on-site');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (15, 'Chaurasi', 2.0, '1.5 to 2 Hours', 4.4, 20.024, 86.115, 'Low', 2, 'Temple & Sacred Sanctum', 'Sacred Heritage Temple', 'Chaurasi, is a small village famous for the ancient temple of Varahi. It is dedicated to Goddess Varahi. The temple belongs to the 9th century A.D.', 'https://s7ap1.scene7.com/is/image/incredibleindia/chaurasi-puri-odisha-1-attr-hero?qlt=82&ts=1726674740718', 'Free entry (Donations welcome; special darshan queue fees may apply)');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (16, 'Chilika Wildlife Sanctuary', 3.0, '2.5 to 3.5 Hours', 4.7, 19.7, 85.45, 'Moderate', 2, 'Nature & Scenic Sanctum', 'Wildlife Sanctum & Eco-Heritage', 'Explore avian diversity at the Chilika Wildlife Sanctuary in Puri. A sanctuary for birdwatching enthusiasts.', 'https://s7ap1.scene7.com/is/image/incredibleindia/chilika-wildlife-sanctuary-puri-odisha-1-attr-hero?qlt=82&ts=1726663755053', 'Entry fee applicable; verify on-site');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (17, 'Gundicha Temple', 2.0, '1.5 to 2 Hours', 4.8, 19.8258, 85.8398, 'Low', 2, 'Temple & Sacred Sanctum', 'Vaishnava Temple', 'Gundicha Temple is a famous Hindu shrine in Puri, India, associated with the annual Rath Yatra festival that draws visitors and devotees from all around.', 'https://s7ap1.scene7.com/is/image/incredibleindia/gundicha-temple-puri-odisha-1-attr-hero?qlt=82&ts=1726663778679', 'Free entry (Donations welcome; special darshan queue fees may apply)');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (18, 'Konark Temple', 2.5, '1.5 to 2 Hours', 5.0, 19.8876, 86.0945, 'Low', 2, 'Temple & Sacred Sanctum', 'Sacred Heritage Temple', 'Konark Sun Temple A world-renowned heritage site in Puri, India, featuring impressive architecture and intricate carvings that depict the Sun God.', 'https://s7ap1.scene7.com/is/image/incredibleindia/konark-temple-puri-odisha-1-attr-hero?qlt=82&ts=1726674697395', 'Free entry (Donations welcome; special darshan queue fees may apply)');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (19, 'Loknath Temple', 2.0, '1.5 to 2 Hours', 4.6, 19.799, 85.808, 'Low', 2, 'Temple & Sacred Sanctum', 'Shiva Temple & Sanctum', 'Loknath Temple in Puri, India, is a significant Hindu shrine devoted to Lord Shiva. It is celebrated for its spiritual significance and the grand Maha Shivaratri festival.', 'https://s7ap1.scene7.com/is/image/incredibleindia/loknath-temple-puri-odisha-1-attr-hero?qlt=82&ts=1726674731200', 'Free entry (Donations welcome; special darshan queue fees may apply)');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (20, 'Ansupa Nature Camp', 3.0, '2.5 to 3.5 Hours', 4.5, 20.463, 85.602, 'Low', 3, 'Nature & Scenic Sanctum', 'Wildlife Sanctum & Eco-Heritage', 'Plan a visit to Ansupa Lake near Cuttack for a peaceful retreat amidst nature''s beauty, with boating, fishing, and birdwatching opportunities for all to enjoy.', 'https://s7ap1.scene7.com/is/image/incredibleindia/ansupa-lake-cuttack-odisha-1-attr-hero?qlt=82&ts=1726674675128', 'Entry fee applicable; verify on-site');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (21, 'Barabati Fort', 2.0, '1 to 2 Hours', 4.7, 20.485, 85.867, 'Low', 3, 'Monument & Fort', 'Cultural Heritage', 'Barabati Fort, nestled in the historic city of Cuttack, stands as a majestic testament to Odisha''s rich heritage, enchanting tourists with its ancient ruins.', 'https://s7ap1.scene7.com/is/image/incredibleindia/barabati-fort-cuttack-odisha-1-attr-hero?qlt=82&ts=1726663491030', 'Entry fee applicable; verify on-site');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (22, 'Barabati Stadium', 2.0, '2.5 to 3.5 Hours', 4.4, 20.482, 85.869, 'Low', 3, 'Nature & Scenic Sanctum', 'Wildlife Sanctum & Eco-Heritage', 'Experience the thrill of cricket at Cuttack''s Barabati Stadium, a world-class venue and home to some of the most exciting matches in the sport.', 'https://s7ap1.scene7.com/is/image/incredibleindia/barabati-stadium-cuttack-odisha-barabati-stadium1-attr-hero?qlt=82&ts=1726674702106', 'Entry fee applicable; verify on-site');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (23, 'Discover a symphony of wildlife', 2.5, '2.5 to 3.5 Hours', 4.3, 20.52, 85.82, 'Low', 3, 'Nature & Scenic Sanctum', 'Wildlife Sanctum & Eco-Heritage', 'Embark on a thrilling wildlife adventure at Chandaka Elephant Sanctuary, a natural reserve near Cuttack known for its majestic elephants and diverse flora and fauna.', 'https://s7ap1.scene7.com/is/image/incredibleindia/cuttack-odisha-bhitarkanika-national-park-cuttack-orissa-1-attr-hero?qlt=82&ts=1726674724638', 'Entry fee applicable; verify on-site');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (24, 'Cuttack Chandi Temple', 1.5, '1.5 to 2 Hours', 4.8, 20.467, 85.863, 'Low', 3, 'Temple & Sacred Sanctum', 'Vaishnava Temple', 'Explore the divine beauty of Cuttack Chandi Temple, a popular Hindu shrine in Cuttack dedicated to Goddess Chandi and adorned with intricate artwork.', 'https://s7ap1.scene7.com/is/image/incredibleindia/cuttack-chandi-temple-cuttack-odisha-chandi-temple1-attr-hero?qlt=82&ts=1726663557866', 'Free entry (Donations welcome; special darshan queue fees may apply)');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (25, 'Dhabaleswar Temple', 2.0, '1.5 to 2 Hours', 4.6, 20.505, 85.83, 'Low', 3, 'Temple & Sacred Sanctum', 'Shiva Temple & Sanctum', 'Discover the spiritual aura of Dhabaleswar Temple, a revered Hindu shrine in Cuttack located on an island in the Mahanadi River and known for its scenic beauty.', 'https://s7ap1.scene7.com/is/image/incredibleindia/dhabaleswar-temple-cuttack-odisha-dhabaleswar-temple1-attr-hero?qlt=82&ts=1726663591172', 'Free entry (Donations welcome; special darshan queue fees may apply)');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (26, 'Explore The Rich Heritage Of Jajpur', 3.5, '2.5 to 3.5 Hours', 4.5, 20.85, 86.33, 'Low', 3, 'Nature & Scenic Sanctum', 'Wildlife Sanctum & Eco-Heritage', 'When I received an invite a month ago to explore a town called Jajpur, I had to look up twice to see if it was actually Jaipur in Rajashtan or did they actually mean Jajpur city. Little did I know that this place bore so much history and is now being', 'https://s7ap1.scene7.com/is/image/incredibleindia/Explore-the-Rich-Heritage-of-Jajpur-City7-hero?qlt=82&ts=1726663567178', 'Entry fee applicable; verify on-site');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (27, 'Jobra Barrage', 1.5, '1.5 to 2 Hours', 4.5, 20.473, 85.898, 'Low', 3, 'Temple & Sacred Sanctum', 'Shiva Temple & Sanctum', 'Explore the beauty of nature at Jobra Barrage, Cuttack''s stunning dam and reservoir offering breathtaking views and a peaceful escape from the city.', 'https://s7ap1.scene7.com/is/image/incredibleindia/jobra-barrage-cuttack-odisha-jobra-barrage1-attr-hero?qlt=82&ts=1726674646012', 'Free entry (Donations welcome; special darshan queue fees may apply)');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (28, 'Mahanadi Barrage', 2.0, '2.5 to 3.5 Hours', 4.4, 20.48, 85.905, 'Low', 3, 'Nature & Scenic Sanctum', 'Wildlife Sanctum & Eco-Heritage', 'Experience the impressive Mahanadi Barrage in Cuttack, a major engineering feat that regulates the flow of the Mahanadi River and provides irrigation for the region.', 'https://s7ap1.scene7.com/is/image/incredibleindia/mahanadi-barrage-cuttack-odisha-1-attr-hero?qlt=82&ts=1726663709252', 'Entry fee applicable; verify on-site');
INSERT INTO PLACES (id, name, duration, duration_label, popularity, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee) VALUES (29, 'Netaji Birth Place Museum', 2.0, '2 to 2.5 Hours', 4.7, 20.461, 85.875, 'Low', 3, 'Arts, Crafts & Museum', 'State Cultural Museum', 'Step back in time and learn about the life of Netaji Subhas Chandra Bose at his birthplace museum in Cuttack, featuring personal belongings and memorabilia.', 'https://s7ap1.scene7.com/is/image/incredibleindia/netaji-birth-place-museum-cuttack-1-odisha-attr-hero?qlt=82&ts=1726674694947', 'Entry fee applicable; verify on-site');

-- 3. Populate OPENING_HOURS
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (1, '06:00 AM', '08:00 PM', 1, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (2, '06:00 AM', '08:00 PM', 1, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (3, '06:00 AM', '08:00 PM', 1, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (4, '06:00 AM', '08:00 PM', 1, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (5, '06:00 AM', '08:00 PM', 1, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (6, '06:00 AM', '08:00 PM', 1, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (7, '06:00 AM', '08:00 PM', 1, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (8, '08:00 AM', '05:30 PM', 2, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (9, '08:00 AM', '05:30 PM', 2, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (10, '08:00 AM', '05:30 PM', 2, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (11, '08:00 AM', '05:30 PM', 2, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (12, '08:00 AM', '05:30 PM', 2, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (13, '08:00 AM', '05:30 PM', 2, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (14, '08:00 AM', '05:30 PM', 2, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (15, '08:00 AM', '05:30 PM', 3, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (16, '08:00 AM', '05:30 PM', 3, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (17, '08:00 AM', '05:30 PM', 3, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (18, '08:00 AM', '05:30 PM', 3, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (19, '08:00 AM', '05:30 PM', 3, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (20, '08:00 AM', '05:30 PM', 3, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (21, '08:00 AM', '05:30 PM', 3, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (22, '06:00 AM', '07:00 PM', 4, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (23, '06:00 AM', '07:00 PM', 4, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (24, '06:00 AM', '07:00 PM', 4, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (25, '06:00 AM', '07:00 PM', 4, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (26, '06:00 AM', '07:00 PM', 4, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (27, '06:00 AM', '07:00 PM', 4, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (28, '06:00 AM', '07:00 PM', 4, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (29, '10:00 AM', '05:30 PM', 5, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (30, '10:00 AM', '05:30 PM', 5, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (31, '10:00 AM', '05:30 PM', 5, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (32, '10:00 AM', '05:30 PM', 5, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (33, '10:00 AM', '05:30 PM', 5, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (34, '10:00 AM', '05:30 PM', 5, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (35, '10:00 AM', '05:30 PM', 5, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (36, '06:00 AM', '09:00 PM', 6, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (37, '06:00 AM', '09:00 PM', 6, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (38, '06:00 AM', '09:00 PM', 6, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (39, '06:00 AM', '09:00 PM', 6, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (40, '06:00 AM', '09:00 PM', 6, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (41, '06:00 AM', '09:00 PM', 6, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (42, '06:00 AM', '09:00 PM', 6, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (43, '09:00 AM', '09:00 PM', 7, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (44, '09:00 AM', '09:00 PM', 7, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (45, '09:00 AM', '09:00 PM', 7, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (46, '09:00 AM', '09:00 PM', 7, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (47, '09:00 AM', '09:00 PM', 7, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (48, '09:00 AM', '09:00 PM', 7, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (49, '09:00 AM', '09:00 PM', 7, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (50, '09:00 AM', '05:00 PM', 8, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (51, '09:00 AM', '05:00 PM', 8, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (52, '09:00 AM', '05:00 PM', 8, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (53, '09:00 AM', '05:00 PM', 8, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (54, '09:00 AM', '05:00 PM', 8, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (55, '09:00 AM', '05:00 PM', 8, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (56, '09:00 AM', '05:00 PM', 8, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (57, '07:00 AM', '07:00 PM', 9, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (58, '07:00 AM', '07:00 PM', 9, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (59, '07:00 AM', '07:00 PM', 9, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (60, '07:00 AM', '07:00 PM', 9, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (61, '07:00 AM', '07:00 PM', 9, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (62, '07:00 AM', '07:00 PM', 9, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (63, '07:00 AM', '07:00 PM', 9, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (64, '06:00 AM', '06:00 PM', 10, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (65, '06:00 AM', '06:00 PM', 10, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (66, '06:00 AM', '06:00 PM', 10, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (67, '06:00 AM', '06:00 PM', 10, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (68, '06:00 AM', '06:00 PM', 10, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (69, '06:00 AM', '06:00 PM', 10, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (70, '06:00 AM', '06:00 PM', 10, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (71, '06:00 AM', '09:30 PM', 11, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (72, '06:00 AM', '09:30 PM', 11, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (73, '06:00 AM', '09:30 PM', 11, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (74, '06:00 AM', '09:30 PM', 11, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (75, '06:00 AM', '09:30 PM', 11, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (76, '06:00 AM', '09:30 PM', 11, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (77, '06:00 AM', '09:30 PM', 11, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (78, '12:00 AM', '11:59 PM', 12, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (79, '12:00 AM', '11:59 PM', 12, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (80, '12:00 AM', '11:59 PM', 12, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (81, '12:00 AM', '11:59 PM', 12, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (82, '12:00 AM', '11:59 PM', 12, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (83, '12:00 AM', '11:59 PM', 12, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (84, '12:00 AM', '11:59 PM', 12, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (85, '06:00 AM', '08:00 PM', 13, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (86, '06:00 AM', '08:00 PM', 13, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (87, '06:00 AM', '08:00 PM', 13, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (88, '06:00 AM', '08:00 PM', 13, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (89, '06:00 AM', '08:00 PM', 13, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (90, '06:00 AM', '08:00 PM', 13, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (91, '06:00 AM', '08:00 PM', 13, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (92, '12:00 AM', '11:59 PM', 14, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (93, '12:00 AM', '11:59 PM', 14, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (94, '12:00 AM', '11:59 PM', 14, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (95, '12:00 AM', '11:59 PM', 14, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (96, '12:00 AM', '11:59 PM', 14, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (97, '12:00 AM', '11:59 PM', 14, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (98, '12:00 AM', '11:59 PM', 14, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (99, '06:00 AM', '08:00 PM', 15, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (100, '06:00 AM', '08:00 PM', 15, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (101, '06:00 AM', '08:00 PM', 15, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (102, '06:00 AM', '08:00 PM', 15, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (103, '06:00 AM', '08:00 PM', 15, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (104, '06:00 AM', '08:00 PM', 15, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (105, '06:00 AM', '08:00 PM', 15, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (106, '06:00 AM', '07:00 PM', 16, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (107, '06:00 AM', '07:00 PM', 16, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (108, '06:00 AM', '07:00 PM', 16, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (109, '06:00 AM', '07:00 PM', 16, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (110, '06:00 AM', '07:00 PM', 16, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (111, '06:00 AM', '07:00 PM', 16, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (112, '06:00 AM', '07:00 PM', 16, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (113, '06:00 AM', '09:00 PM', 17, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (114, '06:00 AM', '09:00 PM', 17, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (115, '06:00 AM', '09:00 PM', 17, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (116, '06:00 AM', '09:00 PM', 17, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (117, '06:00 AM', '09:00 PM', 17, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (118, '06:00 AM', '09:00 PM', 17, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (119, '06:00 AM', '09:00 PM', 17, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (120, '06:00 AM', '08:00 PM', 18, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (121, '06:00 AM', '08:00 PM', 18, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (122, '06:00 AM', '08:00 PM', 18, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (123, '06:00 AM', '08:00 PM', 18, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (124, '06:00 AM', '08:00 PM', 18, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (125, '06:00 AM', '08:00 PM', 18, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (126, '06:00 AM', '08:00 PM', 18, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (127, '05:00 AM', '09:00 PM', 19, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (128, '05:00 AM', '09:00 PM', 19, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (129, '05:00 AM', '09:00 PM', 19, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (130, '05:00 AM', '09:00 PM', 19, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (131, '05:00 AM', '09:00 PM', 19, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (132, '05:00 AM', '09:00 PM', 19, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (133, '05:00 AM', '09:00 PM', 19, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (134, '07:00 AM', '05:00 PM', 20, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (135, '07:00 AM', '05:00 PM', 20, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (136, '07:00 AM', '05:00 PM', 20, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (137, '07:00 AM', '05:00 PM', 20, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (138, '07:00 AM', '05:00 PM', 20, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (139, '07:00 AM', '05:00 PM', 20, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (140, '07:00 AM', '05:00 PM', 20, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (141, '06:00 AM', '06:00 PM', 21, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (142, '06:00 AM', '06:00 PM', 21, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (143, '06:00 AM', '06:00 PM', 21, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (144, '06:00 AM', '06:00 PM', 21, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (145, '06:00 AM', '06:00 PM', 21, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (146, '06:00 AM', '06:00 PM', 21, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (147, '06:00 AM', '06:00 PM', 21, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (148, '06:00 AM', '07:00 PM', 22, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (149, '06:00 AM', '07:00 PM', 22, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (150, '06:00 AM', '07:00 PM', 22, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (151, '06:00 AM', '07:00 PM', 22, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (152, '06:00 AM', '07:00 PM', 22, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (153, '06:00 AM', '07:00 PM', 22, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (154, '06:00 AM', '07:00 PM', 22, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (155, '10:00 AM', '05:00 PM', 23, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (156, '10:00 AM', '05:00 PM', 23, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (157, '10:00 AM', '05:00 PM', 23, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (158, '10:00 AM', '05:00 PM', 23, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (159, '10:00 AM', '05:00 PM', 23, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (160, '10:00 AM', '05:00 PM', 23, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (161, '10:00 AM', '05:00 PM', 23, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (162, '05:00 AM', '09:00 PM', 24, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (163, '05:00 AM', '09:00 PM', 24, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (164, '05:00 AM', '09:00 PM', 24, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (165, '05:00 AM', '09:00 PM', 24, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (166, '05:00 AM', '09:00 PM', 24, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (167, '05:00 AM', '09:00 PM', 24, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (168, '05:00 AM', '09:00 PM', 24, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (169, '06:00 AM', '08:00 PM', 25, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (170, '06:00 AM', '08:00 PM', 25, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (171, '06:00 AM', '08:00 PM', 25, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (172, '06:00 AM', '08:00 PM', 25, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (173, '06:00 AM', '08:00 PM', 25, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (174, '06:00 AM', '08:00 PM', 25, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (175, '06:00 AM', '08:00 PM', 25, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (176, '08:00 AM', '05:30 PM', 26, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (177, '08:00 AM', '05:30 PM', 26, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (178, '08:00 AM', '05:30 PM', 26, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (179, '08:00 AM', '05:30 PM', 26, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (180, '08:00 AM', '05:30 PM', 26, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (181, '08:00 AM', '05:30 PM', 26, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (182, '08:00 AM', '05:30 PM', 26, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (183, '12:00 AM', '11:59 PM', 27, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (184, '12:00 AM', '11:59 PM', 27, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (185, '12:00 AM', '11:59 PM', 27, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (186, '12:00 AM', '11:59 PM', 27, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (187, '12:00 AM', '11:59 PM', 27, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (188, '12:00 AM', '11:59 PM', 27, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (189, '12:00 AM', '11:59 PM', 27, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (190, '12:00 AM', '11:59 PM', 28, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (191, '12:00 AM', '11:59 PM', 28, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (192, '12:00 AM', '11:59 PM', 28, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (193, '12:00 AM', '11:59 PM', 28, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (194, '12:00 AM', '11:59 PM', 28, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (195, '12:00 AM', '11:59 PM', 28, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (196, '12:00 AM', '11:59 PM', 28, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (197, '10:00 AM', '05:00 PM', 29, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (198, '10:00 AM', '05:00 PM', 29, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (199, '10:00 AM', '05:00 PM', 29, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (200, '10:00 AM', '05:00 PM', 29, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (201, '10:00 AM', '05:00 PM', 29, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (202, '10:00 AM', '05:00 PM', 29, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (203, '10:00 AM', '05:00 PM', 29, 'Sunday');

-- 4. Populate MIN_INTEREST
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (1, 1, 4.2, 4.8, 4.9, 2.0, 5.0);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (2, 2, 2.0, 3.5, 3.0, 5.0, 4.0);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (3, 3, 4.8, 5.0, 4.7, 4.5, 4.8);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (4, 4, 4.9, 4.9, 4.8, 3.0, 4.7);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (5, 5, 4.3, 4.5, 2.5, 3.5, 5.0);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (6, 6, 4.5, 4.6, 4.8, 4.2, 4.5);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (7, 7, 5.0, 5.0, 4.0, 3.8, 4.7);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (8, 8, 2.5, 3.0, 2.0, 4.8, 3.5);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (9, 9, 5.0, 5.0, 5.0, 2.5, 5.0);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (10, 10, 1.5, 3.0, 2.0, 5.0, 3.5);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (11, 11, 4.6, 4.8, 4.9, 2.5, 4.8);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (12, 12, 4.8, 4.9, 3.5, 3.0, 4.2);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (13, 13, 2.0, 2.5, 3.0, 5.0, 3.5);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (14, 14, 1.5, 2.5, 2.0, 5.0, 3.0);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (15, 15, 4.8, 4.7, 4.6, 3.0, 4.5);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (16, 16, 1.5, 3.0, 2.5, 5.0, 3.5);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (17, 17, 4.9, 5.0, 5.0, 3.0, 5.0);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (18, 18, 5.0, 5.0, 4.8, 3.5, 5.0);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (19, 19, 4.7, 4.8, 4.9, 3.0, 4.8);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (20, 20, 2.0, 3.0, 2.0, 5.0, 3.5);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (21, 21, 4.8, 5.0, 3.0, 3.5, 4.7);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (22, 22, 3.5, 4.0, 2.0, 3.0, 4.6);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (23, 23, 2.0, 2.5, 2.0, 4.8, 3.5);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (24, 24, 4.7, 4.8, 5.0, 2.0, 4.9);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (25, 25, 4.6, 4.7, 4.9, 4.5, 4.7);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (26, 26, 4.8, 4.9, 4.5, 3.5, 4.8);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (27, 27, 4.0, 4.2, 2.5, 4.5, 4.0);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (28, 28, 3.8, 4.0, 2.0, 4.6, 3.8);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (29, 29, 4.2, 5.0, 2.0, 2.0, 5.0);

-- 5. Populate FESTIVALS
INSERT INTO FESTIVALS (id, name, start_date, end_date, city_id, description) VALUES (1, 'Rath Yatra (Grand Chariot Festival)', '2026-06-27', '2026-07-06', 2, 'World-renowned annual procession of Lord Jagannath, Balabhadra, and Subhadra in majestic chariots along the Bada Danda in Puri.');
INSERT INTO FESTIVALS (id, name, start_date, end_date, city_id, description) VALUES (2, 'Ashokashtami & Rukuna Ratha Yatra', '2026-04-14', '2026-04-18', 1, 'Car festival of Lord Lingaraj celebrated in Bhubaneswar''s ancient Ekamra Kshetra with ancient Kalinga rituals.');
INSERT INTO FESTIVALS (id, name, start_date, end_date, city_id, description) VALUES (3, 'Maha Shivaratri & Jagara', '2026-02-15', '2026-02-16', 1, 'Grand nocturnal vigil at Lingaraj Temple and Dhabaleswar Temple culminating with the Mahadipa offering at midnight.');
INSERT INTO FESTIVALS (id, name, start_date, end_date, city_id, description) VALUES (4, 'Chandan Yatra', '2026-05-09', '2026-05-29', 2, '21-day summer water festival celebrated with divine boat rides in the Narendra Tirtha lake in Puri.');
INSERT INTO FESTIVALS (id, name, start_date, end_date, city_id, description) VALUES (5, 'Durga Puja & Silver Filigree (Chandi Medha)', '2026-10-18', '2026-10-23', 3, 'Historic autumnal celebration in Cuttack featuring exquisite Tarakasi (silver filigree) tableaus and divine energy.');
INSERT INTO FESTIVALS (id, name, start_date, end_date, city_id, description) VALUES (6, 'Bali Yatra (Maritime Trade Festival)', '2026-11-23', '2026-11-30', 3, 'Asia''s largest open-air trade fair on the banks of Mahanadi commemorating ancient maritime trade voyages to Bali and Java.');
INSERT INTO FESTIVALS (id, name, start_date, end_date, city_id, description) VALUES (7, 'Konark Dance & Music Festival', '2026-12-01', '2026-12-05', 2, 'Spectacular classical Indian dance performances set against the illuminated backdrop of the UNESCO World Heritage Sun Temple.');

-- 6. Populate USERS_INPUT
INSERT INTO USERS_INPUT (id, gps_location, start_date, start_time, end_time, age) VALUES (1, '20.2961,85.8245', '2026-10-15', '08:00 AM', '08:00 PM', 58);
INSERT INTO USERS_INPUT (id, gps_location, start_date, start_time, end_time, age) VALUES (2, '19.8135,85.8312', '2026-11-01', '07:30 AM', '07:00 PM', 62);
INSERT INTO USERS_INPUT (id, gps_location, start_date, start_time, end_time, age) VALUES (3, '20.4625,85.8830', '2026-11-24', '09:00 AM', '09:30 PM', 45);

-- =====================================================================
-- Reset Sequences in PostgreSQL for AUTO_INCREMENT
-- =====================================================================
SELECT setval('cities_id_seq', (SELECT COALESCE(MAX(id), 1) FROM CITIES));
SELECT setval('places_id_seq', (SELECT COALESCE(MAX(id), 1) FROM PLACES));
SELECT setval('opening_hours_id_seq', (SELECT COALESCE(MAX(id), 1) FROM OPENING_HOURS));
SELECT setval('min_interest_id_seq', (SELECT COALESCE(MAX(id), 1) FROM MIN_INTEREST));
SELECT setval('festivals_id_seq', (SELECT COALESCE(MAX(id), 1) FROM FESTIVALS));
SELECT setval('users_input_id_seq', (SELECT COALESCE(MAX(id), 1) FROM USERS_INPUT));