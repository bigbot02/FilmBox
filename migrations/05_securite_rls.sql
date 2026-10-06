-- Compteur de vues et champ prive
ALTER TABLE films ADD COLUMN IF NOT EXISTS nb_vues INT NOT NULL DEFAULT 0;
ALTER TABLE journal ADD COLUMN IF NOT EXISTS prive BOOLEAN NOT NULL DEFAULT FALSE;

-- Procedure noter mise a jour avec support du champ prive
CREATE OR REPLACE PROCEDURE noter(
    p_pseudo VARCHAR,
    p_titre VARCHAR,
    p_note NUMERIC,
    INOUT p_moyenne NUMERIC,
    p_prive BOOLEAN DEFAULT FALSE
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_user_id INT;
    v_film_id INT;
BEGIN
    IF p_note < 0.5 OR p_note > 5 OR (p_note * 2) <> ROUND(p_note * 2) THEN
        RAISE EXCEPTION 'Note invalide : % (de 0,5 à 5, par demi-point)', p_note;
    END IF;

    SELECT id INTO v_user_id FROM membres WHERE pseudo = p_pseudo;
    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'Membre inconnu : %', p_pseudo;
    END IF;

    SELECT id INTO v_film_id FROM films WHERE titre = p_titre;
    IF v_film_id IS NULL THEN
        RAISE EXCEPTION 'Film inconnu : %', p_titre;
    END IF;

    INSERT INTO notes (utilisateur_id, film_id, note, note_le)
    VALUES (v_user_id, v_film_id, p_note, CURRENT_TIMESTAMP)
    ON CONFLICT (utilisateur_id, film_id) 
    DO UPDATE SET note = EXCLUDED.note, note_le = EXCLUDED.note_le;

    INSERT INTO journal (utilisateur_id, film_id, date_visionnage, prive)
    VALUES (v_user_id, v_film_id, CURRENT_DATE, p_prive);

    SELECT AVG(note)::NUMERIC(3,2) INTO p_moyenne
    FROM notes
    WHERE film_id = v_film_id;
END;
$$;

-- Recherche securisee
CREATE OR REPLACE FUNCTION rechercher_films(texte TEXT)
RETURNS TABLE (
    id INT,
    titre VARCHAR,
    annee INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT f.id, f.titre, f.annee
    FROM films f
    WHERE f.titre ILIKE '%' || texte || '%'
    ORDER BY f.titre
    LIMIT 5;
END;
$$ LANGUAGE plpgsql STABLE;

-- Role applicatif et RLS
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'filmbox_app') THEN
        CREATE ROLE filmbox_app WITH LOGIN PASSWORD 'filmbox_pass';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE filmbox TO filmbox_app;
GRANT USAGE ON SCHEMA public TO filmbox_app;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO filmbox_app;
GRANT INSERT, UPDATE ON notes, journal TO filmbox_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO filmbox_app;

ALTER TABLE journal ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS journal_select_policy ON journal;
CREATE POLICY journal_select_policy ON journal
    FOR SELECT TO filmbox_app
    USING (
        prive = FALSE 
        OR utilisateur_id = NULLIF(current_setting('app.membre_id', TRUE), '')::INT
    );

DROP POLICY IF EXISTS journal_insert_policy ON journal;
CREATE POLICY journal_insert_policy ON journal
    FOR INSERT TO filmbox_app
    WITH CHECK (
        utilisateur_id = NULLIF(current_setting('app.membre_id', TRUE), '')::INT
    );
