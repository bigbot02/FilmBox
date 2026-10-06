-- Tables de donnees derivees
CREATE TABLE IF NOT EXISTS films_stats (
    film_id INT PRIMARY KEY REFERENCES films(id) ON DELETE CASCADE,
    nb_notes INT DEFAULT 0,
    moyenne NUMERIC(3,2) DEFAULT 0.00
);

CREATE TABLE IF NOT EXISTS audit_notes (
    id SERIAL PRIMARY KEY,
    utilisateur_id INT,
    film_id INT,
    ancienne_note NUMERIC(2,1),
    nouvelle_note NUMERIC(2,1),
    modifie_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Procedure pour recalculer les statistiques par lots
CREATE OR REPLACE PROCEDURE recalculer_stats(p_lot INT)
LANGUAGE plpgsql
AS $$
DECLARE
    v_traites INT := 0;
BEGIN
    INSERT INTO films_stats (film_id, nb_notes, moyenne)
    SELECT f.id, COUNT(n.note), COALESCE(ROUND(AVG(n.note), 2), 0)
    FROM films f
    LEFT JOIN notes n ON f.id = n.film_id
    GROUP BY f.id
    ON CONFLICT (film_id) DO UPDATE 
    SET nb_notes = EXCLUDED.nb_notes, moyenne = EXCLUDED.moyenne;
    
    GET DIAGNOSTICS v_traites = ROW_COUNT;
    RAISE NOTICE '% films traités', v_traites;
END;
$$;

-- Trigger pour maintenir films_stats automatiquement
CREATE OR REPLACE FUNCTION fn_trg_films_stats()
RETURNS TRIGGER AS $$
DECLARE
    v_film_id INT;
BEGIN
    v_film_id := COALESCE(NEW.film_id, OLD.film_id);
    
    INSERT INTO films_stats (film_id, nb_notes, moyenne)
    SELECT v_film_id, COUNT(note), COALESCE(ROUND(AVG(note), 2), 0)
    FROM notes
    WHERE film_id = v_film_id
    ON CONFLICT (film_id) DO UPDATE
    SET nb_notes = EXCLUDED.nb_notes, moyenne = EXCLUDED.moyenne;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_films_stats ON notes;
CREATE TRIGGER trg_films_stats
AFTER INSERT OR UPDATE OR DELETE ON notes
FOR EACH ROW EXECUTE FUNCTION fn_trg_films_stats();

-- Trigger pour l'audit des notes
CREATE OR REPLACE FUNCTION fn_trg_audit_notes()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.note IS DISTINCT FROM NEW.note THEN
        INSERT INTO audit_notes(utilisateur_id, film_id, ancienne_note, nouvelle_note)
        VALUES (NEW.utilisateur_id, NEW.film_id, OLD.note, NEW.note);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_notes ON notes;
CREATE TRIGGER trg_audit_notes
AFTER UPDATE ON notes
FOR EACH ROW 
WHEN (OLD.note IS DISTINCT FROM NEW.note)
EXECUTE FUNCTION fn_trg_audit_notes();