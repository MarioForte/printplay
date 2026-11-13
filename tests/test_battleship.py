from __future__ import annotations

import random

from printplay.games.battleship import BOARD_SIZE, FLEET, ascii_preview, place_fleet
from printplay.i18n import Translator


def _cells(ships) -> set[tuple[int, int]]:
    occupied: set[tuple[int, int]] = set()
    for ship in ships:
        for cell in ship.cells():
            assert cell not in occupied
            occupied.add(cell)
    return occupied


def test_fleet_composition_and_bounds() -> None:
    for seed in range(200):
        ships = place_fleet(random.Random(seed))
        assert len(ships) == len(FLEET)
        assert sorted((ship.length for ship in ships), reverse=True) == list(FLEET)
        for ship in ships:
            for row, col in ship.cells():
                assert 0 <= row < BOARD_SIZE
                assert 0 <= col < BOARD_SIZE


def test_ships_do_not_touch_even_diagonally() -> None:
    for seed in range(200):
        ships = place_fleet(random.Random(seed))
        by_ship = {id(ship): set(ship.cells()) for ship in ships}
        all_cells = _cells(ships)
        for ship in ships:
            own = by_ship[id(ship)]
            for row, col in own:
                for delta_row in (-1, 0, 1):
                    for delta_col in (-1, 0, 1):
                        neighbour = (row + delta_row, col + delta_col)
                        if neighbour in all_cells and neighbour not in own:
                            raise AssertionError("ships touch")


def test_ascii_preview_matches_the_placed_fleet() -> None:
    ships = place_fleet(random.Random(1))
    lines = ascii_preview(ships, player=1, t=Translator("en")).splitlines()

    assert lines[0].startswith("Player 1 · your fleet")
    assert "enemy waters" in lines[0]
    assert "A B C D E F G H I J" in lines[1]
    assert len(lines) == 2 + BOARD_SIZE
    assert sum(line.count("#") for line in lines) == sum(ship.length for ship in ships)
    for line in lines[2:]:
        _, enemy = line.split("   ", 1)
        assert "#" not in enemy


def test_ascii_preview_uses_localized_coordinates() -> None:
    ships = place_fleet(random.Random(1))
    lines = ascii_preview(ships, player=2, t=Translator("ru")).splitlines()
    assert lines[0].startswith("Игрок 2 · твой флот")
    assert "А Б В Г Д Е Ж З И К" in lines[1]
