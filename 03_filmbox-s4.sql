-- =====================================================================
--  FilmBox — complément séance 4
--  À exécuter sur la base filmbox, APRÈS filmbox.sql et filmbox-s2.sql.
--  (Inutile de recharger le volume de la séance 3.)
--  Crée les tables alimentées par les procédures et triggers des missions M13 et M14,
--  et supprime ce qui a été créé lors d'une exécution précédente.
-- =====================================================================

DROP TABLE IF EXISTS films_stats, audit_notes CASCADE;
DROP PROCEDURE IF EXISTS noter(TEXT, TEXT, NUMERIC, NUMERIC), recalculer_stats(INTEGER);
DROP FUNCTION IF EXISTS trg_films_stats(), trg_audit_notes() CASCADE;

CREATE TABLE films_stats (                       -- statistiques dénormalisées, pour un affichage rapide
    film_id   INTEGER PRIMARY KEY REFERENCES films(id),
    nb_notes  INTEGER      NOT NULL,
    moyenne   NUMERIC(3,2) NOT NULL
);

CREATE TABLE audit_notes (                       -- historique des notes modifiées
    id              INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    utilisateur_id  INTEGER      NOT NULL,
    film_id         INTEGER      NOT NULL,
    ancienne        NUMERIC(2,1),
    nouvelle        NUMERIC(2,1),
    le              TIMESTAMP    NOT NULL DEFAULT now()
);

SELECT 'films_stats' AS table_name, COUNT(*) AS lignes FROM films_stats
UNION ALL SELECT 'audit_notes', COUNT(*) FROM audit_notes;
