#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service FastAPI dédié à la réparation et l'analyse de PDF.
Séparé du backend d'optimisation d'images (périmètre fonctionnel distinct).
"""
import sys
import io

# Forcer l'encodage UTF-8 pour Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import tempfile
import uuid
import asyncio
import logging
import os

from repair_pdf import validate_pdf, repair_pdf, get_pdf_info
from pdf_analyzer import analyze_pdf, get_analysis_summary

logger = logging.getLogger(__name__)

# Configuration CORS sécurisée - mêmes origines que le backend image
ALLOWED_ORIGINS = [
    "https://img-optimize.vercel.app",  # Production frontend
    "http://localhost:5173",             # Dev frontend (Vite)
    "http://localhost:3000",             # Dev frontend (alternative)
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000"
]

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

app = FastAPI(title="PDF Repair Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

TEMP_DIR = Path(tempfile.gettempdir()) / "pdf_repair_service"
TEMP_DIR.mkdir(exist_ok=True)


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@app.post("/api/pdf/repair")
async def repair_pdf_endpoint(file: UploadFile = File(...)):
    """
    Répare un fichier PDF corrompu.

    - Upload un PDF (max 50MB)
    - Validation de la structure interne
    - Réparation si possible (reconstruction xref, objets corrompus)
    - Retour du PDF réparé en téléchargement

    Réponses :
        200: PDF réparé avec succès
        400: PDF invalide ou non réparable
        413: Fichier trop volumineux
        422: Type de fichier incorrect
    """

    # Validation du type MIME
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=422,
            detail=f"Type de fichier incorrect. Attendu: application/pdf, reçu: {file.content_type}"
        )

    temp_input = None
    temp_output = None

    try:
        # SÉCURITÉ: Lire et valider la taille du fichier
        pdf_content = await file.read(MAX_FILE_SIZE + 1)

        if len(pdf_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Fichier PDF trop volumineux (max {MAX_FILE_SIZE/1024/1024:.0f}MB)"
            )

        # Sauvegarder temporairement le PDF
        temp_input = TEMP_DIR / f"{uuid.uuid4()}_input.pdf"
        with temp_input.open("wb") as f:
            f.write(pdf_content)

        # Valider le PDF
        validation = validate_pdf(temp_input)

        if validation['errors']:
            # Si des erreurs mais pas corrompu, on peut essayer de réparer
            if not validation['is_corrupted']:
                raise HTTPException(
                    status_code=400,
                    detail=f"PDF invalide: {'; '.join(validation['errors'])}"
                )

        # Réparer le PDF
        temp_output = TEMP_DIR / f"{uuid.uuid4()}_output.pdf"
        success, message, stats = repair_pdf(temp_input, temp_output)

        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Impossible de réparer le PDF: {message}"
            )

        # Retourner le PDF réparé
        def cleanup():
            if temp_input and temp_input.exists():
                try:
                    temp_input.unlink()
                except:
                    pass
            if temp_output and temp_output.exists():
                try:
                    temp_output.unlink()
                except:
                    pass

        response = FileResponse(
            temp_output,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={file.filename or 'repaired.pdf'}"
            },
            background=BackgroundTask(cleanup)
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")
    finally:
        # Nettoyer les fichiers temporaires en cas d'erreur
        if temp_input and temp_input.exists():
            try:
                temp_input.unlink()
            except:
                pass


@app.post("/api/pdf/validate")
async def validate_pdf_endpoint(file: UploadFile = File(...)):
    """
    Valide la structure interne d'un PDF et retourne les informations détaillées.

    Réponses :
        200: Validation complète avec détails (validité, corruption, pages, etc.)
        400: Impossible de valider le fichier
        413: Fichier trop volumineux
        422: Type de fichier incorrect
    """

    # Validation du type MIME
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=422,
            detail=f"Type de fichier incorrect. Attendu: application/pdf, reçu: {file.content_type}"
        )

    temp_file = None

    try:
        # SÉCURITÉ: Lire et valider la taille
        pdf_content = await file.read(MAX_FILE_SIZE + 1)

        if len(pdf_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Fichier PDF trop volumineux (max {MAX_FILE_SIZE/1024/1024:.0f}MB)"
            )

        # Sauvegarder temporairement
        temp_file = TEMP_DIR / f"{uuid.uuid4()}.pdf"
        with temp_file.open("wb") as f:
            f.write(pdf_content)

        # Valider et récupérer les infos
        validation = validate_pdf(temp_file)
        info = get_pdf_info(temp_file)

        return {
            "validation": validation,
            "info": info
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur validation: {str(e)}")
    finally:
        # Nettoyer
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
            except:
                pass


@app.post("/api/pdf/info")
async def get_pdf_info_endpoint(file: UploadFile = File(...)):
    """
    Récupère les informations métadonnées d'un PDF.

    Retour :
        - Pages
        - Titre, Auteur, Sujet
        - Date création, Producteur
        - Chiffrement
        - Taille
    """

    # Validation du type MIME
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=422,
            detail=f"Type de fichier incorrect. Attendu: application/pdf, reçu: {file.content_type}"
        )

    temp_file = None

    try:
        # SÉCURITÉ: Lire et valider la taille
        pdf_content = await file.read(MAX_FILE_SIZE + 1)

        if len(pdf_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Fichier PDF trop volumineux (max {MAX_FILE_SIZE/1024/1024:.0f}MB)"
            )

        # Sauvegarder temporairement
        temp_file = TEMP_DIR / f"{uuid.uuid4()}.pdf"
        with temp_file.open("wb") as f:
            f.write(pdf_content)

        # Récupérer les infos
        info = get_pdf_info(temp_file)

        return info

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    finally:
        # Nettoyer
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
            except:
                pass


@app.post("/api/pdf/smart-repair")
async def smart_repair_pdf_endpoint(file: UploadFile = File(...)):
    """
    Réparation INTELLIGENTE de PDF avec analyse et renommage automatique.

    Workflow :
    1. Valider la structure interne
    2. Analyser le contenu (texte, type, nom)
    3. Réparer le PDF corrompu
    4. Renommer selon les infos trouvées (ex: FACTURE_Jean_Dupont.pdf)
    5. Retourner le PDF réparé et renommé en téléchargement

    Réponses :
        200: PDF réparé et renommé avec métadonnées d'analyse
        400: PDF invalide ou non réparable
        413: Fichier trop volumineux
        422: Type de fichier incorrect
    """

    # Validation du type MIME
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=422,
            detail=f"Type de fichier incorrect. Attendu: application/pdf, reçu: {file.content_type}"
        )

    temp_input = None
    temp_output = None

    try:
        # SÉCURITÉ: Lire et valider la taille du fichier
        pdf_content = await file.read(MAX_FILE_SIZE + 1)

        if len(pdf_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Fichier PDF trop volumineux (max {MAX_FILE_SIZE/1024/1024:.0f}MB)"
            )

        # Sauvegarder temporairement l'entrée
        temp_input = TEMP_DIR / f"{uuid.uuid4()}_input.pdf"
        with temp_input.open("wb") as f:
            f.write(pdf_content)

        # Étape 1 : Valider le PDF
        validation = validate_pdf(temp_input)

        if validation['errors']:
            if not validation['is_corrupted']:
                raise HTTPException(
                    status_code=400,
                    detail=f"PDF invalide: {'; '.join(validation['errors'])}"
                )

        # Étape 2 : Analyser le contenu AVANT réparation
        analysis = analyze_pdf(temp_input)

        if analysis.get('error'):
            # Continuer même si l'analyse échoue
            logger.warning(f"Avertissement analyse: {analysis['error']}")
            suggested_filename = f"document_{uuid.uuid4().hex[:8]}.pdf"
        else:
            suggested_filename = analysis.get('suggested_filename', f"document_{uuid.uuid4().hex[:8]}.pdf")

        # Étape 3 : Réparer le PDF
        temp_output = TEMP_DIR / f"{uuid.uuid4()}_output.pdf"
        success, message, stats = repair_pdf(temp_input, temp_output)

        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Impossible de réparer le PDF: {message}"
            )

        # Étape 4 : Renommer le fichier réparé
        final_output = TEMP_DIR / suggested_filename
        if temp_output.exists():
            temp_output.rename(final_output)

        # Retourner le PDF réparé et renommé
        response = FileResponse(
            final_output,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={suggested_filename}",
                "X-Document-Type": analysis.get('document_type', 'document'),
                "X-Document-Name": analysis.get('extracted_name', ''),
                "X-Confidence": str(analysis.get('document_type_confidence', 0))
            }
        )

        # Nettoyer les fichiers temporaires en arrière-plan
        async def cleanup_after_download():
            await asyncio.sleep(5)  # Attendre le téléchargement
            if final_output.exists():
                try:
                    final_output.unlink()
                except:
                    pass
            if temp_input and temp_input.exists():
                try:
                    temp_input.unlink()
                except:
                    pass

        asyncio.create_task(cleanup_after_download())

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur smart repair: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")
    finally:
        # Nettoyage immédiat en cas d'erreur
        if temp_input and temp_input.exists():
            try:
                temp_input.unlink()
            except:
                pass
        if temp_output and temp_output.exists():
            try:
                temp_output.unlink()
            except:
                pass


@app.post("/api/pdf/analyze")
async def analyze_pdf_endpoint(file: UploadFile = File(...)):
    """
    Analyse un PDF pour détecter son type et extraire le nom du document.

    Retourne les informations d'analyse sans le réparer.

    Réponse :
    {
        "document_type": "facture",
        "document_type_confidence": 0.95,
        "extracted_name": "2026-001",
        "suggested_filename": "FACTURE_2026_001.pdf",
        "metadata": {...},
        "summary": "📄 Type détecté: FACTURE..."
    }
    """

    # Validation du type MIME
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=422,
            detail=f"Type de fichier incorrect. Attendu: application/pdf, reçu: {file.content_type}"
        )

    temp_file = None

    try:
        # SÉCURITÉ: Lire et valider la taille
        pdf_content = await file.read(MAX_FILE_SIZE + 1)

        if len(pdf_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Fichier PDF trop volumineux (max {MAX_FILE_SIZE/1024/1024:.0f}MB)"
            )

        # Sauvegarder temporairement
        temp_file = TEMP_DIR / f"{uuid.uuid4()}.pdf"
        with temp_file.open("wb") as f:
            f.write(pdf_content)

        # Analyser
        analysis = analyze_pdf(temp_file)

        # Générer résumé
        summary = get_analysis_summary(analysis)

        return {
            "document_type": analysis.get('document_type', 'document'),
            "document_type_confidence": analysis.get('document_type_confidence', 0),
            "extracted_name": analysis.get('extracted_name', ''),
            "suggested_filename": analysis.get('suggested_filename', ''),
            "metadata": analysis.get('metadata', {}),
            "summary": summary,
            "error": analysis.get('error')
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analyse: {str(e)}")
    finally:
        # Nettoyer
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
            except:
                pass


if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*60)
    print("PDF REPAIR SERVICE v1.0")
    print("="*60)
    print("\nServeur demarre sur: http://localhost:8001")
    print("="*60 + "\n")

    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
