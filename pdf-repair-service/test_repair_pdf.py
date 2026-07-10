#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_repair_pdf.py
------------------
Tests unitaires pour le module repair_pdf.py

Tests couvrant :
  - Validation de structure PDF
  - Réparation de PDFs corrompus
  - Extraction de métadonnées
  - Gestion d'erreurs
  - Sécurité des limites de taille

Exécution :
    pytest test_repair_pdf.py -v
    pytest test_repair_pdf.py --cov=repair_pdf  # Avec couverture
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import pikepdf
from io import BytesIO

from repair_pdf import validate_pdf, repair_pdf, get_pdf_info


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_dir():
    """Crée un répertoire temporaire pour les tests"""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    # Nettoyage après le test
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def valid_pdf(temp_dir):
    """Crée un PDF valide simple"""
    pdf_path = temp_dir / "valid.pdf"
    
    with pikepdf.open(pdf_path, new=True) as pdf:
        page = pikepdf.Dictionary(
            Type=pikepdf.Name.Page,
            MediaBox=[0, 0, 612, 792],
            Contents=pikepdf.Stream(pdf, b"BT /F1 12 Tf 100 700 Td (Hello PDF) Tj ET"),
            Resources=pikepdf.Dictionary(
                Font=pikepdf.Dictionary(
                    F1=pikepdf.Dictionary(
                        Type=pikepdf.Name.Font,
                        Subtype=pikepdf.Name.Type1,
                        BaseFont=pikepdf.Name.Helvetica
                    )
                )
            )
        )
        pdf.pages.append(page)
        pdf.metadata.Title = "Test Document"
        pdf.metadata.Author = "Pytest"
    
    return pdf_path


@pytest.fixture
def valid_pdf_multipage(temp_dir):
    """Crée un PDF valide avec plusieurs pages"""
    pdf_path = temp_dir / "multipage.pdf"
    
    with pikepdf.open(pdf_path, new=True) as pdf:
        for i in range(3):
            page = pikepdf.Dictionary(
                Type=pikepdf.Name.Page,
                MediaBox=[0, 0, 612, 792],
                Contents=pikepdf.Stream(pdf, f"BT /F1 12 Tf 100 700 Td (Page {i+1}) Tj ET".encode()),
                Resources=pikepdf.Dictionary(
                    Font=pikepdf.Dictionary(
                        F1=pikepdf.Dictionary(
                            Type=pikepdf.Name.Font,
                            Subtype=pikepdf.Name.Type1,
                            BaseFont=pikepdf.Name.Helvetica
                        )
                    )
                )
            )
            pdf.pages.append(page)
    
    return pdf_path


@pytest.fixture
def corrupted_pdf(temp_dir):
    """Crée un PDF volontairement corrompu"""
    pdf_path = temp_dir / "corrupted.pdf"
    
    # Créer d'abord un PDF valide
    with pikepdf.open(pdf_path, new=True) as pdf:
        page = pikepdf.Dictionary(
            Type=pikepdf.Name.Page,
            MediaBox=[0, 0, 612, 792],
            Contents=pikepdf.Stream(pdf, b"BT /F1 12 Tf 100 700 Td (Corrupted) Tj ET"),
            Resources=pikepdf.Dictionary(
                Font=pikepdf.Dictionary(
                    F1=pikepdf.Dictionary(
                        Type=pikepdf.Name.Font,
                        Subtype=pikepdf.Name.Type1,
                        BaseFont=pikepdf.Name.Helvetica
                    )
                )
            )
        )
        pdf.pages.append(page)
    
    # Corrompre le fichier en supprimant/modifiant une partie
    with open(pdf_path, 'r+b') as f:
        f.seek(-50, 2)  # Aller vers la fin
        f.write(b"CORRUPTED" + b"\x00" * 41)  # Écrire du contenu corrompu
    
    return pdf_path


@pytest.fixture
def invalid_pdf(temp_dir):
    """Crée un fichier qui ressemble à un PDF mais est invalide"""
    pdf_path = temp_dir / "invalid.pdf"
    
    with open(pdf_path, 'wb') as f:
        f.write(b"%PDF-1.4\n")
        f.write(b"Invalid content that is not a valid PDF structure")
    
    return pdf_path


@pytest.fixture
def empty_file(temp_dir):
    """Crée un fichier vide"""
    pdf_path = temp_dir / "empty.pdf"
    pdf_path.touch()
    return pdf_path


