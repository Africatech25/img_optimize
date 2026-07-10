# PERFORMANCE — img_optimize

## Baseline initiale
- Temps de traitement moyen par image : à mesurer (objectif : < 1s/image)
- Taille moyenne des images optimisées : à mesurer

## Seuils recommandés
- P95 temps de réponse API : < 2s
- Taille max image uploadée : 5 Mo (à ajuster)
- Utilisation CPU backend : < 70% en pic

## Points de mesure
- Temps de traitement par format (jpg, png, webp)
- Ratio de compression obtenu
- Nombre d’images traitées simultanément

## Actions d’optimisation
- Profiling du code Python (optimize_images.py)
- Utilisation de librairies natives (Pillow, etc.)
- Possibilité de traitement asynchrone (à étudier)
