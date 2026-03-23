"""
Gör pixlar nära en vald bakgrundsfärg transparenta i en PNG.
Standard: medelvärde av hörn (lämpligt för loggor med enhetlig kant).

Användning:
  python scripts/color_to_alpha.py images/usethis.png -o images/logo.png --white
  python scripts/color_to_alpha.py images/logo.png -o images/logo.png --tolerance 50 --soft 22
  python scripts/color_to_alpha.py bild.png --rgb 11,42,34 --tolerance 40
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def sample_corners_rgb(im: Image.Image, margin: int = 4) -> tuple[int, int, int]:
    w, h = im.size
    pts = [
        (margin, margin),
        (w - 1 - margin, margin),
        (margin, h - 1 - margin),
        (w - 1 - margin, h - 1 - margin),
    ]
    rgb = im.convert("RGB")
    acc = [0, 0, 0]
    n = 0
    for x, y in pts:
        r, g, b = rgb.getpixel((x, y))
        acc[0] += r
        acc[1] += g
        acc[2] += b
        n += 1
    return tuple(v // n for v in acc)


def parse_rgb(s: str) -> tuple[int, int, int]:
    parts = [int(x.strip()) for x in s.split(",")]
    if len(parts) != 3:
        raise ValueError("RGB ska vara R,G,B")
    return tuple(max(0, min(255, p)) for p in parts)  # type: ignore[return-value]


def apply_color_to_alpha(
    im: Image.Image,
    target: tuple[int, int, int],
    tolerance: float,
    soft: float,
    green_boost: bool,
) -> Image.Image:
    """tolerance: max RGB-avstånd för helt transparent. soft: feather utåt (högre dist = mer opak)."""
    rgba = im.convert("RGBA")
    pixels = rgba.load()
    w, h = rgba.size
    tr, tg, tb = target

    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            dist = ((r - tr) ** 2 + (g - tg) ** 2 + (b - tb) ** 2) ** 0.5
            d = float(dist)
            if green_boost and g > r + 10 and g > b + 8:
                d = max(0.0, dist - 32.0)

            if d <= tolerance:
                na = 0
            elif soft > 0 and d <= tolerance + soft:
                t = (d - tolerance) / soft
                na = int(round(a * min(1.0, max(0.0, t))))
            else:
                na = a

            pixels[x, y] = (r, g, b, na)

    return rgba


def main() -> None:
    p = argparse.ArgumentParser(description="Gör en färg (nära bakgrund) transparent i PNG")
    p.add_argument("input", type=Path, help="Käll-PNG")
    p.add_argument("-o", "--output", type=Path, help="Utdata (standard: lägger till -transparent)")
    p.add_argument("--rgb", type=str, help="Målfärg R,G,B (annars hörnmedelvärde)")
    p.add_argument(
        "--white",
        action="store_true",
        help="Vit bakgrund → RGB(255,255,255), utan grön-heuristik (bäst för usethis.png-liknande)",
    )
    p.add_argument("--tolerance", type=float, default=None, help="Max avstånd i RGB för full transparens")
    p.add_argument("--soft", type=float, default=None, help="Mjuk kant (0 = hård)")
    p.add_argument("--no-green-boost", action="store_true", help="Stäng av extra heuristik för grön bakgrund")
    args = p.parse_args()

    src = args.input
    if not src.is_file():
        raise SystemExit(f"Saknas: {src}")

    im = Image.open(src)
    green_boost = not args.no_green_boost
    if args.white:
        target = (255, 255, 255)
        green_boost = False
        tol = args.tolerance if args.tolerance is not None else 44.0
        soft = args.soft if args.soft is not None else 26.0
        print("Vit nyckelfärg: RGB(255, 255, 255)")
    elif args.rgb:
        target = parse_rgb(args.rgb)
        tol = args.tolerance if args.tolerance is not None else 48.0
        soft = args.soft if args.soft is not None else 20.0
    else:
        target = sample_corners_rgb(im)
        print(f"Uppskattad bakgrundsfärg (hörn): RGB{target}")
        tol = args.tolerance if args.tolerance is not None else 48.0
        soft = args.soft if args.soft is not None else 20.0

    out = args.output
    if out is None:
        out = src.with_name(src.stem + "-transparent" + src.suffix)

    result = apply_color_to_alpha(
        im,
        target,
        tolerance=tol,
        soft=soft,
        green_boost=green_boost,
    )
    result.save(out, "PNG")
    print(f"Sparad: {out}")


if __name__ == "__main__":
    main()