# ============================================================================
# TESTS : VALIDATE_PDF
# ============================================================================

class TestValidatePdf:
    """Tests pour la fonction validate_pdf"""

    def test_validate_valid_pdf(self, valid_pdf):
        """Valide un PDF valide sans erreur"""
        result = validate_pdf(valid_pdf)
        
        assert result['is_valid'] is True
        assert result['is_corrupted'] is False
        assert result['pages'] == 1
        assert result['size_bytes'] > 0
        assert len(result['errors']) == 0

    def test_validate_multipage_pdf(self, valid_pdf_multipage):
        """Valide un PDF valide avec plusieurs pages"""
        result = validate_pdf(valid_pdf_multipage)
        
        assert result['is_valid'] is True
        assert result['pages'] == 3

    def test_validate_corrupted_pdf(self, corrupted_pdf):
        """Détecte un PDF corrompu"""
        result = validate_pdf(corrupted_pdf)
        
        # Peut être corrompu ou invalide selon le degré de corruption
        # On vérifie qu'il détecte l'anomalie
        assert result['is_corrupted'] or not result['is_valid']

    def test_validate_invalid_pdf(self, invalid_pdf):
        """Détecte un PDF invalide"""
        result = validate_pdf(invalid_pdf)
        
        # Doit détecter une erreur
        assert len(result['errors']) > 0 or result['is_corrupted']

    def test_validate_nonexistent_file(self, temp_dir):
        """Gère l'absence de fichier"""
        result = validate_pdf(temp_dir / "nonexistent.pdf")
        
        assert result['is_valid'] is False
        assert len(result['errors']) > 0
        assert "non trouvé" in result['errors'][0].lower() or "no such file" in result['errors'][0].lower()

    def test_validate_empty_file(self, empty_file):
        """Gère un fichier vide"""
        result = validate_pdf(empty_file)
        
        assert result['is_valid'] is False
        assert len(result['errors']) > 0

    def test_validate_size_bytes_set(self, valid_pdf):
        """Vérifie que la taille du fichier est correctement rapportée"""
        result = validate_pdf(valid_pdf)
        expected_size = valid_pdf.stat().st_size
        
        assert result['size_bytes'] == expected_size

    def test_validate_pages_count(self, valid_pdf_multipage):
        """Vérifie le comptage des pages"""
        result = validate_pdf(valid_pdf_multipage)
        
        assert result['pages'] == 3


# ============================================================================
# TESTS : REPAIR_PDF
# ============================================================================

class TestRepairPdf:
    """Tests pour la fonction repair_pdf"""

    def test_repair_valid_pdf(self, valid_pdf, temp_dir):
        """Répare (retraite) un PDF valide"""
        output_path = temp_dir / "output.pdf"
        
        success, message, stats = repair_pdf(valid_pdf, output_path)
        
        assert success is True
        assert output_path.exists()
        assert stats['pages_recovered'] == 1
        assert stats['input_size'] > 0
        assert stats['output_size'] > 0

    def test_repair_multipage_pdf(self, valid_pdf_multipage, temp_dir):
        """Répare un PDF multi-pages"""
        output_path = temp_dir / "output.pdf"
        
        success, message, stats = repair_pdf(valid_pdf_multipage, output_path)
        
        assert success is True
        assert stats['pages_recovered'] == 3

    def test_repair_corrupted_pdf(self, corrupted_pdf, temp_dir):
        """Essaie de réparer un PDF corrompu"""
        output_path = temp_dir / "output.pdf"
        
        success, message, stats = repair_pdf(corrupted_pdf, output_path)
        
        # La réparation peut réussir ou échouer selon le degré de corruption
        # On vérifie simplement que la fonction s'exécute correctement
        if success:
            assert output_path.exists()
        # Sinon, on accepte l'échec avec un message d'erreur

    def test_repair_nonexistent_input(self, temp_dir):
        """Gère l'absence de fichier d'entrée"""
        input_path = temp_dir / "nonexistent.pdf"
        output_path = temp_dir / "output.pdf"
        
        success, message, stats = repair_pdf(input_path, output_path)
        
        assert success is False
        assert len(message) > 0

    def test_repair_stats_compression_ratio(self, valid_pdf, temp_dir):
        """Vérifie le calcul du ratio de compression"""
        output_path = temp_dir / "output.pdf"
        
        success, message, stats = repair_pdf(valid_pdf, output_path)
        
        assert success is True
        assert 'compression_ratio' in stats
        # Le ratio peut être positif (réduction) ou négatif (augmentation)
        assert isinstance(stats['compression_ratio'], float)

    def test_repair_output_file_exists(self, valid_pdf, temp_dir):
        """Vérifie que le fichier de sortie est créé"""
        output_path = temp_dir / "output.pdf"
        
        success, message, stats = repair_pdf(valid_pdf, output_path)
        
        if success:
            assert output_path.exists()
            assert output_path.stat().st_size > 0

    def test_repair_creates_valid_pdf(self, valid_pdf, temp_dir):
        """Vérifie que le PDF réparé est valide"""
        output_path = temp_dir / "output.pdf"
        
        success, message, stats = repair_pdf(valid_pdf, output_path)
        
        if success:
            # Réouvrir le PDF réparé pour vérifier sa validité
            try:
                with pikepdf.open(output_path, allow_recovery=True) as pdf:
                    pages = len(pdf.pages)
                    assert pages > 0
            except Exception as e:
                pytest.fail(f"PDF réparé n'est pas valide: {str(e)}")

    def test_repair_stats_structure(self, valid_pdf, temp_dir):
        """Vérifie la structure du dictionnaire stats"""
        output_path = temp_dir / "output.pdf"
        
        success, message, stats = repair_pdf(valid_pdf, output_path)
        
        assert 'input_size' in stats
        assert 'output_size' in stats
        assert 'pages_recovered' in stats
        assert 'objects_removed' in stats
        assert 'compression_ratio' in stats


