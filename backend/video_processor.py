#!/usr/bin/env python3
"""
video_processor.py
------------------
Moteur d'optimisation vidéo basé sur FFmpeg.

Supporte : MP4, WebM, AVI, MOV, MKV
Codecs : H.264, H.265/HEVC, VP9, AV1

Usage CLI :
    python video_processor.py --input video.mp4 --codec h264 --quality 28
    python video_processor.py --input video.mov --codec h265 --resolution 720p --max-size 10

Usage API :
    from video_processor import convert_video, get_video_info, check_ffmpeg_support
"""

import subprocess
import shutil
import json
from pathlib import Path
from typing import Optional

# Extensions vidéo supportées en entrée
VIDEO_EXTENSIONS = {".mp4", ".webm", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".m4v", ".3gp"}

# Codecs supportés
CODEC_CONFIG = {
    "h264": {
        "encoder": "libx264",
        "description": "H.264 — Universel, compatible partout (98% navigateurs)",
        "crf_range": (18, 51),
        "default_crf": 28,
        "extension": ".mp4",
        "extra_args": ["-preset", "medium", "-pix_fmt", "yuv420p"],
    },
    "h265": {
        "encoder": "libx265",
        "description": "H.265/HEVC — -50% vs H.264, qualité supérieure",
        "crf_range": (18, 51),
        "default_crf": 30,
        "extension": ".mp4",
        "extra_args": ["-preset", "medium", "-pix_fmt", "yuv420p", "-tag:v", "hvc1"],
    },
    "vp9": {
        "encoder": "libvpx-vp9",
        "description": "VP9 — WebM natif, excellent pour le web",
        "crf_range": (15, 51),
        "default_crf": 30,
        "extension": ".webm",
        "extra_args": ["-speed", "2", "-tile-columns", "2", "-row-mt", "1"],
    },
    "av1": {
        "encoder": "libaom-av1",
        "description": "AV1 — Ultra-compact, -30% vs VP9, futur du web",
        "crf_range": (15, 63),
        "default_crf": 35,
        "extension": ".webm",
        "extra_args": ["-cpu-used", "6", "-tile-columns", "2", "-row-mt", "1", "-tiles", "2x2"],
    },
}

# Résolutions prédéfinies
RESOLUTION_MAP = {
    "4k": (3840, 2160),
    "1080p": (1920, 1080),
    "720p": (1280, 720),
    "480p": (854, 480),
    "360p": (640, 360),
    "original": None,
}


def check_ffmpeg_support() -> bool:
    """Vérifie si FFmpeg est disponible sur le système."""
    return shutil.which("ffmpeg") is not None


