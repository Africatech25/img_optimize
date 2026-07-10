#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdf_analyzer.py
---------------
Analyse avancée de PDFs : extraction de texte, détection du type de document,
extraction du nom/sujet, et génération de noms normalisés.

Dépendances :
    pip install pdfplumber pikepdf
"""

import pdfplumber
import pikepdf
import re
from pathlib import Path
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Patterns de détection de document
DOCUMENT_PATTERNS = {
    'facture': {
        'keywords': [r'\bfacture\b', r'\binvoice\b', r'n[°#]\s*facture', r'invoice\s*#', r'num\.\s*facture'],
        'score_weight': 1.0
    },
    'contrat': {
        'keywords': [r'\bcontrat\b', r'\bagreement\b', r'\bcontract\b', r'contrat de', r'convention'],
        'score_weight': 0.9
    },
    'rapport': {
        'keywords': [r'\brappport\b', r'\breport\b', r'rapport d[\'e]', r'rapport annuel', r'rapport final'],
        'score_weight': 0.85
    },
    'devis': {
        'keywords': [r'\bdevis\b', r'\bquote\b', r'\bestimate\b', r'n[°#]\s*devis'],
        'score_weight': 0.95
    },
    'commande': {
        'keywords': [r'\bcommande\b', r'\border\b', r'bon de commande', r'order\s*#'],
        'score_weight': 0.9
    },
    'livraison': {
        'keywords': [r'\blivraison\b', r'\bbon de livraison\b', r'\bdelivery\b', r'shipping'],
        'score_weight': 0.85
    },
    'cv': {
        'keywords': [r'\bcv\b', r'\bcurriculum\b', r'\bfiche personnelle\b', r'\bresume\b'],
        'score_weight': 0.95
    },
    'facture_credit': {
        'keywords': [r'\bfacture\b.*\bcredit\b', r'\bavoir\b', r'\bcredit\s*note\b'],
        'score_weight': 1.0
    },
    'bulletin': {
        'keywords': [r'\bbulletin\b', r'\bpaie\b', r'\bsalaire\b', r'\bpayslip\b'],
        'score_weight': 0.95
    },
    'certificat': {
        'keywords': [r'\bcertificat\b', r'\bcertificate\b', r'\battestation\b'],
        'score_weight': 0.9
    }
}

# Patterns pour extraction de noms/sujets
NAME_PATTERNS = {
    'facture': [
        r'(?:client|destinataire)\s*[:=]\s*([^\n,;]+)',
        r'(?:facturé à|billed to|sold to)\s*[:=]?\s*([^\n,;]+)',
        r'^([A-Z][a-zé]+(?:\s+[A-Z][a-zé]+)*)\s*(?:\.|\n)',
    ],
    'personne': [
        r'^((?:[A-Z][a-zé]+\s+)+(?:[A-Z][a-zé]+))\s*$',
        r'(?:nom|name)\s*[:=]\s*([^,\n;]+)',
        r'(?:de|from)\s*[:=]\s*([^,\n;]+)'
    ],
    'societe': [
        r'(?:entreprise|company|société)\s*[:=]\s*([^,\n;]+)',
        r'^([A-Z][^,\n;]*(?:SARL|SAS|SA|EIRL|SASU))',
        r'(?:raison sociale)\s*[:=]\s*([^,\n;]+)'
    ]
}


def extract_metadata(file_path: Path) -> Dict[str, str]:
    """
    Extrait les métadonnées standard d'un PDF avec pikepdf.

    Args:
        file_path: Chemin du fichier PDF

    Returns:
        {
            'title': str,
            'author': str,
            'subject': str,
            'producer': str,
            'creation_date': str
        }
    """
    metadata = {
        'title': '',
        'author': '',
        'subject': '',
        'producer': '',
        'creation_date': ''
    }

    try:
        with pikepdf.open(file_path, allow_recovery=True) as pdf:
            if pdf.metadata:
                metadata['title'] = str(pdf.metadata.Title or '').strip()
                metadata['author'] = str(pdf.metadata.Author or '').strip()
                metadata['subject'] = str(pdf.metadata.Subject or '').strip()
                metadata['producer'] = str(pdf.metadata.Producer or '').strip()
                metadata['creation_date'] = str(pdf.metadata.CreationDate or '').strip()
    except Exception as e:
        logger.debug(f"Impossible extraire métadonnées: {e}")

    return metadata


def extract_text(file_path: Path, max_pages: int = 3) -> str:
    """
    Extrait le texte des premières pages d'un PDF avec pdfplumber.

    Args:
        file_path: Chemin du fichier PDF
        max_pages: Nombre maximum de pages à extraire (défaut: 3)

    Returns:
        Texte concaténé des pages
    """
    text = ""

    try:
        with pdfplumber.open(file_path) as pdf:
            pages_to_read = min(max_pages, len(pdf.pages))

            for i in range(pages_to_read):
                page = pdf.pages[i]
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Page {i+1} ---\n{page_text}"

    except Exception as e:
        logger.debug(f"Impossible extraire texte: {e}")

    return text.strip()


def normalize_text(text: str) -> str:
    """
    Normalise le texte pour les recherches.

    Args:
        text: Texte brut

    Returns:
        Texte normalisé (minuscules, accents supprimés partiellement)
    """
    # Minuscules
    text = text.lower()

    # Remplacer les accents courants (approche simple)
    replacements = {
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'à': 'a', 'â': 'a', 'ä': 'a',
        'ù': 'u', 'û': 'u', 'ü': 'u',
        'ï': 'i', 'î': 'i',
        'ô': 'o', 'ö': 'o',
        'ç': 'c',
        'œ': 'oe', 'æ': 'ae'
    }
    for original, replacement in replacements.items():
        text = text.replace(original, replacement)

    return text


def detect_document_type(text: str) -> Tuple[str, float]:
    """
    Détecte le type de document (facture, contrat, etc.) par analyse textuelle.

    Args:
        text: Texte extrait du PDF

    Returns:
        (type_document: str, confidence: float 0-1)
    """
    if not text:
        return 'document', 0.0

    normalized_text = normalize_text(text)
    scores = {}

    # Évaluer chaque type
    for doc_type, patterns_info in DOCUMENT_PATTERNS.items():
        score = 0.0
        keywords = patterns_info['keywords']
        weight = patterns_info['score_weight']

        for keyword_pattern in keywords:
            matches = len(re.findall(keyword_pattern, normalized_text, re.IGNORECASE))
            if matches > 0:
                # Score: présence + fréquence
                score += min(matches * 0.1, 0.5) * weight

        scores[doc_type] = min(score, weight)  # Cap au weight

    # Retourner le type avec le meilleur score
    if scores:
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        return best_type if best_score > 0.1 else 'document', best_score
    else:
        return 'document', 0.0


def extract_name_from_text(text: str, doc_type: str = 'document') -> str:
    """
    Extrait le nom/sujet principal du document du texte.

    Stratégies :
      1. Si doc_type est facture/devis/commande : chercher numéro
      2. Si c'est un CV : chercher un nom
      3. Sinon : chercher titre/sujet général

    Args:
        text: Texte extrait du PDF
        doc_type: Type de document détecté

    Returns:
        Nom/sujet extrait (ou chaîne vide si non trouvé)
    """
    if not text:
        return ''

    # Chercher un numéro de document (facture, devis, etc.)
    if doc_type in ['facture', 'facture_credit', 'devis', 'commande']:
        patterns = [
            r'(?:n[°#]\s*)?(?:facture|invoice|devis|quote|commande|order)\s*[:=]?\s*([0-9]+(?:[/-][0-9]+)*)',
            r'(?:ref|reference|num)\s*[:=]?\s*([A-Z0-9\-/]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

    # Chercher un nom de personne (CV, contrat)
    if doc_type in ['cv', 'contrat']:
        # Première ligne en majuscules (probablement un nom)
        first_line = text.split('\n')[0].strip()
        if first_line and len(first_line) > 3 and len(first_line) < 100:
            return first_line

    # Chercher titre/sujet général
    for pattern in [
        r'(?:titre|title|sujet|subject|re:)\s*[:=]\s*([^\n,;]+)',
        r'^([A-Z][^\n]*?)(?:\n|$)',
    ]:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            name = match.group(1).strip()
            if 3 < len(name) < 100:
                return name

    return ''


def sanitize_filename(name: str, doc_type: str = '') -> str:
    """
    Convertit un nom/sujet en nom de fichier valide.

    Args:
        name: Nom brut extrait
        doc_type: Type de document (optionnel)

    Returns:
        Nom de fichier valide (sans caractères interdits)
    """
    # Minuscules + majuscule début
    name = name.strip()

    # Remplacer caractères problématiques
    name = re.sub(r'[<>:"/\\|?*\n\r\t]', '_', name)
    name = re.sub(r'\s+', '_', name)
    name = re.sub(r'_+', '_', name)

    # Limiter la longueur
    name = name[:50]

    # Construire le nom final
    if doc_type:
        doc_type_upper = doc_type.upper().replace('_', '')
        return f"{doc_type_upper}_{name}"
    else:
        return name


def analyze_pdf(file_path: Path) -> Dict[str, any]:
    """
    Analyse complète d'un PDF : métadonnées, texte, type, nom.

    Args:
        file_path: Chemin du fichier PDF

    Returns:
        {
            'metadata': {...},
            'text': '...',
            'document_type': str,
            'document_type_confidence': float,
            'extracted_name': str,
            'suggested_filename': str,
            'error': None or str
        }
    """
    result = {
        'metadata': {},
        'text': '',
        'document_type': 'document',
        'document_type_confidence': 0.0,
        'extracted_name': '',
        'suggested_filename': '',
        'error': None
    }

    try:
        # Vérifier existence
        if not file_path.exists():
            result['error'] = "Fichier non trouvé"
            return result

        # Extraire métadonnées
        result['metadata'] = extract_metadata(file_path)

        # Extraire texte (premières 3 pages)
        result['text'] = extract_text(file_path, max_pages=3)

        # Utiliser title depuis métadonnées si disponible
        title = result['metadata'].get('title', '').strip()

        # Détecter type
        analysis_text = f"{title}\n{result['text']}" if title else result['text']
        doc_type, confidence = detect_document_type(analysis_text)
        result['document_type'] = doc_type
        result['document_type_confidence'] = round(confidence, 2)

        # Extraire nom
        extracted_name = extract_name_from_text(analysis_text, doc_type)
        if not extracted_name and title:
            extracted_name = title
        result['extracted_name'] = extracted_name

        # Générer nom de fichier suggéré
        if extracted_name:
            sanitized = sanitize_filename(extracted_name, doc_type)
            result['suggested_filename'] = f"{sanitized}.pdf"
        else:
            result['suggested_filename'] = f"{doc_type}.pdf"

    except Exception as e:
        result['error'] = f"Erreur analyse: {str(e)}"
        logger.error(f"Erreur lors de l'analyse du PDF: {e}")

    return result


def get_analysis_summary(analysis: Dict) -> str:
    """
    Génère un résumé textuel de l'analyse pour l'utilisateur.

    Args:
        analysis: Résultat de analyze_pdf()

    Returns:
        String formaté avec les infos principales
    """
    if analysis.get('error'):
        return f"❌ Erreur: {analysis['error']}"

    lines = [
        f"📄 Type détecté: {analysis['document_type'].upper()} ({analysis['document_type_confidence']*100:.0f}%)",
        f"📝 Nom extrait: {analysis['extracted_name'] or 'N/A'}",
        f"🏷️  Nom suggéré: {analysis['suggested_filename']}",
    ]

    if analysis['metadata'].get('title'):
        lines.append(f"📋 Titre (métadonnées): {analysis['metadata']['title']}")

    if analysis['metadata'].get('author'):
        lines.append(f"✍️  Auteur: {analysis['metadata']['author']}")

    if analysis['metadata'].get('subject'):
        lines.append(f"🔍 Sujet: {analysis['metadata']['subject']}")

    return "\n".join(lines)


# Alias pour compatibilité
format_size = lambda size_bytes: f"{size_bytes / (1024*1024):.2f}MB" if size_bytes > 0 else "0 B"
