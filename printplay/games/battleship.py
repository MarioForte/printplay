"""Battleship fleet placement and thermal-printer rendering."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from PIL import Image, ImageDraw

from ..i18n import Translator
from ..rendering import (
    Page,
    dashed_line,
    draw_text_center,
    draw_text_left,
    draw_text_right,
    load_font,
)

BOARD_SIZE = 10
FLEET = (4, 3, 3, 2, 2, 2, 1, 1, 1, 1)
LETTERS = {
    "ru": "АБВГДЕЖЗИК",
    "en": "ABCDEFGHIJ",
}


@dataclass(frozen=True)
class Ship:
    row: int
    col: int
    length: int
    horizontal: bool

    def cells(self) -> list[tuple[int, int]]:
        if self.horizontal:
            return [(self.row, self.col + offset) for offset in range(self.length)]
        return [(self.row + offset, self.col) for offset in range(self.length)]


def _empty_board() -> list[list[int]]:
    return [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]


def _fits(
    board: list[list[int]],
    row: int,
    col: int,
    length: int,
    horizontal: bool,
) -> bool:
    cells = (
        [(row, col + offset) for offset in range(length)]
        if horizontal
        else [(row + offset, col) for offset in range(length)]
    )
    for cell_row, cell_col in cells:
        if not (0 <= cell_row < BOARD_SIZE and 0 <= cell_col < BOARD_SIZE):
            return False
        if board[cell_row][cell_col]:
            return False
    # Russian rules: ships may not touch, including diagonally.
    for cell_row, cell_col in cells:
        for delta_row in (-1, 0, 1):
            for delta_col in (-1, 0, 1):
                neighbour_row = cell_row + delta_row
                neighbour_col = cell_col + delta_col
                if (
                    0 <= neighbour_row < BOARD_SIZE
                    and 0 <= neighbour_col < BOARD_SIZE
                    and board[neighbour_row][neighbour_col]
                ):
                    return False
    return True


def _candidate_placements(
    board: list[list[int]],
    length: int,
) -> list[tuple[int, int, bool]]:
    candidates: list[tuple[int, int, bool]] = []
    for horizontal in (True, False):
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if _fits(board, row, col, length, horizontal):
                    candidates.append((row, col, horizontal))
    return candidates


def place_fleet(rng: random.Random, *, restarts: int = 200) -> list[Ship]:
    """Place the standard Russian fleet without overlaps or touching ships."""
    for _ in range(restarts):
        board = _empty_board()
        ships: list[Ship] = []

        def backtrack(index: int) -> bool:
            if index == len(FLEET):
                return True
            length = FLEET[index]
            candidates = _candidate_placements(board, length)
            rng.shuffle(candidates)
            for row, col, horizontal in candidates:
                ship = Ship(row=row, col=col, length=length, horizontal=horizontal)
                for cell_row, cell_col in ship.cells():
                    board[cell_row][cell_col] = 1
                ships.append(ship)
                if backtrack(index + 1):
                    return True
                ships.pop()
                for cell_row, cell_col in ship.cells():
                    board[cell_row][cell_col] = 0
            return False

        if backtrack(0):
            return ships

    raise RuntimeError("failed to place the battleship fleet")


def _draw_grid(
    draw: ImageDraw.ImageDraw,
    *,
    left: int,
    top: int,
    cell: int,
    size: int,
) -> None:
    for index in range(1, size):
        x = left + index * cell
        y = top + index * cell
        draw.line((x, top, x, top + size * cell), fill=0, width=max(2, cell // 18))
        draw.line((left, y, left + size * cell, y), fill=0, width=max(2, cell // 18))
    outer_width = max(4, cell // 8)
    draw.rectangle(
        (left, top, left + size * cell, top + size * cell),
        outline=0,
        width=outer_width,
    )


def _draw_ship(
    draw: ImageDraw.ImageDraw,
    ship: Ship,
    *,
    left: int,
    top: int,
    cell: int,
) -> None:
    inset = max(2, cell // 12)
    if ship.horizontal:
        x1 = left + ship.col * cell + inset
        y1 = top + ship.row * cell + inset
        x2 = left + (ship.col + ship.length) * cell - inset
        y2 = top + (ship.row + 1) * cell - inset
    else:
        x1 = left + ship.col * cell + inset
        y1 = top + ship.row * cell + inset
        x2 = left + (ship.col + 1) * cell - inset
        y2 = top + (ship.row + ship.length) * cell - inset
    draw.rectangle((x1, y1, x2, y2), fill=0)


def render_battleship(
    ships: list[Ship],
    *,
    width: int,
    player: int,
    role: str,
    t: Translator,
    show_ships: bool,
    tear_off: bool = False,
) -> Page:
    """Render one landscape 10x10 battleship field at exactly ``width`` pixels.

    The board stays square, but the title and fleet legend sit beside it, so the
    fragment is wider than it is tall. ``tear_off`` adds the cut line used after
    the second field of a player's pair.
    """
    margin = max(3, width // 96)
    label_size = max(9, width // 34)
    legend_column = max(36, width // 8)
    available = width - 2 * margin - label_size - legend_column
    cell = max(20, available // BOARD_SIZE)
    board_size = cell * BOARD_SIZE
    grid_left = margin + label_size
    legend_x = grid_left + board_size + max(4, width // 96)

    title_size = max(13, int(cell * 0.50))
    subtitle_size = max(9, int(cell * 0.32))
    coord_size = max(9, int(cell * 0.32))
    legend_size = max(8, int(cell * 0.26))

    title_font = load_font(title_size)
    subtitle_font = load_font(subtitle_size)
    coord_font = load_font(coord_size)
    legend_font = load_font(legend_size)

    header_height = max(20, int(cell * 0.65))
    footer_height = max(12, int(cell * 0.40))
    top = margin
    grid_top = top + header_height + label_size
    board_bottom = grid_top + board_size
    height = board_bottom + footer_height + margin

    image = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(image)

    draw_text_left(draw, (margin, top), t("battleship_title"), title_font)
    role_short = t("battleship_own_short") if role == "own" else t("battleship_enemy_short")
    header_right = f"{t('battleship_player', player=player)} · {role_short}"
    draw_text_right(draw, (width - margin, top + 1), header_right, subtitle_font)

    letters = LETTERS.get(t.lang, LETTERS["en"])
    for col in range(BOARD_SIZE):
        x = grid_left + col * cell + cell / 2
        draw_text_center(draw, (x, grid_top - label_size / 2), letters[col], coord_font)
    for row in range(BOARD_SIZE):
        y = grid_top + row * cell + cell / 2
        draw_text_center(draw, (grid_left - label_size / 2, y), str(row + 1), coord_font)

    _draw_grid(draw, left=grid_left, top=grid_top, cell=cell, size=BOARD_SIZE)

    if show_ships:
        for ship in ships:
            _draw_ship(draw, ship, left=grid_left, top=grid_top, cell=cell)

    # Vertical fleet legend in the right column: one silhouette per ship.
    draw_text_left(draw, (legend_x, grid_top - label_size), t("battleship_fleet"), legend_font)
    legend_y = grid_top + 2
    icon_height = max(4, int(cell * 0.14))
    icon_unit = max(4, int(cell * 0.14))
    for length in FLEET:
        icon_width = max(icon_unit, length * icon_unit)
        draw.rectangle(
            (legend_x, legend_y, legend_x + icon_width, legend_y + icon_height),
            fill=0,
        )
        legend_y += icon_height + max(2, icon_height // 2)

    if tear_off:
        footer_y = height - footer_height
        dashed_line(draw, footer_y + 2, x1=margin, x2=width - margin)
        draw_text_center(
            draw,
            (width / 2, footer_y + footer_height - 3),
            t("tear_off_short"),
            legend_font,
        )

    label = t("battleship_page_label", player=player, role=role_short)
    return Page(image=image, label=label, pause_after=tear_off, tear_off=tear_off)


def build_battleship_pages(
    *,
    width: int,
    players: int,
    t: Translator,
    rng: Optional[random.Random] = None,
) -> list[Page]:
    rng = rng or random.Random()
    pages: list[Page] = []
    for player in range(1, players + 1):
        ships = place_fleet(rng)
        pages.append(
            render_battleship(
                ships,
                width=width,
                player=player,
                role="own",
                t=t,
                show_ships=True,
            )
        )
        pages.append(
            render_battleship(
                [],
                width=width,
                player=player,
                role="enemy",
                t=t,
                show_ships=False,
                tear_off=True,
            )
        )
    return pages


__all__ = [
    "BOARD_SIZE",
    "FLEET",
    "Ship",
    "build_battleship_pages",
    "place_fleet",
    "render_battleship",
]
