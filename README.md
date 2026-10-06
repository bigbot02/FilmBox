# FilmBox

Application web de suivi de films, inspirée de Letterboxd : les membres notent les films qu'ils voient, tiennent un journal de visionnage et consultent des statistiques.

Projet fil rouge de bases de données, développé avec **Python 3**, **Flask** et **psycopg 3**.

## Fonctionnalités

* **Accueil (`/`)** : chiffres clés (films, membres, notes, visionnages), cinq films les mieux notés, derniers visionnages.
* **Films (`/films`)** : recherche par titre et par genre, avec pagination.
* **Fiche film (`/film/<id>`)** : réalisateurs, acteurs, saga, durée, pays, langue, tags et Oscar, notes des membres, formulaire de notation et option d'entrée privée.
* **Membres (`/membres`)** : liste paginée des membres, avec recherche par pseudo.
* **Profil d'un membre (`/membre/<pseudo>`)** : nombre de films notés, note moyenne, genre préféré, coup de cœur, journal de visionnage avec délai entre visionnages et films à voir.
* **Statistiques (`/statistiques`)** : classement pondéré des films, classement des réalisateurs, coups de cœur et déceptions par genre, tags populaires, membres les plus actifs.

### Notation d'un film

Le formulaire de la fiche film enregistre ou met à jour la note du membre (`INSERT … ON CONFLICT DO UPDATE`), ajoute une entrée dans le journal de visionnage (avec gestion des entrées privées) et déclenche l'actualisation automatique des statistiques du film via un trigger PostgreSQL.

## Notions SQL et PostgreSQL mises en œuvre

* Jointures, agrégats, `HAVING`, `FILTER`
* Fonctions de fenêtrage : `LAG` (délai entre deux visionnages), `DENSE_RANK` (classement des réalisateurs)
* Requêtes et agrégations sur colonne JSONB : `->>`, `jsonb_array_elements_text`
* Recherche textuelle optimisée via l'extension `pg_trgm` et index GIN
* Procédures stockées (`CALL recalculer_stats(...)`)
* Triggers d'audit (`audit_notes`) et de calcul d'agrégats (`films_stats`)
* Sécurité au niveau des lignes (Row-Level Security / RLS) sur les entrées privées du journal
* Renommage de la table `utilisateurs` en `membres`
* Gestion des droits d'accès pour le rôle applicatif `filmbox_app`

## Prérequis

* Python 3.10 ou plus récent
* PostgreSQL 14 ou plus récent
* Extension PostgreSQL `pg_trgm`

## Installation et base de données

### 1. Créer la base de données

Créer la base `filmbox` avec PostgreSQL :

```bash
createdb -U postgres filmbox
```

### 2. Exécuter les migrations

Exécuter les scripts SQL **dans l'ordre**, car chaque migration dépend des éléments créés par les précédentes :

```bash
psql -U postgres -d filmbox -f migrations/01_schema_initial.sql
psql -U postgres -d filmbox -f migrations/02_metiers_et_vues.sql
psql -U postgres -d filmbox -f migrations/03_optimisations.sql
psql -U postgres -d filmbox -f migrations/04_procedures_triggers.sql
psql -U postgres -d filmbox -f migrations/05_securite_rls.sql
```

### 3. Recalculer les statistiques initiales

Avant de lancer l'application, recalculer les statistiques des films :

```bash
psql -U postgres -d filmbox -c "CALL recalculer_stats(100);"
```

Cette étape initialise les données utilisées par les différentes fonctionnalités statistiques de l'application.

### 4. Donner les droits au rôle applicatif

Le rôle `filmbox_app` doit avoir les droits nécessaires sur les tables de la base :

```bash
psql -U postgres -d filmbox -c "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO filmbox_app;"
```

Pour permettre également l'utilisation des séquences utilisées par les colonnes `IDENTITY` ou `SERIAL` :

```bash
psql -U postgres -d filmbox -c "GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO filmbox_app;"
```

### 5. Vérifier les statistiques

Il est possible de vérifier que les statistiques ont bien été calculées avec :

```bash
psql -U postgres -d filmbox
```

Puis :

```sql
SELECT * FROM films_stats;
```

La présence de données dans `films_stats` confirme que le calcul initial des statistiques a été effectué.

Pour quitter PostgreSQL :

```sql
\q
```

## Configuration de l'application

### 1. Créer l'environnement virtuel

Depuis le dossier du projet :

```bash
python -m venv .venv
```

### 2. Activer l'environnement virtuel

Sous Linux/macOS :

```bash
source .venv/bin/activate
```

Sous Windows :

```bash
.venv\Scripts\activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

## Variables d'environnement

L'application utilise les variables suivantes pour se connecter à PostgreSQL :

| Variable     | Valeur par défaut |
| ------------ | ----------------- |
| `PGHOST`     | `localhost`       |
| `PGPORT`     | `5432`            |
| `PGDATABASE` | `filmbox`         |
| `PGUSER`     | `filmbox_app`     |
| `PGPASSWORD` | `password`        |

Sous Linux/macOS, elles peuvent être définies avec :

```bash
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=filmbox
export PGUSER=filmbox_app
export PGPASSWORD=password
```

Sous Windows PowerShell :

```powershell
$env:PGHOST="localhost"
$env:PGPORT="5432"
$env:PGDATABASE="filmbox"
$env:PGUSER="filmbox_app"
$env:PGPASSWORD="password"
```

## Lancement de l'application

Une fois PostgreSQL configuré, les migrations exécutées, les statistiques calculées et les dépendances installées :

```bash
python app.py
```

L'application est alors accessible à :

```text
http://127.0.0.1:5000
```

## Vérification des fonctionnalités

Après le lancement de Flask, les principales pages peuvent être testées avec les URLs suivantes :

| Fonctionnalité | URL                                  |
| -------------- | ------------------------------------ |
| Accueil        | `http://127.0.0.1:5000/`             |
| Films          | `http://127.0.0.1:5000/films`        |
| Membres        | `http://127.0.0.1:5000/membres`      |
| Statistiques   | `http://127.0.0.1:5000/statistiques` |

## Ordre complet d'installation

Pour installer et lancer rapidement le projet, suivre cet ordre :

```bash
# 1. Créer la base
createdb -U postgres filmbox

# 2. Exécuter les migrations
psql -U postgres -d filmbox -f migrations/01_schema_initial.sql
psql -U postgres -d filmbox -f migrations/02_metiers_et_vues.sql
psql -U postgres -d filmbox -f migrations/03_optimisations.sql
psql -U postgres -d filmbox -f migrations/04_procedures_triggers.sql
psql -U postgres -d filmbox -f migrations/05_securite_rls.sql

# 3. Calculer les statistiques initiales
psql -U postgres -d filmbox -c "CALL recalculer_stats(100);"

# 4. Donner les droits au rôle applicatif
psql -U postgres -d filmbox -c "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO filmbox_app;"

# 5. Donner les droits sur les séquences
psql -U postgres -d filmbox -c "GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO filmbox_app;"

# 6. Créer l'environnement Python
python -m venv .venv

# 7. Activer l'environnement
source .venv/bin/activate

# 8. Installer les dépendances
pip install -r requirements.txt

# 9. Lancer Flask
python app.py
```

Sous Windows, remplacer uniquement l'activation de l'environnement par :

```powershell
.venv\Scripts\activate
```
## Screenshots
<img width="1685" height="826" alt="image" src="https://github.com/user-attachments/assets/cee28424-e925-4289-a405-695bd9a20a02" />
