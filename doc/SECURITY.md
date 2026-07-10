# SECURITY — img_optimize

## Menaces principales
- Upload de fichiers malicieux (exécutables, scripts)
- Déni de service (fichiers trop volumineux, requêtes massives)
- Fuite d’informations (logs, erreurs détaillées en prod)

## Contrôles en place
- Validation stricte du type de fichier (jpg, png, webp)
- Limite de taille par fichier (à implémenter)
- Pas de stockage persistant (réduit l’impact d’une compromission)
- Logs non exposés côté client

## Exigences à renforcer
- Limiter le nombre de fichiers par requête
- Timeout sur le traitement backend
- Désactiver l’exécution de code arbitraire via les images
- Ajouter un scan antivirus (optionnel, à discuter)

## Checklist sécurité
- [ ] Validation des entrées (type, taille, format)
- [ ] Gestion des erreurs sans fuite d’info sensible
- [ ] Pas de secret/clé en dur dans le code
- [ ] Audit régulier des dépendances (pip/npm audit)
