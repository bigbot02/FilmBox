-- Vues metiers et calculs complexes
CREATE OR REPLACE VIEW vue_classement_films AS
SELECT 
    f.id,
    f.titre,
    f.annee,
    COUNT(n.note) AS nb_notes,
    ROUND(AVG(n.note), 2) AS moyenne
FROM films f
LEFT JOIN notes n ON f.id = n.film_id
GROUP BY f.id, f.titre, f.annee;
