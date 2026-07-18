# Spec — Téléchargement vidéo par URL (ImgOpt)

**Statut** : Implémenté (v1.0) — FastAPI (`backend/`) + Django (`backend_django/`)
**Auteur** : Maurice CODJO
**Date** : 2026-07-18
**Composants impactés** :
- `backend/main.py` + `backend/video_downloader.py` (FastAPI)
- `backend_django/optimizer/views.py` + `optimizer/video_downloader.py` + `optimizer/urls.py` (Django)
- `frontend/src/pages/OptimizeVideos.jsx` + `hooks/useDownloadJob.js` + `components/params/UrlDownloadPanel.jsx`
- `requirements.txt` (les deux), `.env.example` (les deux), `render.yaml`

---

## 1. Objectif

Permettre à l'utilisateur de fournir une **URL de vidéo** (YouTube, TikTok, Facebook, Vimeo, Twitch, Twitter/X, Instagram, et des milliers d'autres) au lieu / en plus d'un upload de fichier. ImgOpt récupère la vidéo source, puis la fait passer dans la chaîne d'optimisation/transcodage FFmpeg déjà existante (`optimize_video`).

Le résultat final est identique à un upload classique : un ZIP (ou fichier unique) téléchargeable, avec suivi de progression SSE en temps réel.

---

## 2. Périmètre

### In scope
- Endpoint `POST /api/download` acceptant une `url` + les mêmes paramètres vidéo que `optimize_video` (codec, CRF, resolution, max_fps, prefix, start_number).
- Support des plateformes via **yt-dlp** (librairie Python, couvre FB/YT/TikTok/etc.).
- Téléchargement asynchrone dans un `OptimizationJob` réutilisant l'infra SSE existante.
- Option **cookies optionnels** pour les vidéos Facebook privées / groupes / stories.
- Réutilisation du pipeline `convert_video` pour l'optimisation post-téléchargement.

### Out of scope (v1)
- Upload + URL dans le **même** job (le job est soit "upload", soit "download").
- Téléchargement d'images par URL (v1 = vidéos uniquement).
- Re-upload vers des plateformes (publishing) — voir spec séparée.
- Playlists entières / channels (limité à 1 URL = 1 vidéo en v1).

---

## 3. Architecture

```
Frontend (champ URL)
   │  POST /api/download {url, codec, video_quality, resolution, max_fps, prefix, start_number, cookies?}
   ▼
Backend FastAPI
   ├─ Création OptimizationJob (status=pending)
   ├─ asyncio.create_task(process_download_async(...))
   │      ├─ validate_url()
   │      ├─ download_with_ytdlp(url, cookies)  → fichier temporaire dans job.output_dir
   │      ├─ convert_video(fichier, ...)          → réutilise video_processor.convert_video
   │      └─ progression SSE (started, video_processed, completed)
   ▼
SSE /api/progress/{job_id}  (identique à l'existant)
   ▼
Download ZIP /api/download/{job_id}  (identique à l'existant)
```

Aucun nouveau mécanisme de job, de nettoyage ou de SSE : on réutilise `OptimizationJob`, `cleanup_old_jobs`, `/api/progress/{job_id}`, `/api/download/{job_id}`.

---

## 4. Nouveau module : `backend/video_downloader.py`

Wrapper mince autour de `yt_dlp`.

```python
# video_downloader.py (esquisse)
import shutil
import subprocess
from pathlib import Path

YTDLP_AVAILABLE = shutil.which("yt-dlp") is not None

def check_ytdlp_support() -> bool:
    return YTDLP_AVAILABLE

def download_video(url: str, output_dir: Path, cookies: str | None = None) -> Path:
    """
    Télécharge la meilleure vidéo progressive (mp4, ≤1080p) dans output_dir.
    Retourne le chemin du fichier téléchargé.
    Lève RuntimeError en cas d'échec (login requis, URL invalide, bloquée).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    tmpl = str(output_dir / "%(id)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "--no-playlist",                 # 1 vidéo par job
        "-f", "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", tmpl,
        url,
    ]
    if cookies:
        # cookies = contenu d'un fichier Netscape, ou "--cookies-from-browser" géré côté front
        cmd += ["--cookies", cookies]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(_clean_ytdlp_error(result.stderr))

    # Retourner le fichier le plus récent du dossier
    files = [f for f in output_dir.iterdir() if f.is_file()]
    return max(files, key=lambda f: f.stat().st_mtime)
```

