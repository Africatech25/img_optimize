#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend FastAPI pour l'optimisation d'images et vidéos avec SSE
"""
import sys
import io
import re
import traceback

# Forcer l'encodage UTF-8 pour Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from pathlib import Path
import shutil
import tempfile
import uuid
from typing import List, Dict, Optional
import json
import asyncio
import zipfile
from io import BytesIO
from datetime import datetime, timedelta
import os

# Importation des moteurs d'optimisation
from optimize_images import FORMAT_CONFIG, convert_image, format_size, check_avif_support, SUPPORTED_EXTENSIONS
from video_processor import (
    CODEC_CONFIG, convert_video, check_ffmpeg_support,
    get_video_info, format_size as format_size_video,
    format_duration, VIDEO_EXTENSIONS
)
from video_downloader import (
    check_ytdlp_support, validate_url, download_video,
    get_supported_platforms, get_supported_domains,
)

# ==================== CONFIGURATION ====================

# CORS - domaines autorises (a modifier en prod)
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    if origin.strip()
]

# Upload
MAX_UPLOAD_SIZE_MB = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "50"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# Téléchargement vidéo par URL
MAX_DOWNLOAD_SIZE_MB = int(os.environ.get("MAX_DOWNLOAD_SIZE_MB", "500"))
MAX_DOWNLOAD_SIZE_BYTES = MAX_DOWNLOAD_SIZE_MB * 1024 * 1024

# Jobs
MAX_CONCURRENT_JOBS = int(os.environ.get("MAX_CONCURRENT_JOBS", "20"))

# Prefixe : lettres, chiffres, tirets, underscores, 1-100 caractères
PREFIX_REGEX = re.compile(r"^[a-zA-Z0-9_-]{1,100}$")

# Dossiers temporaires
TEMP_DIR = Path(tempfile.gettempdir()) / "image_optimizer"
TEMP_DIR.mkdir(exist_ok=True)

# Extensions par type
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}
ALL_MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS


def is_video_file(filename: str) -> bool:
    """Détermine si un fichier est une vidéo basé sur son extension."""
    ext = Path(filename).suffix.lower()
    return ext in VIDEO_EXTENSIONS


def is_image_file(filename: str) -> bool:
    """Détermine si un fichier est une image basé sur son extension."""
    ext = Path(filename).suffix.lower()
    return ext in IMAGE_EXTENSIONS


# Stockage en mémoire des jobs en cours
jobs: Dict[str, 'OptimizationJob'] = {}

# Tâche de nettoyage en arrière-plan
cleanup_task = None


async def cleanup_old_jobs():
    """Nettoie les jobs de plus de 24 heures toutes les heures (mais pas les jobs en cours)"""
    while True:
        await asyncio.sleep(3600)  # 1 heure

        now = datetime.now()
        to_delete = []

        for job_id, job in list(jobs.items()):
            # Ne pas supprimer les jobs en cours de traitement
            if job.status == "processing":
                continue

            if now - job.created_at > timedelta(hours=24):
                to_delete.append(job_id)

        for job_id in to_delete:
            job = jobs[job_id]
            if job.output_dir.exists():
                shutil.rmtree(job.output_dir)
            jobs.pop(job_id, None)

        if to_delete:
            print(f"Nettoyage: {len(to_delete)} job(s) ancien(s) supprime(s)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    global cleanup_task
    # Démarrage : nettoyer les fichiers temporaires residuels
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
        TEMP_DIR.mkdir(exist_ok=True)
    cleanup_task = asyncio.create_task(cleanup_old_jobs())
    yield
    # Arrêt
    if cleanup_task:
        cleanup_task.cancel()


app = FastAPI(title="ImgOpt API", version="3.1.0", lifespan=lifespan)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS restreint aux domaines autorises
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
    expose_headers=["Content-Disposition"],
)


class OptimizationJob:
    """Représente un job d'optimisation (images et/ou vidéos)"""
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.status = "pending"  # pending, processing, completed, error
        self.progress = []
        self.total_files = 0
        self.processed_files = 0
        self.total_images = 0
        self.total_videos = 0

        # Créer le dossier de sortie avec vérification robuste
        self.output_dir = TEMP_DIR / job_id
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            # Vérifier que le dossier a bien été créé
            if not self.output_dir.exists():
                raise RuntimeError(f"Impossible de créer le répertoire {self.output_dir}")
            # Convertir en chemin absolu pour éviter les problèmes Windows 8.3
            self.output_dir = self.output_dir.resolve()
        except Exception as e:
            print(f"Erreur création dossier output: {e}")
            raise

        self.created_at = datetime.now()
        self.stats = {
            "total_before": 0,
            "total_after": 0,
            "successful": 0,
            "errors": 0,
            "images": 0,
            "videos": 0,
        }

    def add_progress(self, message: dict):
        """Ajoute un message de progression"""
        self.progress.append(message)
        if message.get("type") in ("file_processed", "image_processed", "video_processed"):
            self.processed_files += 1
        if message.get("type") == "image_processed":
            self.stats["images"] += 1
        if message.get("type") == "video_processed":
            self.stats["videos"] += 1

    def to_dict(self):
        """Convertit en dictionnaire"""
        reduction = 0
        if self.stats["total_before"] > 0:
            reduction = (1 - self.stats["total_after"] / self.stats["total_before"]) * 100

        return {
            "job_id": self.job_id,
            "status": self.status,
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "total_images": self.total_images,
            "total_videos": self.total_videos,
            "stats": {
                **self.stats,
                "reduction_percent": round(reduction, 1)
            }
        }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "avif_available": check_avif_support(),
        "ffmpeg_available": check_ffmpeg_support(),
        "ytdlp_available": check_ytdlp_support(),
        "image_formats": list(FORMAT_CONFIG.keys()),
        "video_codecs": list(CODEC_CONFIG.keys()),
    }


