# TESTS — img_optimize

## Stratégie de test
- Tests unitaires sur la logique d’optimisation (backend/test_optimization.py)
- Tests d’intégration sur l’API (upload, traitement, réponse)
- Tests manuels sur le frontend (upload, affichage, logs)

## Outils
- Backend : pytest
- Frontend : npm test (à compléter)

## Convention de nommage
- test_[fonction]_[cas]_[résultat_attendu]

## Couverture attendue
- 100% des branches critiques (optimisation, gestion erreurs)
- Cas limites : fichier corrompu, format non supporté, taille excessive

## À faire
- Ajouter des tests d’intégration API
- Automatiser les tests dans la CI/CD
