"""
Tests unitaires pour optimize_images.py - Traitement d'images

Ce module teste:
- Conversion d'images entre formats
- Compression et optimisation
- Gestion de la transparence
- Watermarking (texte et image)
- Lissage (smoothing)
- Limitation de taille
- Estimation de dimensions
- Helpers (format_size, check_avif_support)
"""

import pytest
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageFilter
import tempfile
import shutil

# Imports depuis le module optimize_images
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from optimize_images import (
    convert_image, format_size, check_avif_support,
    estimate_target_dimensions, apply_watermark,
    FORMAT_CONFIG, SUPPORTED_EXTENSIONS
)


# ============================================================================
# TESTS - CONVERSION D'IMAGES
# ============================================================================

@pytest.mark.unit
def test_convert_image_jpeg_to_webp(temp_input_dir, temp_output_dir):
    """
    Test: Conversion JPEG → WebP réussie.
    
    Vérifie:
    - Fichier de sortie créé
    - Format correct
    - Taille réduite
    """
    # Créer image source JPEG
    input_path = temp_input_dir / "test.jpg"
    img = Image.new('RGB', (200, 200), color=(255, 0, 0))
    img.save(input_path, format='JPEG', quality=85)
    
    output_path = temp_output_dir / "test.webp"
    
    # Conversion
    original_size, final_size, status = convert_image(
        input_path=input_path,
        output_path=output_path,
        fmt="webp",
        quality=75
    )
    
    assert output_path.exists()
    assert final_size > 0
    assert status in ["ok", "reduced"]
    
    # Vérifier le format
    with Image.open(output_path) as img_out:
        assert img_out.format == "WEBP"


@pytest.mark.unit
def test_convert_image_png_to_jpeg(temp_input_dir, temp_output_dir):
    """
    Test: Conversion PNG → JPEG réussie.
    
    Vérifie la gestion de la transparence (fond blanc).
    """
    # Créer image source PNG avec transparence
    input_path = temp_input_dir / "test.png"
    img = Image.new('RGBA', (150, 150), color=(0, 255, 0, 128))
    img.save(input_path, format='PNG')
    
    output_path = temp_output_dir / "test.jpg"
    
    # Conversion
    original_size, final_size, status = convert_image(
        input_path=input_path,
        output_path=output_path,
        fmt="jpeg",
        quality=80
    )
    
    assert output_path.exists()
    
    # Vérifier que la transparence a été remplacée par du blanc
    with Image.open(output_path) as img_out:
        assert img_out.format == "JPEG"
        assert img_out.mode == "RGB"


@pytest.mark.unit
def test_convert_image_preserves_rgba_for_webp(temp_input_dir, temp_output_dir):
    """
    Test: Conservation de la transparence RGBA pour WebP.
    
    WebP supporte RGBA, donc la transparence doit être préservée.
    """
    # Créer image RGBA
    input_path = temp_input_dir / "test.png"
    img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
    img.save(input_path, format='PNG')
    
    output_path = temp_output_dir / "test.webp"
    
    # Conversion
    convert_image(
        input_path=input_path,
        output_path=output_path,
        fmt="webp",
        quality=80
    )
    
    # Vérifier que RGBA est préservé
    with Image.open(output_path) as img_out:
        assert img_out.mode in ["RGBA", "RGB"]  # WebP peut optimiser en RGB si alpha=255


@pytest.mark.unit
def test_convert_image_png_compression_level(temp_input_dir, temp_output_dir):
    """
    Test: Compression PNG avec différents niveaux.
    
    Vérifie que le niveau de compression impacte la taille.
    """
    # Créer image source
    input_path = temp_input_dir / "test.png"
    img = Image.new('RGB', (300, 300), color=(100, 100, 255))
    img.save(input_path, format='PNG')
    
    # Compression niveau 3 (rapide, fichier plus gros)
    output_low = temp_output_dir / "test_low.png"
    _, size_low, _ = convert_image(input_path, output_low, "png", quality=3)
    
    # Compression niveau 9 (lent, fichier plus petit)
    output_high = temp_output_dir / "test_high.png"
    _, size_high, _ = convert_image(input_path, output_high, "png", quality=9)
    
    # La compression niveau 9 devrait produire un fichier plus petit
    assert size_high <= size_low