@app.get("/api/download/platforms")
async def get_download_platforms():
    """Retourne les plateformes de téléchargement supportées."""
    return {
        "available": check_ytdlp_support(),
        "platforms": get_supported_platforms(),
        "domains": sorted(get_supported_domains().keys()),
        "max_size_mb": MAX_DOWNLOAD_SIZE_MB,
    }


@app.get("/api/formats")
async def get_formats():
    """Retourne les formats image disponibles avec leurs configurations"""
    avif_ok = check_avif_support()
    return {
        fmt: {
            "description": config.get("description", ""),
            "default_quality": config["default_quality"],
            "quality_range": config["quality_range"],
            "available": True if fmt != "avif" else avif_ok
        }
        for fmt, config in FORMAT_CONFIG.items()
    }


@app.get("/api/video/formats")
async def get_video_formats():
    """Retourne les codecs vidéo disponibles avec leurs configurations"""
    ffmpeg_ok = check_ffmpeg_support()
    return {
        codec: {
            "description": config["description"],
            "encoder": config["encoder"],
            "default_crf": config["default_crf"],
            "crf_range": config["crf_range"],
            "extension": config["extension"],
            "available": ffmpeg_ok,
        }
        for codec, config in CODEC_CONFIG.items()
    }


VALID_MODES = {"optimize_image", "optimize_video", "sign", "smooth"}


def resolve_max_quality_format(filename: str) -> tuple[str, int]:
    """
    Détermine le format et la qualité maximale (sans compression visible) pour
    une image, en conservant au mieux son format d'origine. Utilisé par les
    modes 'sign' et 'smooth', qui ne demandent pas de format/qualité à l'utilisateur.
    """
    ext = Path(filename).suffix.lower()
    if ext in (".jpg", ".jpeg"):
        fmt = "jpeg"
    elif ext == ".webp":
        fmt = "webp"
    else:
        # .png, .bmp, .tiff, .tif -> PNG (sans perte)
        fmt = "png"
    quality = FORMAT_CONFIG[fmt]["quality_range"][1]
    return fmt, quality


