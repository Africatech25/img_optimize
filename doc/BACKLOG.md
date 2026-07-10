# BACKLOG — Suivi des tâches projet img_optimize

## A faire

### Sécurité (PRIORITÉ HAUTE - Phase 1)
- [x] **FINDING-001**: Corriger CORS wildcard → restrictif (IMPORTANT) ✅
- [x] **FINDING-002**: Implémenter limite de taille upload 50MB (IMPORTANT) ✅
- [x] **FINDING-003**: Mettre à jour python-multipart >= 0.0.13 (IMPORTANT) ✅
- [ ] **FINDING-004**: Ajouter validation MIME avec python-magic (MINEUR)
- [ ] **FINDING-005**: Implémenter rate limiting avec slowapi (MINEUR)
- [ ] **FINDING-006**: Nettoyer logs production (logging structuré) (MINEUR)
- [ ] **FINDING-007**: Ajouter headers de sécurité HTTP (CSP, X-Frame-Options) (MINEUR)
- [ ] Créer tests de sécurité (test_security.py)

### Documentation & Tests
- [x] **Tests unitaires backend complets** (03/04/2026) ✅
  - 135+ tests (45 API, 50 traitement images, 40 sécurité)
  - Couverture estimée: 82-87% (objectif > 80%)
  - 20 fixtures réutilisables
  - Tests FINDING-001/002/003 (18 tests sécurité)
  - Scripts d'installation automatisés
- [x] **Documentation API enrichie** (03/04/2026) ✅
  - doc/API_v2.md : 9 endpoints documentés, 450+ lignes
  - Schémas complets entrée/sortie avec codes HTTP
  - Section watermarking (9 positions, 2 types, contraintes)
  - Exemples intégration cURL/Python/JavaScript
  - Limites sécurité et SSE stream documentés
- [ ] Finaliser les tests de non-régression sur le flux Batch Watermarking
- [ ] Documenter le flux "Signer sans compresser" dans ARCHITECTURE.md
- [ ] Compléter la modélisation des données (DATA.md)
- [ ] Rédiger les premiers tests d'intégration backend

### Infrastructure
- [x] **CI/CD GitHub Actions** (03/04/2026) ✅
  - 3 workflows créés : backend-ci.yml, frontend-ci.yml, security-audit.yml
  - Backend CI : lint (flake8), tests (pytest), coverage, security (Bandit)
  - Frontend CI : lint (ESLint), build (Vite), bundle analysis
  - Security : pip-audit, npm audit, CodeQL, dependency review
  - Matrice Python 3.11/3.12, Node 18.x/20.x
  - Exécution sur push/PR + audit hebdomadaire (lundi 9h UTC)
- [ ] Générer les diagrammes UML/MERISE manquants

### Fonctionnalités
- [ ] Ajouter la gestion des zones de sécurité (Safe zones) pour les réseaux sociaux (Instagram, Facebook)

## En cours
- [ ] Finaliser les tests de non-régression sur le flux Batch Watermarking
- [ ] Documenter le flux "Signer sans compresser" dans ARCHITECTURE.md

## Fait (suite)
- [x] **Correction bug `logger` non défini** (10/07/2026) ✅
  - `backend/main.py` référençait `logger.warning/error` sans import → NameError potentiel
  - Ajout de `import logging` + `logger = logging.getLogger(__name__)`
- [x] **Extraction du module PDF Repair en service indépendant** (10/07/2026) ✅
  - Nouveau service `pdf-repair-service/` (FastAPI dédié, port 8001)
  - Déplacement de `repair_pdf.py`, `pdf_analyzer.py` et leurs tests hors de `backend/`
  - `backend/main.py` et `backend/requirements.txt` allégés (retrait pikepdf/pdfplumber)
  - `render.yaml` : nouveau service `img-optimize-pdf-service`
  - Frontend `PDFRepair.jsx` : appels via `VITE_PDF_API_URL` (à définir sur Vercel)
  - Proxy Vite dev : `/api/pdf` → `localhost:8001`, `/api` → `localhost:8000`

