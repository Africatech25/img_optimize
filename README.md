# ImgOpt : Optimiseur d'Images et Videos

**ImgOpt** est une application web moderne pour compresser et convertir vos images et videos sans compromis sur la qualite. Optimise pour le SEO et la performance web.

---

## Sommaire
1. [Utilisation](#utilisation)
2. [Formats supportes](#formats-supportes)
3. [Architecture Technique](#architecture-technique)
4. [Installation Locale](#installation-locale)
5. [API & Endpoints](#api--endpoints)
6. [Configuration](#configuration)
7. [Deploiement](#deploiement)
8. [Securite & Confidentialite](#securite--confidentialite)

---

## Utilisation

1. **Glissez-deposez** vos images (JPG, PNG, WebP, AVIF) et/ou videos (MP4, WebM, AVI, MOV, MKV).
2. **Choisissez le format** de sortie pour les images (WebP, AVIF, JPEG, PNG).
3. **Configurez le codec** pour les videos (H.264, H.265, VP9, AV1).
4. **Ajustez la qualite** : CRF pour les videos, qualite 0-100 pour les images.
5. **Lancez l'optimisation** et suivez la progression en temps reel (SSE).
6. **Telechargez** le fichier ZIP contenant tous vos assets optimises.

---

## Formats supportes

### Images

| Format | Avantages | Recommandation |
| :--- | :--- | :--- |
| **WebP** | Excellent rapport qualite/poids, 96%+ navigateurs. | **Defaut** pour le web moderne. |
| **AVIF** | Compression superieure au WebP (+30% gain). | Performance maximale. |
| **JPEG** | Compatibilite universelle. | Impressions, vieux systemes. |
| **PNG** | Transparence sans perte. | Logos, graphiques transparents. |

### Videos

| Codec | Avantages | Extension |
| :--- | :--- | :--- |
| **H.264** | Universel, compatible 98% navigateurs. | .mp4 |
| **H.265/HEVC** | -50% vs H.264, qualite superieure. | .mp4 |
| **VP9** | WebM natif, excellent pour le web. | .webm |
| **AV1** | Compression maximale, futur du web. | .webm |

Parametres video disponibles :
- **CRF** (15-51) : niveau de qualite (plus bas = meilleur)
- **Resolution** : 4K, 1080p, 720p, 480p, 360p, originale
- **FPS max** : limiter le nombre d'images par seconde

---

## Architecture Technique

- **Frontend** : React 18 + Vite 6 + Tailwind CSS 3 (Glassmorphism)
- **Backend** : FastAPI (Python) + Pillow (images) + FFmpeg (videos)
- **Deploiement** : Backend sur Render, Frontend sur Vercel
- **Analytics** : Vercel Analytics (anonyme)

### Detection automatique des formats
Le frontend interroge dynamiquement le backend (`/api/formats`, `/api/video/formats`) pour savoir quels formats et codecs sont reels supportes. Les formats non disponibles sont automatiquement masques.

---

## Installation Locale

### Pre requis
- Python 3.11+
- Node.js 18+
- FFmpeg (pour l'optimisation video)

### 1. Cloner le projet
```bash
git clone https://github.com/Africatech25/img_optimize.git
cd img_optimize
```

### 2. Configurer le Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```
Le backend tournera sur `http://localhost:8000`.

### 3. Configurer le Frontend
```bash
cd ../frontend
npm install
npm run dev
```
Le frontend sera accessible sur `http://localhost:5173`.

---

## API & Endpoints

| Methode | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Health check (AVIF, FFmpeg status) |
| `GET` | `/api/formats` | Formats image disponibles |
| `GET` | `/api/video/formats` | Codecs video disponibles |
| `POST` | `/api/optimize` | Envoyer images/videos pour traitement |
| `GET` | `/api/progress/{id}` | SSE - progression en temps reel |
| `GET` | `/api/job/{id}` | Statut d'un job |
| `GET` | `/api/download/{id}` | Telecharger le fichier ZIP |
| `GET` | `/api/download/{id}/{filename}` | Telecharger un fichier specifique |
| `GET` | `/api/download-zip/{id}` | Forcer le telechargement ZIP |
| `DELETE` | `/api/cleanup/{id}` | Nettoyer les fichiers d'un job |

### Limites
- **Upload** : 50 MB par fichier
- **Jobs concurrents** : 20 maximum
- **Rate limiting** : 10 requetes/minute sur `/api/optimize`
- **Retention** : jobs auto-nettoyes apres 24h

---

## Configuration

Creer un fichier `.env` dans `backend/` (voir `.env.example`) :

| Variable | Defaut | Description |
| :--- | :--- | :--- |
| `PORT` | 8000 | Port du serveur backend |
| `CORS_ORIGINS` | `http://localhost:5173` | Domaines CORS autorises |
| `MAX_UPLOAD_SIZE_MB` | 50 | Taille max par fichier upload |
| `MAX_CONCURRENT_JOBS` | 20 | Jobs max simultanes |

---

## Deploiement

### Backend (Render)
1. Creer un "Web Service"
2. Build Command : `pip install -r requirements.txt`
3. Start Command : `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. **Important** : Installer FFmpeg sur Render (configurer dans `render.yaml`)

### Frontend (Vercel)
1. Connecter le repo GitHub
2. Root directory : `frontend`
3. Variable d'env : `VITE_API_URL` (URL de votre API Render)

---

## Securite & Confidentialite

- **CORS restreint** : seuls les domaines configures sont autorises
- **Rate limiting** : protection contre les abus
- **Validation des fichiers** : taille, extension, prefixe (injection prevention)
- **Zip Slip protection** : securite sur les archives ZIP
- **Path traversal protection** : validation des noms de fichiers
- **Nettoyage auto** : fichiers temporaires supprimes apres 24h

---

**Developpe par Maurice CODJO**
