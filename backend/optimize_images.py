#!/usr/bin/env python3
"""
optimize_images.py
------------------
Optimise un dossier d'images pour le web :
  - Choix du format de sortie : jpeg, webp, avif, png
  - Compression avec qualité réglable
  - Suppression des métadonnées EXIF
  - Renommage SEO-friendly
  - Limitation de taille maximale par image (défaut : 1 Mo)

Usage :
    python optimize_images.py --input ./mes-photos --prefix mon-projet-2026
    # Utilise la limite par défaut de 1 Mo

    python optimize_images.py --input ./mes-photos --prefix mon-projet-2026 --format webp
    # WebP avec limite 1 Mo

    python optimize_images.py --input ./mes-photos --prefix mon-projet-2026 --max-size 0.5
    # Limite à 500 Ko par image

    python optimize_images.py --input ./mes-photos --prefix mon-projet-2026 --max-size 0
    # Sans limite de taille (non recommandé)

Dépendances :
    pip install Pillow                       ← suffit pour JPEG / WebP / PNG
    pip install Pillow pillow-avif-plugin    ← nécessaire pour AVIF
"""

import argparse
import sys
from pathlib import Path
from PIL import Image

# Extensions supportées en entrée
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}

# Configuration par format
FORMAT_CONFIG = {
    "jpeg": {
        "pil_format":    "JPEG",
        "extension":     ".jpg",
        "save_kwargs":   {"progressive": True, "optimize": True},
        "quality_range": (1, 95),
        "default_quality": 65,
        "description":   "JPEG progressif — compression aggresive (reduction -50%), bon rendu",
    },
    "webp": {
        "pil_format":    "WEBP",
        "extension":     ".webp",
        "save_kwargs":   {"method": 6},
        "quality_range": (1, 100),
        "default_quality": 70,
        "description":   "WebP — ultra-efficace, -50% vs JPEG, 97% navigateurs ⭐",
    },
    "avif": {
        "pil_format":    "AVIF",
        "extension":     ".avif",
        "save_kwargs":   {},
        "quality_range": (1, 100),
        "default_quality": 65,
        "description":   "AVIF — incroyable compression -50-70%, qualite excellente, 90% navigateurs",
    },
    "png": {
        "pil_format":    "PNG",
        "extension":     ".png",
        "save_kwargs":   {"optimize": True},
        "quality_range": (1, 9),
        "default_quality": 7,
        "description":   "PNG — compression maximale (niveau 7/9), sans perte",
    },
}