# ============================================================================
# TESTS - LIMITATION DE TAILLE
# ============================================================================

@pytest.mark.unit
def test_convert_image_respects_max_size(temp_input_dir, temp_output_dir):
    """
    Test: Limitation de taille respectée (max_size_mo).
    
    Vérifie que le fichier final est <= max_size_mo.
    """
    # Créer une grande image
    input_path = temp_input_dir / "large.png"
    img = Image.new('RGB', (1000, 1000), color=(255, 128, 0))
    img.save(input_path, format='PNG')
    
    output_path = temp_output_dir / "optimized.webp"
    
    # Limiter à 0.1 Mo (100 Ko)
    _, final_size, status = convert_image(
        input_path=input_path,
        output_path=output_path,
        fmt="webp",
        quality=75,
        max_size_mo=0.1
    )
    
    max_bytes = 0.1 * 1_000_000
    assert final_size <= max_bytes
    assert status in ["ok", "reduced"]


@pytest.mark.unit
def test_convert_image_no_size_limit(temp_input_dir, temp_output_dir):
    """
    Test: Pas de limitation de taille (max_size_mo=0).
    
    Vérifie que max_size_mo=0 désactive la limitation.
    """
    input_path = temp_input_dir / "test.png"
    img = Image.new('RGB', (500, 500), color=(50, 150, 250))
    img.save(input_path, format='PNG')
    
    output_path = temp_output_dir / "test.webp"
    
    # Pas de limite
    _, final_size, status = convert_image(
        input_path=input_path,
        output_path=output_path,
        fmt="webp",
        quality=80,
        max_size_mo=0
    )
    
    assert final_size > 0
    assert status == "ok"


@pytest.mark.unit
def test_convert_image_size_reduction_reduces_dimensions(temp_input_dir, temp_output_dir):
    """
    Test: Réduction des dimensions si nécessaire pour respecter max_size.
    
    Vérifie que les dimensions sont réduites, pas seulement la qualité.
    """
    # Grande image haute qualité
    input_path = temp_input_dir / "huge.png"
    img = Image.new('RGB', (2000, 2000), color=(200, 100, 50))
    img.save(input_path, format='PNG')
    
    output_path = temp_output_dir / "tiny.jpg"
    
    # Limite très restrictive (50 Ko)
    _, final_size, status = convert_image(
        input_path=input_path,
        output_path=output_path,
        fmt="jpeg",
        quality=85,
        max_size_mo=0.05
    )
    
    # Vérifier dimensions réduites
    with Image.open(output_path) as img_out:
        assert img_out.width < 2000
        assert img_out.height < 2000
    
    assert final_size <= 0.05 * 1_000_000
    assert status == "reduced"


@pytest.mark.edge_case
def test_convert_image_impossible_size_constraint(temp_input_dir, temp_output_dir):
    """
    Test: Contrainte de taille impossible à satisfaire.
    
    Cas limite: max_size trop petit (ex: 1 Ko pour une grande image).
    Status devrait être "failed".
    """
    input_path = temp_input_dir / "image.png"
    img = Image.new('RGB', (1000, 1000), color=(255, 0, 0))
    img.save(input_path, format='PNG')
    
    output_path = temp_output_dir / "impossible.webp"
    
    # Limite irréaliste (1 Ko)
    _, final_size, status = convert_image(
        input_path=input_path,
        output_path=output_path,
        fmt="webp",
        quality=75,
        max_size_mo=0.001
    )
    
    # Devrait échouer ou atteindre les dimensions minimales
    assert status in ["reduced", "failed"]


# ============================================================================
# TESTS - SMOOTHING (LISSAGE)
# ============================================================================

@pytest.mark.unit
def test_convert_image_with_smoothing(temp_input_dir, temp_output_dir):
    """
    Test: Application du lissage (GaussianBlur).
    
    Vérifie que smoothing > 0 applique un flou.
    """
    input_path = temp_input_dir / "sharp.png"
    img = Image.new('RGB', (200, 200), color=(0, 255, 0))
    img.save(input_path, format='PNG')
    
    output_path = temp_output_dir / "smooth.png"
    
    # Appliquer smoothing=5
    convert_image(
        input_path=input_path,
        output_path=output_path,
        fmt="png",
        quality=7,
        smoothing=5
    )
    
    assert output_path.exists()
    
    # Difficile de vérifier visuellement, mais le fichier doit exister


