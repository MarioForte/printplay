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


def test_battleship_pages_are_printer_width_and_own_fleet_is_darker() -> None:
    pages = build_battleship_pages(
        width=384,
        players=2,
        t=Translator("en"),
        rng=random.Random(1),
    )
    assert len(pages) == 4
    for page in pages:
        assert page.image.width == 384
        assert page.image.height > 300
        assert _black_pixels(page.image) > 1000

    own = [_black_pixels(page.image) for page in pages[0::2]]
    enemy = [_black_pixels(page.image) for page in pages[1::2]]
    assert all(own_pixels > enemy_pixels for own_pixels, enemy_pixels in zip(own, enemy))


def test_translation_keys_match() -> None:
    assert set(MESSAGES["en"]) == set(MESSAGES["ru"])