def convert_image(
    input_path: Path,
    output_path: Path,
    fmt: str,
    quality: int,
    max_size_mo: float = 0,
) -> tuple[int, int, str]:
    """
    Convertit, optimise et compresse une image pour respecter une limite de taille.

    Args:
        input_path: Chemin du fichier source
        output_path: Chemin du fichier de sortie
        fmt: Format de sortie (jpeg, webp, avif, png)
        quality: Qualité initiale
        max_size_mo: Taille maximale en Mo (0 = pas de limite)

    Retourne:
        (taille_originale, taille_finale, status)
        status: 'ok' | 'reduced' | 'failed'
    """
    config = FORMAT_CONFIG[fmt]
    original_size = input_path.stat().st_size
    max_size_bytes = int(max_size_mo * 1_000_000) if max_size_mo > 0 else 0

    # Ensure output directory exists
    output_path_obj = Path(output_path) if not isinstance(output_path, Path) else output_path
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    # Convert to string for PIL (important on Windows)
    output_path_str = str(output_path_obj)

    with Image.open(input_path) as img:
        # --- Gestion de la transparence selon le format ---
        if fmt == "jpeg":
            # JPEG ne supporte pas la transparence → fond blanc
            if img.mode in ("RGBA", "P", "LA"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                alpha = img.split()[-1] if img.mode in ("RGBA", "LA") else None
                background.paste(img, mask=alpha)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

        elif fmt in ("webp", "avif"):
            # WebP/AVIF supportent la transparence → on conserve RGBA si présent
            if img.mode == "P":
                img = img.convert("RGBA")
            elif img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")

        # PNG : on garde le mode original, aucune conversion nécessaire

        # --- Compression avec limite de taille si active ---
        final_quality = quality
        scale_factor = 1.0
        status = "ok"

        if max_size_bytes > 0:
            # Boucle d'optimisation
            attempts = 0
            max_attempts = 12  # Réduit de 20 à 12

            while attempts < max_attempts:
                # Sauvegarder avec qualité/dimensions actuelles
                if scale_factor < 1.0:
                    # Redimensionner l'image
                    new_width = int(img.width * scale_factor)
                    new_height = int(img.height * scale_factor)
                    img_to_save = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                else:
                    img_to_save = img

                # Sauvegarder temporairement pour vérifier la taille
                save_kwargs = dict(config["save_kwargs"])
                if fmt == "png":
                    save_kwargs["compress_level"] = final_quality
                else:
                    save_kwargs["quality"] = final_quality

                img_to_save.save(output_path_str, format=config["pil_format"], **save_kwargs)
                final_size = Path(output_path_str).stat().st_size

                # Vérifier si on est sous la limite
                if final_size <= max_size_bytes:
                    if attempts > 0:
                        status = "reduced"
                    break

                attempts += 1

                # Stratégie 1 : Réduire la qualité par paliers de 10 (min 30) au lieu de 5
                if final_quality > 30:
                    final_quality = max(30, final_quality - 10)
                # Stratégie 2 : Réduire les dimensions par paliers de 15% (au lieu de 10%)
                else:
                    scale_factor = max(0.3, scale_factor - 0.15)

        else:
            # Pas de limite de taille, simple sauvegarde
            save_kwargs = dict(config["save_kwargs"])
            if fmt == "png":
                save_kwargs["compress_level"] = quality
            else:
                save_kwargs["quality"] = quality

            img.save(output_path_str, format=config["pil_format"], **save_kwargs)

    final_size = Path(output_path_str).stat().st_size

    # Déterminer le status final
    if max_size_bytes > 0 and final_size > max_size_bytes:
        status = "failed"

    return original_size, final_size, status


def format_size(size_bytes: int) -> str:
    """Formate une taille en Ko ou Mo."""
    if size_bytes >= 1_000_000:
        return f"{size_bytes / 1_000_000:.1f} Mo"
    return f"{size_bytes / 1_000:.0f} Ko"


def check_avif_support() -> bool:
    """Vérifie si AVIF est disponible dans Pillow."""
    try:
        import pillow_avif  # noqa: F401
        return True
    except ImportError:
        pass
    return "avif" in [f.lower() for f in Image.registered_extensions().values()]


def main():
    fmt_choices = list(FORMAT_CONFIG.keys())

    parser = argparse.ArgumentParser(
        description="Optimise des images pour le web avec choix du format de sortie.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Formats disponibles :\n" + "\n".join(
            f"  {k:<6} → {v['description']}" for k, v in FORMAT_CONFIG.items()
        ),
    )
    parser.add_argument("--input",   "-i", required=True,
                        help="Dossier contenant les images sources")
    parser.add_argument("--prefix",  "-p", required=True,
                        help="Prefixe SEO pour le renommage (ex: hotel-bretagne-2026)")
    parser.add_argument("--format",  "-f", default="webp", choices=fmt_choices,
                        help="Format de sortie : jpeg | webp | avif | png  (defaut : webp)")
    parser.add_argument("--quality", "-q", type=int, default=None,
                        help="Qualite (defaut auto : jpeg=65, webp=70, avif=65, png=7)")
    parser.add_argument("--output",  "-o", default=None,
                        help="Dossier de sortie (defaut : <input>/optimisees/)")
    parser.add_argument("--start",   "-s", type=int, default=1,
                        help="Numero de depart pour le renommage (defaut : 1)")
    parser.add_argument("--max-size", "-m", type=float, default=1.0,
                        help="Taille maximale par image en Mo (defaut : 1.0 Mo, obligatoire, 0 = pas de limite)")

    args = parser.parse_args()
    fmt    = args.format
    config = FORMAT_CONFIG[fmt]

    # Qualité par défaut selon le format choisi
    quality = args.quality if args.quality is not None else config["default_quality"]
    q_min, q_max = config["quality_range"]
    if not (q_min <= quality <= q_max):
        print(f"Erreur : La qualite pour {fmt.upper()} doit etre entre {q_min} et {q_max}.")
        sys.exit(1)

    # Vérification support AVIF
    if fmt == "avif" and not check_avif_support():
        print("Erreur : AVIF non disponible sur ton installation. Installe le plugin :")
        print("   pip install pillow-avif-plugin")
        print("   (ou mets a jour Pillow : pip install --upgrade Pillow)")
        sys.exit(1)

    # Vérification dossier source
    input_dir = Path(args.input)
    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Erreur : Dossier introuvable : {input_dir}")
        sys.exit(1)

    # Dossier de sortie
    output_dir = Path(args.output) if args.output else input_dir / "optimisees"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Collecter les images
    images = sorted([
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ])

    if not images:
        print(f"Erreur : Aucune image trouvee dans : {input_dir}")
        print(f"   Extensions supportees : {', '.join(SUPPORTED_EXTENSIONS)}")
        sys.exit(1)

    # --- Traitement ---
    ext = config["extension"]
    max_size_display = f"{args.max_size} Mo" if args.max_size > 0 else "sans limite"
    print(f"\nOptimisation de {len(images)} image(s)")
    print(f"   Format     : {fmt.upper()}  —  {config['description']}")
    print(f"   Qualite    : {quality}")
    print(f"   Prefixe    : {args.prefix}")
    print(f"   Taille max : {max_size_display}")
    print(f"   Sortie     : {output_dir}\n")
    print(f"{'Fichier source':<35} {'Avant':>10} {'Apres':>10} {'Gain':>8} {'Status':>8}")
    print("-" * 80)

    total_before = 0
    total_after  = 0
    errors       = []
    counter      = args.start
    stats_ok     = 0
    stats_reduced = 0
    stats_failed = 0

    for img_path in images:
        new_name    = f"{args.prefix}-{counter:02d}{ext}"
        output_path = output_dir / new_name

        try:
            before, after, status = convert_image(img_path, output_path, fmt, quality, args.max_size)
            gain_pct = (1 - after / before) * 100 if before > 0 else 0

            total_before += before
            total_after  += after

            # Deterministe le symbole de status
            if status == "ok":
                status_symbol = "OK"
                stats_ok += 1
            elif status == "reduced":
                status_symbol = "REDUCED"
                stats_reduced += 1
            else:  # failed
                status_symbol = f"FAILED ({format_size(after)})"
                stats_failed += 1

            print(
                f"{img_path.name:<35} "
                f"{format_size(before):>10} "
                f"{format_size(after):>10} "
                f"{gain_pct:>7.1f}%  "
                f"{status_symbol:>8}"
            )
            counter += 1

        except Exception as e:
            errors.append((img_path.name, str(e)))
            print(f"{'ERREUR ' + img_path.name:<35} {'':>29}  {e}")

    # --- Résumé final ---
    nb_ok      = counter - args.start
    total_gain = (1 - total_after / total_before) * 100 if total_before > 0 else 0

    print("-" * 80)
    print(
        f"\n{nb_ok} image(s) optimisee(s) — "
        f"{format_size(total_before)} → {format_size(total_after)} "
        f"(reduction moyenne de {total_gain:.1f}%)"
    )

    if args.max_size > 0:
        print(f"\nLimite de taille ({args.max_size} Mo) :")
        print(f"   {stats_ok} image(s) OK (dès compression initial)")
        print(f"   {stats_reduced} image(s) optimisee(s) (qualite/dimensions reduites)")
        print(f"   {stats_failed} image(s) non-conformes (dépasse limite malgre optimisation)")

    print(f"\nFichiers dans : {output_dir.resolve()}")

    if errors:
        print(f"\nErreurs ({len(errors)}) :")
        for name, err in errors:
            print(f"   - {name} : {err}")


if __name__ == "__main__":
    main()
