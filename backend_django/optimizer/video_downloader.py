#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
video_downloader.py
-------------------
Téléchargement de vidéos depuis des plateformes externes (YouTube, TikTok,
Facebook, Vimeo, Twitch, Instagram, X, ...) via yt-dlp.

Le binaire `yt-dlp` est invoqué en subprocess (et non via l'API Python) pour
rester isolé et facilement mis à jour (`pip install -U yt-dlp`).

Usage API :
    from video_downloader import download_video, check_ytdlp_support, get_supported_platforms
"""

import ipaddress
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Configuration des plateformes supportées
# ---------------------------------------------------------------------------

# Domaines publics autorisés (clé = domaine, valeur = libellé affiché).
# Les sous-domaines (ex: m.youtube.com, www.facebook.com) sont acceptés.
DEFAULT_SUPPORTED_DOMAINS = {
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "tiktok.com": "TikTok",
    "vm.tiktok.com": "TikTok",
    "facebook.com": "Facebook",
    "fb.watch": "Facebook",
    "instagram.com": "Instagram",
    "vimeo.com": "Vimeo",
    "twitter.com": "X (Twitter)",
    "x.com": "X (Twitter)",
    "twitch.tv": "Twitch",
}

# Plages d'adresses réservées / internes interdites (protection SSRF).
_FORBIDDEN_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("0.0.0.0/8"),
]

# Taille max des cookies fournis par l'utilisateur (50 Ko).
MAX_COOKIES_BYTES = 50 * 1024

# Timeout de téléchargement (secondes).
DOWNLOAD_TIMEOUT = 600


def check_ytdlp_support() -> bool:
    """Vérifie si le binaire yt-dlp est disponible sur le système."""
    return shutil.which("yt-dlp") is not None


def get_supported_domains() -> dict:
    """
    Retourne le dictionnaire des domaines supportés.
    Peut être surchargé via la variable d'env DOWNLOAD_ALLOWED_DOMAINS
    (séparée par virgules). Les libellés non connus deviennent le domaine.
    """
    import os
    override = os.environ.get("DOWNLOAD_ALLOWED_DOMAINS", "").strip()
    if not override:
        return dict(DEFAULT_SUPPORTED_DOMAINS)

    domains = {}
    for raw in override.split(","):
        d = raw.strip().lower()
        if d:
            domains[d] = DEFAULT_SUPPORTED_DOMAINS.get(d, d)
    return domains


def get_supported_platforms() -> list:
    """Retourne la liste des plateformes (libellés uniques) supportées."""
    return sorted(set(get_supported_domains().values()))


def _is_host_allowed(host: str) -> bool:
    """Vérifie que le host est dans l'allowlist (domaine ou sous-domaine)."""
    host = host.lower().lstrip(".")
    domains = get_supported_domains()
    if host in domains:
        return True
    # Accepter les sous-domaines (m.youtube.com, www.facebook.com, ...)
    return any(host == d or host.endswith("." + d) for d in domains)


def validate_url(url: str) -> str:
    """
    Valide une URL de téléchargement.

    Retourne le host (normalisé) si valide.
    Lève ValueError si l'URL est invalide, non http(s), pointe vers une
    IP interne/réservée (SSRF) ou une plateforme non supportée.
    """
    if not url or not url.strip():
        raise ValueError("URL vide")

    if not re.match(r"^https?://", url, re.IGNORECASE):
        raise ValueError("URL invalide (http/https requis)")

    try:
        parsed = urlparse(url)
    except Exception:
        raise ValueError("URL invalide")

    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError("Hôte inconnu dans l'URL")

    # Protection SSRF : refuser les adresses IP réservées / internes.
    try:
        ip = ipaddress.ip_address(host)
        for net in _FORBIDDEN_NETWORKS:
            if ip in net:
                raise ValueError("URL non autorisée (adresse réservée)")
    except ValueError:
        # Ce n'est pas une IP littérale : on continue (c'est un nom d'hôte).
        pass

    if not _is_host_allowed(host):
        raise ValueError("Plateforme non supportée")

    return host


_FACEBOOK_LOGIN_WALL_HINT = (
    " — Facebook bloque souvent l'accès anonyme aux Reels/vidéos (page de "
    "connexion requise). Réessayez en fournissant des cookies de session "
    "(champ « Cookies » ci-dessus, export au format Netscape depuis votre "
    "navigateur connecté)."
)


def _clean_ytdlp_error(stderr: str, host: str = "") -> str:
    """Extrait un message d'erreur lisible depuis la sortie stderr de yt-dlp."""
    if not stderr:
        message = "Échec du téléchargement (erreur inconnue)"
    else:
        lines = [l for l in stderr.splitlines() if l.strip()]
        # yt-dlp émet souvent une ligne explicite "ERROR: ..."
        message = None
        for l in lines:
            if l.startswith("ERROR:"):
                message = l[len("ERROR:"):].strip()
                break
        if message is None:
            message = "\n".join(lines[-5:])[:500]

    is_facebook = "facebook" in host.lower() or "fb.watch" in host.lower()
    looks_like_login_wall = "cannot parse data" in message.lower() or "login" in message.lower()
    if is_facebook and looks_like_login_wall:
        message += _FACEBOOK_LOGIN_WALL_HINT

    return message


def download_video(url: str, output_dir: Path, cookies: str = None) -> Path:
    """
    Télécharge la meilleure vidéo (mp4, ≤1080p) dans `output_dir`.

    Args:
        url: URL validée de la vidéo.
        output_dir: Dossier de destination (sera créé si besoin).
        cookies: Contenu optionnel d'un fichier cookies Netscape (pour FB privé).

    Retourne:
        Le chemin du fichier téléchargé.

    Lève:
        RuntimeError en cas d'échec (login requis, URL invalide, bloquée...).
    """
    if not check_ytdlp_support():
        raise RuntimeError("yt-dlp n'est pas installé sur ce serveur")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Fichier cookies temporaire si fourni.
    cookies_file = None
    if cookies and cookies.strip():
        if len(cookies.encode("utf-8")) > MAX_COOKIES_BYTES:
            raise ValueError("Cookies trop volumineux")
        cookies_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=".txt", dir=str(output_dir)
        )
        cookies_file.write(cookies.encode("utf-8"))
        cookies_file.close()

    template = str(output_dir / "%(id)s.%(ext)s")

    # yt-dlp doit fusionner (via FFmpeg) une piste vidéo et une piste audio
    # séparées quand on demande "bestvideo+bestaudio". Sans FFmpeg sur le
    # serveur, la fusion échoue et laisse deux fichiers distincts (vidéo
    # seule + audio seule, ex: .m4a) au lieu d'un seul fichier vidéo+son.
    # On force donc un format déjà muxé (un seul flux contenant les deux)
    # quand FFmpeg est indisponible, pour ne jamais dépendre de la fusion.
    ffmpeg_available = shutil.which("ffmpeg") is not None
    if ffmpeg_available:
        video_format = "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best"
    else:
        video_format = "best[ext=mp4][height<=1080]/best[height<=1080]/best"

    cmd = [
        "yt-dlp",
        "--no-playlist",  # 1 vidéo par job (pas de playlist/channel)
        "--no-warnings",
        "-f", video_format,
        "--merge-output-format", "mp4",
        "-o", template,
        url,
    ]
    if cookies_file:
        cmd += ["--cookies", cookies_file.name]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=DOWNLOAD_TIMEOUT,
            cwd=str(output_dir),
        )
    finally:
        if cookies_file:
            try:
                Path(cookies_file.name).unlink()
            except OSError:
                pass

    if result.returncode != 0:
        host = urlparse(url).hostname or ""
        raise RuntimeError(_clean_ytdlp_error(result.stderr, host))

    downloaded = [f for f in output_dir.iterdir() if f.is_file()]
    if not downloaded:
        raise RuntimeError("Aucun fichier téléchargé")

    if len(downloaded) > 1:
        # Résidu de fusion échouée : plusieurs flux partiels (vidéo seule +
        # audio seule) au lieu d'un seul fichier. On refuse de deviner
        # lequel garder (ça a produit le bug du fichier .m4a livré à la
        # place de la vidéo) et on échoue avec un message explicite.
        raise RuntimeError(
            "Échec de la fusion audio/vidéo (FFmpeg absent ou indisponible sur le "
            "serveur). Installez FFmpeg, ou réessayez : plusieurs flux partiels ont "
            "été téléchargés sans pouvoir être assemblés en un seul fichier."
        )

    return downloaded[0]