def get_video_info(input_path: Path) -> dict:
    """
    Extrait les métadonnées d'une vidéo via ffprobe.

    Returns:
        dict avec : width, height, duration, fps, codec, size_bytes, bitrate
    """
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(input_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    if result.returncode != 0:
        raise RuntimeError(f"ffprobe échoué: {result.stderr}")

    data = json.loads(result.stdout)

    # Trouver le stream vidéo
    video_stream = None
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            video_stream = stream
            break

    if not video_stream:
        raise ValueError("Aucun stream vidéo trouvé dans le fichier")

    # Extraire le FPS
    fps_str = video_stream.get("r_frame_rate", "30/1")
    if "/" in fps_str:
        num, den = fps_str.split("/")
        fps = round(int(num) / int(den), 2) if int(den) > 0 else 30.0
    else:
        fps = float(fps_str)

    # Extraire la durée
    duration = float(data.get("format", {}).get("duration", 0))

    # Extraire le bitrate
    bitrate = int(data.get("format", {}).get("bit_rate", 0))

    # Taille du fichier
    size_bytes = input_path.stat().st_size

    return {
        "width": int(video_stream.get("width", 0)),
        "height": int(video_stream.get("height", 0)),
        "duration": round(duration, 2),
        "fps": fps,
        "codec": video_stream.get("codec_name", "unknown"),
        "size_bytes": size_bytes,
        "bitrate": bitrate,
    }


def format_size(size_bytes: int) -> str:
    """Formate une taille en Ko ou Mo."""
    if size_bytes >= 1_000_000:
        return f"{size_bytes / 1_000_000:.1f} Mo"
    return f"{size_bytes / 1_000:.0f} Ko"


def format_duration(seconds: float) -> str:
    """Formate une durée en MM:SS."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def _build_ffmpeg_command(
    input_path: Path,
    output_path: Path,
    codec: str,
    crf: int,
    resolution: Optional[str] = None,
    max_fps: Optional[int] = None,
    max_size_bytes: int = 0,
) -> list:
    """Construit la commande FFmpeg pour l'optimisation."""
    config = CODEC_CONFIG[codec]

    cmd = ["ffmpeg", "-y", "-i", str(input_path)]

    # Filtres vidéo
    filters = []

    # Redimensionnement
    if resolution and resolution in RESOLUTION_MAP and RESOLUTION_MAP[resolution] is not None:
        target_w, target_h = RESOLUTION_MAP[resolution]
        # Scale en gardant le ratio
        filters.append(f"scale='min({target_w},iw)':'min({target_h},ih)':force_original_aspect_ratio=decrease")
        # Forcer dimensions paires pour compatibilité codec
        filters.append("pad=ceil(iw/2)*2:ceil(ih/2)*2:(ow-iw)/2:(oh-ih)/2")

    # Forcer le pixel format pour tous les codecs
    filters.append("format=yuv420p")

    # Limite FPS
    if max_fps and max_fps > 0:
        filters.append(f"fps=min({max_fps},source_fps)")

    # Appliquer les filtres
    if filters:
        cmd.extend(["-vf", ",".join(filters)])

    # Codec et qualité
    cmd.extend(["-c:v", config["encoder"]])
    cmd.extend(["-crf", str(crf)])

    # Arguments supplémentaires du codec
    cmd.extend(config["extra_args"])

    # Pas de double encodage audio (copier l'audio existant)
    # Pour WebM (VP9/AV1), l'audio doit être en Opus
    if codec in ("vp9", "av1"):
        cmd.extend(["-c:a", "libopus"])
    else:
        cmd.extend(["-c:a", "copy"])

    # Limite de taille (via bitrate max si spécifié)
    if max_size_bytes > 0:
        # Calculer le bitrate max basé sur la durée
        info = get_video_info(input_path)
        if info["duration"] > 0:
            # Bitrate total en bits/s
            max_bitrate = int((max_size_bytes * 8) / info["duration"])
            # Réserver 10% pour l'audio
            video_bitrate = int(max_bitrate * 0.9)
            cmd.extend(["-maxrate", f"{video_bitrate}", "-bufsize", f"{video_bitrate * 2}"])

    # Sortie
    cmd.append(str(output_path))

    return cmd


def convert_video(
    input_path: Path,
    output_path: Path,
    codec: str = "h264",
    quality: int = 28,
    resolution: Optional[str] = None,
    max_fps: Optional[int] = None,
    max_size_mo: float = 0,
) -> tuple[int, int, str]:
    """
    Convertit et optimise une vidéo.

    Args:
        input_path: Chemin du fichier source
        output_path: Chemin du fichier de sortie
        codec: Codec cible (h264, h265, vp9, av1)
        quality: Niveau CRF (plus bas = meilleure qualité)
        resolution: Résolution cible (4k, 1080p, 720p, 480p, original)
        max_fps: Limite FPS (None = original)
        max_size_mo: Taille maximale en Mo (0 = pas de limite)

    Retourne:
        (taille_originale, taille_finale, status)
        status: 'ok' | 'optimized' | 'failed'
    """
    if not check_ffmpeg_support():
        raise RuntimeError("FFmpeg n'est pas installé sur ce serveur")

    if codec not in CODEC_CONFIG:
        raise ValueError(f"Codec non supporté: {codec}. Disponibles: {', '.join(CODEC_CONFIG.keys())}")

    config = CODEC_CONFIG[codec]
    original_size = input_path.stat().st_size
    max_size_bytes = int(max_size_mo * 1_000_000) if max_size_mo > 0 else 0

    # Valider la plage CRF
    crf_min, crf_max = config["crf_range"]
    crf = max(crf_min, min(crf_max, quality))

    # S'assurer que le dossier de sortie existe
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Construire et exécuter la commande FFmpeg
    cmd = _build_ffmpeg_command(
        input_path, output_path, codec, crf, resolution, max_fps, max_size_bytes
    )

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,  # 10 minutes max par vidéo
    )

    if result.returncode != 0:
        # Extraire le message d'erreur utile
        error_lines = [l for l in result.stderr.split("\n") if l.strip() and not l.startswith("frame=")]
        error_msg = "\n".join(error_lines[-5:]) if error_lines else result.stderr[:500]
        raise RuntimeError(f"FFmpeg a échoué:\n{error_msg}")

    # Vérifier la taille de sortie
    if not output_path.exists():
        raise RuntimeError("Le fichier de sortie n'a pas été créé par FFmpeg")

    final_size = output_path.stat().st_size

    # Si on dépasse la limite, réessayer avec un CRF plus haut
    if max_size_bytes > 0 and final_size > max_size_bytes:
        # Tenter avec un CRF plus agressif (max 2 essais supplémentaires)
        for attempt in range(2):
            crf = min(crf_max, crf + 5)
            cmd = _build_ffmpeg_command(
                input_path, output_path, codec, crf, resolution, max_fps, max_size_bytes
            )
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode == 0 and output_path.exists():
                final_size = output_path.stat().st_size
                if final_size <= max_size_bytes:
                    break

    # Déterminer le status
    if max_size_bytes > 0 and final_size > max_size_bytes:
        status = "failed"
    elif final_size < original_size * 0.95:  # > 5% de réduction
        status = "optimized"
    else:
        status = "ok"

    return original_size, final_size, status


