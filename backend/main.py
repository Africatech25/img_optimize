#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend FastAPI pour l'optimisation d'images avec SSE
"""
import sys
import io

# Forcer l'encodage UTF-8 pour Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
from PIL import Image
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
import logging

# Importation du script optimize_images
from optimize_images import FORMAT_CONFIG, convert_image, format_size, check_avif_support, SUPPORTED_EXTENSIONS

logger = logging.getLogger(__name__)

# Configuration CORS sécurisée - Production
ALLOWED_ORIGINS = [
    "https://img-optimize.vercel.app",  # Production frontend
    "http://localhost:5173",             # Dev frontend (Vite)
    "http://localhost:3000",             # Dev frontend (alternative)
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000"
]

# Limites de sécurité
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_FILES_PER_REQUEST = 200

app = FastAPI(title="Image Optimizer API", version="2.0.0")

# CORS pour permettre les requêtes du frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

# Dossiers temporaires
TEMP_DIR = Path(tempfile.gettempdir()) / "image_optimizer"
TEMP_DIR.mkdir(exist_ok=True)

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
    # Démarrage
    cleanup_task = asyncio.create_task(cleanup_old_jobs())
    yield
    # Arrêt
    if cleanup_task:
        cleanup_task.cancel()


app = FastAPI(title="Image Optimizer API", version="2.0.0", lifespan=lifespan)


class OptimizationJob:
    """Représente un job d'optimisation"""
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.status = "pending"  # pending, processing, completed, error
        self.progress = []
        self.total_images = 0
        self.processed_images = 0

        # Créer le dossier de sortie avec vérification robuste
        self.output_dir = TEMP_DIR / job_id
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            # Vérifier que le dossier a bien été créé
            if not self.output_dir.exists():
                raise RuntimeError(f"Impossibile de créer le répertoire {self.output_dir}")
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
            "errors": 0
        }

    def add_progress(self, message: dict):
        """Ajoute un message de progression"""
        self.progress.append(message)
        if message.get("type") == "image_processed":
            self.processed_images += 1

    def to_dict(self):
        """Convertit en dictionnaire"""
        reduction = 0
        if self.stats["total_before"] > 0:
            reduction = (1 - self.stats["total_after"] / self.stats["total_before"]) * 100

        return {
            "job_id": self.job_id,
            "status": self.status,
            "total_images": self.total_images,
            "processed_images": self.processed_images,
            "stats": {**self.stats, "reduction_percent": round(reduction, 1)}
        }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "avif_available": check_avif_support(),
        "formats": list(FORMAT_CONFIG.keys())
    }


@app.get("/api/formats")
async def get_formats():
    """Retourne les formats disponibles avec leurs configurations"""
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


