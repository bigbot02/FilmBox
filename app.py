"""
FilmBox : application web (Flask + PostgreSQL).
Lancer :   python app.py      puis ouvrir   http://localhost:5000
"""
import os

import psycopg
from flask import Flask, abort, flash, redirect, render_template, request, url_for
from psycopg.rows import dict_row

# Configuration

CONFIG_BASE = {
    "host": os.environ.get("PGHOST", "localhost"),
    "port": os.environ.get("PGPORT", "5432"),
    "dbname": os.environ.get("PGDATABASE", "filmbox"),
    "user": os.environ.get("PGUSER", "postgres"),
    "password": os.environ.get("PGPASSWORD", "123"), 
}

app = Flask(__name__)
app.secret_key = "filmbox-projet-scolaire"

FILMS_PAR_PAGE = 24
MEMBRES_PAR_PAGE = 30

# Acces au BD

def connexion():
    return psycopg.connect(**CONFIG_BASE, row_factory=dict_row)


def lire(sql, params=None, un=False):
    """Exécute un SELECT. un=True renvoie une seule ligne (ou None)."""
    with connexion() as conn, conn.cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchone() if un else cur.fetchall()


# Filtrer l'affichage

@app.template_filter("num")
def filtre_num(valeur, decimales=2):
    if valeur is None:
        return "–"
    return f"{float(valeur):.{decimales}f}".replace(".", ",")


@app.template_filter("date_fr")
def filtre_date(valeur):
    return valeur.strftime("%d/%m/%Y") if valeur else "–"


@app.template_filter("etoiles")
def filtre_etoiles(valeur):
    n = float(valeur)
    return "★" * int(n) + ("½" if n - int(n) >= 0.5 else "")


@app.template_filter("duree")
def filtre_duree(minutes):
    if minutes is None:
        return "–"
    return f"{int(minutes) // 60} h {int(minutes) % 60:02d}"



# Les pages

@app.route("/")
def accueil():
    chiffres = lire(
        """SELECT (SELECT COUNT(*) FROM films) AS films,
                  (SELECT COUNT(*) FROM utilisateurs) AS membres,
                  (SELECT COUNT(*) FROM notes) AS notes,
                  (SELECT COUNT(*) FROM journal) AS visionnages""",
        un=True,
    )
    meilleurs = lire(
        """SELECT f.id, f.titre, f.annee, f.genre,
                  ROUND(AVG(n.note), 2) AS moyenne, COUNT(*) AS nb_notes
           FROM films f JOIN notes n ON n.film_id = f.id
           GROUP BY f.id HAVING COUNT(*) >= 5
           ORDER BY moyenne DESC, nb_notes DESC, f.titre LIMIT 5"""
    )
    recents = lire(
        """SELECT u.pseudo, f.id AS film_id, f.titre, j.date_visionnage
           FROM journal j JOIN utilisateurs u ON u.id = j.utilisateur_id
                          JOIN films f ON f.id = j.film_id
           ORDER BY j.date_visionnage DESC, j.id DESC LIMIT 8"""
    )
    return render_template("accueil.html", c=chiffres, meilleurs=meilleurs, recents=recents)