def get_supported_formats() -> dict:
    """Retourne les formats et codecs disponibles."""
    return {
        codec: {
            "description": config["description"],
            "encoder": config["encoder"],
            "crf_range": config["crf_range"],
            "default_crf": config["default_crf"],
            "extension": config["extension"],
        }
        for codec, config in CODEC_CONFIG.items()
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Optimise une vidéo avec FFmpeg")
    parser.add_argument("--input", "-i", required=True, help="Fichier vidéo source")
    parser.add_argument("--output", "-o", help="Fichier de sortie (défaut: auto)")
    parser.add_argument("--codec", "-c", default="h264", choices=list(CODEC_CONFIG.keys()),
                        help="Codec cible (défaut: h264)")
    parser.add_argument("--quality", "-q", type=int, default=None,
                        help="Niveau CRF (défaut selon codec)")
    parser.add_argument("--resolution", "-r", default=None,
                        choices=list(RESOLUTION_MAP.keys()),
                        help="Résolution cible")
    parser.add_argument("--max-fps", type=int, default=None,
                        help="FPS maximum")
    parser.add_argument("--max-size", "-m", type=float, default=0,
                        help="Taille max en Mo (0 = pas de limite)")

    args = parser.parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Erreur: Fichier introuvable: {input_path}")
        exit(1)

    config = CODEC_CONFIG[args.codec]
    quality = args.quality if args.quality is not None else config["default_crf"]

    output_path = Path(args.output) if args.output else input_path.with_suffix(config["extension"])

    print(f"Optimisation de: {input_path.name}")
    print(f"  Codec: {args.codec.upper()}")
    print(f"  Qualité (CRF): {quality}")
    if args.resolution:
        print(f"  Résolution: {args.resolution}")
    if args.max_fps:
        print(f"  FPS max: {args.max_fps}")
    if args.max_size > 0:
        print(f"  Taille max: {args.max_size} Mo")

    try:
        info = get_video_info(input_path)
        print(f"\nInfos vidéo:")
        print(f"  Résolution: {info['width']}x{info['height']}")
        print(f"  Durée: {format_duration(info['duration'])}")
        print(f"  FPS: {info['fps']}")
        print(f"  Codec: {info['codec']}")
        print(f"  Taille: {format_size(info['size_bytes'])}")

        before, after, status = convert_video(
            input_path, output_path, args.codec, quality,
            args.resolution, args.max_fps, args.max_size
        )

        gain_pct = (1 - after / before) * 100 if before > 0 else 0
        print(f"\nRésultat:")
        print(f"  Avant: {format_size(before)}")
        print(f"  Après: {format_size(after)}")
        print(f"  Gain: {gain_pct:.1f}%")
        print(f"  Status: {status}")
        print(f"  Fichier: {output_path}")

    except Exception as e:
        print(f"\nErreur: {e}")
        exit(1)
