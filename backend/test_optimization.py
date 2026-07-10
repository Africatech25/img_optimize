#!/usr/bin/env python3
"""
Script de test pour l'optimisation d'images avec mesure de performance.

Usage:
    1. Placer une ou plusieurs images de test dans le dossier 'test_images/'
    2. Exécuter: python test_optimization.py
    3. Vérifier les résultats dans 'test_images/optimized/'
"""

import time
import sys
from pathlib import Path

# Importer la fonction d'optimisation
from optimize_images import convert_image, check_avif_support, FORMAT_CONFIG, SUPPORTED_EXTENSIONS


def test_optimization():
    """Teste l'optimisation avec mesure de performance"""

    # Créer les dossiers de test
    test_dir = Path("test_images")
    test_dir.mkdir(exist_ok=True)
    output_dir = test_dir / "optimized"
    output_dir.mkdir(exist_ok=True)

    # Trouver les images de test
    images = sorted([
        f for f in test_dir.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ])

    if not images:
        print("❌ Aucune image trouvée dans './test_images/'")
        print(f"\nPour tester l'optimisation:")
        print(f"  1. Créez le dossier: {test_dir.absolute()}")
        print(f"  2. Placez une ou plusieurs images dedans")
        print(f"  3. Relancez ce script\n")
        print(f"Extensions supportées: {', '.join(SUPPORTED_EXTENSIONS)}")
        sys.exit(1)

    # Paramètres de test
    formats_to_test = ["webp", "avif"] if check_avif_support() else ["webp"]
    quality = 70
    max_size_mo = 1.0

    print("=" * 80)
    print(f"🧪 TEST D'OPTIMISATION - {len(images)} image(s)")
    print("=" * 80)
    print(f"\n📁 Dossier source: {test_dir.absolute()}")
    print(f"📁 Dossier sortie: {output_dir.absolute()}")
    print(f"\n⚙️  Paramètres:")
    print(f"   - Formats testés: {', '.join(formats_to_test)}")
    print(f"   - Qualité: {quality}")
    print(f"   - Limite de taille: {max_size_mo} Mo")
    print("\n")

    # Tester pour chaque format
    for fmt in formats_to_test:
        config = FORMAT_CONFIG[fmt]
        ext = config["extension"]

        print("-" * 80)
        print(f"🎯 Test avec format: {fmt.upper()}")
        print("-" * 80)
        print(f"{'Image':<30} {'Avant':<12} {'Après':<12} {'Gain':<10} {'Temps':<10} {'Status':<12}")
        print("-" * 80)

        total_time = 0
        total_before = 0
        total_after = 0

        for img_path in images:
            output_filename = f"{img_path.stem}_optimized{ext}"
            output_path = output_dir / output_filename

            # Mesurer le temps d'optimisation
            start_time = time.time()

            try:
                before, after, status = convert_image(
                    img_path,
                    output_path,
                    fmt,
                    quality,
                    max_size_mo
                )

                elapsed = time.time() - start_time
                total_time += elapsed
                total_before += before
                total_after += after

                gain_pct = (1 - after / before) * 100 if before > 0 else 0

                # Formater les tailles
                before_str = format_size(before)
                after_str = format_size(after)
                gain_str = f"{gain_pct:.1f}%"
                time_str = f"{elapsed:.2f}s"

                # Symbole de status
                status_symbol = {
                    "ok": "✅ OK",
                    "reduced": "⚠️ REDUCED",
                    "failed": "❌ FAILED"
                }.get(status, status)

                print(
                    f"{img_path.name:<30} "
                    f"{before_str:<12} "
                    f"{after_str:<12} "
                    f"{gain_str:<10} "
                    f"{time_str:<10} "
                    f"{status_symbol:<12}"
                )

            except Exception as e:
                elapsed = time.time() - start_time
                print(f"{img_path.name:<30} {'ERROR':<12} {'-':<12} {'-':<10} {elapsed:.2f}s      ❌ {str(e)[:30]}")

        # Résumé pour ce format
        if total_before > 0:
            avg_time = total_time / len(images)
            total_gain = (1 - total_after / total_before) * 100

            print("-" * 80)
            print(f"📊 Résumé {fmt.upper()}:")
            print(f"   - Temps total: {total_time:.2f}s")
            print(f"   - Temps moyen/image: {avg_time:.2f}s")
            print(f"   - Taille totale avant: {format_size(total_before)}")
            print(f"   - Taille totale après: {format_size(total_after)}")
            print(f"   - Réduction totale: {total_gain:.1f}%")
            print()

    print("=" * 80)
    print("✅ Tests terminés!")
    print(f"📁 Images optimisées dans: {output_dir.absolute()}")
    print("=" * 80)


def format_size(size_bytes: int) -> str:
    """Formate une taille en Ko ou Mo."""
    if size_bytes >= 1_000_000:
        return f"{size_bytes / 1_000_000:.2f} Mo"
    return f"{size_bytes / 1_000:.0f} Ko"


def test_smoothing():
    """Teste spécifiquement la nouvelle fonctionnalité de lissage"""
    test_dir = Path("test_images")
    output_dir = test_dir / "optimized_smoothing"
    output_dir.mkdir(exist_ok=True)

    images = sorted([
        f for f in test_dir.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ])

    if not images:
        return

    print("\n" + "=" * 80)
    print("🧪 TEST DE LISSAGE (Smoothing)")
    print("=" * 80)
    
    img_path = images[0]
    fmt = "webp"
    quality = 80
    
    for level in [0, 2, 5]:
        output_path = output_dir / f"{img_path.stem}_smoothing_{level}.webp"
        print(f"Bruit/Lissage niveau {level} sur {img_path.name}...")
        
        before, after, status = convert_image(
            img_path,
            output_path,
            fmt,
            quality,
            max_size_mo=1.0,
            smoothing=level
        )
        print(f"  → Taille: {format_size(after)} (Gain: {(1-after/before)*100:.1f}%)")

if __name__ == "__main__":
    test_optimization()
    test_smoothing()
