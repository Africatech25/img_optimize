# 🚀 GUIDE RAPIDE - Installation et Exécution des Tests

## ✅ Fichiers Générés

Tous les fichiers de tests ont été créés dans `backend/` :

### Configuration
- ✅ `requirements-dev.txt` - Dépendances de test
- ✅ `pytest.ini` - Configuration pytest
- ✅ `.coveragerc` - Configuration couverture

### Tests (à organiser)
- ✅ `tests_conftest.py` - Fixtures communes
- ✅ `tests_test_main.py` - Tests API (45+ tests)
- ✅ `tests_test_optimize_images.py` - Tests traitement (50+ tests)
- ✅ `tests_test_security.py` - Tests sécurité (40+ tests)
- ✅ `tests_README.md` - Documentation complète

### Scripts
- ✅ `setup_tests.py` - Installation Python
- ✅ `setup_tests.bat` - Installation Windows
- ✅ `run_tests.py` - Lancement avancé

### Documentation
- ✅ `TESTS_GENERATION_REPORT.md` - Rapport complet

---

## 📦 INSTALLATION (3 ÉTAPES)

### Étape 1 : Créer la structure tests/

**Option A - Windows (recommandé)**:
```cmd
cd backend
setup_tests.bat
```

**Option B - Python (multi-plateforme)**:
```bash
cd backend
python setup_tests.py
```

**Résultat attendu**:
```
tests/
├── __init__.py
├── conftest.py
├── test_main.py
├── test_optimize_images.py
├── test_security.py
└── README.md
```

### Étape 2 : Installer les dépendances

```bash
pip install -r requirements-dev.txt
```

**Packages installés**:
- pytest 8.3.4
- pytest-asyncio 0.24.0
- pytest-cov 6.0.0
- pytest-mock 3.14.0
- httpx 0.28.1
- pytest-benchmark 5.1.0
- coverage 7.6.9

### Étape 3 : Lancer les tests

```bash
pytest -v
```

---

## 🎯 COMMANDES ESSENTIELLES

### Tests complets avec couverture
```bash
pytest -v
```

### Tests par catégorie
```bash
pytest -m security          # Sécurité (40+ tests)
pytest -m unit              # Unitaires (60+ tests)
pytest -m edge_case         # Cas limites (25+ tests)
```

### Tests par module
```bash
pytest tests/test_main.py -v                   # API endpoints
pytest tests/test_optimize_images.py -v        # Traitement images
pytest tests/test_security.py -v               # Sécurité
```

### Rapport HTML de couverture
```bash
pytest --cov=. --cov-report=html
# Ouvrir htmlcov/index.html dans le navigateur
```

### Script avancé
```bash
python run_tests.py              # Complet
python run_tests.py --quick      # Rapide (sans couverture)
python run_tests.py --security   # Sécurité uniquement
python run_tests.py --html       # Avec rapport HTML
```

---

## 📊 VÉRIFICATION

### 1. Vérifier l'installation
```bash
pytest --version
# pytest 8.3.4
```

### 2. Compter les tests découverts
```bash
pytest --collect-only
# Devrait afficher ~135+ tests
```

### 3. Lancer un test simple
```bash
pytest tests/test_main.py::test_health_check_returns_ok -v
```

### 4. Vérifier la couverture
```bash
pytest --cov=. --cov-report=term-missing
# Objectif: > 80%
```

---

## 🐛 RÉSOLUTION DE PROBLÈMES

### Erreur: "No module named 'pytest'"
```bash
pip install -r requirements-dev.txt
```

### Erreur: "tests/ not found"
```bash
# Lancer le script de setup
setup_tests.bat   # ou python setup_tests.py
```

### Erreur: "ModuleNotFoundError: No module named 'main'"
```bash
# S'assurer d'être dans le dossier backend/
cd backend
pytest -v
```

### Erreur: "fixture 'client' not found"
```bash
# Vérifier que conftest.py est dans tests/
ls tests/conftest.py
```

### Tests qui échouent
```bash
# Mode debug verbeux
pytest -vvs --log-cli-level=DEBUG

# Arrêter au premier échec
pytest -x

# Mode debugger
pytest --pdb
```

---

## 📈 RÉSULTATS ATTENDUS

### Couverture estimée
- `main.py`: **85-90%**
- `optimize_images.py`: **85-90%**
- Endpoints API: **90-95%**
- Validations sécurité: **100%**

**Global**: **82-87%** ✅ (objectif: > 80%)

### Tests par catégorie
- Tests unitaires: **60+**
- Tests sécurité: **40+**
- Tests edge cases: **25+**
- Tests intégration: **10+**
- Tests performance: **5+**

**Total**: **~135+ tests**

---

## 📚 DOCUMENTATION

### Lire la documentation complète
```bash
# Windows
type tests\README.md

# Linux/Mac
cat tests/README.md
```

### Lire le rapport de génération
```bash
# Windows
type TESTS_GENERATION_REPORT.md

# Linux/Mac
cat TESTS_GENERATION_REPORT.md
```

---

## ✅ CHECKLIST DE VALIDATION

Exécuter dans l'ordre :

- [ ] 1. Lancer `setup_tests.bat` ou `setup_tests.py`
- [ ] 2. Vérifier que `tests/` existe avec 6 fichiers
- [ ] 3. Installer dépendances : `pip install -r requirements-dev.txt`
- [ ] 4. Lancer tests : `pytest -v`
- [ ] 5. Vérifier qu'aucun test n'échoue
- [ ] 6. Mesurer couverture : `pytest --cov=. --cov-report=html`
- [ ] 7. Vérifier couverture > 80%
- [ ] 8. Exécuter 3 fois pour détecter tests flaky
- [ ] 9. Tester filtres : `pytest -m security -v`
- [ ] 10. Générer rapport HTML : ouvrir `htmlcov/index.html`

---

## 🎓 PROCHAINES ACTIONS

### Immédiat
1. ✅ Exécuter setup : `setup_tests.bat`
2. ⏳ Installer : `pip install -r requirements-dev.txt`
3. ⏳ Tester : `pytest -v`

### Validation
4. ⏳ Mesurer couverture réelle
5. ⏳ Corriger échecs éventuels
6. ⏳ Vérifier stabilité (3 exécutions)

### Intégration
7. ⏳ Ajouter au CI/CD (GitHub Actions)
8. ⏳ Mettre à jour `doc/BACKLOG.md`
9. ⏳ Créer badge de couverture

---

## 📞 AIDE

**Documentation complète**: `tests/README.md`  
**Rapport détaillé**: `TESTS_GENERATION_REPORT.md`  
**Agent**: DRX-TEST  
**Standards**: `.github/copilot-instructions.md`

---

## 🎯 COMMANDE UNIQUE POUR TOUT INSTALLER

**Windows**:
```cmd
setup_tests.bat && pip install -r requirements-dev.txt && pytest -v
```

**Linux/Mac**:
```bash
python setup_tests.py && pip install -r requirements-dev.txt && pytest -v
```

---

**Statut**: ✅ **PRÊT À LANCER**  
**Couverture cible**: > 80%  
**Tests générés**: ~135+  
**Date**: 2026-04-03
