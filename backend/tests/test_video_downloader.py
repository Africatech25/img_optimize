#!/usr/bin/env python3
"""
Tests unitaires pour video_downloader.py

Usage:
    cd backend
    python -m pytest tests/test_video_downloader.py -v
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from video_downloader import (
    validate_url,
    download_video,
    check_ytdlp_support,
    get_supported_platforms,
    get_supported_domains,
    _FORBIDDEN_NETWORKS,
)


# ---------------------------------------------------------------------------
# validate_url
# ---------------------------------------------------------------------------

def test_validate_url_valid_youtube():
    host = validate_url("https://www.youtube.com/watch?v=abc123")
    assert host == "www.youtube.com"


def test_validate_url_valid_facebook_subdomain():
    host = validate_url("https://m.facebook.com/watch/?v=123")
    assert host == "m.facebook.com"


def test_validate_url_valid_short_youtu_be():
    host = validate_url("https://youtu.be/abc123")
    assert host == "youtu.be"


def test_validate_url_empty_raises():
    with pytest.raises(ValueError):
        validate_url("")


def test_validate_url_no_scheme_raises():
    with pytest.raises(ValueError):
        validate_url("youtube.com/watch?v=1")


def test_validate_url_ftp_raises():
    with pytest.raises(ValueError):
        validate_url("ftp://example.com/video")


def test_validate_url_unsupported_platform_raises():
    with pytest.raises(ValueError):
        validate_url("https://example.com/video.mp4")


def test_validate_url_ssrf_localhost_raises():
    with pytest.raises(ValueError):
        validate_url("http://localhost/video")


def test_validate_url_ssrf_private_ip_raises():
    with pytest.raises(ValueError):
        validate_url("http://192.168.1.10/video")


def test_validate_url_ssrf_metadata_ip_raises():
    with pytest.raises(ValueError):
        validate_url("http://169.254.169.254/latest/meta-data/")


# ---------------------------------------------------------------------------
# get_supported_platforms / domains
# ---------------------------------------------------------------------------

def test_get_supported_platforms_non_empty():
    platforms = get_supported_platforms()
    assert "YouTube" in platforms
    assert "Facebook" in platforms
    assert "TikTok" in platforms


def test_get_supported_domains_includes_fbwatch():
    domains = get_supported_domains()
    assert "fb.watch" in domains


# ---------------------------------------------------------------------------
# download_video (subprocess mocké)
# ---------------------------------------------------------------------------

def test_download_video_success(tmp_path):
    # Simule un fichier téléchargé et un yt-dlp qui réussit.
    fake_file = tmp_path / "abc123.mp4"
    fake_file.write_bytes(b"fake video content")

    with patch("video_downloader.check_ytdlp_support", return_value=True), \
         patch("video_downloader.subprocess.run") as mock_run, \
         patch("video_downloader.tempfile.NamedTemporaryFile") as mock_nf:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        # Pas de cookies -> NamedTemporaryFile ne doit pas créer de fichier
        mock_nf.side_effect = FileNotFoundError  # simule l'absence d'appel
        result = download_video("https://youtu.be/abc", tmp_path)
        assert result.name == "abc123.mp4"


def test_download_video_failure_raises(tmp_path):
    with patch("video_downloader.check_ytdlp_support", return_value=True), \
         patch("video_downloader.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="",
            stderr="ERROR: Private video. Sign in to watch."
        )
        with pytest.raises(RuntimeError) as exc:
            download_video("https://youtu.be/private", tmp_path)
        assert "Private video" in str(exc.value)


def test_download_video_no_ytdlp_raises(tmp_path):
    with patch("video_downloader.check_ytdlp_support", return_value=False):
        with pytest.raises(RuntimeError):
            download_video("https://youtu.be/abc", tmp_path)