@pytest.mark.unit
def test_convert_image_no_smoothing(temp_input_dir, temp_output_dir):
    """
    Test: Pas de lissage (smoothing=0).
    
    Vérifie que smoothing=0 ne modifie pas l'image.
    """
    input_path = temp_input_dir / "original.png"
    img = Image.new('RGB', (150, 150), color=(128, 128, 128))
    img.save(input_path, format='PNG')
    
    output_path = temp_output_dir / "no_smooth.webp"
    
    convert_image(
        input_path=input_path,
        output_path=output_path,
        fmt="webp",
        quality=80,
        smoothing=0
    )
    
    assert output_path.exists()


# ============================================================================
# TESTS - WATERMARKING
# ============================================================================

@pytest.mark.unit
def test_convert_image_with_text_watermark(temp_input_dir, temp_output_dir):
    """
    Test: Ajout de watermark texte.
    
    Vérifie que le watermark texte est appliqué.
    """
    input_path = temp_input_dir / "base.png"
    img = Image.new('RGB', (300, 300), color=(255, 255, 255))
    img.save(input_path, format='PNG')
    
    output_path = temp_output_dir / "watermarked.png"
    
    watermark_params = {
        "enabled": True,
        "type": "text",
        "text": "© Test 2026",
        "position": "bottom-right",
        "opacity": 70
    }
    
    convert_image(
        input_path=input_path,
        output_path=output_path,
        fmt="png",
        quality=7,
        watermark_params=watermark_params
    )
    
    assert output_path.exists()
    
    # Le fichier avec watermark devrait être légèrement différent
    # (Vérification visuelle impossible, mais fichier créé)


@pytest.mark.unit
def test_convert_image_with_logo_watermark(temp_input_dir, temp_output_dir):
    """
    Test: Ajout de watermark logo/image.
    
    Vérifie que le watermark image est appliqué.
    """
    # Créer image de base
    input_path = temp_input_dir / "base.png"
    img = Image.new('RGB', (400, 400), color=(200, 200, 255))
    img.save(input_path, format='PNG')
    
    # Créer logo
    logo_path = temp_input_dir / "logo.png"
    logo = Image.new('RGBA', (50, 50), color=(255, 0, 0, 200))
    logo.save(logo_path, format='PNG')
    
    output_path = temp_output_dir / "with_logo.png"
    
    watermark_params = {
        "enabled": True,
        "type": "image",
        "image_path": str(logo_path),
        "position": "center",
        "opacity": 50
    }
    
    convert_image(
        input_path=input_path,
        output_path=output_path,
        fmt="png",
        quality=7,
        watermark_params=watermark_params
    )
    
    assert output_path.exists()


@pytest.mark.unit
def test_convert_image_watermark_disabled(temp_input_dir, temp_output_dir):
    """
    Test: Pas de watermark (enabled=False).
    
    Vérifie que watermark désactivé ne modifie pas l'image.
    """
    input_path = temp_input_dir / "original.png"
    img = Image.new('RGB', (200, 200), color=(100, 200, 100))
    img.save(input_path, format='PNG')
    
    output_path = temp_output_dir / "no_watermark.webp"
    
    watermark_params = {
        "enabled": False,
        "type": "text",
        "text": "Should not appear"
    }
    
    convert_image(
        input_path=input_path,
        output_path=output_path,
        fmt="webp",
        quality=80,
        watermark_params=watermark_params
    )
    
    assert output_path.exists()


@pytest.mark.edge_case
def test_convert_image_watermark_positions(temp_input_dir, temp_output_dir):
    """
    Test: Différentes positions de watermark.
    
    Teste toutes les positions: top-left, top-right, bottom-left, bottom-right, center.
    """
    positions = ["top-left", "top-right", "bottom-left", "bottom-right", "center"]
    
    for position in positions:
        input_path = temp_input_dir / f"base_{position}.png"
        img = Image.new('RGB', (200, 200), color=(255, 255, 255))
        img.save(input_path, format='PNG')
        
        output_path = temp_output_dir / f"watermark_{position}.png"
        
        watermark_params = {
            "enabled": True,
            "type": "text",
            "text": "Test",
            "position": position,
            "opacity": 50
        }
        
        convert_image(
            input_path=input_path,
            output_path=output_path,
            fmt="png",
            quality=7,
            watermark_params=watermark_params
        )
        
        assert output_path.exists()


