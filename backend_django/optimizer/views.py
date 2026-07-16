import json
import os
import re
import shutil
import tempfile
import threading
import time
import traceback
import uuid
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, HttpResponse, JsonResponse, StreamingHttpResponse
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from .image_engine import (
    FORMAT_CONFIG,
    SUPPORTED_EXTENSIONS,
    check_avif_support,
    convert_image,
    format_size,
)
from .models import OptimizationJob
from .video_engine import (
    CODEC_CONFIG,
    VIDEO_EXTENSIONS,
    check_ffmpeg_support,
    convert_video,
    format_duration,
    get_video_info,
)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}
PREFIX_REGEX = re.compile(r"^[a-zA-Z0-9_-]{1,100}$")
VALID_MODES = {"optimize_image", "optimize_video", "sign", "smooth"}


def is_video_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in VIDEO_EXTENSIONS


def is_image_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in IMAGE_EXTENSIONS


def resolve_max_quality_format(filename: str) -> tuple[str, int]:
    """Détermine format + qualité maximale en conservant le format d'origine.
    Utilisé par les modes 'sign' et 'smooth' (pas de format/qualité demandés)."""
    ext = Path(filename).suffix.lower()
    if ext in (".jpg", ".jpeg"):
        fmt = "jpeg"
    elif ext == ".webp":
        fmt = "webp"
    else:
        fmt = "png"
    return fmt, FORMAT_CONFIG[fmt]["quality_range"][1]


# ==================== ENDPOINTS SIMPLES ====================


@api_view(["GET"])
def health_check(request):
    return Response({
        "status": "ok",
        "avif_available": check_avif_support(),
        "ffmpeg_available": check_ffmpeg_support(),
        "image_formats": list(FORMAT_CONFIG.keys()),
        "video_codecs": list(CODEC_CONFIG.keys()),
    })


@api_view(["GET"])
def get_formats(request):
    avif_ok = check_avif_support()
    return Response({
        fmt: {
            "description": config.get("description", ""),
            "default_quality": config["default_quality"],
            "quality_range": config["quality_range"],
            "available": True if fmt != "avif" else avif_ok,
        }
        for fmt, config in FORMAT_CONFIG.items()
    })


@api_view(["GET"])
def get_video_formats(request):
    ffmpeg_ok = check_ffmpeg_support()
    return Response({
        codec: {
            "description": config["description"],
            "encoder": config["encoder"],
            "default_crf": config["default_crf"],
            "crf_range": config["crf_range"],
            "extension": config["extension"],
            "available": ffmpeg_ok,
        }
        for codec, config in CODEC_CONFIG.items()
    })


# ==================== DEMARRAGE D'UN JOB ====================


class OptimizeThrottle(ScopedRateThrottle):
    scope = "optimize"


