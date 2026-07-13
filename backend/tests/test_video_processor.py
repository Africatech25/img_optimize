#!/usr/bin/env python3
"""
Tests unitaires pour video_processor.py

Usage:
    cd backend
    python -m pytest tests/test_video_processor.py -v
"""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Ajouter le répertoire parent au path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from video_processor import (
    check_ffmpeg_support,
    get_video_info,
    convert_video,
    get_supported_formats,
    format_size,
    format_duration,
    CODEC_CONFIG,
    RESOLUTION_MAP,
)


class TestCheckFFmpegSupport:
    """Tests pour check_ffmpeg_support()"""

    def test_returns_bool(self):
        result = check_ffmpeg_support()
        assert isinstance(result, bool)

    def test_returns_true_when_ffmpeg_installed(self):
        # Sur la plupart des systèmes de dev, FFmpeg est installé
        # Ce test vérifie juste que la fonction ne plante pas
        result = check_ffmpeg_support()
        assert result in (True, False)


class TestFormatSize:
    """Tests pour format_size()"""

    def test_bytes_to_ko(self):
        # 500 / 1000 = 0.5, arrondi a 0 avec :.0f
        assert format_size(500) == "0 Ko"

    def test_ko_to_mo(self):
        assert format_size(1_500_000) == "1.5 Mo"

    def test_exact_mo(self):
        assert format_size(1_000_000) == "1.0 Mo"

    def test_zero(self):
        assert format_size(0) == "0 Ko"


class TestFormatDuration:
    """Tests pour format_duration()"""

    def test_zero_seconds(self):
        assert format_duration(0) == "00:00"

    def test_minutes_and_seconds(self):
        assert format_duration(90) == "01:30"

    def test_large_duration(self):
        assert format_duration(3661) == "61:01"


class TestGetSupportedFormats:
    """Tests pour get_supported_formats()"""

    def test_returns_dict(self):
        result = get_supported_formats()
        assert isinstance(result, dict)

    def test_contains_expected_codecs(self):
        result = get_supported_formats()
        assert "h264" in result
        assert "h265" in result
        assert "vp9" in result
        assert "av1" in result

    def test_codec_structure(self):
        result = get_supported_formats()
        for codec, config in result.items():
            assert "description" in config
            assert "encoder" in config
            assert "crf_range" in config
            assert "default_crf" in config
            assert "extension" in config


class TestCodeConfig:
    """Tests pour la constante CODEC_CONFIG"""

    def test_all_codecs_have_required_keys(self):
        required_keys = {"encoder", "description", "crf_range", "default_crf", "extension", "extra_args"}
        for codec, config in CODEC_CONFIG.items():
            missing = required_keys - set(config.keys())
            assert not missing, f"Codec {codec} manque: {missing}"

    def test_crf_ranges_are_valid(self):
        for codec, config in CODEC_CONFIG.items():
            crf_min, crf_max = config["crf_range"]
            assert crf_min < crf_max, f"Codec {codec}: CRF range invalide"
            assert config["default_crf"] >= crf_min
            assert config["default_crf"] <= crf_max


class TestResolutionMap:
    """Tests pour RESOLUTION_MAP"""

    def test_original_is_none(self):
        assert RESOLUTION_MAP["original"] is None

    def test_all_resolutions_have_valid_dimensions(self):
        for name, dims in RESOLUTION_MAP.items():
            if dims is not None:
                w, h = dims
                assert w > 0, f"Résolution {name}: largeur invalide"
                assert h > 0, f"Résolution {name}: hauteur invalide"


@pytest.mark.skipif(not check_ffmpeg_support(), reason="FFmpeg non installé")
class TestVideoConversion:
    """Tests d'intégration pour convert_video() - nécessite FFmpeg"""

    @pytest.fixture
    def sample_video(self, tmp_path):
        """Crée une vidéo de test de 1 seconde"""
        video_path = tmp_path / "test_input.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac",
            str(video_path)
        ]
        subprocess.run(cmd, capture_output=True, timeout=30)
        assert video_path.exists(), "Impossible de créer la vidéo de test"
        return video_path

    def test_convert_h264(self, sample_video, tmp_path):
        output = tmp_path / "test_output.mp4"
        before, after, status = convert_video(sample_video, output, "h264", quality=28)

        assert output.exists()
        assert before > 0
        assert after > 0
        assert status in ("ok", "optimized", "failed")

    def test_convert_with_resolution(self, sample_video, tmp_path):
        output = tmp_path / "test_output_720p.mp4"
        before, after, status = convert_video(
            sample_video, output, "h264", quality=28,
            resolution="720p"
        )

        assert output.exists()

    def test_convert_vp9(self, sample_video, tmp_path):
        output = tmp_path / "test_output.webm"
        before, after, status = convert_video(sample_video, output, "vp9", quality=30)

        assert output.exists()

    def test_invalid_codec_raises(self, sample_video, tmp_path):
        output = tmp_path / "test_output.mp4"
        with pytest.raises(ValueError, match="Codec non supporté"):
            convert_video(sample_video, output, "invalid_codec", quality=28)


@pytest.mark.skipif(not check_ffmpeg_support(), reason="FFmpeg non installé")
class TestGetVideoInfo:
    """Tests pour get_video_info() - nécessite FFmpeg"""

    @pytest.fixture
    def sample_video(self, tmp_path):
        """Crée une vidéo de test"""
        video_path = tmp_path / "test_info.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=duration=2:size=640x480:rate=25",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac",
            str(video_path)
        ]
        subprocess.run(cmd, capture_output=True, timeout=30)
        assert video_path.exists()
        return video_path

    def test_returns_valid_info(self, sample_video):
        info = get_video_info(sample_video)

        assert info["width"] == 640
        assert info["height"] == 480
        assert info["duration"] > 0
        assert info["fps"] > 0
        assert info["size_bytes"] > 0
        assert info["codec"] == "h264"

    def test_nonexistent_file_raises(self, tmp_path):
        with pytest.raises(RuntimeError):
            get_video_info(tmp_path / "nonexistent.mp4")
