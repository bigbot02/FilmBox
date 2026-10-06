import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect, url_for, flash, g, session

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'filmbox_secret_key_dev')

DB_CONFIG = {
    'dbname': 'filmbox',
    'user': 'filmbox_app',
    'password': 'filmbox_pass',
    'host': 'localhost',
    'port': 5432
}

def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        membre_id = session.get('membre_id', '')
        with g.db.cursor() as cur:
            cur.execute("SET app.membre_id = %s;", (str(membre_id),))
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.template_filter('num')
def num_filter(val, precision=2):
    if val is None:
        return '–'
    return f"{float(val):.{precision}f}"

@app.template_filter('date_fr')
def date_fr_filter(val):
    if not val:
        return '–'
    return val.strftime('%d/%m/%Y')

@app.template_filter('etoiles')
def etoiles_filter(val):
    if val is None:
        return ''
    val = float(val)
    pleines = int(val)
    demi = 1 if (val - pleines) >= 0.5 else 0
    vides = 5 - pleines - demi
    return '★' * pleines + ('½' if demi else '') + '☆' * vides

@app.template_filter('duree')
def duree_filter(minutes):
    if not minutes:
        return '–'
    h = minutes // 60
    m = minutes % 60
    return f"{h}h{m:02d}" if h else f"{m}min"

@app.route('/')
def accueil():
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS films FROM films")
        nb_films = cur.fetchone()['films']
        cur.execute("SELECT COUNT(*) AS membres FROM membres")
        nb_membres = cur.fetchone()['membres']
        cur.execute("SELECT COUNT(*) AS notes FROM notes")
        nb_notes = cur.fetchone()['notes']
        cur.execute("SELECT COUNT(*) AS visionnages FROM journal")
        nb_visionnages = cur.fetchone()['visionnages']
        
        c = {'films': nb_films, 'membres': nb_membres, 'notes': nb_notes, 'visionnages': nb_visionnages}

        cur.execute("""
            SELECT f.id, f.titre, f.annee, fs.moyenne, fs.nb_notes
            FROM films_stats fs
            JOIN films f ON f.id = fs.film_id
            WHERE fs.nb_notes >= 5
            ORDER BY fs.moyenne DESC
            LIMIT 5
        """)
        meilleurs = cur.fetchall()

        cur.execute("""
            SELECT m.pseudo, f.id AS film_id, f.titre, j.date_visionnage
            FROM journal j
            JOIN membres m ON m.id = j.utilisateur_id
            JOIN films f ON f.id = j.film_id
            ORDER BY j.date_visionnage DESC
            LIMIT 5
        """)
        recents = cur.fetchall()

    return render_template('accueil.html', c=c, meilleurs=meilleurs, recents=recents)