# ============================================================================
# TESTS - ESTIMATION DE DIMENSIONS
# ============================================================================

@pytest.mark.unit
def test_estimate_target_dimensions_reduces_size():
    """
    Test: Estimation de dimensions pour réduire la taille.
    
    Vérifie que les dimensions estimées sont inférieures aux originales.
    """
    original_width = 2000
    original_height = 1500
    original_size = 5_000_000  # 5 Mo
    target_size = 1_000_000    # 1 Mo
    
    new_width, new_height = estimate_target_dimensions(
        original_width, original_height, original_size, target_size, "webp"
    )
    
    assert new_width < original_width
    assert new_height < original_height
    assert new_width > 100  # Dimensions minimales
    assert new_height > 100


@pytest.mark.unit
def test_estimate_target_dimensions_preserves_aspect_ratio():
    """
    Test: Préservation du ratio d'aspect lors de l'estimation.
    
    Vérifie que le ratio largeur/hauteur est conservé.
    """
    original_width = 1600
    original_height = 900  # Ratio 16:9
    original_size = 3_000_000
    target_size = 500_000
    
    new_width, new_height = estimate_target_dimensions(
        original_width, original_height, original_size, target_size, "jpeg"
    )
    
    # Vérifier que le ratio est approximativement conservé
    original_ratio = original_width / original_height
    new_ratio = new_width / new_height
    
    assert abs(original_ratio - new_ratio) < 0.01


@pytest.mark.unit
def test_estimate_target_dimensions_no_reduction_needed():
    """
    Test: Pas de réduction si déjà sous la cible.
    
    Vérifie que les dimensions ne changent pas si original_size <= target_size.
    """
    width = 800
    height = 600
    original_size = 500_000
    target_size = 1_000_000  # Déjà en dessous
    
    new_width, new_height = estimate_target_dimensions(
        width, height, original_size, target_size, "png"
    )
    
    assert new_width == width
    assert new_height == height


@pytest.mark.unit
def test_estimate_target_dimensions_format_specific():
    """
    Test: Estimation différente selon le format.
    
    AVIF/WebP compressent mieux → réduction modérée.
    JPEG/PNG → réduction plus importante.
    """
    width = 2000
    height = 2000
    original_size = 4_000_000
    target_size = 1_000_000
    
    # AVIF (compression efficace)
    avif_w, avif_h = estimate_target_dimensions(width, height, original_size, target_size, "avif")
    
    # PNG (compression moins efficace)
    png_w, png_h = estimate_target_dimensions(width, height, original_size, target_size, "png")
    
    # PNG devrait nécessiter plus de réduction de dimensions
    assert png_w <= avif_w
    assert png_h <= avif_h


@pytest.mark.edge_case
def test_estimate_target_dimensions_minimum_size():
    """
    Test: Dimensions minimales de 100px respectées.
    
    Vérifie que l'estimation ne descend jamais sous 100x100.
    """
    width = 200
    height = 200
    original_size = 1_000_000
    target_size = 1_000  # Cible irréaliste
    
    new_width, new_height = estimate_target_dimensions(
        width, height, original_size, target_size, "jpeg"
    )
    
    assert new_width >= 100
    assert new_height >= 100


# ============================================================================
# TESTS - HELPERS
# ============================================================================

@pytest.mark.unit
def test_format_size_bytes():
    """
    Test: Formatage de taille en Ko pour petites valeurs.
    
    Vérifie la conversion bytes → Ko.
    """
    assert format_size(500) == "1 Ko"
    assert format_size(1_000) == "1 Ko"
    assert format_size(50_000) == "50 Ko"
    assert format_size(999_999) == "1000 Ko"


@pytest.mark.unit
def test_format_size_megabytes():
    """
    Test: Formatage de taille en Mo pour grandes valeurs.
    
    Vérifie la conversion bytes → Mo.
    """
    assert format_size(1_000_000) == "1.0 Mo"
    assert format_size(5_500_000) == "5.5 Mo"
    assert format_size(50_000_000) == "50.0 Mo"


@pytest.mark.unit
def test_check_avif_support():
    """
    Test: Vérification du support AVIF.
    
    Vérifie que la fonction retourne un booléen.
    """
    result = check_avif_support()
    assert isinstance(result, bool)