@app.post("/api/optimize")
async def start_optimization(
    files: List[UploadFile] = File(...),
    format: str = Form("webp"),
    quality: int = Form(None),
    prefix: str = Form("image"),
    start_number: int = Form(1),
    smoothing: int = Form(0),
    watermark_enabled: str = Form("false"),
    watermark_type: str = Form("text"),
    watermark_text: str = Form(""),
    watermark_logo: Optional[UploadFile] = File(None),
    watermark_position: str = Form("bottom-right"),
    watermark_opacity: str = Form("50"),
):
    """
    Démarre l'optimisation d'images et retourne un job_id
    pour suivre la progression via SSE
    """
    # SÉCURITÉ: Validation du nombre de fichiers
    if len(files) > MAX_FILES_PER_REQUEST:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_FILES_PER_REQUEST} fichiers autorisés (reçu: {len(files)})"
        )
    
    # Conversion des strings reçues du FormData en types appropriés
    watermark_enabled = watermark_enabled.lower() in ('true', '1', 'yes', 'on')
    try:
        watermark_opacity = int(watermark_opacity)
    except (ValueError, TypeError):
        watermark_opacity = 50
    
    # Validation du format
    if format not in FORMAT_CONFIG:
        raise HTTPException(status_code=400, detail=f"Format non supporté: {format}")
    
    # Vérification spécifique pour AVIF
    if format == "avif" and not check_avif_support():
        raise HTTPException(
            status_code=400, 
            detail="Le format AVIF n'est pas disponible sur ce serveur. Veuillez utiliser WebP ou JPEG."
        )

    config = FORMAT_CONFIG[format]

    # Qualité par défaut si non spécifiée
    if quality is None:
        quality = config["default_quality"]

    # On autorise la qualité 100 pour le mode "Signature uniquement" (sans compression)
    # même si la config format limite par défaut à 95 par exemple
    q_min, q_max = config["quality_range"]
    if quality != 100 and not (q_min <= quality <= q_max):
        raise HTTPException(
            status_code=400,
            detail=f"Qualité pour {format.upper()} doit être entre {q_min} et {q_max}"
        )

    # Validation du lissage (0 à 10 par exemple)
    if not (0 <= smoothing <= 10):
        raise HTTPException(
            status_code=400,
            detail="Le lissage doit être entre 0 et 10"
        )

    # Validation de l'opacité du watermark (0-100)
    if not (0 <= watermark_opacity <= 100):
        raise HTTPException(
            status_code=400,
            detail="L'opacité du watermark doit être entre 0 et 100"
        )

    # Création des paramètres de watermark
    watermark_params = {
        "enabled": watermark_enabled,
        "type": watermark_type,
        "text": watermark_text,
        "position": watermark_position,
        "opacity": watermark_opacity,
        "image_path": None
    }

    # Sauvegarder temporairement le logo si fourni
    logo_temp_path = None
    if watermark_enabled and watermark_type == "image" and watermark_logo:
        try:
            # SÉCURITÉ: Validation de la taille du logo
            logo_content = await watermark_logo.read(MAX_FILE_SIZE + 1)
            
            if len(logo_content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"Logo trop volumineux (max {MAX_FILE_SIZE/1024/1024:.0f}MB)"
                )
            
            logo_ext = Path(watermark_logo.filename).suffix.lower()
            if logo_ext not in SUPPORTED_EXTENSIONS:
                raise HTTPException(status_code=400, detail="Format de logo non supporté")
            
            logo_temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=logo_ext)
            logo_temp_file.write(logo_content)
            logo_temp_file.close()
            logo_temp_path = logo_temp_file.name
            watermark_params["image_path"] = logo_temp_path
        except HTTPException:
            raise  # Re-lancer les HTTPException
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erreur lors de la lecture du logo: {str(e)}")

    # IMPORTANT: Lire les fichiers IMMÉDIATEMENT avant que FastAPI les ferme
    file_data = []
    for file in files:
        try:
            # SÉCURITÉ: Validation de la taille du fichier
            content = await file.read(MAX_FILE_SIZE + 1)
            
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"Fichier '{file.filename}' trop volumineux (max {MAX_FILE_SIZE/1024/1024:.0f}MB)"
                )
            
            file_data.append({
                "filename": file.filename,
                "content": content
            })
        except HTTPException:
            raise  # Re-lancer les HTTPException
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erreur lecture fichier {file.filename}: {str(e)}")

    if not file_data:
        raise HTTPException(status_code=400, detail="Aucun fichier valide fourni")

    # Créer un nouveau job
    job_id = str(uuid.uuid4())
    job = OptimizationJob(job_id)
    job.total_images = len(file_data)
    jobs[job_id] = job

    # Lancer le traitement en arrière-plan avec les données des fichiers (pas les objets UploadFile)
    asyncio.create_task(
        process_images_async(job, file_data, format, quality, prefix, start_number, smoothing, watermark_params)
    )

    return {
        "job_id": job_id,
        "total_images": len(file_data),
        "status": "pending"
    }


