#!/usr/bin/env python3
"""
Script de lancement de la suite de tests img_optimize backend

Usage:
    python run_tests.py                    # Tests complets avec couverture
    python run_tests.py --quick            # Tests rapides sans couverture
    python run_tests.py --security         # Tests sécurité uniquement
    python run_tests.py --unit             # Tests unitaires uniquement
    python run_tests.py --coverage-only    # Génération rapport couverture uniquement
"""

import sys
import subprocess
from pathlib import Path
import argparse


def run_command(cmd: list, description: str) -> int:
    """
    Exécute une commande et affiche le résultat.
    
    Args:
        cmd: Liste des arguments de commande
        description: Description de l'action
        
    Returns:
        Code de retour (0 = succès)
    """
    print(f"\n{'='*70}")
    print(f"📋 {description}")
    print(f"{'='*70}")
    print(f"Commande: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Lancement des tests backend img_optimize")
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Tests rapides sans couverture"
    )
    
    parser.add_argument(
        "--security",
        action="store_true",
        help="Tests de sécurité uniquement"
    )
    
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Tests unitaires uniquement"
    )
    
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Tests d'intégration uniquement"
    )
    
    parser.add_argument(
        "--coverage-only",
        action="store_true",
        help="Génération du rapport de couverture uniquement (sans exécuter les tests)"
    )
    
    parser.add_argument(
        "--html",
        action="store_true",
        help="Génération du rapport HTML et ouverture dans le navigateur"
    )
    
    parser.add_argument(
        "--no-cov",
        action="store_true",
        help="Désactiver la couverture de code"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Mode verbeux"
    )
    
    parser.add_argument(
        "--markers",
        "-m",
        type=str,
        help="Filtrer par markers pytest (ex: 'security and not slow')"
    )
    
    parser.add_argument(
        "--file",
        "-f",
        type=str,
        help="Exécuter un fichier de test spécifique (ex: tests/test_main.py)"
    )
    
    args = parser.parse_args()
    
    # Vérifier que pytest est installé
    try:
        subprocess.run(
            ["pytest", "--version"],
            capture_output=True,
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ERREUR: pytest n'est pas installé.")
        print("Installation: pip install -r requirements-dev.txt")
        return 1
    
    # Construire la commande pytest
    cmd = ["pytest"]
    
    # Mode verbeux
    if args.verbose or not args.quick:
        cmd.append("-v")
    
    # Filtrage par markers
    if args.security:
        cmd.extend(["-m", "security"])
        description = "Tests de sécurité"
    elif args.unit:
        cmd.extend(["-m", "unit"])
        description = "Tests unitaires"
    elif args.integration:
        cmd.extend(["-m", "integration"])
        description = "Tests d'intégration"
    elif args.markers:
        cmd.extend(["-m", args.markers])
        description = f"Tests (markers: {args.markers})"
    else:
        description = "Suite de tests complète"
    
    # Fichier spécifique
    if args.file:
        cmd.append(args.file)
        description = f"Tests de {args.file}"
    
    # Couverture
    if not args.no_cov and not args.quick:
        cmd.extend([
            "--cov=.",
            "--cov-report=term-missing:skip-covered",
            "--cov-report=json:coverage.json"
        ])
        
        if args.html or args.coverage_only:
            cmd.append("--cov-report=html:htmlcov")
    
    # Mode coverage-only
    if args.coverage_only:
        print("📊 Génération du rapport de couverture uniquement...")
        cmd = ["coverage", "html"]
        return_code = run_command(cmd, "Génération rapport HTML")
        
        if return_code == 0:
            print("\n✅ Rapport généré: htmlcov/index.html")
            
            # Ouvrir dans le navigateur
            import webbrowser
            report_path = Path("htmlcov/index.html").absolute()
            webbrowser.open(f"file://{report_path}")
        
        return return_code
    
    # Exécuter les tests
    return_code = run_command(cmd, description)
    
    # Résumé
    print(f"\n{'='*70}")
    if return_code == 0:
        print("✅ SUCCÈS: Tous les tests sont passés!")
    else:
        print("❌ ÉCHEC: Certains tests ont échoué.")
    print(f"{'='*70}\n")
    
    # Ouvrir le rapport HTML si demandé
    if args.html and return_code == 0:
        print("📊 Ouverture du rapport de couverture HTML...")
        import webbrowser
        report_path = Path("htmlcov/index.html").absolute()
        
        if report_path.exists():
            webbrowser.open(f"file://{report_path}")
            print(f"✅ Rapport ouvert: {report_path}")
        else:
            print("⚠️  Rapport HTML non trouvé. Générer avec --html")
    
    # Afficher le résumé de couverture si disponible
    coverage_json = Path("coverage.json")
    if coverage_json.exists() and not args.quick and not args.no_cov:
        try:
            import json
            with open(coverage_json) as f:
                data = json.load(f)
                total_coverage = data["totals"]["percent_covered"]
                
                print(f"\n📊 Couverture totale: {total_coverage:.1f}%")
                
                if total_coverage >= 80:
                    print("✅ Objectif de couverture atteint (≥ 80%)")
                else:
                    print(f"⚠️  Couverture insuffisante (cible: 80%, actuel: {total_coverage:.1f}%)")
        except Exception as e:
            print(f"⚠️  Impossible de lire coverage.json: {e}")
    
    return return_code


if __name__ == "__main__":
    sys.exit(main())