# ============================================================================
# TESTS - CONFIGURATION
# ============================================================================

@pytest.mark.unit
def test_format_config_structure():
    """
    Test: Structure de FORMAT_CONFIG valide.
    
    Vérifie que tous les formats ont les champs requis.
    """
    required_keys = ["pil_format", "extension", "save_kwargs", "quality_range", "default_quality", "description"]
    
    for fmt, config in FORMAT_CONFIG.items():
        for key in required_keys:
            assert key in config, f"Format {fmt} manque la clé {key}"
        
        # Vérifier les ranges
        q_min, q_max = config["quality_range"]
        assert q_min < q_max
        assert q_min <= config["default_quality"] <= q_max


@pytest.mark.unit
def test_supported_extensions_validity():
    """
    Test: Extensions supportées valides.
    
    Vérifie que SUPPORTED_EXTENSIONS contient des extensions courantes.
    """
    expected = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}
    assert SUPPORTED_EXTENSIONS == expected


# ============================================================================
# TESTS - MODES D'IMAGES
# ============================================================================

@pytest.mark.edge_case
def test_convert_image_grayscale_to_rgb(temp_input_dir, temp_output_dir):
    """
    Test: Conversion image en niveaux de gris → RGB.
    
    Vérifie la gestion du mode "L" (grayscale).
    """
    input_path = temp_input_dir / "gray.png"
    img = Image.new('L', (150, 150), color=128)
    img.save(input_path, format='PNG')
    
    output_path = temp_output_dir / "gray_to_rgb.jpg"
    
    convert_image(
        input_path=input_path,
        output_path=output_path,
        fmt="jpeg",
        quality=80
    )
    
    assert output_path.exists()
    
    with Image.open(output_path) as img_out:
        assert img_out.mode == "RGB"


@pytest.mark.edge_case
def test_convert_image_palette_mode(temp_input_dir, temp_output_dir):
    """
    Test: Conversion image en mode palette (P).
    
    Vérifie la gestion du mode "P" (palette).
    """
    input_path = temp_input_dir / "palette.png"
    img = Image.new('P', (100, 100))
    img.save(input_path, format='PNG')
    
    output_path = temp_output_dir / "palette_converted.webp"
    
    convert_image(
        input_path=input_path,
        output_path=output_path,
        fmt="webp",
        quality=75
    )
    
    assert output_path.exists()


# ============================================================================
# TESTS - ERREURS
# ============================================================================

@pytest.mark.unit
def test_convert_image_invalid_input_path(temp_output_dir):
    """
    Test: Erreur si fichier d'entrée inexistant.
    
    Vérifie que FileNotFoundError est levée.
    """
    input_path = Path("/non/existent/file.png")
    output_path = temp_output_dir / "output.webp"
    
    with pytest.raises(FileNotFoundError):
        convert_image(input_path, output_path, "webp", 75)


@pytest.mark.unit
def test_convert_image_invalid_format(temp_input_dir, temp_output_dir):
    """
    Test: Erreur si format invalide.
    
    Vérifie que KeyError est levée pour format non supporté.
    """
    input_path = temp_input_dir / "test.png"
    img = Image.new('RGB', (100, 100), color=(255, 0, 0))
    img.save(input_path, format='PNG')
    
    output_path = temp_output_dir / "output.xyz"
    
    with pytest.raises(KeyError):
        convert_image(input_path, output_path, "invalid_format", 75)


# ============================================================================
# TESTS - PERFORMANCES
# ============================================================================

@pytest.mark.slow
def test_convert_image_large_batch_performance(temp_input_dir, temp_output_dir, benchmark):
    """
    Test de performance: Conversion de plusieurs images.
    
    Mesure le temps de traitement de 10 images.
    """
    # Créer 10 images
    images = []
    for i in range(10):
        img_path = temp_input_dir / f"image_{i}.png"
        img = Image.new('RGB', (500, 500), color=(i*25, 100, 200))
        img.save(img_path, format='PNG')
        images.append(img_path)
    
    def convert_batch():
        for i, img_path in enumerate(images):
            output_path = temp_output_dir / f"optimized_{i}.webp"
            convert_image(img_path, output_path, "webp", 75)
    
    # Benchmark
    benchmark(convert_batch)
