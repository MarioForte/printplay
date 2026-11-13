from __future__ import annotations

import random

from printplay.games.battleship import BOARD_SIZE, FLEET, place_fleet


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
