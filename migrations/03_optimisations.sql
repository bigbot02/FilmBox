-- Optimisations, Indexation et Performances
CREATE INDEX IF NOT EXISTS idx_notes_film_id ON notes(film_id);
CREATE INDEX IF NOT EXISTS idx_notes_utilisateur_id ON notes(utilisateur_id);
CREATE INDEX IF NOT EXISTS idx_journal_utilisateur_id ON journal(utilisateur_id);
CREATE INDEX IF NOT EXISTS idx_films_titre_trgm ON films USING gin (titre gin_trgm_ops);