@app.route("/films")
def films():
    q = request.args.get("q", "").strip()
    genre = request.args.get("genre", "").strip()
    page = max(1, request.args.get("page", 1, type=int))

    conditions, params = [], []
    if q:
        conditions.append("titre ILIKE %s")
        params.append(f"%{q}%")
    if genre:
        conditions.append("genre = %s")
        params.append(genre)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    total = lire(f"SELECT COUNT(*) AS n FROM films {where}", params, un=True)["n"]
    nb_pages = max(1, -(-total // FILMS_PAR_PAGE))
    page = min(page, nb_pages)

    liste = lire(
        f"""SELECT f.id, f.titre, f.annee, f.genre, s.nb_notes, s.moyenne
            FROM (SELECT * FROM films {where} ORDER BY titre
                  LIMIT %s OFFSET %s) f
            LEFT JOIN LATERAL (SELECT COUNT(*) AS nb_notes, ROUND(AVG(note), 2) AS moyenne
                               FROM notes WHERE film_id = f.id) s ON TRUE
            ORDER BY f.titre""",
        params + [FILMS_PAR_PAGE, (page - 1) * FILMS_PAR_PAGE],
    )
    genres = [r["genre"] for r in lire("SELECT DISTINCT genre FROM films ORDER BY genre")]
    return render_template(
        "films.html", films=liste, genres=genres, q=q, genre=genre,
        page=page, nb_pages=nb_pages, total=total,
    )


@app.route("/film/<int:film_id>")
def film(film_id):
    f = lire(
        """SELECT f.*, s.nom AS saga,
                  (f.details->>'duree')::int AS duree,
                  f.details->>'langue' AS langue,
                  (f.details->>'oscar_meilleur_film')::boolean AS oscar,
                  ARRAY(SELECT jsonb_array_elements_text(f.details->'pays')) AS pays,
                  ARRAY(SELECT jsonb_array_elements_text(f.details->'tags')) AS tags
           FROM films f LEFT JOIN sagas s ON s.id = f.saga_id
           WHERE f.id = %s""",
        [film_id], un=True,
    )
    if f is None:
        abort(404)
    equipe = lire(
        """SELECT p.nom, c.role FROM casting c JOIN personnes p ON p.id = c.personne_id
           WHERE c.film_id = %s ORDER BY c.role DESC, p.nom""",
        [film_id],
    )
    realisateurs = [e["nom"] for e in equipe if e["role"] == "realisateur"]
    acteurs = [e["nom"] for e in equipe if e["role"] == "acteur"]
    stats = lire(
        "SELECT COUNT(*) AS nb, ROUND(AVG(note), 2) AS moyenne FROM notes WHERE film_id = %s",
        [film_id], un=True,
    )
    notes = lire(
        """SELECT u.pseudo, n.note, n.note_le FROM notes n
           JOIN utilisateurs u ON u.id = n.utilisateur_id
           WHERE n.film_id = %s ORDER BY n.note_le DESC LIMIT 30""",
        [film_id],
    )
    membres = lire("SELECT pseudo FROM utilisateurs ORDER BY id LIMIT 50")
    return render_template(
        "film.html", f=f, realisateurs=realisateurs, acteurs=acteurs,
        stats=stats, notes=notes, membres=membres,
    )


@app.route("/film/<int:film_id>/noter", methods=["POST"])
def noter(film_id):
    """Enregistre (ou remplace) une note et ajoute un visionnage au journal."""
    pseudo = request.form.get("pseudo", "").strip()
    try:
        note = float(request.form.get("note", "").replace(",", "."))
    except ValueError:
        note = None

    if note is None or not (0.5 <= note <= 5) or (note * 2) != int(note * 2):
        flash(f"Note invalide : {request.form.get('note')} (de 0,5 à 5, par demi-point).", "erreur")
        return redirect(url_for("film", film_id=film_id))

    with connexion() as conn, conn.cursor() as cur:
        cur.execute("SELECT id FROM utilisateurs WHERE pseudo = %s", [pseudo])
        membre = cur.fetchone()
        if membre is None:
            flash(f"Membre inconnu : {pseudo}", "erreur")
            return redirect(url_for("film", film_id=film_id))
        cur.execute(
            """INSERT INTO notes (utilisateur_id, film_id, note, note_le)
               VALUES (%s, %s, %s, CURRENT_DATE)
               ON CONFLICT (utilisateur_id, film_id)
               DO UPDATE SET note = EXCLUDED.note, note_le = EXCLUDED.note_le""",
            [membre["id"], film_id, note],
        )
        cur.execute(
            """INSERT INTO journal (utilisateur_id, film_id, date_visionnage)
               VALUES (%s, %s, CURRENT_DATE)""",
            [membre["id"], film_id],
        )
        cur.execute("SELECT ROUND(AVG(note), 2) AS m FROM notes WHERE film_id = %s", [film_id])
        moyenne = cur.fetchone()["m"]
    flash(f"Merci {pseudo} ! Note enregistrée. Nouvelle moyenne du film : {filtre_num(moyenne)} / 5.", "ok")
    return redirect(url_for("film", film_id=film_id))


@app.route("/membres")
def membres():
    q = request.args.get("q", "").strip()
    page = max(1, request.args.get("page", 1, type=int))
    total = lire(
        "SELECT COUNT(*) AS n FROM utilisateurs WHERE pseudo ILIKE %s", [f"%{q}%"], un=True
    )["n"]
    nb_pages = max(1, -(-total // MEMBRES_PAR_PAGE))
    page = min(page, nb_pages)
    liste = lire(
        """SELECT pseudo, ville, inscrit_le FROM utilisateurs
           WHERE pseudo ILIKE %s ORDER BY id LIMIT %s OFFSET %s""",
        [f"%{q}%", MEMBRES_PAR_PAGE, (page - 1) * MEMBRES_PAR_PAGE],
    )
    return render_template("membres.html", membres=liste, q=q, page=page, nb_pages=nb_pages, total=total)


@app.route("/membre/<pseudo>")
def membre(pseudo):
    u = lire("SELECT * FROM utilisateurs WHERE pseudo = %s", [pseudo], un=True)
    if u is None:
        abort(404)
    uid = u["id"]

    carte = lire(
        """SELECT COUNT(*) AS nb_notes, ROUND(AVG(note), 2) AS moyenne
           FROM notes WHERE utilisateur_id = %s""",
        [uid], un=True,
    )
    genre_prefere = lire(
        """SELECT f.genre, COUNT(*) AS n FROM notes n JOIN films f ON f.id = n.film_id
           WHERE n.utilisateur_id = %s GROUP BY f.genre ORDER BY n DESC, f.genre LIMIT 1""",
        [uid], un=True,
    )
    coup_de_coeur = lire(
        """SELECT f.id, f.titre, n.note FROM notes n JOIN films f ON f.id = n.film_id
           WHERE n.utilisateur_id = %s ORDER BY n.note DESC, n.note_le, f.titre LIMIT 1""",
        [uid], un=True,
    )
    journal = lire(
        """WITH chrono AS (
               SELECT j.id, j.date_visionnage, f.id AS film_id, f.titre,
                      j.date_visionnage - LAG(j.date_visionnage)
                          OVER (ORDER BY j.date_visionnage, j.id) AS jours
               FROM journal j JOIN films f ON f.id = j.film_id
               WHERE j.utilisateur_id = %s)
           SELECT * FROM chrono ORDER BY date_visionnage DESC, id DESC LIMIT 40""",
        [uid],
    )
    a_voir = lire(
        """SELECT f.id, f.titre, f.annee FROM films f
           WHERE NOT EXISTS (SELECT 1 FROM journal j
                             WHERE j.film_id = f.id AND j.utilisateur_id = %s)
           ORDER BY f.annee DESC, f.titre LIMIT 10""",
        [uid],
    )
    return render_template(
        "membre.html", u=u, carte=carte, genre_prefere=genre_prefere,
        coup_de_coeur=coup_de_coeur, journal=journal, a_voir=a_voir,
    )


@app.route("/statistiques")
def statistiques():
    ponderes = lire(
        """WITH s AS (SELECT film_id, COUNT(*) AS v, AVG(note) AS r FROM notes GROUP BY film_id),
                c AS (SELECT AVG(note) AS c FROM notes)
           SELECT f.id, f.titre, s.v AS nb_notes, ROUND(s.r, 2) AS moyenne,
                  ROUND((s.v / (s.v + 5.0)) * s.r + (5.0 / (s.v + 5.0)) * c.c, 2) AS ponderee
           FROM s JOIN films f ON f.id = s.film_id CROSS JOIN c
           ORDER BY ponderee DESC, f.titre LIMIT 10"""
    )
    realisateurs = lire(
        """SELECT DENSE_RANK() OVER (ORDER BY AVG(n.note) DESC) AS rang,
                  p.nom, ROUND(AVG(n.note), 2) AS moyenne, COUNT(*) AS nb_notes
           FROM casting c JOIN personnes p ON p.id = c.personne_id
                          JOIN notes n ON n.film_id = c.film_id
           WHERE c.role = 'realisateur'
           GROUP BY p.id, p.nom ORDER BY rang, p.nom LIMIT 10"""
    )
    genres = lire(
        """SELECT f.genre, COUNT(*) AS nb_notes,
                  COUNT(*) FILTER (WHERE n.note >= 4.5) AS coups_de_coeur,
                  COUNT(*) FILTER (WHERE n.note <= 2.5) AS deceptions
           FROM notes n JOIN films f ON f.id = n.film_id
           GROUP BY f.genre ORDER BY nb_notes DESC, f.genre"""
    )
    tags = lire(
        """SELECT tag, COUNT(*) AS nb_films
           FROM films, jsonb_array_elements_text(details->'tags') AS tag
           GROUP BY tag ORDER BY nb_films DESC, tag LIMIT 8"""
    )
    actifs = lire(
        """SELECT u.pseudo, COUNT(*) AS nb_visionnages, COUNT(DISTINCT j.film_id) AS nb_films
           FROM journal j JOIN utilisateurs u ON u.id = j.utilisateur_id
           GROUP BY u.id, u.pseudo ORDER BY nb_visionnages DESC, u.pseudo LIMIT 8"""
    )
    return render_template(
        "statistiques.html", ponderes=ponderes, realisateurs=realisateurs,
        genres=genres, tags=tags, actifs=actifs,
    )


# les erreurs

@app.errorhandler(404)
def page_introuvable(_):
    return render_template("erreur.html", titre="Page introuvable",
                           message="Cette page n'existe pas ou a été supprimée."), 404


@app.errorhandler(psycopg.OperationalError)
def base_injoignable(e):
    return render_template(
        "erreur.html", titre="Base de données injoignable",
        message="Impossible de se connecter à PostgreSQL. Vérifiez que le serveur est démarré "
                "et que le mot de passe dans app.py (CONFIG_BASE) est le bon.",
        detail=str(e),
    ), 500


@app.errorhandler(psycopg.Error)
def erreur_sql(e):
    return render_template(
        "erreur.html", titre="Erreur dans la base de données",
        message="Une requête a échoué. Avez-vous bien exécuté filmbox.sql puis filmbox-s2.sql ?",
        detail=str(e),
    ), 500


if __name__ == "__main__":
    app.run(debug=True)