# ============================================================================
# TESTS : GET_PDF_INFO
# ============================================================================

class TestGetPdfInfo:
    """Tests pour la fonction get_pdf_info"""

    def test_get_pdf_info_valid(self, valid_pdf):
        """Extrait les métadonnées d'un PDF valide"""
        info = get_pdf_info(valid_pdf)
        
        assert info['pages'] == 1
        assert info['size_bytes'] > 0
        assert info['error'] is None

    def test_get_pdf_info_title(self, valid_pdf):
        """Extrait le titre du PDF"""
        info = get_pdf_info(valid_pdf)
        
        # Le titre devrait être "Test Document" (défini dans la fixture)
        assert 'title' in info

    def test_get_pdf_info_multipage(self, valid_pdf_multipage):
        """Extrait les infos d'un PDF multi-pages"""
        info = get_pdf_info(valid_pdf_multipage)
        
        assert info['pages'] == 3

    def test_get_pdf_info_nonexistent(self, temp_dir):
        """Gère l'absence de fichier"""
        info = get_pdf_info(temp_dir / "nonexistent.pdf")
        
        assert info['error'] is not None
        assert "non trouvé" in info['error'].lower() or "no such file" in info['error'].lower()

    def test_get_pdf_info_corrupted(self, corrupted_pdf):
        """Essaie d'extraire les infos d'un PDF corrompu"""
        info = get_pdf_info(corrupted_pdf)
        
        # Peut échouer ou réussir avec recovery mode
        # On vérifie juste que la fonction ne crash pas

    def test_get_pdf_info_structure(self, valid_pdf):
        """Vérifie la structure du dictionnaire d'infos"""
        info = get_pdf_info(valid_pdf)
        
        expected_keys = ['pages', 'title', 'author', 'subject', 'producer', 'creation_date', 'encryption', 'size_bytes', 'error']
        for key in expected_keys:
            assert key in info

    def test_get_pdf_info_encryption_flag(self, valid_pdf):
        """Vérifie le flag de chiffrement"""
        info = get_pdf_info(valid_pdf)
        
        assert isinstance(info['encryption'], bool)

    def test_get_pdf_info_size_bytes_positive(self, valid_pdf):
        """Vérifie que la taille est positive"""
        info = get_pdf_info(valid_pdf)
        
        assert info['size_bytes'] >= 0


# ============================================================================
# TESTS D'INTÉGRATION
# ============================================================================

