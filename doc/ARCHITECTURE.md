# ARCHITECTURE — img_optimize

## Vision système
ImgOpt est un automate multi-fonctionnalité haute performance pour :
1. **Optimisation d'images** : Compresser massivement des visuels tout en appliquant une identité visuelle (Watermarking) en un clic, garantissant protection et uniformité sur les réseaux sociaux (images simples et carrousels).
2. **Réparation de PDFs** : Valider et réparer les fichiers PDF corrompus en reconstructuisant la structure interne (xref table) et supprimant les objets invalides.

## Stack technique
- Frontend : React (Vite) + TailwindCSS (Glassmorphism)
- Backend : Python (FastAPI) + Pillow (Traitement d'image) + pikepdf (Réparation PDF)
- Base de données : NoDB (Stateless, stockage temporaire des jobs en RAM/Disk)
- Traitement : Asyncio (Backend) pour l'asynchronicité, multiprocessing pour parallelisation intensive

## Modules principaux

### Backend
- `main.py` : Serveur API & Gestion des jobs (images et PDFs)
- `optimize_images.py` : Moteur de compression & Watermarking (images)
- `repair_pdf.py` (NEW) : Moteur de validation et réparation de PDFs

### Frontend
- `DropZone` : Upload massif (images et PDFs avec détection type)
- `ParamsPanel` : Réglages compression + Watermarking (images)
- `PDFRepair` (NEW) : Flux de réparation PDF (validation, info, réparation)
- `ImageGrid` : Galerie de résultats avec aperçu poids gagné (images)
- `Optimizer.jsx` : Conteneur principal avec tabs (Images | Réparation PDF)

## Flux principal - Optimisation d'images
1. Upload : L'utilisateur glisse-dépose ses images via `DropZone` (modeType='images')
2. Configuration : Réglages de qualité (WebP/AVIF) + watermarking optionnel via `ParamsPanel`
3. Traitement : Backend génère en parallèle les versions optimisées et marquées
4. Export : Récupération d'un pack ZIP contenant les visuels prêts à l'emploi

## Flux principal - Réparation de PDF
1. Upload : L'utilisateur glisse-dépose son PDF via `DropZone` (modeType='pdf')
2. Validation : Analyse structure interne via `/api/pdf/validate` → détection erreurs/corruptions
3. Extraction métadonnées : Récupération titre, auteur, pages via `/api/pdf/info`
4. Réparation : Reconstruction xref + suppression objets corrompus via `/api/pdf/repair`
5. Téléchargement : Retour du PDF réparé et optimisé en download direct

## Sécurité & Confidentialité

### Images
- Validation stricte MIME (types images seulement)
- Limite 50 MB/fichier, max 200 fichiers/requête
- Suppression auto fichiers temp après téléchargement ou 24h
- Anonymisation métadonnées lors marquage

### PDFs (NEW)
- Validation MIME `application/pdf` stricte
- Limite 50 MB/fichier (cohérent avec images)
- Sandboxing via tempfiles isolés
- Pas de stockage métadonnées sensibles
- Suppression auto PDFs temporaires après téléchargement

## Endpoints API

### Images (Existants)
- `GET /api/health` : État du service
- `GET /api/formats` : Formats disponibles
- `POST /api/optimize` : Démarrer job optimisation
- `GET /api/progress/{job_id}` : SSE progression (streaming)
- `GET /api/job/{job_id}` : Statut job
- `GET /api/download/{job_id}` : Récupérer résultats
- `DELETE /api/cleanup/{job_id}` : Nettoyer job

### PDFs (NEW)
- `POST /api/pdf/validate` : Valider structure PDF
- `POST /api/pdf/repair` : Réparer PDF corrompu
- `POST /api/pdf/info` : Extraire métadonnées PDF

## Diagrammes
Voir doc/DIAGRAMMES/README.md
