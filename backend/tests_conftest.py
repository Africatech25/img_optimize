"""
Configuration pytest et fixtures communes pour les tests du backend img_optimize.

Ce module contient:
- Fixtures pour les images de test (en mémoire, pas de dépendance fichiers)
- Fixtures pour le client de test FastAPI
- Fixtures pour les données de test (mock data)
- Configuration du TestClient
"""

import pytest
import asyncio
from io import BytesIO
from pathlib import Path
from typing import Generator, Dict
from PIL import Image
from fastapi.testclient import TestClient
import tempfile
import shutil

# Import de l'application FastAPI
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from main import app, jobs, OptimizationJob, TEMP_DIR, MAX_FILE_SIZE, MAX_FILES_PER_REQUEST
from optimize_images import FORMAT_CONFIG, SUPPORTED_EXTENSIONS


# ============================================================================
# FIXTURES - CLIENT DE TEST
# ============================================================================

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Fixture du client de test FastAPI.
    
    Fournit un TestClient configuré pour tester l'API.
    Nettoie automatiquement après chaque test.
    """
    # Nettoyer les jobs avant chaque test
    jobs.clear()
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Nettoyer après le test
    jobs.clear()


# ============================================================================
# FIXTURES - IMAGES DE TEST (EN MÉMOIRE)
# ============================================================================

@pytest.fixture
def simple_image_bytes() -> bytes:
    """
    Crée une image RGB simple de 100x100px en mémoire (format PNG).
    
    Returns:
        bytes: Contenu de l'image PNG
    """
    img = Image.new('RGB', (100, 100), color=(255, 0, 0))
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer.read()


@pytest.fixture
def rgba_image_bytes() -> bytes:
    """
    Crée une image RGBA avec transparence de 100x100px en mémoire.
    
    Returns:
        bytes: Contenu de l'image PNG avec canal alpha
    """
    img = Image.new('RGBA', (100, 100), color=(0, 255, 0, 128))
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer.read()


@pytest.fixture
def large_image_bytes() -> bytes:
    """
    Crée une grande image de 2000x2000px en mémoire (~12MB).
    
    Returns:
        bytes: Contenu de l'image PNG volumineuse
    """
    img = Image.new('RGB', (2000, 2000), color=(0, 0, 255))
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer.read()


@pytest.fixture
def jpeg_image_bytes() -> bytes:
    """
    Crée une image JPEG de 200x200px en mémoire.
    
    Returns:
        bytes: Contenu de l'image JPEG
    """
    img = Image.new('RGB', (200, 200), color=(255, 255, 0))
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)
    return buffer.read()


@pytest.fixture
def webp_image_bytes() -> bytes:
    """
    Crée une image WebP de 150x150px en mémoire.
    
    Returns:
        bytes: Contenu de l'image WebP
    """
    img = Image.new('RGB', (150, 150), color=(128, 128, 128))
    buffer = BytesIO()
    img.save(buffer, format='WEBP', quality=80)
    buffer.seek(0)
    return buffer.read()


@pytest.fixture
def watermark_logo_bytes() -> bytes:
    """
    Crée un petit logo PNG pour les tests de watermarking.
    
    Returns:
        bytes: Contenu du logo PNG 50x50px
    """
    img = Image.new('RGBA', (50, 50), color=(255, 255, 255, 200))
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer.read()


# ============================================================================
# FIXTURES - FICHIERS UPLOAD SIMULÉS
# ============================================================================

@pytest.fixture
def upload_file_simple(simple_image_bytes):
    """
    Crée un UploadFile simulé avec une image simple.
    
    Returns:
        dict: Structure simulant un UploadFile pour les tests
    """
    return {
        "filename": "test_image.png",
        "content": simple_image_bytes,
        "content_type": "image/png"
    }


@pytest.fixture
def upload_file_jpeg(jpeg_image_bytes):
    """
    Crée un UploadFile simulé avec une image JPEG.
    
    Returns:
        dict: Structure simulant un UploadFile JPEG
    """
    return {
        "filename": "test_image.jpg",
        "content": jpeg_image_bytes,
        "content_type": "image/jpeg"
    }


@pytest.fixture
def upload_file_large(large_image_bytes):
    """
    Crée un UploadFile simulé avec une grande image.
    
    Returns:
        dict: Structure simulant un UploadFile volumineux
    """
    return {
        "filename": "large_image.png",
        "content": large_image_bytes,
        "content_type": "image/png"
    }


# ============================================================================
# FIXTURES - RÉPERTOIRES TEMPORAIRES
# ============================================================================

@pytest.fixture
def temp_output_dir() -> Generator[Path, None, None]:
    """
    Crée un répertoire temporaire pour les tests d'output.
    Nettoie automatiquement après le test.
    
    Yields:
        Path: Chemin du répertoire temporaire
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="test_optimize_"))
    yield temp_dir
    
    # Nettoyage
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_input_dir() -> Generator[Path, None, None]:
    """
    Crée un répertoire temporaire pour les fichiers d'entrée de test.
    Nettoie automatiquement après le test.
    
    Yields:
        Path: Chemin du répertoire temporaire
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="test_input_"))
    yield temp_dir
    
    # Nettoyage
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================================
# FIXTURES - DONNÉES DE TEST
# ============================================================================

@pytest.fixture
def valid_optimization_params() -> Dict:
    """
    Paramètres valides pour une optimisation standard.
    
    Returns:
        dict: Paramètres de test valides
    """
    return {
        "format": "webp",
        "quality": 75,
        "prefix": "test",
        "start_number": 1,
        "smoothing": 0,
        "watermark_enabled": "false",
        "watermark_type": "text",
        "watermark_text": "",
        "watermark_position": "bottom-right",
        "watermark_opacity": "50"
    }


@pytest.fixture
def watermark_text_params() -> Dict:
    """
    Paramètres pour un test de watermark texte.
    
    Returns:
        dict: Paramètres de watermark texte
    """
    return {
        "format": "webp",
        "quality": 80,
        "prefix": "watermarked",
        "start_number": 1,
        "smoothing": 0,
        "watermark_enabled": "true",
        "watermark_type": "text",
        "watermark_text": "© Test 2026",
        "watermark_position": "bottom-right",
        "watermark_opacity": "70"
    }


@pytest.fixture
def edge_case_params() -> Dict:
    """
    Paramètres de cas limites pour les tests.
    
    Returns:
        dict: Paramètres de test avec valeurs limites
    """
    return {
        "format": "jpeg",
        "quality": 100,  # Qualité maximale
        "prefix": "a" * 50,  # Préfixe long
        "start_number": 999,
        "smoothing": 10,  # Smoothing maximal
        "watermark_enabled": "false",
        "watermark_type": "text",
        "watermark_text": "",
        "watermark_position": "center",
        "watermark_opacity": "100"
    }


# ============================================================================
# FIXTURES - MOCKS
# ============================================================================

@pytest.fixture
def mock_job() -> OptimizationJob:
    """
    Crée un job d'optimisation simulé pour les tests.
    
    Returns:
        OptimizationJob: Instance de job de test
    """
    job = OptimizationJob("test-job-id-12345")
    job.total_images = 5
    job.processed_images = 0
    return job


# ============================================================================
# FIXTURES - NETTOYAGE
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_jobs():
    """
    Fixture auto-utilisée pour nettoyer les jobs entre chaque test.
    S'exécute automatiquement avant et après chaque test.
    """
    # Avant le test
    jobs.clear()
    yield
    # Après le test
    jobs.clear()


@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """
    Fixture auto-utilisée pour nettoyer les fichiers temporaires.
    S'exécute automatiquement après chaque test.
    """
    yield
    # Nettoyer le répertoire TEMP_DIR après chaque test
    if TEMP_DIR.exists():
        for item in TEMP_DIR.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                item.unlink(missing_ok=True)


# ============================================================================
# HELPERS
# ============================================================================

def create_test_image_file(path: Path, width: int = 100, height: int = 100, 
                           format: str = 'PNG', color=(255, 0, 0)):
    """
    Helper pour créer un fichier image de test sur disque.
    
    Args:
        path: Chemin du fichier à créer
        width: Largeur de l'image
        height: Hauteur de l'image
        format: Format de l'image (PNG, JPEG, etc.)
        color: Couleur de remplissage RGB
    """
    img = Image.new('RGB', (width, height), color=color)
    img.save(path, format=format)


def assert_image_valid(image_bytes: bytes):
    """
    Helper pour vérifier qu'un contenu bytes est une image valide.
    
    Args:
        image_bytes: Contenu de l'image à valider
        
    Raises:
        AssertionError: Si l'image n'est pas valide
    """
    try:
        img = Image.open(BytesIO(image_bytes))
        img.verify()
        assert img.format in ['PNG', 'JPEG', 'WEBP', 'AVIF']
    except Exception as e:
        raise AssertionError(f"Image invalide: {e}")


def get_image_info(image_bytes: bytes) -> Dict:
    """
    Helper pour extraire les informations d'une image.
    
    Args:
        image_bytes: Contenu de l'image
        
    Returns:
        dict: Informations sur l'image (format, taille, dimensions, mode)
    """
    img = Image.open(BytesIO(image_bytes))
    return {
        "format": img.format,
        "size": len(image_bytes),
        "width": img.width,
        "height": img.height,
        "mode": img.mode
    }
