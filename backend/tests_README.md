# 🧪 Suite de Tests - Backend img_optimize

## 📋 Vue d'ensemble

Suite de tests complète pour le backend d'optimisation d'images avec **couverture > 80%** des chemins critiques.

**Framework**: pytest 8.3.4  
**Python**: 3.11+  
**Dernière exécution**: 2026-04-03

---

## 🏗️ Structure

```
tests/
├── __init__.py                 # Package tests
├── conftest.py                 # Fixtures communes et configuration
├── test_main.py                # Tests API endpoints (FastAPI)
├── test_optimize_images.py     # Tests traitement d'images (Pillow)
└── test_security.py            # Tests sécurité (FINDING-001/002/003)
```

---

## 🚀 Installation

### 1. Installer les dépendances de test

```bash
cd backend
pip install -r requirements-dev.txt
```

### 2. Vérifier l'installation

```bash
pytest --version
# pytest 8.3.4
```

---

## ▶️ Lancer les tests

### Tests complets avec couverture

```bash
pytest -v
```

**Sortie attendue**:
- Affichage verbeux des tests
- Rapport de couverture inline
- Génération `htmlcov/index.html`
- Génération `coverage.json`

### Tests par module

```bash
# Tests API uniquement
pytest tests/test_main.py -v

# Tests traitement images uniquement
pytest tests/test_optimize_images.py -v

# Tests sécurité uniquement
pytest tests/test_security.py -v
```

### Tests par catégorie (markers)

```bash
# Tests unitaires uniquement
pytest -m unit

# Tests de sécurité uniquement
pytest -m security

# Tests edge cases uniquement
pytest -m edge_case

# Tests d'intégration
pytest -m integration

# Exclure les tests lents
pytest -m "not slow"
```

### Mode rapide (sans couverture)

```bash
pytest --no-cov -v
```

### Tests en parallèle (si pytest-xdist installé)

```bash
pytest -n auto
```

---

## 📊 Rapport de couverture

### Génération du rapport HTML

```bash
pytest --cov=. --cov-report=html
# Ouvrir htmlcov/index.html dans le navigateur
```

### Rapport détaillé terminal

```bash
pytest --cov=. --cov-report=term-missing
```

### Vérifier le seuil minimum (80%)

```bash
pytest --cov-fail-under=80
# FAIL si couverture < 80%
```

---

## 🎯 Objectifs de couverture

| Module                | Cible | Priorité |
|-----------------------|-------|----------|
| `main.py`             | > 85% | Haute    |
| `optimize_images.py`  | > 85% | Haute    |
| Endpoints API         | > 90% | Critique |
| Validations sécurité  | 100%  | Critique |
| Gestion erreurs       | > 80% | Haute    |

---

## 📝 Conventions de nommage

### Tests

```python
def test_[unite]_[scenario]_[resultat_attendu]():
    """
    Test: Description claire de ce qui est testé.
    
    Vérifie:
    - Point 1
    - Point 2
    """
```

**Exemples**:
- `test_health_check_returns_ok()`
- `test_optimize_rejects_oversized_file()`
- `test_convert_image_jpeg_to_webp()`
- `test_security_file_size_exactly_at_limit()`

### Fixtures

```python
@pytest.fixture
def simple_image_bytes() -> bytes:
    """Crée une image RGB simple de 100x100px en mémoire."""
```

---

## 🔍 Tests de sécurité

Couvrent les **FINDINGS** du rapport d'audit :

### FINDING-001 : Validation taille fichiers
- ✅ `test_security_file_size_exactly_at_limit`
- ✅ `test_security_file_size_just_over_limit`
- ✅ `test_security_logo_watermark_size_limit`
- ✅ `test_security_dos_too_many_files`

### FINDING-002 : Validation formats
- ✅ `test_security_invalid_image_format_rejected`
- ✅ `test_security_logo_watermark_invalid_format`
- ✅ `test_security_supported_extensions_whitelist`
- ✅ `test_security_format_parameter_strict_validation`