Notes :
- `yt-dlp` exécuté en **binaire** (`subprocess`), pas via l'API Python, pour isolation et facilité de mise à jour (`pip install -U yt-dlp`).
- `timeout=600` cohérent avec `convert_video`.

---

## 5. Endpoint `POST /api/download`

Ajout dans `main.py`, **à côté** de `/api/optimize`, avec le même rate-limit (`10/minute`) et les mêmes garde-fous (jobs concurrents, prefix regex).

### Signature
```python
@app.post("/api/download")
@limiter.limit("10/minute")
async def start_download(
    request: Request,
    url: str = Form(...),
    prefix: str = Form("video"),
    start_number: int = Form(1),
    codec: str = Form("h264"),
    video_quality: int = Form(None),
    resolution: Optional[str] = Form(None),
    max_fps: Optional[int] = Form(None),
    cookies: Optional[str] = Form(None),   # contenu fichier cookies Netscape (optionnel, pour FB privé)
):
```

### Validations
| Contrôle | Règle | Erreur HTTP |
|---|---|---|
| `url` présente | non vide | 400 |
| Format URL | `re.match(r"^https?://", url)` | 400 "URL invalide" |
| Domaine autorisé (allowlist) | voir §6 | 400 "Plateforme non supportée" |
| `prefix` | `PREFIX_REGEX` (existant) | 400 |
| `codec` | dans `CODEC_CONFIG` | 400 |
| FFmpeg + yt-dlp | dispo | 400 / 503 |
| Jobs concurrents | `< MAX_CONCURRENT_JOBS` | 429 |
| Taille résultat | `< MAX_DOWNLOAD_SIZE_BYTES` (nouvelle env, défaut 500 MB) | 413 |
| Cookies (si fournis) | chaîne non vide, < 50 KB | 400 |

### Réponse (immédiate)
Identique à `/api/optimize` :
```json
{ "job_id": "...", "total_files": 1, "total_videos": 1, "status": "pending" }
```

---

## 6. Allowlist des plateformes (sécurité + légal)

Pour limiter les abus (et le risque légal), on n'accepte **pas** n'importe quelle URL. Allowlist de domaines (extensible via env `DOWNLOAD_ALLOWED_DOMAINS`).

Cibles v1 :
- `youtube.com`, `youtu.be`, `m.youtube.com`
- `tiktok.com`, `vm.tiktok.com`
- `facebook.com`, `fb.watch`, `m.facebook.com`
- `instagram.com`, `instagram.com/reel/*`
- `vimeo.com`
- `twitter.com`, `x.com`
- `twitch.tv`

Toute URL hors allowlist → `400 "Plateforme non supportée"`. La liste est retournée par un nouvel endpoint `GET /api/download/platforms` (pour masquer les champs non supportés côté front, comme `/api/formats`).

---

## 7. Job asynchrone : `process_download_async`

```python
async def process_download_async(job, url, codec, video_quality, resolution, max_fps, prefix, start_number, cookies):
    job.status = "processing"
    job.total_files = 1
    job.total_videos = 1

    job.add_progress({"type": "started", "message": f"Téléchargement depuis {host(url)}...", ...})

    # 1) Download
    try:
        raw_path = await asyncio.to_thread(download_video, url, job.output_dir, cookies)
    except Exception as e:
        job.status = "error"
        job.add_progress({"type": "video_error", "original_name": url, "error": str(e), ...})
        return

    # 2) Optimisation (réutilise convert_video comme process_single_video)
    await process_single_video(job, {"filename": raw_path.name, "content": raw_path.read_bytes()},
                               codec, video_quality, resolution, max_fps, prefix, start_number, idx=1)

    # 3) Nettoyage du fichier brut (on garde uniquement l'optimisé)
    raw_path.unlink(missing_ok=True)

    job.status = "completed"
    job.add_progress({"type": "completed", ...})
```

Le fichier brut téléchargé est **supprimé** après optimisation ; seul le fichier optimisé reste dans `output_dir` pour le ZIP final.

---

## 8. Frontend

Dans `Optimizer.jsx`, ajouter un **onglet / bascule** « Coller une URL » à côté de la DropZone :
- Champ texte `url` + helper « YouTube, TikTok, Facebook… ».
- Champ optionnel « Cookies (FB privé) » (textarea, masqué par défaut).
- Les mêmes panneaux de paramètres vidéo (codec, CRF, résolution, FPS) restent utilisés.
- Au submit : `POST /api/download` → récupère `job_id` → branche le même `EventSource` SSE que l'upload.
- Appel `GET /api/download/platforms` au montage pour afficher les plateformes supportées et désactiver le bouton si URL hors liste (validation légère côté client, la source de vérité restant le backend).