@app.post("/api/optimize")
@limiter.limit("10/minute")
async def start_optimization(
    request: Request,
    files: List[UploadFile] = File(...),
    mode: str = Form("optimize_image"),
    format: str = Form("webp"),
    quality: int = Form(None),
    prefix: str = Form("image"),
    start_number: int = Form(1),
    codec: str = Form("h264"),
    video_quality: int = Form(None),
    resolution: Optional[str] = Form(None),
    max_fps: Optional[int] = Form(None),
    smoothing: int = Form(0),
    watermark_type: str = Form("text"),
    watermark_text: str = Form(""),
    watermark_logo: Optional[UploadFile] = File(None),
    watermark_position: str = Form("bottom-right"),
    watermark_opacity: str = Form("50"),
):
    """
    Démarre une action (optimisation ou traitement) et retourne un job_id
    pour suivre la progression via SSE.

    Le paramètre `mode` détermine l'action et les paramètres attendus :
    - optimize_image : format + quality, images uniquement
    - optimize_video : codec + video_quality + resolution + max_fps, vidéos uniquement
    - sign : watermark_type/text/logo/position/opacity, images uniquement, qualité maximale
    - smooth : smoothing, images uniquement, qualité maximale
    """
    if mode not in VALID_MODES:
        raise HTTPException(status_code=400, detail=f"Mode non supporté: {mode}")

    # Séparer les images et les vidéos
    image_files = []
    video_files = []

    for file in files:
        if is_video_file(file.filename):
            video_files.append(file)
        elif is_image_file(file.filename):
            image_files.append(file)
        else:
            # Extension non supportée
            raise HTTPException(
                status_code=400,
                detail=f"Format non supporté: {Path(file.filename).suffix}. Utilisez des images ou des vidéos."
            )

    if not image_files and not video_files:
        raise HTTPException(status_code=400, detail="Aucun fichier valide fourni")

    # Chaque mode est dédié à un seul type de fichier
    if mode == "optimize_video" and image_files:
        raise HTTPException(status_code=400, detail="Ce mode n'accepte que des vidéos.")
    if mode in ("optimize_image", "sign", "smooth") and video_files:
        raise HTTPException(status_code=400, detail="Ce mode n'accepte que des images.")

    # B5: Valider le prefixe (injection prevention)
    if not PREFIX_REGEX.match(prefix):
        raise HTTPException(
            status_code=400,
            detail="Prefixe invalide. Utilisez uniquement lettres, chiffres, tirets ou underscores (1-100 car.)"
        )

    # I1: Limiter les jobs concurrents
    active_jobs = sum(1 for j in jobs.values() if j.status in ("pending", "processing"))
    if active_jobs >= MAX_CONCURRENT_JOBS:
        raise HTTPException(
            status_code=429,
            detail=f"Trop de jobs en cours ({active_jobs}/{MAX_CONCURRENT_JOBS}). Reessayez dans quelques secondes."
        )

    # Paramètres résolus selon le mode
    img_format_val: Optional[str] = None   # None = qualité maximale, format auto par fichier
    img_quality_val: Optional[int] = None
    max_size_mo = 0
    smoothing_val = 0
    watermark_params = None

    if mode == "optimize_image":
        if format not in FORMAT_CONFIG:
            raise HTTPException(status_code=400, detail=f"Format image non supporté: {format}")
        if format == "avif" and not check_avif_support():
            raise HTTPException(
                status_code=400,
                detail="Le format AVIF n'est pas disponible sur ce serveur."
            )
        config = FORMAT_CONFIG[format]
        img_quality = quality if quality is not None else config["default_quality"]
        q_min, q_max = config["quality_range"]
        if not (q_min <= img_quality <= q_max):
            raise HTTPException(
                status_code=400,
                detail=f"Qualité pour {format.upper()} doit être entre {q_min} et {q_max}"
            )
        img_format_val = format
        img_quality_val = img_quality
        max_size_mo = 1.0

    elif mode == "smooth":
        if not (1 <= smoothing <= 10):
            raise HTTPException(
                status_code=400,
                detail="Le lissage doit être entre 1 et 10"
            )
        smoothing_val = smoothing

    elif mode == "sign":
        try:
            watermark_opacity_val = int(watermark_opacity)
        except (ValueError, TypeError):
            watermark_opacity_val = 50
        if not (0 <= watermark_opacity_val <= 100):
            raise HTTPException(
                status_code=400,
                detail="L'opacité de la signature doit être entre 0 et 100"
            )
        if watermark_type == "text" and not watermark_text.strip():
            raise HTTPException(status_code=400, detail="Le texte de la signature est requis")
        if watermark_type == "image" and not watermark_logo:
            raise HTTPException(status_code=400, detail="Un logo est requis pour ce type de signature")

        watermark_params = {
            "enabled": True,
            "type": watermark_type,
            "text": watermark_text,
            "position": watermark_position,
            "opacity": watermark_opacity_val,
            "image_path": None,
        }

        # Sauvegarder temporairement le logo si fourni
        if watermark_type == "image" and watermark_logo:
            try:
                logo_content = await watermark_logo.read(MAX_UPLOAD_SIZE_BYTES + 1)
                if len(logo_content) > MAX_UPLOAD_SIZE_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Logo trop volumineux (max {MAX_UPLOAD_SIZE_MB}MB)"
                    )
                logo_ext = Path(watermark_logo.filename).suffix.lower()
                if logo_ext not in SUPPORTED_EXTENSIONS:
                    raise HTTPException(status_code=400, detail="Format de logo non supporté")

                logo_temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=logo_ext, dir=TEMP_DIR)
                logo_temp_file.write(logo_content)
                logo_temp_file.close()
                watermark_params["image_path"] = logo_temp_file.name
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Erreur lors de la lecture du logo: {str(e)}")

    # Valider les paramètres vidéos si des vidéos sont présentes (mode optimize_video)
    if video_files:
        if codec not in CODEC_CONFIG:
            raise HTTPException(status_code=400, detail=f"Codec vidéo non supporté: {codec}")
        if not check_ffmpeg_support():
            raise HTTPException(
                status_code=400,
                detail="FFmpeg n'est pas installé sur ce serveur. L'optimisation vidéo n'est pas disponible."
            )
        v_config = CODEC_CONFIG[codec]
        vid_quality = video_quality if video_quality is not None else v_config["default_crf"]
        v_min, v_max = v_config["crf_range"]
        if not (v_min <= vid_quality <= v_max):
            raise HTTPException(
                status_code=400,
                detail=f"Qualité vidéo (CRF) pour {codec.upper()} doit être entre {v_min} et {v_max}"
            )

    # Lire tous les fichiers IMMÉDIATEMENT
    file_data = []
    for file in (image_files + video_files):
        try:
            content = await file.read()
            # B3: Verifier la taille du fichier
            if len(content) > MAX_UPLOAD_SIZE_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail=f"Fichier {file.filename} trop volumineux ({len(content) // (1024*1024)} MB). Maximum : {MAX_UPLOAD_SIZE_MB} MB."
                )
            file_data.append({
                "filename": file.filename,
                "content": content,
                "is_video": is_video_file(file.filename),
            })
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erreur lecture fichier {file.filename}: {str(e)}")

    if not file_data:
        raise HTTPException(status_code=400, detail="Aucun fichier valide fourni")

    # Créer un nouveau job
    job_id = str(uuid.uuid4())
    job = OptimizationJob(job_id)
    job.total_files = len(file_data)
    job.total_images = len(image_files)
    job.total_videos = len(video_files)
    jobs[job_id] = job

    # Préparer les paramètres pour le traitement
    vid_quality_val = vid_quality if video_files else None

    # Lancer le traitement en arrière-plan
    asyncio.create_task(
        process_mixed_async(
            job, file_data, img_format_val, img_quality_val,
            codec, vid_quality_val, resolution, max_fps,
            prefix, start_number, smoothing_val, watermark_params, max_size_mo
        )
    )

    return {
        "job_id": job_id,
        "total_files": len(file_data),
        "total_images": len(image_files),
        "total_videos": len(video_files),
        "status": "pending"
    }


