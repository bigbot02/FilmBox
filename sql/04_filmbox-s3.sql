-- =====================================================================
--  FilmBox — complément séance 3 : passage à l'échelle
--  À exécuter sur la base filmbox, APRÈS filmbox.sql et filmbox-s2.sql.
--  Ajoute 100 000 films, 20 000 membres, 1 million de notes et 1 million de visionnages
--  (données générées, déterministes). Durée : 20 secondes à 2 minutes selon la machine.
--  Ne crée AUCUN index secondaire : c'est l'objet des missions M11 et M12.
-- =====================================================================

-- Supprime les index créés lors d'une exécution précédente des missions
DROP INDEX IF EXISTS idx_journal_profil, idx_journal_date, idx_films_titre_trgm, idx_notes_film;

-- ---------- 100 000 films générés (id 31 et suivants) ----------
INSERT INTO films (titre, annee, genre, details)
SELECT (ARRAY['Le Dernier','La Nuit du','Les Enfants du','Le Secret du','La Chute du','Le Retour du',
              'L''Ombre du','La Légende du','Le Cri du','Les Gardiens du'])[1 + i % 10]
         || ' ' ||
       (ARRAY['Phare','Désert','Volcan','Marais','Glacier','Labyrinthe','Temple','Faubourg','Nord','Loup',
              'Cyclone','Pendule','Miroir','Canyon','Silence','Carrousel','Sablier','Brouillard','Récif','Métronome'])[1 + (i / 10) % 20]
         || ' ' || (1 + i / 200),
       1950 + (i * 7) % 76,
       (ARRAY['Drame','Comédie','Thriller','Science-fiction','Action','Policier','Romance','Aventure','Horreur','Animation'])[1 + (i * 3) % 10],
       jsonb_build_object('duree', 80 + (i * 13) % 100,
                          'tags', jsonb_build_array((ARRAY['culte','indé','festival','blockbuster','classique'])[1 + i % 5]))
FROM generate_series(1, 100000) AS i;

-- ---------- 20 000 membres générés (id 9 et suivants) ----------
INSERT INTO utilisateurs (pseudo, ville, inscrit_le)
SELECT 'membre_' || i,
       (ARRAY['Paris','Lyon','Marseille','Lille','Nantes','Bordeaux','Toulouse','Rennes'])[1 + i % 8],
       DATE '2023-01-01' + (i * 37) % 1000
FROM generate_series(1, 20000) AS i;

-- ---------- 1 million de notes ----------
INSERT INTO notes (utilisateur_id, film_id, note, note_le)
SELECT 8 + 1 + (i % 20000),
       1 + (i * 7919) % 100030,
       (1 + (i * 31) % 10) / 2.0,
       DATE '2025-01-01' + ((i * 13) % 630)::INTEGER
FROM generate_series(1::BIGINT, 1000000) AS i
ON CONFLICT DO NOTHING;

-- ---------- 1 million de visionnages ----------
INSERT INTO journal (utilisateur_id, film_id, date_visionnage)
SELECT 8 + 1 + (i * 17) % 20000,
       1 + (i * 104729) % 100030,
       DATE '2025-01-01' + ((i * 7) % 630)::INTEGER
FROM generate_series(1::BIGINT, 1000000) AS i;

VACUUM ANALYZE films, utilisateurs, notes, journal;

-- ---------- Contrôle ----------
SELECT 'films' AS table_name, COUNT(*) AS lignes FROM films
UNION ALL SELECT 'utilisateurs', COUNT(*) FROM utilisateurs
UNION ALL SELECT 'notes', COUNT(*) FROM notes
UNION ALL SELECT 'journal', COUNT(*) FROM journal;