### Nouveaux endpoints consommés par le front
- `POST /api/download`
- `GET /api/download/platforms`

---

## 9. Dépendances & déploiement

### `requirements.txt`
```
yt-dlp>=2024.1.0
```
(yt-dlp fournit son propre binaire ; pas besoin d'ajouter ffmpeg, déjà requis.)

### `.env.example` (ajouts)
```
# Téléchargement vidéo par URL
MAX_DOWNLOAD_SIZE_MB=500
DOWNLOAD_ALLOWED_DOMAINS=youtube.com,youtu.be,tiktok.com,facebook.com,fb.watch,instagram.com,vimeo.com,twitter.com,x.com,twitch.tv
```

### `render.yaml`
- `yt-dlp` s'installe via `pip install -r requirements.txt` (aucun changement système).
- FFmpeg déjà présent (requis pour l'optimisation vidéo actuelle).

---

## 10. Sécurité

| Risque | Mitigation |
|---|---|
| SSRF (URL pointant vers une IP interne / métadonnées cloud) | Allowlist stricte de domaines publiques ; interdiction des IP/hostnames internes (`169.254.x`, `localhost`, `10.x`, `192.168.x`) |
| Zip Slip / Path traversal | Réutilise les garde-fous existants (`output_dir.name` uniquement, validation `..`/slash) |
| Fichier trop volumineux | `MAX_DOWNLOAD_SIZE_MB` (défaut 500) vérifié après download |
| Abuse / scraping massif | Rate-limit `10/minute` (existant) + limite jobs concurrents |
| Injection cookies | Cookies traités comme donnée opaque, écrits dans fichier temporaire à accès restreint, jamais interprétés par le shell |
| Command injection yt-dlp | URL et cookies passés comme **arguments** (liste), jamais via `shell=True` |
| Contenu malveillant | Le fichier téléchargé n'est jamais exécuté ; seul FFmpeg le lit en lecture seule |

---

## 11. Légal & conformité (à afficher côté UI)

- Avertissement obligatoire dans l'UI : *« Le téléchargement peut enfreindre les CGU des plateformes et le droit d'auteur. À utiliser uniquement pour du contenu dont vous détenez les droits ou en usage personnel autorisé. »*
- Facebook : les vidéos privées/groupes/stories nécessitent des cookies de session → l'utilisateur en est responsable.
- yt-dlp doit être maintenu à jour (`pip install -U yt-dlp`) car les plateformes changent fréquemment leurs protections.

---

## 12. Tests (à ajouter dans `tests/`)

- `test_video_downloader.py` :
  - `check_ytdlp_support()` retourne bool.
  - `download_video()` sur URL factice mockée (subprocess patché) retourne un chemin.
  - Erreur propre si `returncode != 0`.
- `tests_test_main.py` (ajouts) :
  - `POST /api/download` avec URL hors allowlist → 400.
  - `POST /api/download` sans `url` → 400.
  - `POST /api/download` avec IP interne → 400 (SSRF guard).
  - `GET /api/download/platforms` retourne la liste.
  - Intégration (si yt-dlp dispo en CI) : téléchargement + optimisation d'une vidéo de test publique.

---

## 13. Plan d'implémentation (ordre suggéré)

1. `video_downloader.py` + `check_ytdlp_support()`.
2. Env `MAX_DOWNLOAD_SIZE_MB`, `DOWNLOAD_ALLOWED_DOMAINS` + validation URL/SSRF.
3. Endpoint `GET /api/download/platforms`.
4. Endpoint `POST /api/download` + `process_download_async`.
5. Intégration SSE (réutilisation totale, aucun changement).
6. Front : onglet URL + appel platforms.
7. `requirements.txt`, `.env.example`, `render.yaml`.
8. Tests + doc (`API_README.md`, `README.md`).

---

## 14. Open questions

- **Limite de taille** : 500 MB par défaut raisonnable ? (vidéos 1080p longues peuvent dépasser).
- **Playlist / plusieurs URLs** : reporter en v2 ?
- **Cookies FB** : fournir un upload de fichier cookies (Netscape) plutôt qu'un textarea ? (plus sûr, moins d'erreurs de saisie).
- **Métadonnées** : conserver le nom de la vidéo source comme `prefix` par défaut ?