@app.route('/films')
def films():
    q = request.args.get('q', '').strip()
    genre = request.args.get('genre', '').strip()
    page = max(1, request.args.get('page', 1, type=int))
    limit = 12
    offset = (page - 1) * limit

    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT DISTINCT genre FROM films WHERE genre IS NOT NULL ORDER BY genre")
        genres = [r['genre'] for r in cur.fetchall()]

        if q and not genre:
            cur.execute("SELECT * FROM rechercher_films(%s)", (q,))
            res_f = cur.fetchall()
            total = len(res_f)
            film_ids = [r['id'] for r in res_f[offset:offset+limit]]
            if film_ids:
                cur.execute("""
                    SELECT f.*, fs.moyenne, fs.nb_notes
                    FROM films f
                    LEFT JOIN films_stats fs ON fs.film_id = f.id
                    WHERE f.id = ANY(%s)
                """, (film_ids,))
                liste_films = cur.fetchall()
            else:
                liste_films = []
        else:
            conds = []
            params = []
            if q:
                conds.append("f.titre ILIKE %s")
                params.append(f"%{q}%")
            if genre:
                conds.append("f.genre = %s")
                params.append(genre)
            
            where_clause = " WHERE " + " AND ".join(conds) if conds else ""
            
            cur.execute(f"SELECT COUNT(*) AS total FROM films f {where_clause}", params)
            total = cur.fetchone()['total']

            cur.execute(f"""
                SELECT f.*, fs.moyenne, fs.nb_notes
                FROM films f
                LEFT JOIN films_stats fs ON fs.film_id = f.id
                {where_clause}
                ORDER BY f.titre
                LIMIT %s OFFSET %s
            """, params + [limit, offset])
            liste_films = cur.fetchall()

    nb_pages = max(1, (total + limit - 1) // limit)
    return render_template('films.html', films=liste_films, genres=genres, q=q, genre=genre, page=page, total=total, nb_pages=nb_pages)

@app.route('/film/<int:film_id>')
def film(film_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("UPDATE films SET nb_vues = nb_vues + 1 WHERE id = %s", (film_id,))
        db.commit()

        cur.execute("SELECT * FROM films WHERE id = %s", (film_id,))
        f = cur.fetchone()
        if not f:
            return render_template('erreur.html', titre="Film introuvable", message="Ce film n'existe pas."), 404

        cur.execute("SELECT fs.nb_notes AS nb, fs.moyenne FROM films_stats fs WHERE film_id = %s", (film_id,))
        stats = cur.fetchone() or {'nb': 0, 'moyenne': None}

        cur.execute("""
            SELECT m.pseudo, n.note, n.note_le
            FROM notes n
            JOIN membres m ON m.id = n.utilisateur_id
            WHERE n.film_id = %s
            ORDER BY n.note_le DESC
            LIMIT 10
        """, (film_id,))
        notes = cur.fetchall()

        cur.execute("SELECT pseudo FROM membres ORDER BY pseudo")
        membres = cur.fetchall()

    return render_template('film.html', f=f, stats=stats, notes=notes, membres=membres, realisateurs=[], acteurs=[])

@app.route('/film/<int:film_id>/noter', methods=['POST'])
def noter(film_id):
    pseudo = request.form.get('pseudo', '').strip()
    prive = True if request.form.get('prive') else False
    
    try:
        note = float(request.form.get('note', 0))
    except ValueError:
        flash("Format de note invalide.", "erreur")
        return redirect(url_for('film', film_id=film_id))

    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("SELECT titre FROM films WHERE id = %s", (film_id,))
            res = cur.fetchone()
            if not res:
                flash("Film inconnu.", "erreur")
                return redirect(url_for('films'))
            
            titre = res['titre']
            
            cur.execute("CALL noter(%s, %s, %s, NULL, %s)", (pseudo, titre, note, prive))
            db.commit()

            cur.execute("SELECT id FROM membres WHERE pseudo = %s", (pseudo,))
            m = cur.fetchone()
            if m:
                session['membre_id'] = m['id']

            flash("Votre note a été enregistrée avec succès !", "succes")
    except Exception as e:
        db.rollback()
        flash(f"Erreur lors de l'enregistrement : {e}", "erreur")

    return redirect(url_for('film', film_id=film_id))

@app.route('/membres')
def membres():
    q = request.args.get('q', '').strip()
    page = max(1, request.args.get('page', 1, type=int))
    limit = 15
    offset = (page - 1) * limit

    db = get_db()
    with db.cursor() as cur:
        cond = "WHERE pseudo ILIKE %s" if q else ""
        params = [f"%{q}%"] if q else []

        cur.execute(f"SELECT COUNT(*) AS total FROM membres {cond}", params)
        total = cur.fetchone()['total']

        cur.execute(f"""
            SELECT * FROM membres
            {cond}
            ORDER BY pseudo
            LIMIT %s OFFSET %s
        """, params + [limit, offset])
        liste_membres = cur.fetchall()

    nb_pages = max(1, (total + limit - 1) // limit)
    return render_template('membres.html', membres=liste_membres, q=q, page=page, total=total, nb_pages=nb_pages)

@app.route('/membre/<pseudo>')
def membre(pseudo):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT * FROM membres WHERE pseudo = %s", (pseudo,))
        u = cur.fetchone()
        if not u:
            return render_template('erreur.html', titre="Membre introuvable", message="Ce membre n'existe pas."), 404

        cur.execute("""
            SELECT COUNT(*) AS nb_notes, AVG(note) AS moyenne
            FROM notes WHERE utilisateur_id = %s
        """, (u['id'],))
        carte = cur.fetchone()

        cur.execute("""
            SELECT j.date_visionnage, f.id AS film_id, f.titre,
                   j.date_visionnage - LAG(j.date_visionnage) OVER (ORDER BY j.date_visionnage) AS jours
            FROM journal j
            JOIN films f ON f.id = j.film_id
            WHERE j.utilisateur_id = %s
            ORDER BY j.date_visionnage DESC
            LIMIT 40
        """, (u['id'],))
        journal = cur.fetchall()

    return render_template('membre.html', u=u, carte=carte, journal=journal, genre_prefere=None, coup_de_coeur=None, a_voir=[])

@app.route('/statistiques')
def statistiques():
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT f.id, f.titre, fs.nb_notes, fs.moyenne,
                   ((fs.nb_notes * fs.moyenne + 5 * 3.0) / (fs.nb_notes + 5)) AS ponderee
            FROM films_stats fs
            JOIN films f ON f.id = fs.film_id
            WHERE fs.nb_notes > 0
            ORDER BY ponderee DESC
            LIMIT 10
        """)
        ponderes = cur.fetchall()

    return render_template('statistiques.html', ponderes=ponderes, realisateurs=[], genres=[], tags=[], actifs=[])

if __name__ == '__main__':
    app.run(debug=True)
