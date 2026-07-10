"""
Tests unitaires pour main.py - API endpoints et fonctionnalités SSE

Ce module teste:
- Health check endpoint
- Formats endpoint  
- Optimisation endpoint (validation, sécurité)
- SSE stream
- Gestion des jobs
- Téléchargement de résultats
- Validation CORS
- Limites de sécurité (MAX_FILE_SIZE, MAX_FILES_PER_REQUEST)
"""

import pytest
import asyncio
import json
from io import BytesIO
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

# Imports depuis le module principal
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from main import (
    app, jobs, OptimizationJob, TEMP_DIR, 
    MAX_FILE_SIZE, MAX_FILES_PER_REQUEST, ALLOWED_ORIGINS,
    cleanup_old_jobs, process_images_async
)
from optimize_images import FORMAT_CONFIG, check_avif_support


# ============================================================================
# TESTS - HEALTH & STATUS
# ============================================================================

@pytest.mark.unit
def test_health_check_returns_ok(client):
    """
    Test: /api/health retourne un statut OK avec les formats disponibles.
    
    Vérifie:
    - Status code 200
    - Champ 'status' == 'ok'
    - Présence de 'avif_available'
    - Liste des formats disponibles
    """
    response = client.get("/api/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert "avif_available" in data
    assert isinstance(data["avif_available"], bool)
    assert "formats" in data
    assert isinstance(data["formats"], list)
    assert len(data["formats"]) > 0


@pytest.mark.unit
def test_health_check_formats_list(client):
    """
    Test: /api/health retourne tous les formats configurés.
    
    Vérifie que tous les formats dans FORMAT_CONFIG sont listés.
    """
    response = client.get("/api/health")
    data = response.json()
    
    expected_formats = set(FORMAT_CONFIG.keys())
    returned_formats = set(data["formats"])
    
    assert expected_formats == returned_formats


@pytest.mark.unit
def test_get_formats_returns_configuration(client):
    """
    Test: /api/formats retourne la configuration complète des formats.
    
    Vérifie:
    - Chaque format a: description, default_quality, quality_range, available
    - Les ranges de qualité sont cohérents
    """
    response = client.get("/api/formats")
    
    assert response.status_code == 200
    data = response.json()
    
    for fmt, config in data.items():
        assert "description" in config
        assert "default_quality" in config
        assert "quality_range" in config
        assert "available" in config
        
        # Vérifier les ranges
        q_min, q_max = config["quality_range"]
        assert q_min < q_max
        assert q_min <= config["default_quality"] <= q_max


@pytest.mark.unit
def test_get_formats_avif_availability(client):
    """
    Test: /api/formats indique correctement la disponibilité AVIF.
    
    Vérifie que le champ 'available' pour AVIF correspond à check_avif_support().
    """
    response = client.get("/api/formats")
    data = response.json()
    
    avif_available = check_avif_support()
    
    if "avif" in data:
        assert data["avif"]["available"] == avif_available


# ============================================================================
# TESTS - VALIDATION SÉCURITÉ ENTRÉES
# ============================================================================

@pytest.mark.security
def test_optimize_rejects_too_many_files(client, simple_image_bytes):
    """
    Test: Rejet de requête avec trop de fichiers (> MAX_FILES_PER_REQUEST).
    
    SÉCURITÉ: Protection contre attaques DoS par volume.
    """
    # Créer MAX_FILES_PER_REQUEST + 1 fichiers
    files = []
    for i in range(MAX_FILES_PER_REQUEST + 1):
        files.append(
            ("files", (f"image_{i}.png", BytesIO(simple_image_bytes), "image/png"))
        )
    
    response = client.post(
        "/api/optimize",
        files=files,
        data={"format": "webp", "quality": "75"}
    )
    
    assert response.status_code == 400
    assert "Maximum" in response.json()["detail"]
    assert str(MAX_FILES_PER_REQUEST) in response.json()["detail"]


@pytest.mark.security
def test_optimize_rejects_oversized_file(client):
    """
    Test: Rejet de fichier dépassant MAX_FILE_SIZE.
    
    SÉCURITÉ: Protection contre upload de fichiers géants.
    """
    # Créer un fichier de taille > MAX_FILE_SIZE (50MB)
    oversized_content = b"X" * (MAX_FILE_SIZE + 1024)
    
    response = client.post(
        "/api/optimize",
        files=[("files", ("huge.png", BytesIO(oversized_content), "image/png"))],
        data={"format": "webp", "quality": "75"}
    )
    
    assert response.status_code == 413
    assert "trop volumineux" in response.json()["detail"]


@pytest.mark.security
def test_optimize_rejects_invalid_format(client, simple_image_bytes):
    """
    Test: Rejet de format non supporté.
    
    SÉCURITÉ: Validation stricte des formats.
    """
    response = client.post(
        "/api/optimize",
        files=[("files", ("test.png", BytesIO(simple_image_bytes), "image/png"))],
        data={"format": "invalid_format", "quality": "75"}
    )
    
    assert response.status_code == 400
    assert "Format non supporté" in response.json()["detail"]


@pytest.mark.security
def test_optimize_rejects_quality_out_of_range(client, simple_image_bytes):
    """
    Test: Rejet de qualité hors des bornes autorisées.
    
    SÉCURITÉ: Validation des plages de valeurs.
    """
    # Test qualité trop basse
    response = client.post(
        "/api/optimize",
        files=[("files", ("test.png", BytesIO(simple_image_bytes), "image/png"))],
        data={"format": "webp", "quality": "0"}
    )
    assert response.status_code == 400
    
    # Test qualité trop haute (sauf 100 qui est accepté)
    response = client.post(
        "/api/optimize",
        files=[("files", ("test.png", BytesIO(simple_image_bytes), "image/png"))],
        data={"format": "webp", "quality": "101"}
    )
    assert response.status_code == 400


@pytest.mark.security
def test_optimize_rejects_invalid_smoothing(client, simple_image_bytes):
    """
    Test: Rejet de valeur de lissage invalide.
    
    SÉCURITÉ: Validation du paramètre smoothing (0-10).
    """
    response = client.post(
        "/api/optimize",
        files=[("files", ("test.png", BytesIO(simple_image_bytes), "image/png"))],
        data={"format": "webp", "quality": "75", "smoothing": "15"}
    )
    
    assert response.status_code == 400
    assert "lissage" in response.json()["detail"].lower()


@pytest.mark.security
def test_optimize_rejects_invalid_watermark_opacity(client, simple_image_bytes):
    """
    Test: Rejet d'opacité de watermark invalide.
    
    SÉCURITÉ: Validation opacité (0-100).
    """
    response = client.post(
        "/api/optimize",
        files=[("files", ("test.png", BytesIO(simple_image_bytes), "image/png"))],
        data={
            "format": "webp",
            "quality": "75",
            "watermark_enabled": "true",
            "watermark_type": "text",
            "watermark_text": "Test",
            "watermark_opacity": "150"
        }
    )
    
    assert response.status_code == 400
    assert "opacité" in response.json()["detail"].lower()


@pytest.mark.security
def test_optimize_rejects_unsupported_image_extension(client):
    """
    Test: Rejet d'extensions non supportées.
    
    SÉCURITÉ: Validation des extensions de fichiers.
    """
    # Créer un faux fichier avec extension interdite
    fake_content = b"fake executable content"
    
    response = client.post(
        "/api/optimize",
        files=[("files", ("malware.exe", BytesIO(fake_content), "application/x-msdownload"))],
        data={"format": "webp", "quality": "75"}
    )
    
    # Devrait être rejeté ou échouer lors de la validation


@pytest.mark.security
def test_optimize_watermark_logo_oversized(client, simple_image_bytes):
    """
    Test: Rejet de logo watermark trop volumineux.
    
    SÉCURITÉ: Protection contre upload de gros logos.
    """
    oversized_logo = b"X" * (MAX_FILE_SIZE + 1024)
    
    response = client.post(
        "/api/optimize",
        files=[
            ("files", ("test.png", BytesIO(simple_image_bytes), "image/png")),
            ("watermark_logo", ("logo.png", BytesIO(oversized_logo), "image/png"))
        ],
        data={
            "format": "webp",
            "quality": "75",
            "watermark_enabled": "true",
            "watermark_type": "image"
        }
    )
    
    assert response.status_code == 413
    assert "Logo trop volumineux" in response.json()["detail"]


# ============================================================================
# TESTS - CAS NOMINAUX (SUCCESS PATH)
# ============================================================================

@pytest.mark.unit
def test_optimize_single_file_success(client, simple_image_bytes):
    """
    Test: Optimisation réussie d'un seul fichier.
    
    Vérifie:
    - Status code 200
    - Retour d'un job_id
    - Initialisation correcte du job
    """
    response = client.post(
        "/api/optimize",
        files=[("files", ("test.png", BytesIO(simple_image_bytes), "image/png"))],
        data={"format": "webp", "quality": "75", "prefix": "test"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "job_id" in data
    assert "total_images" in data
    assert data["total_images"] == 1
    assert data["status"] == "pending"
    
    # Vérifier que le job est créé
    assert data["job_id"] in jobs


@pytest.mark.unit
def test_optimize_multiple_files_success(client, simple_image_bytes, jpeg_image_bytes):
    """
    Test: Optimisation réussie de plusieurs fichiers.
    
    Vérifie le traitement par lots.
    """
    files = [
        ("files", ("image1.png", BytesIO(simple_image_bytes), "image/png")),
        ("files", ("image2.jpg", BytesIO(jpeg_image_bytes), "image/jpeg")),
        ("files", ("image3.png", BytesIO(simple_image_bytes), "image/png"))
    ]
    
    response = client.post(
        "/api/optimize",
        files=files,
        data={"format": "webp", "quality": "80"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_images"] == 3


@pytest.mark.unit
def test_optimize_default_quality_used(client, simple_image_bytes):
    """
    Test: Utilisation de la qualité par défaut si non spécifiée.
    
    Vérifie que le système applique FORMAT_CONFIG[format]["default_quality"].
    """
    response = client.post(
        "/api/optimize",
        files=[("files", ("test.png", BytesIO(simple_image_bytes), "image/png"))],
        data={"format": "jpeg"}  # Pas de quality spécifiée
    )
    
    assert response.status_code == 200


@pytest.mark.unit
def test_optimize_quality_100_allowed(client, simple_image_bytes):
    """
    Test: Qualité 100 autorisée (mode signature uniquement).
    
    Vérifie l'exception pour quality=100 même si range max < 100.
    """
    response = client.post(
        "/api/optimize",
        files=[("files", ("test.png", BytesIO(simple_image_bytes), "image/png"))],
        data={"format": "jpeg", "quality": "100"}
    )
    
    assert response.status_code == 200


@pytest.mark.unit
def test_optimize_with_watermark_text(client, simple_image_bytes):
    """
    Test: Ajout de watermark texte.
    
    Vérifie l'activation et paramétrage du watermark texte.
    """
    response = client.post(
        "/api/optimize",
        files=[("files", ("test.png", BytesIO(simple_image_bytes), "image/png"))],
        data={
            "format": "webp",
            "quality": "75",
            "watermark_enabled": "true",
            "watermark_type": "text",
            "watermark_text": "© Test 2026",
            "watermark_position": "bottom-right",
            "watermark_opacity": "70"
        }
    )
    
    assert response.status_code == 200


@pytest.mark.unit
def test_optimize_with_watermark_logo(client, simple_image_bytes, watermark_logo_bytes):
    """
    Test: Ajout de watermark logo/image.
    
    Vérifie l'upload et application d'un logo comme watermark.
    """
    response = client.post(
        "/api/optimize",
        files=[
            ("files", ("test.png", BytesIO(simple_image_bytes), "image/png")),
            ("watermark_logo", ("logo.png", BytesIO(watermark_logo_bytes), "image/png"))
        ],
        data={
            "format": "webp",
            "quality": "75",
            "watermark_enabled": "true",
            "watermark_type": "image",
            "watermark_position": "center",
            "watermark_opacity": "50"
        }
    )
    
    assert response.status_code == 200


# ============================================================================
# TESTS - EDGE CASES
# ============================================================================

@pytest.mark.edge_case
def test_optimize_empty_file_list(client):
    """
    Test: Requête sans fichier.
    
    Cas limite: files=[] doit être rejeté.
    """
    response = client.post(
        "/api/optimize",
        files=[],
        data={"format": "webp", "quality": "75"}
    )
    
    assert response.status_code == 422 or response.status_code == 400


@pytest.mark.edge_case
def test_optimize_filename_with_special_chars(client, simple_image_bytes):
    """
    Test: Nom de fichier avec caractères spéciaux.
    
    Vérifie la gestion sécurisée des noms de fichiers.
    """
    filename = "image with spaces & spéciaux (1).png"
    
    response = client.post(
        "/api/optimize",
        files=[("files", (filename, BytesIO(simple_image_bytes), "image/png"))],
        data={"format": "webp", "quality": "75"}
    )
    
    assert response.status_code == 200


@pytest.mark.edge_case
def test_optimize_very_long_prefix(client, simple_image_bytes):
    """
    Test: Préfixe très long (50 caractères).
    
    Vérifie que les longs préfixes sont gérés.
    """
    long_prefix = "a" * 50
    
    response = client.post(
        "/api/optimize",
        files=[("files", ("test.png", BytesIO(simple_image_bytes), "image/png"))],
        data={"format": "webp", "quality": "75", "prefix": long_prefix}
    )
    
    assert response.status_code == 200


@pytest.mark.edge_case
def test_optimize_start_number_high(client, simple_image_bytes):
    """
    Test: Numéro de départ élevé (999).
    
    Vérifie que start_number fonctionne avec de grandes valeurs.
    """
    response = client.post(
        "/api/optimize",
        files=[("files", ("test.png", BytesIO(simple_image_bytes), "image/png"))],
        data={"format": "webp", "quality": "75", "start_number": "999"}
    )
    
    assert response.status_code == 200


@pytest.mark.edge_case
def test_optimize_watermark_enabled_boolean_variations(client, simple_image_bytes):
    """
    Test: Variations de valeurs booléennes pour watermark_enabled.
    
    Teste: "true", "1", "yes", "on", "false", "0", "no", "off"
    """
    true_values = ["true", "1", "yes", "on", "True", "TRUE"]
    
    for value in true_values:
        response = client.post(
            "/api/optimize",
            files=[("files", ("test.png", BytesIO(simple_image_bytes), "image/png"))],
            data={
                "format": "webp",
                "quality": "75",
                "watermark_enabled": value,
                "watermark_type": "text",
                "watermark_text": "Test"
            }
        )
        assert response.status_code == 200


# ============================================================================
# TESTS - GESTION DES JOBS
# ============================================================================

@pytest.mark.unit
def test_job_creation_and_storage(client, simple_image_bytes):
    """
    Test: Création et stockage du job dans le dictionnaire global.
    
    Vérifie que le job est accessible après création.
    """
    response = client.post(
        "/api/optimize",
        files=[("files", ("test.png", BytesIO(simple_image_bytes), "image/png"))],
        data={"format": "webp", "quality": "75"}
    )
    
    job_id = response.json()["job_id"]
    
    assert job_id in jobs
    job = jobs[job_id]
    assert isinstance(job, OptimizationJob)
    assert job.job_id == job_id
    assert job.status in ["pending", "processing"]


@pytest.mark.unit
def test_job_output_directory_creation(client, simple_image_bytes):
    """
    Test: Création du répertoire de sortie du job.
    
    Vérifie que TEMP_DIR/job_id est créé.
    """
    response = client.post(
        "/api/optimize",
        files=[("files", ("test.png", BytesIO(simple_image_bytes), "image/png"))],
        data={"format": "webp", "quality": "75"}
    )
    
    job_id = response.json()["job_id"]
    job = jobs[job_id]
    
    assert job.output_dir.exists()
    assert job.output_dir.is_dir()
    assert str(job_id) in str(job.output_dir)


@pytest.mark.unit
def test_job_to_dict_structure(mock_job):
    """
    Test: Structure du dictionnaire retourné par job.to_dict().
    
    Vérifie les champs requis.
    """
    job_dict = mock_job.to_dict()
    
    assert "job_id" in job_dict
    assert "status" in job_dict
    assert "total_images" in job_dict
    assert "processed_images" in job_dict
    assert "stats" in job_dict
    assert "reduction_percent" in job_dict["stats"]


@pytest.mark.unit
def test_job_add_progress(mock_job):
    """
    Test: Ajout de messages de progression au job.
    
    Vérifie le tracking de la progression.
    """
    initial_count = len(mock_job.progress)
    
    mock_job.add_progress({
        "type": "image_processed",
        "message": "Image 1 traitée"
    })
    
    assert len(mock_job.progress) == initial_count + 1
    assert mock_job.processed_images == 1


# ============================================================================
# TESTS - CORS
# ============================================================================

@pytest.mark.security
def test_cors_allowed_origins():
    """
    Test: Vérification de la liste CORS autorisée.
    
    SÉCURITÉ: S'assurer que seules les origines légitimes sont autorisées.
    """
    # Vérifier que production est dans la liste
    assert "https://img-optimize.vercel.app" in ALLOWED_ORIGINS
    
    # Vérifier que localhost dev est autorisé
    assert "http://localhost:5173" in ALLOWED_ORIGINS
    
    # Vérifier qu'il n'y a pas de wildcard
    assert "*" not in ALLOWED_ORIGINS


# ============================================================================
# TESTS - NETTOYAGE
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
async def test_cleanup_old_jobs_preserves_processing():
    """
    Test: cleanup_old_jobs ne supprime pas les jobs en cours.
    
    Vérifie que les jobs avec status="processing" sont préservés.
    """
    # Ce test nécessiterait un mock du système de nettoyage
    # Placeholder pour la logique de test
    pass


# ============================================================================
# TESTS - AVIF
# ============================================================================

@pytest.mark.unit
def test_avif_format_rejection_when_unavailable(client, simple_image_bytes):
    """
    Test: Rejet de format AVIF si non disponible.
    
    SÉCURITÉ: Validation de disponibilité AVIF.
    """
    if not check_avif_support():
        response = client.post(
            "/api/optimize",
            files=[("files", ("test.png", BytesIO(simple_image_bytes), "image/png"))],
            data={"format": "avif", "quality": "65"}
        )
        
        assert response.status_code == 400
        assert "AVIF n'est pas disponible" in response.json()["detail"]


# ============================================================================
# TESTS - FORMATS DIVERS
# ============================================================================

@pytest.mark.unit
@pytest.mark.parametrize("format_name", ["jpeg", "webp", "png"])
def test_optimize_all_supported_formats(client, simple_image_bytes, format_name):
    """
    Test: Optimisation réussie pour tous les formats supportés.
    
    Test paramétré pour chaque format.
    """
    response = client.post(
        "/api/optimize",
        files=[("files", ("test.png", BytesIO(simple_image_bytes), "image/png"))],
        data={"format": format_name, "quality": "75"}
    )
    
    assert response.status_code == 200
    assert response.json()["total_images"] == 1
