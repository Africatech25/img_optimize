# RUNBOOK — Exploitation img_optimize

## Démarrage backend
- Prérequis : Python 3.9+, dépendances (voir backend/requirements.txt)
- Lancer le serveur :
  ```bash
  cd backend
  python main.py
  ```
- Arrêt : Ctrl+C

## Démarrage frontend
- Prérequis : Node.js 18+, npm
- Lancer le serveur :
  ```bash
  cd frontend
  npm install
  npm run dev
  ```
- Arrêt : Ctrl+C

## Procédure d’incident
- Vérifier les logs backend (console)
- Vérifier les erreurs navigateur (frontend)
- Redémarrer le service concerné
- Si persistant : escalader à l’équipe technique

## Sauvegarde/restauration
- Pas de données persistées (stateless)

## Points de surveillance
- Charge CPU/mémoire lors de traitements massifs
- Taille des fichiers uploadés