@app.post("/api/download")
@limiter.limit("10/minute")
async def start_download(
    request: Request,
    url: str = Form(...),
    prefix: str = Form("video"),
    start_number: int = Form(1),
    optimize: bool = Form(True),
    codec: str = Form("h264"),
    video_quality: int = Form(None),
    resolution: Optional[str] = Form(None),
    max_fps: Optional[int] = Form(None),
    cookies: Optional[str] = Form(None),
):
    """
    Télécharge une vidéo depuis une URL (YouTube, TikTok, Facebook, ...) puis,
    au choix, l'optimise via le pipeline vidéo existant ou la conserve telle
    quelle. Retourne un job_id suivi en SSE.
    """
    # Valider l'URL (format, SSRF, allowlist plateformes)
    try:
        host = validate_url(url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # B5: Valider le prefixe (injection prevention)
    if not PREFIX_REGEX.match(prefix):
        raise HTTPException(
            status_code=400,
            detail="Prefixe invalide. Utilisez uniquement lettres, chiffres, tirets ou underscores (1-100 car.)"
        )

    if not check_ytdlp_support():
        raise HTTPException(
            status_code=503,
            detail="Le téléchargement vidéo n'est pas disponible sur ce serveur (yt-dlp manquant)."
        )

    vid_quality = None
    if optimize:
        # Valider codec / ffmpeg uniquement si l'optimisation est demandée
        if codec not in CODEC_CONFIG:
            raise HTTPException(status_code=400, detail=f"Codec vidéo non supporté: {codec}")
        if not check_ffmpeg_support():
            raise HTTPException(
                status_code=400,
                detail="FFmpeg n'est pas installé sur ce serveur. L'optimisation vidéo n'est pas disponible."
            )

        v_config = CODEC_CONFIG[codec]
        vid_quality = video_quality if video_quality is not None else v_config["default_crf"]
        v_min, v_max = v_config["crf_range"]
        if not (v_min <= vid_quality <= v_max):
            raise HTTPException(
                status_code=400,
                detail=f"Qualité vidéo (CRF) pour {codec.upper()} doit être entre {v_min} et {v_max}"
            )

    # I1: Limiter les jobs concurrents
    active_jobs = sum(1 for j in jobs.values() if j.status in ("pending", "processing"))
    if active_jobs >= MAX_CONCURRENT_JOBS:
        raise HTTPException(
            status_code=429,
            detail=f"Trop de jobs en cours ({active_jobs}/{MAX_CONCURRENT_JOBS}). Reessayez dans quelques secondes."
        )

    # Créer le job (réutilise OptimizationJob)
    job_id = str(uuid.uuid4())
    job = OptimizationJob(job_id)
    job.total_files = 1
    job.total_videos = 1
    job.stats["optimized"] = optimize
    jobs[job_id] = job

    asyncio.create_task(
        process_download_async(
            job, url, host, optimize, codec, vid_quality, resolution, max_fps,
            prefix, start_number, cookies
        )
    )

    return {
        "job_id": job_id,
        "total_files": 1,
        "total_videos": 1,
        "status": "pending",
    }


async def process_download_async(
    job: OptimizationJob,
    url: str,
    host: str,
    optimize: bool,
    video_codec: str,
    video_quality: Optional[int],
    resolution: Optional[str],
    max_fps: Optional[int],
    prefix: str,
    start_number: int,
    cookies: Optional[str],
):
    """
    Télécharge une vidéo depuis une URL puis, au choix, l'optimise via
    convert_video ou la conserve telle quelle. Réutilise l'infra de job SSE
    existante.
    """
    job.status = "processing"

    job.add_progress({
        "type": "started",
        "message": f"Téléchargement depuis {host}...",
        "timestamp": datetime.now().isoformat(),
    })

    # Dossier isolé pour le téléchargement brut (et le fichier cookies
    # temporaire) : évite qu'un résidu (verrou Windows sur le fichier
    # cookies, etc.) ne pollue job.output_dir et ne fasse basculer le
    # téléchargement du résultat en ZIP au lieu du fichier unique attendu.
    raw_dir = Path(tempfile.mkdtemp(prefix="dl_", dir=str(TEMP_DIR)))
    raw_path = None
    try:
        # 1) Téléchargement (subprocess yt-dlp, exécuté hors boucle asyncio)
        raw_path = await asyncio.to_thread(
            download_video, url, raw_dir, cookies
        )

        # Vérifier la taille du fichier téléchargé
        raw_size = raw_path.stat().st_size
        if raw_size > MAX_DOWNLOAD_SIZE_BYTES:
            raise RuntimeError(
                f"Vidéo téléchargée trop volumineuse "
                f"({raw_size // (1024 * 1024)} MB). Maximum : {MAX_DOWNLOAD_SIZE_MB} MB."
            )

        job.add_progress({
            "type": "download_done",
            "original_name": url,
            "message": f"Téléchargement terminé ({format_size(raw_size)}). "
                        + ("Optimisation..." if optimize else "Finalisation..."),
            "timestamp": datetime.now().isoformat(),
        })

        if optimize:
            # 2) Optimisation (réutilise process_single_video)
            await process_single_video(
                job, {"filename": raw_path.name, "content": raw_path.read_bytes()},
                video_codec, video_quality, resolution, max_fps,
                prefix, start_number, idx=1
            )
        else:
            # 2) Conservation du fichier brut (sans optimisation)
            await asyncio.to_thread(
                register_raw_download, job, raw_path, prefix, start_number, 1
            )

    except Exception as e:
        full_trace = traceback.format_exc()
        print(f"Erreur téléchargement {url}:")
        print(f"  → {str(e)}")
        print(f"  → Traceback:\n{full_trace}")

        job.stats["errors"] += 1
        job.add_progress({
            "type": "video_error",
            "original_name": url,
            "error": str(e),
            "success": False,
            "index": 1,
            "timestamp": datetime.now().isoformat(),
        })
    finally:
        # 3) Nettoyer le dossier de téléchargement brut (on conserve
        # uniquement le résultat final dans job.output_dir)
        shutil.rmtree(raw_dir, ignore_errors=True)

        job.status = "completed"
        job.add_progress({
            "type": "completed",
            "message": f"Traitement terminé ! {job.stats['successful']}/{job.total_files} fichier(s) traité(s)",
            "timestamp": datetime.now().isoformat(),
            "stats": job.to_dict()["stats"],
        })


async def process_mixed_async(
    job: OptimizationJob,
    file_data: list,
    img_format: Optional[str],
    img_quality: Optional[int],
    video_codec: str,
    video_quality: Optional[int],
    resolution: Optional[str],
    max_fps: Optional[int],
    prefix: str,
    start_number: int,
    smoothing: int = 0,
    watermark_params: dict = None,
    max_size_mo: float = 0
):
    """
    Traite les images et vidéos de manière asynchrone.
    Le type est détecté automatiquement pour chaque fichier.
    """
    job.status = "processing"
    counter = start_number

    # Message de démarrage
    parts = []
    if job.total_images > 0:
        parts.append(f"{job.total_images} image(s)")
    if job.total_videos > 0:
        parts.append(f"{job.total_videos} vidéo(s)")

    job.add_progress({
        "type": "started",
        "message": f"Démarrage de l'optimisation de {', '.join(parts)}...",
        "timestamp": datetime.now().isoformat()
    })

    # Traiter chaque fichier
    for idx, file_info in enumerate(file_data, start=1):
        if file_info["is_video"]:
            counter = await process_single_video(
                job, file_info, video_codec, video_quality,
                resolution, max_fps, prefix, counter, idx
            )
        else:
            counter = await process_single_image(
                job, file_info, img_format, img_quality, prefix, counter, idx,
                smoothing, watermark_params, max_size_mo
            )

    # Nettoyage du logo temporaire de watermark si nécessaire
    if watermark_params and watermark_params.get("image_path"):
        try:
            os.unlink(watermark_params["image_path"])
        except OSError:
            pass

    # Terminer le job
    job.status = "completed"
    job.add_progress({
        "type": "completed",
        "message": f"Optimisation terminée ! {job.stats['successful']}/{job.total_files} fichiers traités",
        "timestamp": datetime.now().isoformat(),
        "stats": job.to_dict()["stats"]
    })


async def process_single_image(
    job: OptimizationJob,
    file_info: dict,
    fmt: Optional[str],
    quality: Optional[int],
    prefix: str,
    counter: int,
    idx: int,
    smoothing: int = 0,
    watermark_params: dict = None,
    max_size_mo: float = 0
) -> int:
    """Traite une seule image et retourne le compteur mis à jour"""
    # fmt/quality non fournis (modes sign/smooth) : qualité maximale,
    # format déterminé par fichier pour préserver le format d'origine.
    if fmt is None:
        fmt, quality = resolve_max_quality_format(file_info['filename'])

    config = FORMAT_CONFIG[fmt]
    ext = config["extension"]
    temp_input = None

    try:
        # Sauvegarder le fichier temporairement depuis les données en bytes
        temp_input = TEMP_DIR / f"{uuid.uuid4()}_{file_info['filename']}"

        # Écrire les données directement (pas besoin de await, données déjà en mémoire)
        with temp_input.open("wb") as buffer:
            buffer.write(file_info['content'])

        # Nom du fichier optimisé
        output_filename = f"{prefix}-{counter:02d}{ext}"
        output_path = job.output_dir / output_filename

        # Optimiser l'image (limite de taille, lissage et watermark selon le mode)
        before, after, status = await asyncio.to_thread(
            convert_image, temp_input, output_path, fmt, quality,
            max_size_mo=max_size_mo, smoothing=smoothing, watermark_params=watermark_params
        )

        gain_pct = (1 - after / before) * 100 if before > 0 else 0

        # Mettre à jour les statistiques
        job.stats["total_before"] += before
        job.stats["total_after"] += after
        job.stats["successful"] += 1

        # Ajouter à la progression
        job.add_progress({
            "type": "image_processed",
            "original_name": file_info['filename'],
            "optimized_name": output_filename,
            "before": before,
            "after": after,
            "gain_percent": round(gain_pct, 1),
            "before_formatted": format_size(before),
            "after_formatted": format_size(after),
            "success": True,
            "index": idx,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        # Logger l'erreur pour le debug
        full_trace = traceback.format_exc()
        print(f"Erreur traitement {file_info['filename']}:")
        print(f"  → {str(e)}")
        print(f"  → Traceback:\n{full_trace}")

        job.stats["errors"] += 1

        error_msg = str(e) if str(e) else f"Exception {type(e).__name__}"
        error_type = type(e).__name__
        if error_type and error_type != "Exception":
            error_msg = f"[{error_type}] {error_msg}"

        job.add_progress({
            "type": "image_error",
            "original_name": file_info['filename'],
            "error": error_msg,
            "success": False,
            "index": idx,
            "timestamp": datetime.now().isoformat()
        })

    finally:
        # TOUJOURS incrémenter le compteur, même en cas d'erreur
        counter += 1

        # Nettoyer le fichier temporaire
        if temp_input and temp_input.exists():
            temp_input.unlink()

    return counter


async def process_single_video(
    job: OptimizationJob,
    file_info: dict,
    codec: str,
    quality: int,
    resolution: Optional[str],
    max_fps: Optional[int],
    prefix: str,
    counter: int,
    idx: int
) -> int:
    """Traite une seule vidéo et retourne le compteur mis à jour"""
    config = CODEC_CONFIG[codec]
    ext = config["extension"]
    temp_input = None

    try:
        # Sauvegarder le fichier temporairement
        temp_input = TEMP_DIR / f"{uuid.uuid4()}_{file_info['filename']}"

        with temp_input.open("wb") as buffer:
            buffer.write(file_info['content'])

        # Nom du fichier optimisé
        output_filename = f"{prefix}-{counter:02d}{ext}"
        output_path = job.output_dir / output_filename

        # Obtenir les infos de la vidéo source
        info = get_video_info(temp_input)

        # Optimiser la vidéo
        before, after, status = convert_video(
            temp_input, output_path, codec, quality,
            resolution, max_fps, max_size_mo=0
        )

        gain_pct = (1 - after / before) * 100 if before > 0 else 0

        # Mettre à jour les statistiques
        job.stats["total_before"] += before
        job.stats["total_after"] += after
        job.stats["successful"] += 1

        # Ajouter à la progression
        job.add_progress({
            "type": "video_processed",
            "original_name": file_info['filename'],
            "optimized_name": output_filename,
            "before": before,
            "after": after,
            "gain_percent": round(gain_pct, 1),
            "before_formatted": format_size(before),
            "after_formatted": format_size(after),
            "duration": format_duration(info["duration"]),
            "resolution": f"{info['width']}x{info['height']}",
            "codec": codec,
            "optimized": True,
            "success": True,
            "index": idx,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        full_trace = traceback.format_exc()
        print(f"Erreur traitement vidéo {file_info['filename']}:")
        print(f"  → {str(e)}")
        print(f"  → Traceback:\n{full_trace}")

        job.stats["errors"] += 1

        error_msg = str(e) if str(e) else f"Exception {type(e).__name__}"
        error_type = type(e).__name__
        if error_type and error_type != "Exception":
            error_msg = f"[{error_type}] {error_msg}"

        job.add_progress({
            "type": "video_error",
            "original_name": file_info['filename'],
            "error": error_msg,
            "success": False,
            "index": idx,
            "timestamp": datetime.now().isoformat()
        })

    finally:
        counter += 1
        if temp_input and temp_input.exists():
            temp_input.unlink()

    return counter


def register_raw_download(job: OptimizationJob, raw_path: Path, prefix: str, counter: int, idx: int) -> int:
    """Range le fichier téléchargé tel quel (sans optimisation) comme résultat du job."""
    output_filename = f"{prefix}-{counter:02d}{raw_path.suffix.lower()}"
    output_path = job.output_dir / output_filename

    try:
        size = raw_path.stat().st_size
        try:
            info = get_video_info(raw_path)
            duration = format_duration(info["duration"])
            video_resolution = f"{info['width']}x{info['height']}"
        except Exception:
            duration = None
            video_resolution = None

        shutil.move(str(raw_path), str(output_path))

        job.stats["total_before"] += size
        job.stats["total_after"] += size
        job.stats["successful"] += 1

        job.add_progress({
            "type": "video_processed",
            "original_name": raw_path.name,
            "optimized_name": output_filename,
            "before": size,
            "after": size,
            "gain_percent": 0,
            "before_formatted": format_size(size),
            "after_formatted": format_size(size),
            "duration": duration,
            "resolution": video_resolution,
            "codec": None,
            "optimized": False,
            "success": True,
            "index": idx,
            "timestamp": datetime.now().isoformat(),
        })
    except Exception as e:
        full_trace = traceback.format_exc()
        print(f"Erreur enregistrement téléchargement brut {raw_path}:")
        print(f"  → {str(e)}")
        print(f"  → Traceback:\n{full_trace}")

        job.stats["errors"] += 1
        job.add_progress({
            "type": "video_error",
            "original_name": raw_path.name,
            "error": str(e) or type(e).__name__,
            "success": False,
            "index": idx,
            "timestamp": datetime.now().isoformat(),
        })
    finally:
        counter += 1

    return counter


@app.get("/api/progress/{job_id}")
async def stream_progress(job_id: str):
    """
    Stream SSE de la progression d'un job
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job non trouvé")

    job = jobs[job_id]

    async def event_generator():
        """Génère les événements SSE"""
        last_index = 0

        while True:
            # Envoyer les nouveaux messages de progression
            if last_index < len(job.progress):
                for message in job.progress[last_index:]:
                    yield f"data: {json.dumps(message)}\n\n"
                last_index = len(job.progress)

            # Si le job est terminé, envoyer un événement final et arrêter
            if job.status in ["completed", "error"]:
                yield f"data: {json.dumps({'type': 'done', 'status': job.status})}\n\n"
                break

            # Attendre un peu avant de vérifier à nouveau
            await asyncio.sleep(0.2)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/api/job/{job_id}")
async def get_job_status(job_id: str):
    """Récupère le statut d'un job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job non trouvé")

    return jobs[job_id].to_dict()


@app.get("/api/download/{job_id}")
async def download_file(job_id: str):
    """
    Télécharge les images optimisées.
    - Si 1 seule image : télécharge directement le fichier
    - Si plusieurs images : télécharge un ZIP
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job non trouvé")

    job = jobs[job_id]

    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Job pas encore terminé")

    if not job.output_dir.exists():
        raise HTTPException(status_code=404, detail="Aucun fichier optimisé trouvé")

    # Récupérer tous les fichiers
    files = list(job.output_dir.iterdir())
    files = [f for f in files if f.is_file()]

    if not files:
        raise HTTPException(status_code=404, detail="Aucun fichier optimisé trouvé")

    # Si une seule image : téléchargement direct
    if len(files) == 1:
        file_path = files[0]
        return FileResponse(
            file_path,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={file_path.name}"
            }
        )

    # Si plusieurs images : créer un ZIP
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in files:
            # B6: Protection Zip Slip — s'assurer que le chemin reste dans output_dir
            safe_name = file_path.name
            if ".." in safe_name or "/" in safe_name or "\\" in safe_name:
                raise HTTPException(status_code=500, detail="Chemin de fichier invalide")
            zip_file.write(file_path, safe_name)

    zip_buffer.seek(0)

    return StreamingResponse(
        iter([zip_buffer.getvalue()]),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=optimized-images-{job_id[:8]}.zip"
        }
    )


@app.get("/api/download/{job_id}/{filename}")
async def download_single_file(job_id: str, filename: str):
    """
    Télécharge une seule image optimisée spécifique
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job non trouvé")

    job = jobs[job_id]

    if not job.output_dir.exists():
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    # B6: Protection Path Traversal — valider le nom du fichier
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nom de fichier invalide")

    file_path = job.output_dir / filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Fichier non trouvé")

    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@app.get("/api/download-zip/{job_id}")
async def download_zip_only(job_id: str):
    """
    Force le téléchargement en ZIP (même pour une seule image)
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job non trouvé")

    job = jobs[job_id]

    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Job pas encore terminé")

    if not job.output_dir.exists() or not list(job.output_dir.iterdir()):
        raise HTTPException(status_code=404, detail="Aucun fichier optimisé trouvé")

    # Créer un ZIP en mémoire
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in job.output_dir.iterdir():
            if file_path.is_file():
                # B6: Protection Zip Slip
                safe_name = file_path.name
                if ".." in safe_name or "/" in safe_name or "\\" in safe_name:
                    raise HTTPException(status_code=500, detail="Chemin de fichier invalide")
                zip_file.write(file_path, safe_name)

    zip_buffer.seek(0)

    return StreamingResponse(
        iter([zip_buffer.getvalue()]),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=optimized-images-{job_id[:8]}.zip"
        }
    )


@app.delete("/api/cleanup/{job_id}")
async def cleanup_job(job_id: str):
    """Nettoie les fichiers d'un job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job non trouvé")

    job = jobs[job_id]

    # Supprimer le dossier de sortie
    if job.output_dir.exists():
        shutil.rmtree(job.output_dir)

    # Retirer du dictionnaire
    del jobs[job_id]

    return {"status": "cleaned"}


if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*60)
    print("IMGOPT API v3.0 — Images + Vidéos")
    print("="*60)
    print(f"Formats image: {', '.join(FORMAT_CONFIG.keys()).upper()}")
    print(f"Codecs vidéo:  {', '.join(CODEC_CONFIG.keys()).upper()}")

    if not check_avif_support():
        print("AVIF non disponible (plugin non installé)")
        print("   → pip install pillow-avif-plugin")

    if not check_ffmpeg_support():
        print("FFmpeg non disponible (vidéo désactivée)")
        print("   → apt install ffmpeg")
    else:
        print("FFmpeg disponible ✓")

    print("\nServeur démarré sur: http://localhost:8000")
    print("SSE actif pour le suivi en temps réel")
    print("="*60 + "\n")

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
