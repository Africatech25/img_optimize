"""
Tests pour l'endpoint de téléchargement vidéo par URL (/api/download)

Teste la validation, la sécurité (SSRF, allowlist) et le flux de job.
"""

import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from main import app, jobs, OptimizationJob

from video_downloader import validate_url


# ============================================================================
# GET /api/download/platforms
# ============================================================================

@pytest.mark.unit
def test_download_platforms_returns_list(client):
    response = client.get("/api/download/platforms")
    assert response.status_code == 200
    data = response.json()
    assert "platforms" in data
    assert isinstance(data["platforms"], list)
    assert "YouTube" in data["platforms"]
    assert "Facebook" in data["platforms"]


# ============================================================================
# POST /api/download — validation
# ============================================================================

@pytest.mark.unit
def test_download_missing_url(client):
    response = client.post("/api/download", data={"prefix": "v"})
    assert response.status_code == 422  # champ requis manquant


@pytest.mark.unit
def test_download_unsupported_platform(client):
    with patch("main.check_ytdlp_support", return_value=True), \
         patch("main.check_ffmpeg_support", return_value=True):
        response = client.post(
            "/api/download",
            data={"url": "https://example.com/video.mp4", "prefix": "v"},
        )
    assert response.status_code == 400
    assert "non support" in response.json()["detail"].lower()


@pytest.mark.unit
def test_download_ssrf_internal_ip(client):
    with patch("main.check_ytdlp_support", return_value=True), \
         patch("main.check_ffmpeg_support", return_value=True):
        response = client.post(
            "/api/download",
            data={"url": "http://192.168.0.1/video", "prefix": "v"},
        )
    assert response.status_code == 400
    assert "non autoris" in response.json()["detail"].lower()


@pytest.mark.unit
def test_download_invalid_prefix(client):
    with patch("main.check_ytdlp_support", return_value=True), \
         patch("main.check_ffmpeg_support", return_value=True):
        response = client.post(
            "/api/download",
            data={"url": "https://youtu.be/abc", "prefix": "../evil"},
        )
    assert response.status_code == 400


@pytest.mark.unit
def test_download_unsupported_codec(client):
    with patch("main.check_ytdlp_support", return_value=True), \
         patch("main.check_ffmpeg_support", return_value=True):
        response = client.post(
            "/api/download",
            data={"url": "https://youtu.be/abc", "prefix": "v", "codec": "badcodec"},
        )
    assert response.status_code == 400
    assert "codec" in response.json()["detail"].lower()


# ============================================================================
# POST /api/download — flux complet (mock du download + conversion)
# ============================================================================

@pytest.mark.unit
def test_download_full_flow_success(client, tmp_path):
    # Préparer un fichier vidéo factice téléchargé + optimisé
    fake_raw = tmp_path / "raw.mp4"
    fake_raw.write_bytes(b"x" * 1000)
    fake_optimized = tmp_path / "v-01.mp4"
    fake_optimized.write_bytes(b"y" * 500)

    with patch("main.check_ytdlp_support", return_value=True), \
         patch("main.check_ffmpeg_support", return_value=True), \
         patch("main.validate_url", return_value="youtu.be"), \
         patch("main.download_video", return_value=fake_raw) as mock_dl, \
         patch("main.process_single_video", new=AsyncMock()) as mock_proc:

        # Forcer le dossier de sortie du job vers tmp_path
        orig_init = OptimizationJob.__init__

        def fake_init(self, job_id):
            orig_init(self, job_id)
            self.output_dir = tmp_path

        with patch.object(OptimizationJob, "__init__", fake_init):
            response = client.post(
                "/api/download",
                data={"url": "https://youtu.be/abc", "prefix": "v", "codec": "h264"},
            )
            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data
            mock_dl.assert_called_once()
            # Le job async s'exécute en arrière-plan ; on vérifie au moins
            # que l'appel de téléchargement a été déclenché.
