#!/usr/bin/env python3
"""
Script d'installation de la suite de tests

Crée la structure tests/ et déplace les fichiers de tests au bon endroit.
"""

import shutil
from pathlib import Path


def setup_test_structure():
    """Crée la structure tests/ et organise les fichiers."""
    
    backend_dir = Path(__file__).parent
    tests_dir = backend_dir / "tests"
    
    print("🔧 Installation de la suite de tests...")
    print(f"Backend: {backend_dir}")
    print(f"Tests: {tests_dir}")
    
    # Créer le dossier tests/
    if not tests_dir.exists():
        tests_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Créé: {tests_dir}")
    else:
        print(f"ℹ️  Existe déjà: {tests_dir}")
    
    # Fichiers à déplacer
    files_to_move = {
        "tests_conftest.py": "conftest.py",
        "tests_test_main.py": "test_main.py",
        "tests_test_optimize_images.py": "test_optimize_images.py",
        "tests_test_security.py": "test_security.py",
        "tests_README.md": "README.md"
    }
    
    # Déplacer les fichiers
    moved_count = 0
    for source_name, target_name in files_to_move.items():
        source_path = backend_dir / source_name
        target_path = tests_dir / target_name
        
        if source_path.exists():
            # Déplacer (ou copier si déplacement échoue)
            try:
                shutil.move(str(source_path), str(target_path))
                print(f"✅ Déplacé: {source_name} → tests/{target_name}")
                moved_count += 1
            except Exception as e:
                # Si move échoue, essayer copy
                try:
                    shutil.copy2(str(source_path), str(target_path))
                    print(f"✅ Copié: {source_name} → tests/{target_name}")
                    moved_count += 1
                except Exception as e2:
                    print(f"❌ Erreur: {source_name}: {e2}")
        else:
            print(f"⚠️  Non trouvé: {source_name}")
    
    # Créer __init__.py si absent
    init_file = tests_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text('"""\nTests unitaires et d\'intégration pour img_optimize backend\n"""\n')
        print(f"✅ Créé: tests/__init__.py")
    
    print(f"\n✅ Installation terminée! {moved_count} fichiers configurés.")
    print("\n📋 Prochaines étapes:")
    print("1. Installer les dépendances: pip install -r requirements-dev.txt")
    print("2. Lancer les tests: pytest -v")
    print("3. Voir le README: cat tests/README.md")


if __name__ == "__main__":
    setup_test_structure()
