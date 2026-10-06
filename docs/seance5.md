# 🎬 FilmBox — Séance 5 : Concurrence, Transactions & RLS

## M15. Des compteurs fiables
- **M15.1 Vues perdues** : La réécriture non atomique entraîne la perte de données en contexte concurrentiel.
- **M15.2 Inscription atomique** : Utilisation de `UPDATE films SET nb_vues = nb_vues + 1` pour poser un verrou de ligne.
- **M15.3 Transactions (ROLLBACK)** : Annulation complète d'un bloc transactionnel en cas d'erreur Foreign Key.

## M16. Sécuriser FilmBox
- **M16.1 Rôle applicatif `filmbox_app`** : Restriction des droits (pas de DELETE sur notes, pas d'UPDATE sur films).
- **M16.2 RLS sur `journal`** : Masquage des entrées privées des autres utilisateurs via `app.membre_id`.
- **M16.3 Recherche sécurisée** : Utilisation de la fonction SQL `reviser_films()` pour bloquer les injections.
