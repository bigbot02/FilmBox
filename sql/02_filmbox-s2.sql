-- =====================================================================
--  FilmBox — complément séance 2
--  À exécuter sur la base filmbox, APRÈS filmbox.sql.
--  Ajoute à chaque film une fiche détaillée en JSONB.
--  Durées indicatives (en minutes) ; tags attribués par la rédaction FilmBox.
--  Script ré-exécutable : il supprime aussi les objets créés pendant les missions M9 et M10.
-- =====================================================================

DROP MATERIALIZED VIEW IF EXISTS mv_stats_films CASCADE;
DROP VIEW IF EXISTS v_fiche_film, v_films_sf CASCADE;
DROP FUNCTION IF EXISTS duree_texte(INTEGER), note_ponderee(INTEGER, INTEGER), compatibilite(TEXT, TEXT);
ALTER TABLE films DROP COLUMN IF EXISTS details CASCADE;

ALTER TABLE films ADD COLUMN details JSONB;

UPDATE films f
SET details = v.details::JSONB
FROM (VALUES
 ('Apollo 13',                            '{"duree": 140, "pays": ["États-Unis"], "langue": "anglais", "tags": ["espace", "histoire vraie"]}'),
 ('Mystic River',                         '{"duree": 138, "pays": ["États-Unis"], "langue": "anglais", "tags": ["enquête", "drame familial"]}'),
 ('Des hommes d''honneur',                '{"duree": 138, "pays": ["États-Unis"], "langue": "anglais", "tags": ["procès", "armée"]}'),
 ('X-Men : Le Commencement',              '{"duree": 132, "pays": ["États-Unis"], "langue": "anglais", "tags": ["super-héros", "mutants"]}'),
 ('X-Men : Days of Future Past',          '{"duree": 132, "pays": ["États-Unis"], "langue": "anglais", "tags": ["super-héros", "mutants", "voyage dans le temps"]}'),
 ('X-Men : Apocalypse',                   '{"duree": 144, "pays": ["États-Unis"], "langue": "anglais", "tags": ["super-héros", "mutants"]}'),
 ('Forrest Gump',                         '{"duree": 142, "pays": ["États-Unis"], "langue": "anglais", "tags": ["destin", "histoire américaine"], "oscar_meilleur_film": true}'),
 ('Seul au monde',                        '{"duree": 143, "pays": ["États-Unis"], "langue": "anglais", "tags": ["survie", "île"]}'),
 ('Il faut sauver le soldat Ryan',        '{"duree": 169, "pays": ["États-Unis"], "langue": "anglais", "tags": ["seconde guerre mondiale"]}'),
 ('Arrête-moi si tu peux',                '{"duree": 141, "pays": ["États-Unis"], "langue": "anglais", "tags": ["histoire vraie", "arnaque"]}'),
 ('Titanic',                              '{"duree": 194, "pays": ["États-Unis"], "langue": "anglais", "tags": ["romance", "naufrage"], "oscar_meilleur_film": true}'),
 ('Inception',                            '{"duree": 148, "pays": ["États-Unis", "Royaume-Uni"], "langue": "anglais", "tags": ["rêves", "braquage"]}'),
 ('Les Infiltrés',                        '{"duree": 151, "pays": ["États-Unis"], "langue": "anglais", "tags": ["mafia", "remake"], "oscar_meilleur_film": true}'),
 ('Once Upon a Time… in Hollywood',       '{"duree": 161, "pays": ["États-Unis"], "langue": "anglais", "tags": ["Hollywood", "années 60"]}'),
 ('Le Loup de Wall Street',               '{"duree": 180, "pays": ["États-Unis"], "langue": "anglais", "tags": ["histoire vraie", "finance"]}'),
 ('Fight Club',                           '{"duree": 139, "pays": ["États-Unis"], "langue": "anglais", "tags": ["culte", "twist"]}'),
 ('Ocean''s Eleven',                      '{"duree": 116, "pays": ["États-Unis"], "langue": "anglais", "tags": ["braquage", "Las Vegas"]}'),
 ('Seven',                                '{"duree": 127, "pays": ["États-Unis"], "langue": "anglais", "tags": ["enquête", "tueur en série", "twist"]}'),
 ('Batman Begins',                        '{"duree": 140, "pays": ["États-Unis", "Royaume-Uni"], "langue": "anglais", "tags": ["super-héros", "Gotham"]}'),
 ('The Dark Knight',                      '{"duree": 152, "pays": ["États-Unis", "Royaume-Uni"], "langue": "anglais", "tags": ["super-héros", "Gotham", "culte"]}'),
 ('The Dark Knight Rises',                '{"duree": 164, "pays": ["États-Unis", "Royaume-Uni"], "langue": "anglais", "tags": ["super-héros", "Gotham"]}'),
 ('Les Évadés',                           '{"duree": 142, "pays": ["États-Unis"], "langue": "anglais", "tags": ["prison", "amitié", "culte"]}'),
 ('Intouchables',                         '{"duree": 112, "pays": ["France"], "langue": "français", "tags": ["histoire vraie", "amitié"]}'),
 ('La Môme',                              '{"duree": 140, "pays": ["France"], "langue": "français", "tags": ["biopic", "musique"]}'),
 ('The Artist',                           '{"duree": 100, "pays": ["France"], "langue": "muet", "tags": ["cinéma muet", "Hollywood"], "oscar_meilleur_film": true}'),
 ('Le Fabuleux Destin d''Amélie Poulain', '{"duree": 122, "pays": ["France"], "langue": "français", "tags": ["Paris", "culte"]}'),
 ('La Haine',                             '{"duree": 98,  "pays": ["France"], "langue": "français", "tags": ["banlieue", "noir et blanc", "culte"]}'),
 ('Retour vers le futur',                 '{"duree": 116, "pays": ["États-Unis"], "langue": "anglais", "tags": ["voyage dans le temps", "culte"]}'),
 ('Retour vers le futur II',              '{"duree": 108, "pays": ["États-Unis"], "langue": "anglais", "tags": ["voyage dans le temps"]}'),
 ('Retour vers le futur III',             '{"duree": 118, "pays": ["États-Unis"], "langue": "anglais", "tags": ["voyage dans le temps", "western"]}')
) AS v(titre, details)
WHERE f.titre = v.titre;

ALTER TABLE films ALTER COLUMN details SET NOT NULL;

-- ---------- Contrôle ----------
SELECT COUNT(*) AS films_avec_fiche,
       COUNT(*) FILTER (WHERE details ? 'oscar_meilleur_film') AS oscarises
FROM films;
