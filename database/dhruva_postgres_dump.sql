-- =====================================================================
-- DHRUVA Cultural Travel Planner - PostgreSQL Standalone Database Dump
-- Generated: 2026-08-28T19:56:06.285967
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
-- Table 2: CITY_INTEREST
-- ---------------------------------------------------------------------
CREATE TABLE CITY_INTEREST (
    id SERIAL PRIMARY KEY,
    city_id INTEGER NOT NULL UNIQUE,
    architecture DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    history DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    spiritual DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    nature DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    culture DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    CONSTRAINT fk_city_interest_city FOREIGN KEY (city_id) REFERENCES CITIES(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Table 3: PLACES
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
    CONSTRAINT fk_places_city FOREIGN KEY (city_id) REFERENCES CITIES(id) ON DELETE CASCADE
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
    CONSTRAINT fk_hours_place FOREIGN KEY (place_id) REFERENCES PLACES(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Table 5: MIN_INTEREST
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
-- Table 6: FESTIVALS
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
    CONSTRAINT fk_trips_city FOREIGN KEY (city_id) REFERENCES CITIES(id) ON DELETE CASCADE
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
    CONSTRAINT fk_time_windows_trip FOREIGN KEY (trip_id) REFERENCES TRIPS(id) ON DELETE CASCADE
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
    CONSTRAINT fk_itinerary_items_trip FOREIGN KEY (trip_id) REFERENCES TRIPS(id) ON DELETE CASCADE,
    CONSTRAINT fk_itinerary_items_place FOREIGN KEY (place_id) REFERENCES PLACES(id) ON DELETE CASCADE
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

-- ---------------------------------------------------------------------
-- Seed Inserts
-- ---------------------------------------------------------------------
INSERT INTO CITIES (id, name, state, lat, long) VALUES (1, 'Bhubaneswar', 'Odisha', 20.2961, 85.8245);
INSERT INTO CITIES (id, name, state, lat, long) VALUES (2, 'Puri', 'Odisha', 19.8135, 85.8312);
INSERT INTO CITIES (id, name, state, lat, long) VALUES (3, 'Cuttack', 'Odisha', 20.4625, 85.883);
INSERT INTO CITY_INTEREST (id, city_id, architecture, history, spiritual, nature, culture) VALUES (1, 1, 4.58, 4.71, 4.35, 2.35, 4.52);
INSERT INTO CITY_INTEREST (id, city_id, architecture, history, spiritual, nature, culture) VALUES (2, 2, 4.63, 4.76, 4.61, 2.64, 4.87);
INSERT INTO CITY_INTEREST (id, city_id, architecture, history, spiritual, nature, culture) VALUES (3, 3, 4.85, 4.9, 4.38, 2.62, 4.83);
INSERT INTO PLACES (id, name, duration, duration_label, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee, source, source_url, last_updated) VALUES (1, 'Lingaraja Temple', 2.0, '1.5 to 2.5 Hours', 20.238333, 85.833611, 'Low', 1, 'Temple & Sacred Sanctum', 'Kalinga Architecture Shiva Temple', 'Lingaraja Temple, dedicated to Lord Shiva, is the largest and most prominent historic temple in Bhubaneswar, exemplifying the quintessence of Kalinga architecture. Built primarily by the Somavamsi dynasty with later Ganga additions, it remains an active place of worship and draws thousands of devotees daily.', 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Lingaraj_Temple_%2C_Bhubaneswar.jpg/960px-Lingaraj_Temple_%2C_Bhubaneswar.jpg?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=thumbnail', 'Free entry', 'Wikipedia & SerpApi', 'https://en.wikipedia.org/wiki/Lingaraja_Temple', '2026-08-26T22:26:58Z');
INSERT INTO PLACES (id, name, duration, duration_label, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee, source, source_url, last_updated) VALUES (2, 'Mukteshvara Temple, Bhubaneswar', 1.0, '1 to 2 Hours', 20.2427, 85.840392, 'Low', 1, 'Temple & Sacred Sanctum', 'Kalinga Architecture Shiva Temple', 'Mukteshvara Temple, dating to c. 950–975 CE, is a 10th‑century Hindu shrine dedicated to Shiva and celebrated as the "Gem of Odisha architecture" for its pioneering torana and intricate Kalinga carvings.', 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/Muktesvar_Temple.jpg/960px-Muktesvar_Temple.jpg?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=thumbnail', 'Free entry (Donations welcome)', 'Wikipedia & SerpApi', 'https://en.wikipedia.org/wiki/Mukteshvara_Temple,_Bhubaneswar', '2026-08-11T23:17:34Z');
INSERT INTO PLACES (id, name, duration, duration_label, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee, source, source_url, last_updated) VALUES (3, 'Rajarani Temple', 2.0, '1.5 to 2.5 Hours', 20.243444, 85.843522, 'Low', 1, 'Heritage & Archaeological Site', '11th-Century Non-Functioning Sandstone Temple Monument (ASI)', 'Rajarani Temple, an 11th‑century Hindu shrine in Bhubaneswar, is famed for its distinctive yellow‑red sandstone construction and intricate erotic carvings. Built in the pancharatha style with a curvilinear vimana and pyramidal jagamohana, the monument reflects the mature Kalinga architectural tradition and is maintained by the ASI.', 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Rajarani_Temple_2.jpg/960px-Rajarani_Temple_2.jpg?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=thumbnail', '₹25 for Indians, ₹250 for Foreigners (Children below 15 free)', 'Wikipedia & SerpApi', 'https://en.wikipedia.org/wiki/Rajarani_Temple', '2026-08-11T23:20:56Z');
INSERT INTO PLACES (id, name, duration, duration_label, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee, source, source_url, last_updated) VALUES (4, 'Dhauli', 2.0, '1.5 to 2.5 Hours', 20.192372, 85.839489, 'Low', 1, 'Heritage & Archaeological Site', 'Buddhist Heritage Site', 'Dhauli, a hill on the banks of the Daya River about 8 km south of Bhubaneswar, is traditionally identified as the battlefield of the Kalinga War that transformed Emperor Ashoka. The site houses the modern Santi Stupa, a peace pagoda built in 1972 by Japanese Buddhist organisations, and serves as a focal point for Buddhist heritage and research in Odisha.', 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/bd/ShantiSthupa_Dhauli.jpg/960px-ShantiSthupa_Dhauli.jpg?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=thumbnail', '₹50 per person (general entry)', 'Wikipedia & SerpApi', 'https://en.wikipedia.org/wiki/Dhauli', '2026-08-16T22:52:28Z');
INSERT INTO PLACES (id, name, duration, duration_label, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee, source, source_url, last_updated) VALUES (5, 'Udayagiri and Khandagiri caves', 2.0, '1.5 to 2.5 Hours', 20.262831, 85.78603, 'Low', 1, 'Heritage & Archaeological Site', 'Jain Rock‑Cut Caves', 'The Udayagiri and Khandagiri caves, located about 3 km south of Bhubaneswar, are a group of 33 partially natural, partially artificial rock‑cut caves dating to the 2nd–1st century BCE. Carved under King Kharavela for Jain ascetics, they showcase intricate reliefs, double‑storeyed monastic cells and historic sculptures such as the famous Rani Gumpha and Hathi Gumpha.', 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Khandagari_and_Udaygiri_featured_image.jpg/960px-Khandagari_and_Udaygiri_featured_image.jpg?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=thumbnail', '₹25 per person', 'Wikipedia & SerpApi', 'https://en.wikipedia.org/wiki/Udayagiri_and_Khandagiri_caves', '2026-08-26T22:27:07Z');
INSERT INTO PLACES (id, name, duration, duration_label, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee, source, source_url, last_updated) VALUES (6, 'Chausath Yogini Temple, Hirapur', 2.0, '1.5 to 2.5 Hours', 20.226515, 85.875595, 'Low', 1, 'Temple & Sacred Sanctum', 'Kalinga Architecture Sacred Sanctum', 'The Chausathi Yogini Temple (64-Yogini Temple) of Hirapur, also known as the Mahamaya Temple, is 20 km outside Bhubaneswar, the capital of Odisha state of Eastern India. It is devoted to the worship of the yoginis, auspicious goddess-like figures.', 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Chausath_Yogini_Temple_-_Outside.JPG/960px-Chausath_Yogini_Temple_-_Outside.JPG?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=thumbnail', 'Free entry (Donations welcome; special darshan queue fees may apply)', 'Wikipedia & SerpApi', 'https://en.wikipedia.org/wiki/Chausath_Yogini_Temple,_Hirapur', '2026-08-26T22:26:50Z');
INSERT INTO PLACES (id, name, duration, duration_label, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee, source, source_url, last_updated) VALUES (7, 'Brahmeswara Temple', 2.0, '1.5 to 2.5 Hours', 20.239701, 85.851764, 'Low', 1, 'Temple & Sacred Sanctum', 'Kalinga Architecture Shiva Temple', 'Brahmeswara Temple, erected in 1058 CE by Queen Kolavati Devi during the Somavamsi dynasty, is a richly carved 9th‑century Shiva shrine in Bhubaneswar. It exemplifies mature Kalinga architecture with a panchatanaya layout, intricate stone carvings, and early use of iron beams, while remaining an active place of worship.', 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0d/Brahmeswar_Temple%2C_Bhubaneswar.JPG/960px-Brahmeswar_Temple%2C_Bhubaneswar.JPG?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=thumbnail', 'Free entry', 'Wikipedia & SerpApi', 'https://en.wikipedia.org/wiki/Brahmeswara_Temple', '2026-08-11T19:27:45Z');
INSERT INTO PLACES (id, name, duration, duration_label, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee, source, source_url, last_updated) VALUES (8, 'Ananta Vasudeva Temple', 2.0, '1.5 to 2.5 Hours', 20.240606, 85.835781, 'Low', 1, 'Temple & Sacred Sanctum', 'Kalinga Architecture Vaishnavite Temple', 'Ananta Vasudeva Temple, built in the 13th century under the Eastern Ganga dynasty, is a prominent Vaishnavite shrine in Bhubaneswar dedicated to Krishna, Balarama and Subhadra. Its architecture mirrors the Lingaraj temple with distinctive miniature shikharas and richly carved stone idols, and it remains an active place of worship offering free darshan and community prasad.', 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/Ananta_Vasudev.jpg/960px-Ananta_Vasudev.jpg?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=thumbnail', 'Free entry (Donations welcome)', 'Wikipedia & SerpApi', 'https://en.wikipedia.org/wiki/Ananta_Vasudeva_Temple', '2026-08-21T09:18:11Z');
INSERT INTO PLACES (id, name, duration, duration_label, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee, source, source_url, last_updated) VALUES (9, 'Sisupalgarh', 2.5, '2 to 3 Hours', 20.226639, 85.853056, 'Moderate', 1, 'Heritage & Archaeological Site', 'Ancient Kalinga Monument', 'Sisupalgarh or Sisupalagada (Odia: [sisupaːl̪ɔɡɔɽɔ] ) is situated in Khurda District in Odisha, India, and houses ruined fortifications. First inhabited around 7th to 6th centuries BCE, it is one of the largest and best-preserved early historic fortifications in India, and was once the capital of ancient Kalinga.', 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Sisupalgarh_fortified_urban_center.jpg/960px-Sisupalgarh_fortified_urban_center.jpg?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=thumbnail', 'Free entry (Open monument)', 'Wikipedia & SerpApi', 'https://en.wikipedia.org/wiki/Sisupalgarh', '2026-08-26T22:27:13Z');
INSERT INTO PLACES (id, name, duration, duration_label, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee, source, source_url, last_updated) VALUES (10, 'Odisha State Museum', 2.5, '2 to 3 Hours', 20.2562, 85.8415, 'Low', 1, 'Arts, Crafts & Museum', 'State Museum', 'The Odisha State Museum in Bhubaneswar, established in 1932 and housed in its present building since 1960, showcases eleven galleries covering archaeology, epigraphy, numismatics, natural history, art, crafts, and more. Managed by the Cultural Affairs Department of the Government of Odisha, it offers visitors a comprehensive view of the region''s cultural and historical heritage.', 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Bhubaneswar_State_Museum.jpg/960px-Bhubaneswar_State_Museum.jpg?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=thumbnail', '₹20 (general admission)', 'Wikipedia & SerpApi', 'https://en.wikipedia.org/wiki/Odisha_State_Museum', '2026-08-12T08:46:38Z');
INSERT INTO PLACES (id, name, duration, duration_label, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee, source, source_url, last_updated) VALUES (11, 'Parsurameswara Temple', 2.0, '1.5 to 2.5 Hours', 20.243131, 85.839047, 'Low', 1, 'Temple & Sacred Sanctum', 'Kalinga Architecture Sacred Sanctum', 'Parsurameswara Temple (IAST: Paraśurāmeśvara) also spelt Parashurameshvara, is a Hindu temple, located in the East Indian city of Bhubaneswar, the capital of Odisha, India, is considered the best preserved specimen of an early Odia Hindu temple dated to the Shailodbhava period between the 7th and 8th centuries CE. The temple is dedicated to the Hindu god Shiva and is one of the oldest existing temples in the state.', 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Parsurameswara_temple_complex.jpg/960px-Parsurameswara_temple_complex.jpg?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=thumbnail', 'Free entry (Donations welcome; special darshan queue fees may apply)', 'Wikipedia & SerpApi', 'https://en.wikipedia.org/wiki/Parsurameswara_Temple', '2026-08-11T23:17:34Z');
INSERT INTO PLACES (id, name, duration, duration_label, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee, source, source_url, last_updated) VALUES (12, 'Jagannath Temple, Puri', 2.0, '1.5 to 2.5 Hours', 19.804722, 85.818333, 'Low', 2, 'Temple & Sacred Sanctum', 'Kalinga Architecture Sacred Sanctum', 'The Jagannath Temple is a Hindu temple dedicated to Jagannath, a form of Vishnu. It is located in Puri, Odisha, on the eastern coast of India.', 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/Shri_Jagannath_temple.jpg/960px-Shri_Jagannath_temple.jpg?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=thumbnail', 'Free entry (Donations welcome; special darshan queue fees may apply)', 'Wikipedia & SerpApi', 'https://en.wikipedia.org/wiki/Jagannath_Temple,_Puri', '2026-08-26T22:26:58Z');
INSERT INTO PLACES (id, name, duration, duration_label, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee, source, source_url, last_updated) VALUES (13, 'Gundicha Temple', 2.0, '1.5 to 2.5 Hours', 19.816917, 85.840361, 'Low', 2, 'Temple & Sacred Sanctum', 'Kalinga Architecture Sacred Sanctum', 'Gundicha Temple (Odia: ଗୁଣ୍ଡିଚା ମନ୍ଦିର), is a Hindu temple, situated in the temple town of Puri in the state of Odisha, India. It is significant for being the destination of the celebrated annual Rath Yatra of Puri.', 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Gundicha_Temple%2C_Puri%2C_Odisha1.JPG/960px-Gundicha_Temple%2C_Puri%2C_Odisha1.JPG?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=thumbnail', 'Free entry (Donations welcome; special darshan queue fees may apply)', 'Wikipedia & SerpApi', 'https://en.wikipedia.org/wiki/Gundicha_Temple', '2026-08-23T09:08:26Z');
INSERT INTO PLACES (id, name, duration, duration_label, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee, source, source_url, last_updated) VALUES (14, 'Lokanatha Temple', 2.0, '1.5 to 2.5 Hours', 19.920493, 85.818156, 'Low', 2, 'Temple & Sacred Sanctum', 'Shiva Temple', 'Lokanatha Temple in Puri, Odisha, is a Hindu shrine dedicated to Lord Shiva as Lokanatha, famed for its linga that remains perpetually under water. The deity is regarded as the guardian of the Jagannath Temple’s treasures, and the temple celebrates festivals such as Shivaratri, Sankranti Somavar and weekly fairs that attract many devotees seeking the linga’s reputed healing powers.', 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Lokanath_temple.jpeg/960px-Lokanath_temple.jpeg?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=thumbnail', 'Free entry (Donations welcome)', 'Wikipedia & SerpApi', 'https://en.wikipedia.org/wiki/Lokanatha_Temple', '2026-08-10T12:31:17Z');
INSERT INTO PLACES (id, name, duration, duration_label, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee, source, source_url, last_updated) VALUES (15, 'Raghurajpur', 2.5, '2 to 3 Hours', 19.885556, 85.826389, 'Low', 2, 'Arts, Crafts & Museum', 'Traditional Handloom & Crafts Village', 'Raghurajpur is a heritage crafts village in Puri district, Odisha, India, known for its master Pattachitra painters, an art form which dates back to 5 BC in the region, and Gotipua dance troupes, the precursor to the Indian classical dance form of Odissi. It is also known as the birthplace of the Odissi exponents Padma Vibhushan Guru and Kelucharan Mohapatra and the Gotipua dancer Padma Shri Guru Maguni Charan Das.', 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Entrance_of_Raghurajpur.jpg/960px-Entrance_of_Raghurajpur.jpg?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=thumbnail', 'Free entry to artisan workshops', 'Wikipedia & SerpApi', 'https://en.wikipedia.org/wiki/Raghurajpur', '2026-08-14T19:37:15Z');
INSERT INTO PLACES (id, name, duration, duration_label, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee, source, source_url, last_updated) VALUES (16, 'Konark Sun Temple', 2.5, '2 to 2.5 Hours', 19.8875, 86.094722, 'Low', 2, 'Heritage & Sacred Sanctum', 'UNESCO World Heritage Sun Temple', 'Konark Sun Temple is a 13th-century CE Hindu Sun temple at Konark about 35 kilometres (22 mi) northeast from Puri city on the coastline in Puri district, Odisha, India. The temple is attributed to king Narasingha Deva I of the Eastern Ganga dynasty about 1250 CE.', 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/Konarka_Temple.jpg/960px-Konarka_Temple.jpg?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=thumbnail', '₹40 for Indians, ₹600 for Foreigners (ASI ticketed)', 'Wikipedia & SerpApi', 'https://en.wikipedia.org/wiki/Konark_Sun_Temple', '2026-08-26T22:27:09Z');
INSERT INTO PLACES (id, name, duration, duration_label, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee, source, source_url, last_updated) VALUES (17, 'Varahi Deula, Chaurasi', 2.0, '1.5 to 2.5 Hours', 20.058536, 86.118472, 'Low', 2, 'Temple & Sacred Sanctum', 'Kalinga Architecture Sacred Sanctum', 'Barahi Deula (Odia:ବାରାହୀ ଦେଉଳ) is an ancient 10th century built temple situated on the eastern coast of Odisha in Puri district, India. The barahi temple of Chaurasi is unique in more than one way.', 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ed/Varahi_Temple_1.jpg/960px-Varahi_Temple_1.jpg?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=thumbnail', 'Free entry (Donations welcome; special darshan queue fees may apply)', 'Wikipedia & SerpApi', 'https://en.wikipedia.org/wiki/Varahi_Deula,_Chaurasi', '2026-08-21T09:18:11Z');
INSERT INTO PLACES (id, name, duration, duration_label, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee, source, source_url, last_updated) VALUES (18, 'Alarnatha Mandira', 2.0, '1.5 to 2.5 Hours', 19.79488, 85.650201, 'Low', 2, 'Temple & Sacred Sanctum', 'Kalinga Architecture Sacred Sanctum', 'Alarnatha Mandira or Alvarnaatha Mandira (Sanskrit: अल्वार् नाथ), (Odia: ଅଲାରନାଥ) is a Hindu temple dedicated to Vishnu and located in Brahmagiri, Odisha, near Puri. The temple also houses a shrine for his consort Mahalakshmi.', 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Alarnatha_Mandira.jpg/960px-Alarnatha_Mandira.jpg?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=thumbnail', 'Free entry (Donations welcome; special darshan queue fees may apply)', 'Wikipedia & SerpApi', 'https://en.wikipedia.org/wiki/Alarnatha_Mandira', '2026-08-21T09:18:11Z');
INSERT INTO PLACES (id, name, duration, duration_label, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee, source, source_url, last_updated) VALUES (19, 'Barabati fort', 2.0, '1.5 to 2.5 Hours', 20.484631, 85.864425, 'Low', 3, 'Monument & Fort', '10th-Century Somavamshi Fortification Ruins', 'Barabati Fort is a 987 CE fort built by Marakata Keshari of Somavanshi (Keshari) dynasty in Cuttack, Odisha. The ruins of the fort remain with its moat, gate, and the earthen mound of the nine-storied palace.', 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/Entrance_of_Barabati_fort.jpg/960px-Entrance_of_Barabati_fort.jpg?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=thumbnail', 'Free entry (ASI protected monument)', 'Wikipedia & SerpApi', 'https://en.wikipedia.org/wiki/Barabati_fort', '2026-08-22T21:37:30Z');
INSERT INTO PLACES (id, name, duration, duration_label, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee, source, source_url, last_updated) VALUES (20, 'Kataka Chandi Mandir', 2.0, '1.5 to 2.5 Hours', 20.477244, 85.862564, 'Low', 3, 'Temple & Sacred Sanctum', 'Kalinga Architecture Sacred Sanctum', 'The Kataka Chandi Mandir is a temple dedicated to the Hindu goddess Chandi in Kataka, Odisha, India, near the banks of the Mahanadi River. Chandi Devi Chandi Mandir, Chandigarh Chandi Devi Temple, Haridwar.', 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Katak_Chandi_temple.jpg/960px-Katak_Chandi_temple.jpg?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=thumbnail', 'Free entry (Donations welcome; special darshan queue fees may apply)', 'Wikipedia & SerpApi', 'https://en.wikipedia.org/wiki/Kataka_Chandi_Mandir', '2026-08-21T10:57:31Z');
INSERT INTO PLACES (id, name, duration, duration_label, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee, source, source_url, last_updated) VALUES (21, 'Dhabaleswar Temple', 2.0, '1.5 to 2.5 Hours', 20.504117, 85.803524, 'Low', 3, 'Temple & Sacred Sanctum', 'Kalinga Architecture Sacred Sanctum', 'Dhabaleswar Temple is dedicated to the worship of Lord Shiva. It is situated at a distance of 27 km from the city of Cuttack, Odisha, India, on the riverine island of Lord Dhabaleshwar.', 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fd/Dhabaleswar_Temple.JPG/960px-Dhabaleswar_Temple.JPG?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=thumbnail', 'Free entry (Donations welcome; special darshan queue fees may apply)', 'Wikipedia & SerpApi', 'https://en.wikipedia.org/wiki/Dhabaleswar_Temple', '2026-08-12T08:46:38Z');
INSERT INTO PLACES (id, name, duration, duration_label, lat, long, risk, city_id, category, sub_category, description, image_url, entry_fee, source, source_url, last_updated) VALUES (22, 'Choudwar', 2.0, '1.5 to 2.5 Hours', 20.533333, 85.917222, 'Low', 3, 'Temple & Sacred Sanctum', 'Kalinga Architecture Sacred Sanctum', 'Choudwar is a town and a municipality in Cuttack district in the Indian state of Odisha. It comes under Bhubaneswar-Cuttack commissionerate.', 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/Choudwar_Cuttack.jpg/960px-Choudwar_Cuttack.jpg?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=thumbnail', 'Free entry (Donations welcome; special darshan queue fees may apply)', 'Wikipedia & SerpApi', 'https://en.wikipedia.org/wiki/Choudwar', '2026-08-18T03:51:41Z');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (1, '06:30 AM', '07:30 PM', 1, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (2, '06:30 AM', '07:30 PM', 1, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (3, '06:30 AM', '07:30 PM', 1, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (4, '06:30 AM', '07:30 PM', 1, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (5, '06:30 AM', '07:30 PM', 1, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (6, '06:30 AM', '07:30 PM', 1, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (7, '06:30 AM', '07:30 PM', 1, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (8, '06:30 AM', '07:30 PM', 2, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (9, '06:30 AM', '07:30 PM', 2, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (10, '06:30 AM', '07:30 PM', 2, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (11, '06:30 AM', '07:30 PM', 2, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (12, '06:30 AM', '07:30 PM', 2, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (13, '06:30 AM', '07:30 PM', 2, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (14, '06:30 AM', '07:30 PM', 2, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (15, '06:30 AM', '07:30 PM', 3, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (16, '06:30 AM', '07:30 PM', 3, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (17, '06:30 AM', '07:30 PM', 3, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (18, '06:30 AM', '07:30 PM', 3, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (19, '06:30 AM', '07:30 PM', 3, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (20, '06:30 AM', '07:30 PM', 3, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (21, '06:30 AM', '07:30 PM', 3, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (22, '06:00 AM', '07:00 PM', 4, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (23, '06:00 AM', '07:00 PM', 4, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (24, '06:00 AM', '07:00 PM', 4, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (25, '06:00 AM', '07:00 PM', 4, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (26, '06:00 AM', '07:00 PM', 4, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (27, '06:00 AM', '07:00 PM', 4, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (28, '06:00 AM', '07:00 PM', 4, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (29, '08:00 AM', '05:00 PM', 5, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (30, '08:00 AM', '05:00 PM', 5, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (31, '08:00 AM', '05:00 PM', 5, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (32, '08:00 AM', '05:00 PM', 5, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (33, '08:00 AM', '05:00 PM', 5, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (34, '08:00 AM', '05:00 PM', 5, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (35, '08:00 AM', '05:00 PM', 5, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (36, '06:00 AM', '08:30 PM', 6, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (37, '06:00 AM', '08:30 PM', 6, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (38, '06:00 AM', '08:30 PM', 6, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (39, '06:00 AM', '08:30 PM', 6, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (40, '06:00 AM', '08:30 PM', 6, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (41, '06:00 AM', '08:30 PM', 6, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (42, '06:00 AM', '08:30 PM', 6, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (43, '05:00 AM', '09:00 PM', 7, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (44, '05:00 AM', '09:00 PM', 7, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (45, '05:00 AM', '09:00 PM', 7, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (46, '05:00 AM', '09:00 PM', 7, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (47, '05:00 AM', '09:00 PM', 7, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (48, '05:00 AM', '09:00 PM', 7, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (49, '05:00 AM', '09:00 PM', 7, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (50, '06:00 AM', '08:00 PM', 8, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (51, '06:00 AM', '08:00 PM', 8, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (52, '06:00 AM', '08:00 PM', 8, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (53, '06:00 AM', '08:00 PM', 8, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (54, '06:00 AM', '08:00 PM', 8, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (55, '06:00 AM', '08:00 PM', 8, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (56, '06:00 AM', '08:00 PM', 8, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (57, '08:00 AM', '05:00 PM', 9, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (58, '08:00 AM', '05:00 PM', 9, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (59, '08:00 AM', '05:00 PM', 9, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (60, '08:00 AM', '05:00 PM', 9, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (61, '08:00 AM', '05:00 PM', 9, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (62, '08:00 AM', '05:00 PM', 9, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (63, '08:00 AM', '05:00 PM', 9, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (64, '10:00 AM', '05:00 PM', 10, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (65, '10:00 AM', '05:00 PM', 10, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (66, '10:00 AM', '05:00 PM', 10, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (67, '10:00 AM', '05:00 PM', 10, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (68, '10:00 AM', '05:00 PM', 10, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (69, '10:00 AM', '05:00 PM', 10, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (70, '06:00 AM', '08:30 PM', 11, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (71, '06:00 AM', '08:30 PM', 11, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (72, '06:00 AM', '08:30 PM', 11, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (73, '06:00 AM', '08:30 PM', 11, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (74, '06:00 AM', '08:30 PM', 11, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (75, '06:00 AM', '08:30 PM', 11, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (76, '06:00 AM', '08:30 PM', 11, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (77, '06:00 AM', '08:30 PM', 12, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (78, '06:00 AM', '08:30 PM', 12, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (79, '06:00 AM', '08:30 PM', 12, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (80, '06:00 AM', '08:30 PM', 12, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (81, '06:00 AM', '08:30 PM', 12, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (82, '06:00 AM', '08:30 PM', 12, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (83, '06:00 AM', '08:30 PM', 12, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (84, '06:00 AM', '08:30 PM', 13, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (85, '06:00 AM', '08:30 PM', 13, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (86, '06:00 AM', '08:30 PM', 13, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (87, '06:00 AM', '08:30 PM', 13, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (88, '06:00 AM', '08:30 PM', 13, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (89, '06:00 AM', '08:30 PM', 13, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (90, '06:00 AM', '08:30 PM', 13, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (91, '05:00 AM', '09:00 PM', 14, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (92, '05:00 AM', '09:00 PM', 14, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (93, '05:00 AM', '09:00 PM', 14, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (94, '05:00 AM', '09:00 PM', 14, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (95, '05:00 AM', '09:00 PM', 14, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (96, '05:00 AM', '09:00 PM', 14, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (97, '05:00 AM', '09:00 PM', 14, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (98, '08:00 AM', '07:00 PM', 15, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (99, '08:00 AM', '07:00 PM', 15, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (100, '08:00 AM', '07:00 PM', 15, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (101, '08:00 AM', '07:00 PM', 15, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (102, '08:00 AM', '07:00 PM', 15, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (103, '08:00 AM', '07:00 PM', 15, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (104, '08:00 AM', '07:00 PM', 15, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (105, '06:00 AM', '06:00 PM', 16, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (106, '06:00 AM', '06:00 PM', 16, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (107, '06:00 AM', '06:00 PM', 16, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (108, '06:00 AM', '06:00 PM', 16, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (109, '06:00 AM', '06:00 PM', 16, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (110, '06:00 AM', '06:00 PM', 16, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (111, '06:00 AM', '06:00 PM', 16, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (112, '06:00 AM', '08:30 PM', 17, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (113, '06:00 AM', '08:30 PM', 17, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (114, '06:00 AM', '08:30 PM', 17, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (115, '06:00 AM', '08:30 PM', 17, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (116, '06:00 AM', '08:30 PM', 17, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (117, '06:00 AM', '08:30 PM', 17, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (118, '06:00 AM', '08:30 PM', 17, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (119, '06:00 AM', '08:30 PM', 18, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (120, '06:00 AM', '08:30 PM', 18, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (121, '06:00 AM', '08:30 PM', 18, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (122, '06:00 AM', '08:30 PM', 18, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (123, '06:00 AM', '08:30 PM', 18, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (124, '06:00 AM', '08:30 PM', 18, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (125, '06:00 AM', '08:30 PM', 18, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (126, '06:00 AM', '06:00 PM', 19, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (127, '06:00 AM', '06:00 PM', 19, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (128, '06:00 AM', '06:00 PM', 19, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (129, '06:00 AM', '06:00 PM', 19, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (130, '06:00 AM', '06:00 PM', 19, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (131, '06:00 AM', '06:00 PM', 19, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (132, '06:00 AM', '06:00 PM', 19, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (133, '06:00 AM', '08:30 PM', 20, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (134, '06:00 AM', '08:30 PM', 20, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (135, '06:00 AM', '08:30 PM', 20, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (136, '06:00 AM', '08:30 PM', 20, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (137, '06:00 AM', '08:30 PM', 20, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (138, '06:00 AM', '08:30 PM', 20, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (139, '06:00 AM', '08:30 PM', 20, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (140, '06:00 AM', '08:30 PM', 21, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (141, '06:00 AM', '08:30 PM', 21, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (142, '06:00 AM', '08:30 PM', 21, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (143, '06:00 AM', '08:30 PM', 21, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (144, '06:00 AM', '08:30 PM', 21, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (145, '06:00 AM', '08:30 PM', 21, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (146, '06:00 AM', '08:30 PM', 21, 'Sunday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (147, '06:00 AM', '08:30 PM', 22, 'Monday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (148, '06:00 AM', '08:30 PM', 22, 'Tuesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (149, '06:00 AM', '08:30 PM', 22, 'Wednesday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (150, '06:00 AM', '08:30 PM', 22, 'Thursday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (151, '06:00 AM', '08:30 PM', 22, 'Friday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (152, '06:00 AM', '08:30 PM', 22, 'Saturday');
INSERT INTO OPENING_HOURS (id, opens_at, closes_at, place_id, day_of_week) VALUES (153, '06:00 AM', '08:30 PM', 22, 'Sunday');
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (1, 1, 4.9, 4.8, 5.0, 2.5, 4.8);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (2, 2, 4.8, 4.5, 4.9, 2.0, 4.5);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (3, 3, 4.8, 4.5, 4.2, 1.5, 4.3);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (4, 4, 3.5, 4.8, 4.9, 3.0, 4.0);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (5, 5, 4.8, 4.7, 4.0, 3.0, 4.0);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (6, 6, 4.9, 4.9, 5.0, 2.5, 4.9);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (7, 7, 4.9, 4.7, 5.0, 2.3, 4.6);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (8, 8, 4.6, 4.5, 5.0, 2.0, 4.5);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (9, 9, 4.8, 5.0, 3.8, 3.5, 4.7);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (10, 10, 3.5, 4.5, 1.0, 1.0, 4.5);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (11, 11, 4.9, 4.9, 5.0, 2.5, 4.9);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (12, 12, 4.9, 4.9, 5.0, 2.5, 4.9);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (13, 13, 4.9, 4.9, 5.0, 2.5, 4.9);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (14, 14, 3.5, 4.0, 5.0, 3.0, 4.5);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (15, 15, 4.3, 4.7, 2.5, 2.5, 5.0);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (16, 16, 5.0, 5.0, 4.8, 3.0, 5.0);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (17, 17, 4.9, 4.9, 5.0, 2.5, 4.9);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (18, 18, 4.9, 4.9, 5.0, 2.5, 4.9);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (19, 19, 4.7, 4.9, 2.5, 3.0, 4.6);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (20, 20, 4.9, 4.9, 5.0, 2.5, 4.9);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (21, 21, 4.9, 4.9, 5.0, 2.5, 4.9);
INSERT INTO MIN_INTEREST (id, place_id, architecture, history, spiritual, nature, culture) VALUES (22, 22, 4.9, 4.9, 5.0, 2.5, 4.9);

SELECT setval('cities_id_seq', (SELECT COALESCE(MAX(id), 1) FROM CITIES));
SELECT setval('city_interest_id_seq', (SELECT COALESCE(MAX(id), 1) FROM CITY_INTEREST));
SELECT setval('places_id_seq', (SELECT COALESCE(MAX(id), 1) FROM PLACES));
SELECT setval('opening_hours_id_seq', (SELECT COALESCE(MAX(id), 1) FROM OPENING_HOURS));
SELECT setval('min_interest_id_seq', (SELECT COALESCE(MAX(id), 1) FROM MIN_INTEREST));
SELECT setval('festivals_id_seq', (SELECT COALESCE(MAX(id), 1) FROM FESTIVALS));
