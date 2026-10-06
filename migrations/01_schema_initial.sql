-- Schema de base de FilmBox
CREATE TABLE IF NOT EXISTS films (
    id SERIAL PRIMARY KEY,
    titre VARCHAR(255) NOT NULL,
    annee INT CHECK (annee >= 1888),
    genre VARCHAR(100),
    duree INT CHECK (duree > 0),
    saga VARCHAR(255),
    oscar BOOLEAN DEFAULT FALSE,
    langue VARCHAR(50),
    pays TEXT[],
    tags TEXT[]
);

CREATE TABLE IF NOT EXISTS membres (
    id SERIAL PRIMARY KEY,
    pseudo VARCHAR(50) UNIQUE NOT NULL,
    ville VARCHAR(100),
    inscrit_le DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS notes (
    utilisateur_id INT REFERENCES membres(id) ON DELETE CASCADE,
    film_id INT REFERENCES films(id) ON DELETE CASCADE,
    note NUMERIC(2,1) CHECK (note >= 0.5 AND note <= 5.0),
    note_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (utilisateur_id, film_id)
);

CREATE TABLE IF NOT EXISTS journal (
    id SERIAL PRIMARY KEY,
    utilisateur_id INT REFERENCES membres(id) ON DELETE CASCADE,
    film_id INT REFERENCES films(id) ON DELETE CASCADE,
    date_visionnage DATE DEFAULT CURRENT_DATE
);