### FINDING-003 : Protection CORS
- ✅ `test_security_cors_allowed_origins_whitelist`
- ✅ `test_security_cors_no_wildcard`
- ✅ `test_security_cors_headers_strict`

### Attaques testées
- Path traversal (`../../../etc/passwd`)
- Null byte injection (`\x00`)
- SQL injection (dans prefix)
- XSS (dans watermark)
- Command injection (dans filename)
- DoS (fichiers multiples, tailles extrêmes)

---

## 🛠️ Fixtures disponibles

### Client & App
- `client` : TestClient FastAPI configuré
- `mock_job` : Job d'optimisation simulé

### Images (en mémoire)
- `simple_image_bytes` : RGB 100x100px PNG
- `rgba_image_bytes` : RGBA 100x100px PNG avec transparence
- `large_image_bytes` : 2000x2000px (~12MB)
- `jpeg_image_bytes` : 200x200px JPEG
- `webp_image_bytes` : 150x150px WebP
- `watermark_logo_bytes` : Logo 50x50px PNG

### Paramètres
- `valid_optimization_params` : Paramètres standard
- `watermark_text_params` : Config watermark texte
- `edge_case_params` : Valeurs limites

### Répertoires temporaires
- `temp_output_dir` : Dossier sortie (auto-nettoyé)
- `temp_input_dir` : Dossier entrée (auto-nettoyé)

---

## ⚡ Performance

### Tests de performance (markers `slow`)

```bash
# Exclure les tests lents
pytest -m "not slow"

# Uniquement les tests de performance
pytest -m slow
```

### Benchmark

Si `pytest-benchmark` installé :

```python
def test_optimization_performance(benchmark):
    result = benchmark(optimize_function)
```

---

## 🐛 Debugging

### Mode verbeux + logs

```bash
pytest -v -s --log-cli-level=DEBUG
```

### Arrêter au premier échec

```bash
pytest -x
```

### Debugger interactif (pdb)

```bash
pytest --pdb
```

### Afficher les warnings

```bash
pytest -v -p no:warnings
```

---

## 🔄 CI/CD

### GitHub Actions (exemple)

```yaml
- name: Run tests
  run: |
    pip install -r requirements-dev.txt
    pytest --cov=. --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

---

## ✅ Checklist avant commit

- [ ] Tous les tests passent : `pytest -v`
- [ ] Couverture ≥ 80% : `pytest --cov-fail-under=80`
- [ ] Pas de tests flaky : exécuter 3 fois
- [ ] Tests sécurité OK : `pytest -m security`
- [ ] Pas de warnings : `pytest -p no:warnings`

---

## 📚 Ressources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pillow Documentation](https://pillow.readthedocs.io/)

---

## 🤝 Contribution

### Ajouter un test

1. Choisir le bon fichier (`test_main.py`, `test_optimize_images.py`, `test_security.py`)
2. Suivre la convention de nommage
3. Ajouter les markers appropriés (`@pytest.mark.unit`, `@pytest.mark.security`, etc.)
4. Documenter clairement ce qui est testé
5. Vérifier la couverture : `pytest --cov=. --cov-report=term-missing`

### Ajouter une fixture

Ajouter dans `conftest.py` :

```python
@pytest.fixture
def my_fixture():
    """Description claire de la fixture."""
    # Setup
    data = create_test_data()
    yield data
    # Teardown (optionnel)
    cleanup(data)
```

---

## 📞 Support

**Problèmes courants**:

1. **Import errors** : Vérifier que `backend/` est dans PYTHONPATH
2. **Fixtures not found** : S'assurer que `conftest.py` est présent
3. **Async errors** : Vérifier `pytest-asyncio` installé
4. **Coverage trop basse** : Identifier les branches non testées avec `--cov-report=html`

---

**Version**: 1.0.0  
**Auteur**: DRX-TEST (sous-agent tests)  
**Date**: 2026-04-03
