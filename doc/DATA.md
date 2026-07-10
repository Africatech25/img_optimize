# DATA — Modèle de données img_optimize

## Données manipulées
- Images uploadées (fichiers binaires, formats : jpg, png, webp, etc.)
- Paramètres d’optimisation (qualité, format cible, options avancées)
- Résultats d’optimisation (nom, taille, ratio, logs)

## Structure type d’une image optimisée
```
{
  "filename": "image1.webp",
  "size": 12345,
  "original_size": 45678,
  "ratio": 0.27
}
```

## Contraintes
- Taille max par image : à définir (ex : 5 Mo)
- Formats supportés : jpg, png, webp (extensible)
- Pas de stockage persistant (stateless)

## Règles d’intégrité
- Refuser tout fichier non image ou corrompu
- Vérifier la cohérence des paramètres reçus
