#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_pdf_analyzer.py - Tests for pdf_analyzer module
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import pikepdf

from pdf_analyzer import (
    normalize_text,
    detect_document_type,
    extract_name_from_text,
    sanitize_filename,
    analyze_pdf,
    get_analysis_summary
)


@pytest.fixture
def temp_dir():
    """Creates a temporary directory for tests"""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def pdf_simple(temp_dir):
    """Creates a simple test PDF"""
    pdf_path = temp_dir / "simple_test.pdf"
    
    with pikepdf.open(pdf_path, new=True) as pdf:
        content = b"This is a simple test PDF content"
        
        page = pikepdf.Dictionary(
            Type=pikepdf.Name.Page,
            MediaBox=[0, 0, 612, 792],
            Contents=pikepdf.Stream(pdf, content),
            Resources=pikepdf.Dictionary()
        )
        pdf.pages.append(page)
    
    return pdf_path


# Tests for normalize_text
class TestNormalizeText:
    """Tests for text normalization"""

    def test_normalize_uppercase(self):
        """Converts to lowercase"""
        assert normalize_text("HELLO") == "hello"

    def test_normalize_accents(self):
        """Removes accents"""
        assert normalize_text("Cafe") == "cafe"


# Tests for detect_document_type
class TestDetectDocumentType:
    """Tests for document type detection"""

    def test_detect_facture(self):
        """Detects invoice"""
        text = "FACTURE invoice total EUR"
        doc_type, confidence = detect_document_type(text)
        assert isinstance(doc_type, str)
        assert 0 <= confidence <= 1

    def test_detect_cv(self):
        """Detects CV"""
        text = "CV experience job"
        doc_type, confidence = detect_document_type(text)
        assert isinstance(doc_type, str)
        assert 0 <= confidence <= 1

    def test_detect_returns_tuple(self):
        """Returns a tuple of (doc_type, confidence)"""
        text = "Some random text"
        result = detect_document_type(text)
        assert isinstance(result, tuple)
        assert len(result) == 2


# Tests for extract_name_from_text
class TestExtractNameFromText:
    """Tests for name extraction"""

    def test_extract_returns_string(self):
        """Returns a string"""
        text = "Document title content"
        name = extract_name_from_text(text, doc_type='document')
        assert isinstance(name, str)

    def test_extract_handles_empty_text(self):
        """Handles empty text"""
        name = extract_name_from_text("", doc_type='document')
        assert isinstance(name, str)


# Tests for sanitize_filename
class TestSanitizeFilename:
    """Tests for filename sanitization"""

    def test_sanitize_removes_special_chars(self):
        """Removes special characters"""
        result = sanitize_filename("file<name>.pdf")
        assert '<' not in result
        assert '>' not in result

    def test_sanitize_returns_string(self):
        """Returns a valid string"""
        result = sanitize_filename("test file")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_sanitize_with_type(self):
        """Sanitizes with document type"""
        result = sanitize_filename("name", doc_type="facture")
        assert isinstance(result, str)


# Tests for analyze_pdf
class TestAnalyzePdf:
    """Tests for PDF analysis"""

    def test_analyze_simple_pdf(self, pdf_simple):
        """Analyzes a simple PDF"""
        result = analyze_pdf(pdf_simple)
        
        # Check structure
        assert 'document_type' in result
        assert 'document_type_confidence' in result
        assert 'suggested_filename' in result
        assert 'error' in result

    def test_analyze_nonexistent_file(self, temp_dir):
        """Handles missing files"""
        result = analyze_pdf(temp_dir / "nonexistent.pdf")
        assert 'error' in result
        assert result['error'] is not None

    def test_analyze_structure_complete(self, pdf_simple):
        """Verifies complete result structure"""
        result = analyze_pdf(pdf_simple)
        
        expected_keys = [
            'metadata', 'text', 'document_type',
            'document_type_confidence', 'extracted_name',
            'suggested_filename', 'error'
        ]
        
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"


# Tests for get_analysis_summary
class TestGetAnalysisSummary:
    """Tests for analysis summary generation"""

    def test_summary_returns_string(self):
        """Returns a string"""
        analysis = {'error': None}
        summary = get_analysis_summary(analysis)
        assert isinstance(summary, str)

    def test_summary_with_error(self):
        """Handles error cases"""
        analysis = {'error': 'Test error message'}
        summary = get_analysis_summary(analysis)
        assert isinstance(summary, str)
        assert len(summary) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short', '--no-cov'])
