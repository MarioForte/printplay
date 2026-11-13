"""Shared raster rendering helpers.

The game renderers intentionally produce plain grayscale images at the exact
printer width. TiMini-Print applies the paper layout and converts the image to
the printer's 1-bit pipeline, so no scaling happens later.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = (
    os.environ.get("PRINTPLAY_FONT"),
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
)


@dataclass(frozen=True)
class Page:
    image: Image.Image
    label: str
    ascii_preview: Optional[str] = None
    pause_after: bool = True
    tear_off: bool = False


@lru_cache(maxsize=64)
def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in FONT_CANDIDATES:
        if not candidate or not os.path.exists(candidate):
            continue
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # older Pillow
        return ImageFont.load_default()


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def draw_text_left(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    *,
    fill: int = 0,
) -> None:
    draw.text(xy, text, font=font, fill=fill, anchor="lt")


def draw_text_right(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    *,
    fill: int = 0,
) -> None:
    draw.text(xy, text, font=font, fill=fill, anchor="rt")


def draw_text_center(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    font: ImageFont.ImageFont,
    *,
    fill: int = 0,
) -> None:
    draw.text(xy, text, font=font, fill=fill, anchor="mm")


def dashed_line(
    draw: ImageDraw.ImageDraw,
    y: int,
    *,
    x1: int,
    x2: int,
    dash: int = 8,
    gap: int = 6,
    width: int = 1,
) -> None:
    x = x1
    while x < x2:
        draw.line((x, y, min(x + dash, x2), y), fill=0, width=width)
        x += dash + gap
