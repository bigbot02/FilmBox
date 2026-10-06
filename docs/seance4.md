# 🎬 FilmBox — Séance 4 : Procédures et Triggers

## M13. Publier une note
- **`noter(pseudo, titre, note, INOUT moyenne)`** : Procédure enregistrant la note, le visionnage et renvoyant la moyenne mise à jour.
- **`recalculer_stats(lot)`** : Initialisation par lots de la table `films_stats`.

## M14. Statistiques toujours justes
- **Trigger `trg_films_stats`** : Recalcule automatiquement la moyenne et le nombre de notes sur modification de `notes`.
- **Trigger `trg_audit_notes`** : Trace chaque changement de note effectif dans `audit_notes`.