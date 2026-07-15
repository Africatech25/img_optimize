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
from PIL import Image, ImageFilter, ImageDraw, ImageFont

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
    smoothing: int = 0,
    watermark_params: dict = None,
) -> tuple[int, int, str]:
    """
    Convertit, optimise et compresse une image pour respecter une limite de taille.

    Args:
        input_path: Chemin du fichier source
        output_path: Chemin du fichier de sortie
        fmt: Format de sortie (jpeg, webp, avif, png)
        quality: Qualité initiale
        max_size_mo: Taille maximale en Mo (0 = pas de limite)
        smoothing: Intensité du lissage (0 = aucun, >0 = rayon du flou gaussien)
        watermark_params: Paramètres de marquage (optionnel)

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
        # --- Signature (Watermarking) ---
        if watermark_params and watermark_params.get("enabled"):
            img = apply_watermark(img, watermark_params)

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

        # --- Lissage ---
        if smoothing > 0:
            img = img.filter(ImageFilter.GaussianBlur(radius=smoothing))

        # --- PRÉ-DIMENSIONNEMENT INTELLIGENT (OPTIMISATION) ---
        # Si une limite de taille est active, estimer les dimensions optimales AVANT la boucle
        # Cela évite de multiples encodages coûteux (surtout pour AVIF)
        img_to_process = img
        pre_scaled = False

        if max_size_bytes > 0 and original_size > max_size_bytes:
            # Estimation des dimensions cibles
            target_width, target_height = estimate_target_dimensions(
                img.width,
                img.height,
                original_size,
                max_size_bytes,
                fmt
            )

            # Si réduction nécessaire (> 5%), pré-dimensionner
            if target_width < img.width * 0.95:
                img_to_process = img.resize(
                    (target_width, target_height),
                    Image.Resampling.LANCZOS
                )
                pre_scaled = True

        # --- Compression avec limite de taille si active ---
        final_quality = quality
        scale_factor = 1.0
        status = "ok"

        if max_size_bytes > 0:
            # Boucle d'optimisation (réduite car pré-dimensionnement fait le gros du travail)
            attempts = 0
            max_attempts = 6  # Réduit de 12 à 6 grâce au pré-dimensionnement

            while attempts < max_attempts:
                # Sauvegarder avec qualité/dimensions actuelles
                if scale_factor < 1.0:
                    # Redimensionnement additionnel si nécessaire (rare avec pré-dimensionnement)
                    new_width = int(img_to_process.width * scale_factor)
                    new_height = int(img_to_process.height * scale_factor)
                    img_to_save = img_to_process.resize((new_width, new_height), Image.Resampling.LANCZOS)
                else:
                    img_to_save = img_to_process

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
                    if attempts > 0 or pre_scaled:
                        status = "reduced"
                    break

                attempts += 1

                # Stratégie 1 : Réduire la qualité par paliers de 15 (min 30) - plus agressif
                if final_quality > 30:
                    final_quality = max(30, final_quality - 15)
                # Stratégie 2 : Réduire les dimensions par paliers de 20% - plus agressif
                else:
                    scale_factor = max(0.3, scale_factor - 0.20)

        else:
            # Pas de limite de taille, simple sauvegarde
            save_kwargs = dict(config["save_kwargs"])
            if fmt == "png":
                save_kwargs["compress_level"] = quality
            else:
                save_kwargs["quality"] = quality

            img_to_process.save(output_path_str, format=config["pil_format"], **save_kwargs)

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


def estimate_target_dimensions(
    img_width: int,
    img_height: int,
    original_size_bytes: int,
    target_size_bytes: int,
    fmt: str
) -> tuple[int, int]:
    """
    Estime les dimensions optimales pour atteindre une taille cible.

    Utilise une heuristique basée sur la relation non-linéaire entre
    le nombre de pixels et la taille du fichier compressé.

    Args:
        img_width: Largeur originale
        img_height: Hauteur originale
        original_size_bytes: Taille du fichier original
        target_size_bytes: Taille cible
        fmt: Format de sortie (jpeg, webp, avif, png)

    Returns:
        (new_width, new_height) dimensions optimales estimées
    """
    # Si déjà sous la cible, pas besoin de réduire
    if original_size_bytes <= target_size_bytes:
        return img_width, img_height

    # Ratio de compression nécessaire
    ratio = target_size_bytes / original_size_bytes

    # Exposant basé sur le format (compression plus efficace = exposant plus élevé)
    # AVIF/WebP compressent mieux → besoin de moins réduire les dimensions
    # JPEG/PNG compressent moins → besoin de plus réduire les dimensions
    exponent_map = {
        "avif": 0.65,  # Très efficace, réduction modérée
        "webp": 0.68,  # Efficace, réduction modérée
        "jpeg": 0.72,  # Standard, réduction standard
        "png": 0.75,   # Moins efficace, réduction plus importante
    }
    exponent = exponent_map.get(fmt, 0.7)

    # Calculer le facteur de réduction des dimensions
    # Formule: taille_fichier ≈ (pixels)^exponent
    scale = ratio ** (1 / exponent)

    # Limiter entre 30% et 100% (sécurité)
    scale = max(0.3, min(1.0, scale))

    # Calculer nouvelles dimensions
    new_width = int(img_width * scale)
    new_height = int(img_height * scale)

    # S'assurer que les dimensions sont au moins 100px
    if new_width < 100 or new_height < 100:
        scale_min = max(100 / img_width, 100 / img_height)
        new_width = max(100, int(img_width * scale_min))
        new_height = max(100, int(img_height * scale_min))

    return new_width, new_height


def apply_watermark(
    img: Image.Image,
    watermark_params: dict,
) -> Image.Image:
    """
    Applique un marquage (texte ou image) sur une image Pillow.

    Args:
        img: Image source (Pillow Object)
        watermark_params: Dictionnaire contenant:
            enabled: bool
            type: 'text' | 'image'
            text: str (si type='text')
            image_path: str (si type='image')
            position: 'top-left' | 'top-center' | 'top-right' | 
                      'middle-left' | 'middle-center' | 'middle-right' | 
                      'bottom-left' | 'bottom-center' | 'bottom-right'
            opacity: int (0-100)
            scale: float (0.1-1.0, défaut 0.15) relative à la largeur de l'image
    """
    if not watermark_params.get("enabled", False):
        return img

    # S'assurer que l'image est en RGBA pour le compositing
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # Création d'une couche transparente pour le watermark
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    w_img, h_img = img.size
    opacity = int(watermark_params.get("opacity", 50) * 2.55)
    position = watermark_params.get("position", "bottom-right")
    
    # 1. Préparation du contenu du watermark
    mark_content = None
    
    if watermark_params.get("type") == "text":
        text = watermark_params.get("text", "ImgOpt Branding")
        # Calcul de la taille de police relative (5% de la largeur par défaut)
        font_size = int(w_img * 0.04)
        try:
            # Tenter de charger une police système standard
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
            
        # Mesurer le texte
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        w_mark, h_mark = right - left, bottom - top
        
        # Dessiner le texte sur l'overlay avec l'opacité
        # On ajoute un léger contour/ombre pour la lisibilité
        def draw_text_at(x, y, fill_color):
            draw.text((x, y), text, font=font, fill=fill_color)

        mark_content = (w_mark, h_mark, "text", text, font)
        
    elif watermark_params.get("type") == "image":
        img_path = watermark_params.get("image_path")
        if img_path and Path(img_path).exists():
            with Image.open(img_path) as watermark_img_ref:
                # Charger l'image immédiatement en mémoire pour éviter les fermetures de contexte
                if watermark_img_ref.mode != "RGBA":
                    watermark_img = watermark_img_ref.convert("RGBA")
                else:
                    watermark_img = watermark_img_ref.copy()
                
                # Redimensionnement relatif (15% de la largeur par défaut)
                rel_scale = watermark_params.get("scale", 0.15)
                w_mark = int(w_img * rel_scale)
                aspect_ratio = watermark_img.height / watermark_img.width
                h_mark = int(w_mark * aspect_ratio)
                
                watermark_img = watermark_img.resize((w_mark, h_mark), Image.Resampling.LANCZOS)
                
                # Appliquer l'opacité globale si nécessaire
                if watermark_params.get("opacity", 100) < 100:
                    alpha = watermark_img.split()[3]
                    alpha = alpha.point(lambda p: int(p * (watermark_params["opacity"] / 100)))
                    watermark_img.putalpha(alpha)
                
                mark_content = (w_mark, h_mark, "image", watermark_img)

    if not mark_content:
        return img

    # 2. Calcul des coordonnées (x, y) selon l'ancrage
    w_mark, h_mark = mark_content[0], mark_content[1]
    margin = int(w_img * 0.02) # 2% de marge de sécurité
    
    # X Position
    if "left" in position:
        x = margin
    elif "center" in position:
        x = (w_img - w_mark) // 2
    else: # right
        x = w_img - w_mark - margin
        
    # Y Position
    if "top" in position:
        y = margin
    elif "middle" in position:
        y = (h_img - h_mark) // 2
    else: # bottom
        y = h_img - h_mark - margin

    # 3. Application finale
    if mark_content[2] == "text":
        text, font = mark_content[3], mark_content[4]
        # Ombre portée pour lisibilité universelle (contraste)
        draw.text((x+2, y+2), text, font=font, fill=(0, 0, 0, int(opacity * 0.5)))
        draw.text((x, y), text, font=font, fill=(255, 255, 255, opacity))
        return Image.alpha_composite(img, overlay)
    else:
        watermark_img = mark_content[3]
        # Créer une image RGBA de la taille de img pour la composition
        overlay_with_logo = Image.new("RGBA", img.size, (0, 0, 0, 0))
        overlay_with_logo.paste(watermark_img, (x, y), watermark_img)
        return Image.alpha_composite(img, overlay_with_logo)


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