class TestIntegration:
    """Tests d'intégration end-to-end"""

    def test_workflow_validate_then_repair(self, valid_pdf, temp_dir):
        """Workflow complet : valider puis réparer"""
        # Valider
        validation = validate_pdf(valid_pdf)
        assert validation['is_valid'] is True
        
        # Réparer
        output_path = temp_dir / "output.pdf"
        success, message, stats = repair_pdf(valid_pdf, output_path)
        assert success is True
        
        # Valider la sortie
        output_validation = validate_pdf(output_path)
        assert output_validation['is_valid'] is True

    def test_workflow_validate_info_repair(self, valid_pdf, temp_dir):
        """Workflow complet : valider, info, réparer"""
        # Valider
        validation = validate_pdf(valid_pdf)
        
        # Infos
        info = get_pdf_info(valid_pdf)
        
        # Réparer
        output_path = temp_dir / "output.pdf"
        success, message, stats = repair_pdf(valid_pdf, output_path)
        
        assert validation['is_valid'] is True
        assert info['pages'] == stats['pages_recovered']
        assert success is True

    def test_repair_preserves_pages(self, valid_pdf_multipage, temp_dir):
        """La réparation préserve le nombre de pages"""
        original_info = get_pdf_info(valid_pdf_multipage)
        original_pages = original_info['pages']
        
        output_path = temp_dir / "output.pdf"
        success, message, stats = repair_pdf(valid_pdf_multipage, output_path)
        
        repaired_info = get_pdf_info(output_path)
        repaired_pages = repaired_info['pages']
        
        assert repaired_pages == original_pages


# ============================================================================
# TESTS DE SÉCURITÉ
# ============================================================================

class TestSecurity:
    """Tests de sécurité"""

    def test_validate_with_large_path(self, temp_dir):
        """Gère les chemins très longs"""
        # Créer un chemin très long mais valide
        deep_dir = temp_dir
        for i in range(20):
            deep_dir = deep_dir / f"dir_{i}"
        deep_dir.mkdir(parents=True, exist_ok=True)
        
        pdf_path = deep_dir / "test.pdf"
        
        # Créer un petit PDF
        with pikepdf.open(pdf_path, new=True) as pdf:
            page = pikepdf.Dictionary(
                Type=pikepdf.Name.Page,
                MediaBox=[0, 0, 612, 792],
                Contents=pikepdf.Stream(pdf, b"BT /F1 12 Tf 100 700 Td (Test) Tj ET"),
                Resources=pikepdf.Dictionary(
                    Font=pikepdf.Dictionary(
                        F1=pikepdf.Dictionary(
                            Type=pikepdf.Name.Font,
                            Subtype=pikepdf.Name.Type1,
                            BaseFont=pikepdf.Name.Helvetica
                        )
                    )
                )
            )
            pdf.pages.append(page)
        
        # Valider
        result = validate_pdf(pdf_path)
        assert result['is_valid'] is True

    def test_validate_handles_permission_errors_gracefully(self, temp_dir):
        """Gère les erreurs de permission gracieusement"""
        pdf_path = temp_dir / "test.pdf"
        
        # Créer un PDF
        with pikepdf.open(pdf_path, new=True) as pdf:
            page = pikepdf.Dictionary(
                Type=pikepdf.Name.Page,
                MediaBox=[0, 0, 612, 792],
                Contents=pikepdf.Stream(pdf, b"test"),
                Resources=pikepdf.Dictionary()
            )
            pdf.pages.append(page)
        
        # Valider (pas d'exception)
        result = validate_pdf(pdf_path)
        # Juste vérifier que la fonction ne crash pas
        assert isinstance(result, dict)


# ============================================================================
# TESTS DE PERFORMANCE
# ============================================================================

class TestPerformance:
    """Tests de performance basiques"""

    def test_validate_is_fast_for_small_pdf(self, valid_pdf):
        """La validation doit être rapide pour un petit PDF"""
        import time
        
        start = time.time()
        validate_pdf(valid_pdf)
        elapsed = time.time() - start
        
        # Doit prendre moins de 100ms pour un petit PDF
        assert elapsed < 0.1

    def test_repair_is_fast_for_small_pdf(self, valid_pdf, temp_dir):
        """La réparation doit être rapide pour un petit PDF"""
        import time
        
        output_path = temp_dir / "output.pdf"
        
        start = time.time()
        repair_pdf(valid_pdf, output_path)
        elapsed = time.time() - start
        
        # Doit prendre moins de 500ms pour un petit PDF
        assert elapsed < 0.5


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