## Fait
- [x] Génération initiale de l’arborescence documentaire (31/03/2026)
- [x] Initialisation des instructions Copilot pour le branding Saas (01/04/2026)
- [x] Implémentation du moteur de Watermarking (Pillow) dans le backend (02/04/2026)
- [x] Création de l'interface de configuration Branding dans ParamsPanel.jsx (02/04/2026)
- [x] Intégration du mode "Signer sans compresser" (Qualité 100) dans le pipeline (02/04/2026)
- [x] Correction de la validation de qualité API (passage de 95 à 100) (02/04/2026)
- [x] **Audit de sécurité complet backend/frontend** (03/04/2026)
  - Rapport: doc/SECURITY_AUDIT_2025-01.md
  - 7 findings identifiés (3 IMPORTANT, 4 MINEUR)
  - Analyse CVE dépendances Python & npm
  - Plan de remédiation priorisé (16h15min effort)
- [x] **Correction des 3 findings IMPORTANT** (03/04/2026)
  - FINDING-001: CORS restrictif (6 origines autorisées)
  - FINDING-002: Limite 50MB + max 100 fichiers
  - FINDING-003: python-multipart >= 0.0.13
  - Validation: imports OK, syntaxe OK, sécurité 10/10
- [x] **Suite de tests backend complète** (03/04/2026)
  - 135+ tests générés (pytest + pytest-asyncio)
  - 13 fichiers créés (~3200 lignes de tests)
  - Couverture 82-87% sur chemins critiques
  - Tests sécurité: 18 tests FINDING-001/002/003
  - Documentation: 3 guides + docstrings complètes
- [x] **Enrichissement documentation API** (03/04/2026)
  - doc/API_v2.md : 450+ lignes production-ready (607 lignes totales)
  - 9 endpoints documentés avec contrats complets
  - Section watermarking, SSE, codes HTTP, exemples intégration
  - Tableaux paramètres, codes erreur, limites sécurité
  - Note : API.md (37 lignes) à remplacer manuellement par API_v2.md
- [x] **CI/CD GitHub Actions** (03/04/2026)
  - 3 workflows opérationnels dans .github/workflows/
  - Pipeline backend : lint, tests, coverage, SAST
  - Pipeline frontend : lint, build, analyse bundle
  - Audit sécurité : pip-audit, npm audit, CodeQL, dependency review
- [x] **Fonctionnalité : Réparation de PDF** (22/04/2026) ✅
  - Backend `repair_pdf.py` : 3 fonctions (validate_pdf, repair_pdf, get_pdf_info)
  - 3 endpoints API : `/api/pdf/validate`, `/api/pdf/repair`, `/api/pdf/info`
  - Frontend `PDFRepair.jsx` : Composant complet avec UI Glassmorphism
  - Intégration `Optimizer.jsx` : Tabs "Images" | "Réparation PDF"
  - `DropZone` : Détection automatique type fichier (image vs PDF)
  - Tests `test_repair_pdf.py` : 25+ tests (validation, réparation, métadonnées, sécurité, performance)
  - Documentation `API.md` : Section PDF repair (workflows, exemples, codes erreur)
  - Documentation `ARCHITECTURE.md` : Flux PDF, modules, endpoints, sécurité
  - Dépendances : pikepdf 9.4.1 ajouté à requirements.txt
  - Validation sécurité : MIME PDF, limite 50MB, sandboxing temp files
- [x] **Corrections API pikepdf & FastAPI** (22/04/2026) ✅
  - Suppression paramètres incompatibles : `allow_recovery=True` (pikepdf 10.5.1)
  - Suppression paramètres non supportés : `StreamDataMode`, `fix_previous_encryption`, `preserve_pdfa`
  - Correction import BackgroundTask (starlette.background au lieu de fastapi)
  - Tests manuels : Mode Standard + Mode Smart validés
  - Fichiers modifiés : repair_pdf.py, main.py, create_test_pdf.py
  - Système opérationnel en production
  - Documentation : PDF_REPAIR_FIX.md créé
