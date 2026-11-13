from __future__ import annotations

import random

from printplay.games.battleship import build_battleship_pages
from printplay.games.sudoku import build_sudoku_pages
from printplay.i18n import MESSAGES, Translator


def _black_pixels(image) -> int:
    return sum(1 for value in image.get_flattened_data() if value < 128)


def test_sudoku_pages_are_printer_width() -> None:
    pages = build_sudoku_pages(
        width=384,
        level=3,
        count=2,
        t=Translator("en"),
        rng=random.Random(1),
    )
    assert len(pages) == 2
    for page in pages:
        assert page.image.width == 384
        assert page.image.height > 300
        assert _black_pixels(page.image) > 1000
        assert page.ascii_preview


def test_battleship_pairs_are_rotated_fragments() -> None:
    pages = build_battleship_pages(
        width=384,
        players=2,
        t=Translator("en"),
        rng=random.Random(1),
    )
    assert len(pages) == 2
    for page in pages:
        assert page.image.width == 384
        assert page.image.height > 600
        assert page.pause_after is True
        assert page.tear_off is True

        # The two boards are stacked in the printed strip and become left and
        # right after the user rotates the fragment.
        top = page.image.crop((0, 0, page.image.width, page.image.height // 2))
        bottom = page.image.crop((0, page.image.height // 2, page.image.width, page.image.height))
        assert _black_pixels(top) > 1000
        assert _black_pixels(bottom) > 1000


def test_translation_keys_match() -> None:
    assert set(MESSAGES["en"]) == set(MESSAGES["ru"])