@api_view(["POST"])
@throttle_classes([OptimizeThrottle])
def start_optimization(request):
    """
    Démarre une action (optimisation ou traitement) et retourne un job_id
    pour suivre la progression via SSE (/api/progress/<job_id>).

    Le paramètre `mode` détermine l'action et les paramètres attendus :
    - optimize_image : format + quality, images uniquement
    - optimize_video : codec + video_quality + resolution + max_fps, vidéos uniquement
    - sign : watermark_type/text/logo/position/opacity, images uniquement, qualité maximale
    - smooth : smoothing, images uniquement, qualité maximale
    """
    mode = request.data.get("mode", "optimize_image")
    if mode not in VALID_MODES:
        return Response({"detail": f"Mode non supporté: {mode}"}, status=400)

    files = request.FILES.getlist("files")
    if not files:
        return Response({"detail": "Aucun fichier valide fourni"}, status=400)

    image_files, video_files = [], []
    for f in files:
        if is_video_file(f.name):
            video_files.append(f)
        elif is_image_file(f.name):
            image_files.append(f)
        else:
            return Response(
                {"detail": f"Format non supporté: {Path(f.name).suffix}. Utilisez des images ou des vidéos."},
                status=400,
            )

    if mode == "optimize_video" and image_files:
        return Response({"detail": "Ce mode n'accepte que des vidéos."}, status=400)
    if mode in ("optimize_image", "sign", "smooth") and video_files:
        return Response({"detail": "Ce mode n'accepte que des images."}, status=400)

    prefix = request.data.get("prefix", "image")
    if not PREFIX_REGEX.match(prefix):
        return Response(
            {"detail": "Prefixe invalide. Utilisez uniquement lettres, chiffres, tirets ou underscores (1-100 car.)"},
            status=400,
        )

    active_jobs = OptimizationJob.objects.filter(status__in=["pending", "processing"]).count()
    if active_jobs >= settings.MAX_CONCURRENT_JOBS:
        return Response(
            {"detail": f"Trop de jobs en cours ({active_jobs}/{settings.MAX_CONCURRENT_JOBS}). Reessayez dans quelques secondes."},
            status=429,
        )

    try:
        start_number = int(request.data.get("start_number", 1))
    except (TypeError, ValueError):
        start_number = 1

    img_format_val = None
    img_quality_val = None
    max_size_mo = 0
    smoothing_val = 0
    watermark_params = None

    if mode == "optimize_image":
        img_format = request.data.get("format", "webp")
        if img_format not in FORMAT_CONFIG:
            return Response({"detail": f"Format image non supporté: {img_format}"}, status=400)
        if img_format == "avif" and not check_avif_support():
            return Response({"detail": "Le format AVIF n'est pas disponible sur ce serveur."}, status=400)

        config = FORMAT_CONFIG[img_format]
        quality_raw = request.data.get("quality")
        img_quality = int(quality_raw) if quality_raw not in (None, "") else config["default_quality"]
        q_min, q_max = config["quality_range"]
        if not (q_min <= img_quality <= q_max):
            return Response(
                {"detail": f"Qualité pour {img_format.upper()} doit être entre {q_min} et {q_max}"},
                status=400,
            )
        img_format_val = img_format
        img_quality_val = img_quality
        max_size_mo = 1.0

    elif mode == "smooth":
        try:
            smoothing = int(request.data.get("smoothing", 0))
        except (TypeError, ValueError):
            smoothing = 0
        if not (1 <= smoothing <= 10):
            return Response({"detail": "Le lissage doit être entre 1 et 10"}, status=400)
        smoothing_val = smoothing

    elif mode == "sign":
        watermark_type = request.data.get("watermark_type", "text")
        watermark_text = request.data.get("watermark_text", "")
        watermark_position = request.data.get("watermark_position", "bottom-right")
        watermark_logo = request.FILES.get("watermark_logo")

        try:
            watermark_opacity_val = int(request.data.get("watermark_opacity", 50))
        except (TypeError, ValueError):
            watermark_opacity_val = 50
        if not (0 <= watermark_opacity_val <= 100):
            return Response({"detail": "L'opacité de la signature doit être entre 0 et 100"}, status=400)
        if watermark_type == "text" and not watermark_text.strip():
            return Response({"detail": "Le texte de la signature est requis"}, status=400)
        if watermark_type == "image" and not watermark_logo:
            return Response({"detail": "Un logo est requis pour ce type de signature"}, status=400)

        watermark_params = {
            "enabled": True,
            "type": watermark_type,
            "text": watermark_text,
            "position": watermark_position,
            "opacity": watermark_opacity_val,
            "image_path": None,
        }

        if watermark_type == "image" and watermark_logo:
            if watermark_logo.size > settings.MAX_UPLOAD_SIZE_BYTES:
                return Response(
                    {"detail": f"Logo trop volumineux (max {settings.MAX_UPLOAD_SIZE_MB}MB)"},
                    status=413,
                )
            logo_ext = Path(watermark_logo.name).suffix.lower()
            if logo_ext not in SUPPORTED_EXTENSIONS:
                return Response({"detail": "Format de logo non supporté"}, status=400)

            logo_temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=logo_ext, dir=settings.TEMP_DIR)
            for chunk in watermark_logo.chunks():
                logo_temp_file.write(chunk)
            logo_temp_file.close()
            watermark_params["image_path"] = logo_temp_file.name

    codec = request.data.get("codec", "h264")
    video_quality = None
    resolution = request.data.get("resolution")
    max_fps = request.data.get("max_fps")
    max_fps = int(max_fps) if max_fps not in (None, "") else None

    if video_files:
        if codec not in CODEC_CONFIG:
            return Response({"detail": f"Codec vidéo non supporté: {codec}"}, status=400)
        if not check_ffmpeg_support():
            return Response(
                {"detail": "FFmpeg n'est pas installé sur ce serveur. L'optimisation vidéo n'est pas disponible."},
                status=400,
            )
        v_config = CODEC_CONFIG[codec]
        vq_raw = request.data.get("video_quality")
        video_quality = int(vq_raw) if vq_raw not in (None, "") else v_config["default_crf"]
        v_min, v_max = v_config["crf_range"]
        if not (v_min <= video_quality <= v_max):
            return Response(
                {"detail": f"Qualité vidéo (CRF) pour {codec.upper()} doit être entre {v_min} et {v_max}"},
                status=400,
            )

    # Lire tous les fichiers IMMÉDIATEMENT (en mémoire, comme FastAPI)
    file_data = []
    for f in (image_files + video_files):
        content = f.read()
        if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
            return Response(
                {"detail": f"Fichier {f.name} trop volumineux ({len(content) // (1024*1024)} MB). Maximum : {settings.MAX_UPLOAD_SIZE_MB} MB."},
                status=413,
            )
        file_data.append({"filename": f.name, "content": content, "is_video": is_video_file(f.name)})

    if not file_data:
        return Response({"detail": "Aucun fichier valide fourni"}, status=400)

    job_id = uuid.uuid4()
    output_dir = settings.TEMP_DIR / str(job_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    job = OptimizationJob.objects.create(
        job_id=job_id,
        mode=mode,
        user=request.user if request.user.is_authenticated else None,
        total_files=len(file_data),
        total_images=len(image_files),
        total_videos=len(video_files),
        output_dir=str(output_dir.resolve()),
    )

    thread = threading.Thread(
        target=_process_job,
        args=(
            job.job_id, file_data, img_format_val, img_quality_val,
            codec, video_quality, resolution, max_fps,
            prefix, start_number, smoothing_val, watermark_params, max_size_mo,
        ),
        daemon=True,
    )
    thread.start()

    return Response({
        "job_id": str(job.job_id),
        "total_files": len(file_data),
        "total_images": len(image_files),
        "total_videos": len(video_files),
        "status": "pending",
    })


# ==================== TRAITEMENT EN ARRIERE-PLAN (thread) ====================


def _process_job(
    job_id, file_data, img_format, img_quality,
    video_codec, video_quality, resolution, max_fps,
    prefix, start_number, smoothing, watermark_params, max_size_mo,
):
    job = OptimizationJob.objects.get(job_id=job_id)
    job.status = "processing"
    job.save(update_fields=["status"])

    counter = start_number
    parts = []
    if job.total_images > 0:
        parts.append(f"{job.total_images} image(s)")
    if job.total_videos > 0:
        parts.append(f"{job.total_videos} vidéo(s)")

    job.add_progress({
        "type": "started",
        "message": f"Démarrage de l'optimisation de {', '.join(parts)}...",
        "timestamp": datetime.now().isoformat(),
    })

    for idx, file_info in enumerate(file_data, start=1):
        if file_info["is_video"]:
            counter = _process_single_video(
                job, file_info, video_codec, video_quality, resolution, max_fps, prefix, counter, idx
            )
        else:
            counter = _process_single_image(
                job, file_info, img_format, img_quality, prefix, counter, idx,
                smoothing, watermark_params, max_size_mo,
            )

    if watermark_params and watermark_params.get("image_path"):
        try:
            os.unlink(watermark_params["image_path"])
        except OSError:
            pass

    job.refresh_from_db()
    job.status = "completed"
    job.save(update_fields=["status"])
    job.add_progress({
        "type": "completed",
        "message": f"Optimisation terminée ! {job.stats.get('successful', 0)}/{job.total_files} fichiers traités",
        "timestamp": datetime.now().isoformat(),
        "stats": job.to_dict()["stats"],
    })


def _process_single_image(job, file_info, fmt, quality, prefix, counter, idx, smoothing, watermark_params, max_size_mo):
    if fmt is None:
        fmt, quality = resolve_max_quality_format(file_info["filename"])

    config = FORMAT_CONFIG[fmt]
    ext = config["extension"]
    temp_input = None

    try:
        temp_input = settings.TEMP_DIR / f"{uuid.uuid4()}_{file_info['filename']}"
        with temp_input.open("wb") as buffer:
            buffer.write(file_info["content"])

        output_filename = f"{prefix}-{counter:02d}{ext}"
        output_path = Path(job.output_dir) / output_filename

        before, after, status = convert_image(
            temp_input, output_path, fmt, quality,
            max_size_mo=max_size_mo, smoothing=smoothing, watermark_params=watermark_params,
        )

        gain_pct = (1 - after / before) * 100 if before > 0 else 0

        job.refresh_from_db()
        job.stats["total_before"] = job.stats.get("total_before", 0) + before
        job.stats["total_after"] = job.stats.get("total_after", 0) + after
        job.stats["successful"] = job.stats.get("successful", 0) + 1
        job.save(update_fields=["stats"])

        job.add_progress({
            "type": "image_processed",
            "original_name": file_info["filename"],
            "optimized_name": output_filename,
            "before": before,
            "after": after,
            "gain_percent": round(gain_pct, 1),
            "before_formatted": format_size(before),
            "after_formatted": format_size(after),
            "success": True,
            "index": idx,
            "timestamp": datetime.now().isoformat(),
        })

    except Exception as e:
        print(f"Erreur traitement {file_info['filename']}:\n  -> {e}\n  -> {traceback.format_exc()}")

        job.refresh_from_db()
        job.stats["errors"] = job.stats.get("errors", 0) + 1
        job.save(update_fields=["stats"])

        error_type = type(e).__name__
        error_msg = str(e) or f"Exception {error_type}"
        if error_type != "Exception":
            error_msg = f"[{error_type}] {error_msg}"

        job.add_progress({
            "type": "image_error",
            "original_name": file_info["filename"],
            "error": error_msg,
            "success": False,
            "index": idx,
            "timestamp": datetime.now().isoformat(),
        })

    finally:
        counter += 1
        if temp_input and temp_input.exists():
            temp_input.unlink()

    return counter


def _process_single_video(job, file_info, codec, quality, resolution, max_fps, prefix, counter, idx):
    config = CODEC_CONFIG[codec]
    ext = config["extension"]
    temp_input = None

    try:
        temp_input = settings.TEMP_DIR / f"{uuid.uuid4()}_{file_info['filename']}"
        with temp_input.open("wb") as buffer:
            buffer.write(file_info["content"])

        output_filename = f"{prefix}-{counter:02d}{ext}"
        output_path = Path(job.output_dir) / output_filename

        info = get_video_info(temp_input)
        before, after, status = convert_video(
            temp_input, output_path, codec, quality, resolution, max_fps, max_size_mo=0
        )

        gain_pct = (1 - after / before) * 100 if before > 0 else 0

        job.refresh_from_db()
        job.stats["total_before"] = job.stats.get("total_before", 0) + before
        job.stats["total_after"] = job.stats.get("total_after", 0) + after
        job.stats["successful"] = job.stats.get("successful", 0) + 1
        job.save(update_fields=["stats"])

        job.add_progress({
            "type": "video_processed",
            "original_name": file_info["filename"],
            "optimized_name": output_filename,
            "before": before,
            "after": after,
            "gain_percent": round(gain_pct, 1),
            "before_formatted": format_size(before),
            "after_formatted": format_size(after),
            "duration": format_duration(info["duration"]),
            "resolution": f"{info['width']}x{info['height']}",
            "codec": codec,
            "success": True,
            "index": idx,
            "timestamp": datetime.now().isoformat(),
        })

    except Exception as e:
        print(f"Erreur traitement vidéo {file_info['filename']}:\n  -> {e}\n  -> {traceback.format_exc()}")

        job.refresh_from_db()
        job.stats["errors"] = job.stats.get("errors", 0) + 1
        job.save(update_fields=["stats"])

        error_type = type(e).__name__
        error_msg = str(e) or f"Exception {error_type}"
        if error_type != "Exception":
            error_msg = f"[{error_type}] {error_msg}"

        job.add_progress({
            "type": "video_error",
            "original_name": file_info["filename"],
            "error": error_msg,
            "success": False,
            "index": idx,
            "timestamp": datetime.now().isoformat(),
        })

    finally:
        counter += 1
        if temp_input and temp_input.exists():
            temp_input.unlink()

    return counter


# ==================== SUIVI / TELECHARGEMENT ====================


def stream_progress(request, job_id):
    """Stream SSE de la progression d'un job (polling de la DB toutes les
    0.2s) — le frontend continue de consommer ceci via EventSource, comme
    avec le backend FastAPI d'origine, sans aucun changement côté client.

    Vue Django "brute" (pas de @api_view/DRF) : DRF fait de la négociation
    de contenu sur l'en-tête Accept, et le navigateur envoie
    "Accept: text/event-stream" pour EventSource, que DRF ne sait pas
    négocier (406 Not Acceptable). On bypass donc DRF ici.
    """
    try:
        OptimizationJob.objects.get(job_id=job_id)
    except OptimizationJob.DoesNotExist:
        return JsonResponse({"detail": "Job non trouvé"}, status=404)

    def event_generator():
        last_index = 0
        while True:
            job = OptimizationJob.objects.get(job_id=job_id)
            if last_index < len(job.progress):
                for message in job.progress[last_index:]:
                    yield f"data: {json.dumps(message)}\n\n"
                last_index = len(job.progress)

            if job.status in ("completed", "error"):
                yield f"data: {json.dumps({'type': 'done', 'status': job.status})}\n\n"
                break

            time.sleep(0.2)

    response = StreamingHttpResponse(event_generator(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


@api_view(["GET"])
def get_job_status(request, job_id):
    try:
        job = OptimizationJob.objects.get(job_id=job_id)
    except OptimizationJob.DoesNotExist:
        return Response({"detail": "Job non trouvé"}, status=404)
    return Response(job.to_dict())


def _get_output_files(job):
    output_dir = Path(job.output_dir)
    if not output_dir.exists():
        return []
    return [f for f in output_dir.iterdir() if f.is_file()]


@api_view(["GET"])
def download_file(request, job_id):
    try:
        job = OptimizationJob.objects.get(job_id=job_id)
    except OptimizationJob.DoesNotExist:
        return Response({"detail": "Job non trouvé"}, status=404)

    if job.status != "completed":
        return Response({"detail": "Job pas encore terminé"}, status=400)

    files = _get_output_files(job)
    if not files:
        return Response({"detail": "Aucun fichier optimisé trouvé"}, status=404)

    if len(files) == 1:
        file_path = files[0]
        response = FileResponse(open(file_path, "rb"), content_type="application/octet-stream")
        response["Content-Disposition"] = f"attachment; filename={file_path.name}"
        return response

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in files:
            safe_name = file_path.name
            if ".." in safe_name or "/" in safe_name or "\\" in safe_name:
                return Response({"detail": "Chemin de fichier invalide"}, status=500)
            zip_file.write(file_path, safe_name)
    zip_buffer.seek(0)

    response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = f"attachment; filename=optimized-images-{str(job_id)[:8]}.zip"
    return response


@api_view(["GET"])
def download_single_file(request, job_id, filename):
    try:
        job = OptimizationJob.objects.get(job_id=job_id)
    except OptimizationJob.DoesNotExist:
        return Response({"detail": "Job non trouvé"}, status=404)

    if ".." in filename or "/" in filename or "\\" in filename:
        return Response({"detail": "Nom de fichier invalide"}, status=400)

    file_path = Path(job.output_dir) / filename
    if not file_path.exists() or not file_path.is_file():
        return Response({"detail": "Fichier non trouvé"}, status=404)

    response = FileResponse(open(file_path, "rb"), content_type="application/octet-stream")
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


@api_view(["GET"])
def download_zip_only(request, job_id):
    try:
        job = OptimizationJob.objects.get(job_id=job_id)
    except OptimizationJob.DoesNotExist:
        return Response({"detail": "Job non trouvé"}, status=404)

    if job.status != "completed":
        return Response({"detail": "Job pas encore terminé"}, status=400)

    files = _get_output_files(job)
    if not files:
        return Response({"detail": "Aucun fichier optimisé trouvé"}, status=404)

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in files:
            safe_name = file_path.name
            if ".." in safe_name or "/" in safe_name or "\\" in safe_name:
                return Response({"detail": "Chemin de fichier invalide"}, status=500)
            zip_file.write(file_path, safe_name)
    zip_buffer.seek(0)

    response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = f"attachment; filename=optimized-images-{str(job_id)[:8]}.zip"
    return response


@api_view(["DELETE"])
def cleanup_job(request, job_id):
    try:
        job = OptimizationJob.objects.get(job_id=job_id)
    except OptimizationJob.DoesNotExist:
        return Response({"detail": "Job non trouvé"}, status=404)

    output_dir = Path(job.output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    job.delete()

    return Response({"status": "cleaned"})
