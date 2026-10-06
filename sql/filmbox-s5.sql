-- =====================================================================
--  FilmBox — complément séance 5
--  À exécuter sur la base filmbox avec le compte postgres,
--  APRÈS filmbox.sql et filmbox-s2.sql.
--  Ajoute un compteur de vues aux films et un statut privé aux entrées du journal.
--  Script ré-exécutable : il supprime le rôle, les politiques et la fonction
--  créés pendant les missions M15 et M16.
-- =====================================================================

-- Politiques et fonction des missions
ALTER TABLE journal DISABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS journal_lecture ON journal;
DROP POLICY IF EXISTS journal_ecriture ON journal;
DROP FUNCTION IF EXISTS rechercher_films(TEXT);

-- Rôle de l'application (les rôles existent pour tout le serveur)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'filmbox_app') THEN
        DROP OWNED BY filmbox_app;
        DROP ROLE filmbox_app;
    END IF;
END $$;

-- Compteur de vues des fiches films
ALTER TABLE films DROP COLUMN IF EXISTS nb_vues;
ALTER TABLE films ADD COLUMN nb_vues INTEGER NOT NULL DEFAULT 0;

-- Entrées de journal privées (environ une sur quatre)
ALTER TABLE journal DROP COLUMN IF EXISTS prive;
ALTER TABLE journal ADD COLUMN prive BOOLEAN NOT NULL DEFAULT false;
UPDATE journal SET prive = true WHERE id % 4 = 0;

SELECT COUNT(*) AS entrees_journal,
       COUNT(*) FILTER (WHERE prive) AS entrees_privees
FROM journal;
