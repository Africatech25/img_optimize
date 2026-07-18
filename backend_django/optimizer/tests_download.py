"""
Tests de la feature de téléchargement vidéo par URL.

On teste la validation (SSRF, allowlist, prefix), l'endpoint platforms, et le
flux de l'endpoint /api/download en mockant yt-dlp + FFmpeg.
"""

import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase

from optimizer import views
from optimizer.video_downloader import validate_url, get_supported_platforms


class VideoDownloadValidationTests(TestCase):
    def test_valid_youtube(self):
        self.assertEqual(validate_url("https://www.youtube.com/watch?v=abc"), "www.youtube.com")

    def test_valid_facebook_subdomain(self):
        self.assertEqual(validate_url("https://m.facebook.com/watch/?v=1"), "m.facebook.com")

    def test_valid_fbwatch(self):
        self.assertEqual(validate_url("https://fb.watch/abc123"), "fb.watch")

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            validate_url("")

    def test_no_scheme_raises(self):
        with self.assertRaises(ValueError):
            validate_url("youtube.com/watch?v=1")

    def test_unsupported_platform_raises(self):
        with self.assertRaises(ValueError):
            validate_url("https://example.com/video.mp4")

    def test_ssrf_localhost_raises(self):
        with self.assertRaises(ValueError):
            validate_url("http://localhost/video")

    def test_ssrf_private_ip_raises(self):
        with self.assertRaises(ValueError):
            validate_url("http://192.168.1.10/video")

    def test_ssrf_metadata_ip_raises(self):
        with self.assertRaises(ValueError):
            validate_url("http://169.254.169.254/latest/meta-data/")

    def test_supported_platforms(self):
        platforms = get_supported_platforms()
        self.assertIn("YouTube", platforms)
        self.assertIn("Facebook", platforms)
        self.assertIn("TikTok", platforms)


class DownloadEndpointTests(TestCase):
    def setUp(self):
        self.patches = [
            patch("optimizer.views.check_ytdlp_support", return_value=True),
            patch("optimizer.views.check_ffmpeg_support", return_value=True),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def test_platforms_endpoint(self):
        resp = self.client.get("/api/download/platforms")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("platforms", data)
        self.assertIn("YouTube", data["platforms"])
        # "domains" est utilisé par le frontend pour valider le host de l'URL
        # (les libellés "platforms" ne sont pas comparables à un hostname).
        self.assertIn("domains", data)
        self.assertIn("facebook.com", data["domains"])

    def test_download_unsupported_platform(self):
        resp = self.client.post(
            "/api/download",
            data={"url": "https://example.com/video.mp4", "prefix": "v"},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("non support", resp.json()["detail"].lower())

    def test_download_ssrf_rejected(self):
        resp = self.client.post(
            "/api/download",
            data={"url": "http://192.168.0.1/video", "prefix": "v"},
        )
        self.assertEqual(resp.status_code, 400)
        # IP interne : rejetée (soit SSRF, soit plateforme non supportée)
        detail = resp.json()["detail"].lower()
        self.assertTrue("non autoris" in detail or "non support" in detail)

    def test_download_invalid_prefix(self):
        resp = self.client.post(
            "/api/download",
            data={"url": "https://youtu.be/abc", "prefix": "../evil"},
        )
        self.assertEqual(resp.status_code, 400)

    def test_download_unsupported_codec(self):
        resp = self.client.post(
            "/api/download",
            data={"url": "https://youtu.be/abc", "prefix": "v", "codec": "badcodec"},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("codec", resp.json()["detail"].lower())

    def test_download_optimize_false_skips_codec_validation(self):
        """optimize=false: le codec (invalide ou non fourni) n'est pas validé,
        puisque la vidéo n'est pas ré-encodée."""
        with patch("optimizer.views.validate_url", return_value="youtu.be"), \
             patch("optimizer.views._process_download") as mock_job:

            resp = self.client.post(
                "/api/download",
                data={"url": "https://youtu.be/abc", "prefix": "v", "optimize": "false", "codec": "badcodec"},
            )

        self.assertEqual(resp.status_code, 200)
        job_id = resp.json()["job_id"]
        self.assertIn("job_id", resp.json())
        mock_job.assert_called_once()
        # Le flag optimize=False doit être propagé au job en arrière-plan.
        self.assertEqual(mock_job.call_args[0][3], False)
        # ... et persisté sur le job pour que le frontend sache ne pas
        # afficher "optimisation terminée" sur le récap.
        job = views.OptimizationJob.objects.get(job_id=job_id)
        self.assertEqual(job.stats.get("optimized"), False)

    def test_download_full_flow_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw.mp4"
            raw.write_bytes(b"x" * 1000)
            optimized = Path(tmp) / "v-01.mp4"
            optimized.write_bytes(b"y" * 500)

            with patch("optimizer.views.validate_url", return_value="youtu.be"), \
                 patch("optimizer.views.download_video", return_value=raw), \
                 patch("optimizer.views._process_download") as mock_job:

                resp = self.client.post(
                    "/api/download",
                    data={"url": "https://youtu.be/abc", "prefix": "v", "codec": "h264"},
                )

            self.assertEqual(resp.status_code, 200)
            self.assertIn("job_id", resp.json())
            mock_job.assert_called_once()

    def test_download_no_optimize_leaves_only_one_file_in_output_dir(self):
        """Régression : un résidu dans le dossier de téléchargement brut
        (ex. fichier cookies non supprimé à cause d'un verrou Windows) ne
        doit jamais faire basculer /api/download/{job_id} en ZIP, puisque
        le brut est isolé dans son propre dossier temporaire."""
        job_id = uuid.uuid4()
        output_dir = settings.TEMP_DIR / str(job_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        job = views.OptimizationJob.objects.create(
            job_id=job_id, mode="optimize_video", total_files=1, total_videos=1,
            output_dir=str(output_dir), stats={"optimized": False},
        )

        def fake_download_video(url, raw_dir, cookies):
            raw_dir = Path(raw_dir)
            # Simule un fichier cookies temporaire non supprimé (résidu).
            (raw_dir / "leftover_cookies.txt").write_bytes(b"stale")
            raw = raw_dir / "raw.mp4"
            raw.write_bytes(b"x" * 1000)
            return raw

        with patch("optimizer.views.download_video", side_effect=fake_download_video):
            views._process_download(
                str(job_id), "https://youtu.be/abc", "youtu.be", False,
                "h264", None, None, None, "v", 1, None,
            )

        files = [f for f in output_dir.iterdir() if f.is_file()]
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "v-01.mp4")
