#!/usr/bin/env python3
"""Render README previews from the same game renderers used for printing."""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from printplay.games.battleship import compose_battleship_pair, place_fleet
from printplay.games.sudoku import build_sudoku_pages
from printplay.i18n import Translator
from printplay.rendering import load_font

PREVIEW_WIDTH = 768  # 2x the 384 px print width, for crisp README images.


def _fit(image: Image.Image, width: int, height: int) -> Image.Image:
    ratio = min(width / image.width, height / image.height)
    size = (max(1, int(image.width * ratio)), max(1, int(image.height * ratio)))
    return image.resize(size, Image.Resampling.LANCZOS)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(ROOT / "docs" / "images"))
    parser.add_argument("--width", type=int, default=PREVIEW_WIDTH)
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t = Translator("en")

    sudoku = build_sudoku_pages(
        width=args.width,
        level=3,
        count=1,
        t=t,
        rng=random.Random(7),
    )[0].image
    sudoku.save(out / "sudoku.png")

    battleship = compose_battleship_pair(
        place_fleet(random.Random(7)),
        width=args.width,
        player=1,
        t=t,
        auto_ships=True,
    )
    battleship.save(out / "battleship.png")

    canvas = Image.new("L", (1600, 900), 255)
    sudoku_fit = _fit(sudoku, 720, 810)
    battleship_fit = _fit(battleship, 820, 500)
    canvas.paste(sudoku_fit, (40, 30))
    canvas.paste(battleship_fit, (780, 205))

    caption = "Previews rendered at 2x for clarity. Actual print width: 384 px / 203 dpi."
    draw = ImageDraw.Draw(canvas)
    draw.text((40, 860), caption, font=load_font(18), fill=80)
    canvas.save(out / "preview.png")

    print(f"Wrote {out / 'sudoku.png'}")
    print(f"Wrote {out / 'battleship.png'}")
    print(f"Wrote {out / 'preview.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
