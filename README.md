# FilmBox

Application web de suivi de films, inspirée de Letterboxd : les membres notent les films qu'ils voient, tiennent un journal de visionnage et consultent des statistiques.

Projet fil rouge de bases de données, développé avec **Python 3**, **Flask** et **psycopg 3**.

## Fonctionnalités

Accueil (/) : chiffres clés, cinq films les mieux notés, derniers visionnages.
Films (/films) : recherche par titre et par genre, avec pagination.
Fiche film (/film/<id>) : réalisateurs, acteurs, saga, durée, pays, langue, tags et Oscar, notes des membres et formulaire pour noter le film.
Membres (/membres) : liste paginée des membres, avec recherche par pseudo.
Profil d'un membre (/membre/<pseudo>) : nombre de films notés, note moyenne, genre préféré, coup de cœur, journal de visionnage avec le nombre de jours depuis le visionnage précédent, et films à voir.
Statistiques (/statistiques) : classement pondéré des films, classement des réalisateurs, coups de cœur et déceptions par genre, tags populaires, membres les plus actifs.

### Notation d'un film

Le formulaire de la fiche film enregistre ou remplace la note du membre (`INSERT … ON CONFLICT DO UPDATE`), ajoute un visionnage au journal et affiche la nouvelle moyenne. La note doit être comprise entre 0,5 et 5, par demi-point ; le pseudo doit exister. Les deux écritures sont faites dans une même transaction.

## Notions SQL mises en œuvre

- Jointures, agrégats, `HAVING`, `FILTER`
- Fonctions de fenêtrage : `LAG` (délai entre deux visionnages), `DENSE_RANK` (classement des réalisateurs)
- `LEFT JOIN LATERAL` pour calculer les moyennes uniquement sur la page affichée
- Requêtes sur colonne JSONB : `->>`, `jsonb_array_elements_text`
- Note pondérée selon la formule du Top 250 d'IMDb : `(v / (v + m)) × R + (m / (v + m)) × C`, avec `m = 5`
- Upsert et transaction pour la notation

## Prérequis

- Python 3.10 ou plus récent
- PostgreSQL 14 ou plus récent (pgAdmin facultatif)

## Installation

Créer une base nommée `filmbox`, puis exécuter dans l'ordre les scripts du dossier [`sql/`](sql) :

1. `01_filmbox.sql` : schéma et données de base (30 films, 8 membres, notes et journal)
2. `02_filmbox-s2.sql` : fiche détaillée des films en JSONB (requise par l'application)
3. `03_filmbox-s4.sql` : tables `films_stats` et `audit_notes` (facultatif)
4. `04_filmbox-s3.sql` : jeu de données volumineux, pour les tests de performance (facultatif)

Avec `psql` :

```bash
createdb filmbox
psql -d filmbox -f sql/01_filmbox.sql
psql -d filmbox -f sql/02_filmbox-s2.sql
psql -d filmbox -f sql/03_filmbox-s4.sql
```

# Installer les dépendances

```bash
python -m venv .venv
pip install -r requirements.txt
```

# Configurer la connexion

L'application lit sa configuration dans les variables d'environnement suivantes. Les valeurs par défaut sont indiquées.

| Variable | Défaut |
|---|---|
| `PGHOST` | `localhost` |
| `PGPORT` | `5432` |
| `PGDATABASE` | `filmbox` |
| `PGUSER` | `postgres` |
| `PGPASSWORD` | `postgres` |


# Lancer l'application

```bash
python app.py
```

Ouvrir ensuite <http://localhost:5000>.

## Structure du projet

```
filmbox_app/
├── app.py              # routes Flask et requêtes SQL
├── requirements.txt    # dépendances Python
├── sql/                # scripts de création et de remplissage de la base
├── static/
│   └── style.css       # feuille de style
└── templates/          # pages HTML
    ├── base.html
    ├── accueil.html
    ├── films.html
    ├── film.html
    ├── membres.html
    ├── membre.html
    ├── statistiques.html
    └── erreur.html
```

## Performances

Avec le jeu de données volumineux (`04_filmbox-s3.sql` : 100 000 films, 1 million de notes), le calcul des moyennes par film devient lent sans index. L'index suivant corrige le problème :

```sql
CREATE INDEX idx_notes_film ON notes(film_id);
```

## Remarques

- L'application ne comporte pas d'authentification : le pseudo est saisi dans le formulaire de notation.