async def process_images_async(
    job: OptimizationJob,
    file_data: list,
    fmt: str,
    quality: int,
    prefix: str,
    start_number: int,
    smoothing: int = 0,
    watermark_params: dict = None
):
    """
    Traite les images de manière asynchrone et met à jour la progression.
    Si plus de 10 images, procède par lots de 10.
    """
    job.status = "processing"
    config = FORMAT_CONFIG[fmt]
    ext = config["extension"]
    counter = start_number
    batch_size = 10

    job.add_progress({
        "type": "started",
        "message": f"Démarrage de l'optimisation de {job.total_images} image(s)...",
        "timestamp": datetime.now().isoformat()
    })

    # Si plus de 10 images, traiter par lots
    if job.total_images > batch_size:
        # Diviser en lots
        batches = [file_data[i:i + batch_size] for i in range(0, len(file_data), batch_size)]

        for batch_num, batch in enumerate(batches, start=1):
            job.add_progress({
                "type": "batch_started",
                "message": f"Traitement du lot {batch_num}/{len(batches)} ({len(batch)} image(s))...",
                "timestamp": datetime.now().isoformat()
            })

            # Traiter ce lot
            counter = await process_batch(job, batch, fmt, quality, prefix, counter, batch_size, smoothing, watermark_params)
    else:
        # Moins de 10 images, traiter normalement
        for idx, file_info in enumerate(file_data, start=1):
            counter = await process_single_image(job, file_info, fmt, quality, prefix, counter, idx, smoothing, watermark_params)

    # Nettoyage du logo temporaire si nécessaire
    if watermark_params and watermark_params.get("image_path"):
        try:
            os.unlink(watermark_params["image_path"])
        except:
            pass

    # Terminer le job
    job.status = "completed"
    job.add_progress({
        "type": "completed",
        "message": f"Optimisation terminée ! {job.stats['successful']}/{job.total_images} images traitées",
        "timestamp": datetime.now().isoformat(),
        "stats": job.to_dict()["stats"]
    })


async def process_batch(
    job: OptimizationJob,
    batch: list,
    fmt: str,
    quality: int,
    prefix: str,
    start_counter: int,
    batch_size: int,
    smoothing: int = 0,
    watermark_params: dict = None
) -> int:
    """Traite un lot d'images"""
    counter = start_counter
    config = FORMAT_CONFIG[fmt]
    ext = config["extension"]

    for idx, file_info in enumerate(batch, start=1):
        counter = await process_single_image(job, file_info, fmt, quality, prefix, counter, idx, smoothing, watermark_params)

    return counter


async def process_single_image(
    job: OptimizationJob,
    file_info: dict,
    fmt: str,
    quality: int,
    prefix: str,
    counter: int,
    idx: int,
    smoothing: int = 0,
    watermark_params: dict = None
) -> int:
    """Traite une seule image et retourne le compteur mis à jour"""
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

        # Optimiser l'image avec limite OBLIGATOIRE de 1 Mo et lissage optionnel
        # Appel synchrone car convert_image fait du calcul lourd
        # On utilise asyncio.to_thread pour ne pas bloquer la boucle d'événements
        before, after, status = await asyncio.to_thread(
            convert_image, 
            temp_input, 
            output_path, 
            fmt, 
            quality, 
            max_size_mo=1.0, 
            smoothing=smoothing,
            watermark_params=watermark_params
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
        import traceback
        error_detail = f"{str(e)}"
        full_trace = traceback.format_exc()
        print(f"Erreur traitement {file_info['filename']}:")
        print(f"  → {error_detail}")
        print(f"  → Traceback:\n{full_trace}")

        job.stats["errors"] += 1

        # Message d'erreur plus explicite pour l'utilisateur
        if str(e):
            error_msg = str(e)
        else:
            error_msg = f"Exception {type(e).__name__}"

        # Ajouter le type d'erreur si disponible
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

    # Petit délai pour éviter la surcharge
    await asyncio.sleep(0.1)

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
            zip_file.write(file_path, file_path.name)

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
                zip_file.write(file_path, file_path.name)

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
    print("IMAGE OPTIMIZER API v2.0")
    print("="*60)
    print(f"Formats disponibles: {', '.join(FORMAT_CONFIG.keys()).upper()}")

    if not check_avif_support():
        print("AVIF non disponible (plugin non installe)")
        print("   Pour activer AVIF: pip install pillow-avif-plugin")

    print("\nServeur demarre sur: http://localhost:8000")
    print("SSE active pour le suivi en temps reel")
    print("="*60 + "\n")

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
