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
    # A light fill keeps the ship visible while leaving room for pen marks.
    # Atkinson turns the gray into a sparse dot pattern; threshold leaves it
    # white with only the outline, which is also easy to write over.
    draw.rectangle(
        (x1, y1, x2, y2),
        fill=200,
        outline=0,
        width=max(2, cell // 14),
    )


def _draw_board_section(
    draw: ImageDraw.ImageDraw,
    ships: list[Ship],
    *,
    x: int,
    grid_top: int,
    cell: int,
    label_size: int,
    header_height: int,
    player: int,
    role: str,
    t: Translator,
    show_ships: bool,
) -> None:
    board_size = cell * BOARD_SIZE
    grid_left = x + label_size

    title_font = load_font(max(13, int(cell * 0.45)))
    subtitle_font = load_font(max(8, int(cell * 0.27)))
    coord_font = load_font(max(9, int(cell * 0.30)))
    legend_font = load_font(max(8, int(cell * 0.25)))

    header_top = grid_top - header_height - label_size
    draw_text_left(draw, (x, header_top + 1), t("battleship_title"), title_font)
    role_short = t("battleship_own_short") if role == "own" else t("battleship_enemy_short")
    header_right = f"{t('battleship_player', player=player)} · {role_short}"
    draw_text_right(
        draw,
        (grid_left + board_size, header_top + 2),
        header_right,
        subtitle_font,
    )

    letters = LETTERS.get(t.lang, LETTERS["en"])
    for col in range(BOARD_SIZE):
        center_x = grid_left + col * cell + cell / 2
        draw_text_center(draw, (center_x, grid_top - label_size / 2), letters[col], coord_font)
    for row in range(BOARD_SIZE):
        center_y = grid_top + row * cell + cell / 2
        draw_text_center(draw, (grid_left - label_size / 2, center_y), str(row + 1), coord_font)

    _draw_grid(draw, left=grid_left, top=grid_top, cell=cell, size=BOARD_SIZE)

    if show_ships:
        for ship in ships:
            _draw_ship(draw, ship, left=grid_left, top=grid_top, cell=cell)

    # Horizontal fleet legend under the board, like the earlier portrait layout.
    legend_y = grid_top + board_size + 2
    draw_text_left(draw, (x, legend_y), t("battleship_fleet"), legend_font)
    legend_x = x + max(24, int(cell * 0.8))
    icon_unit = max(4, int(cell * 0.15))
    icon_height = max(5, int(cell * 0.18))
    for length in FLEET:
        icon_width = length * icon_unit
        draw.rectangle(
            (legend_x, legend_y + 1, legend_x + icon_width, legend_y + 1 + icon_height),
            fill=0,
        )
        legend_x += icon_width + max(3, icon_unit - 1)


def compose_battleship_pair(
    ships: list[Ship],
    *,
    width: int,
    player: int,
    t: Translator,
    auto_ships: bool = True,
) -> Image.Image:
    """Compose one player's two boards side by side, before printer rotation."""
    margin = max(3, width // 96)
    label_size = max(9, width // 34)
    header_height = max(18, int(width * 0.055))
    legend_height = max(18, int(width * 0.05))
    cell = max(
        20,
        (width - 2 * margin - header_height - label_size - legend_height) // BOARD_SIZE,
    )
    board_size = cell * BOARD_SIZE
    section_width = label_size + board_size + margin
    gap = max(12, width // 24)
    pair_width = 2 * section_width + gap + 2 * margin
    grid_top = margin + header_height + label_size
    pair_height = width

    pair = Image.new("L", (pair_width, pair_height), 255)
    draw = ImageDraw.Draw(pair)
    _draw_board_section(
        draw,
        ships,
        x=margin,
        grid_top=grid_top,
        cell=cell,
        label_size=label_size,
        header_height=header_height,
        player=player,
        role="own",
        t=t,
        show_ships=auto_ships,
    )
    _draw_board_section(
        draw,
        [],
        x=margin + section_width + gap,
        grid_top=grid_top,
        cell=cell,
        label_size=label_size,
        header_height=header_height,
        player=player,
        role="enemy",
        t=t,
        show_ships=False,
    )
    return pair


def render_battleship_pair(
    ships: list[Ship],
    *,
    width: int,
    player: int,
    t: Translator,
    auto_ships: bool = True,
) -> Page:
    """Render one player's pair, rotated 90 degrees for the printer width.

    Tear the fragment off, rotate the paper, and the two boards sit left and
    right.
    """
    pair = compose_battleship_pair(
        ships,
        width=width,
        player=player,
        t=t,
        auto_ships=auto_ships,
    )
    margin = max(3, width // 96)
    footer = max(12, width // 24)
    rotated = pair.transpose(Image.Transpose.ROTATE_270)
    final = Image.new("L", (rotated.width, rotated.height + footer), 255)
    final.paste(rotated, (0, 0))
    draw = ImageDraw.Draw(final)
    dashed_line(draw, rotated.height + 2, x1=margin, x2=final.width - margin)
    draw_text_center(
        draw,
        (final.width / 2, rotated.height + footer - 3),
        t("tear_off_short"),
        load_font(max(8, width // 48)),
    )

    label_key = "battleship_pair_label_auto" if auto_ships else "battleship_pair_label_empty"
    return Page(
        image=final,
        label=t(label_key, player=player),
        pause_after=True,
        tear_off=True,
    )


def build_battleship_pages(
    *,
    width: int,
    players: int,
    t: Translator,
    auto_ships: bool = True,
    rng: Optional[random.Random] = None,
) -> list[Page]:
    rng = rng or random.Random()
    pages: list[Page] = []
    for player in range(1, players + 1):
        ships = place_fleet(rng) if auto_ships else []
        pages.append(
            render_battleship_pair(
                ships,
                width=width,
                player=player,
                t=t,
                auto_ships=auto_ships,
            )
        )
    return pages


__all__ = [
    "BOARD_SIZE",
    "FLEET",
    "Ship",
    "build_battleship_pages",
    "compose_battleship_pair",
    "place_fleet",
    "render_battleship_pair",
]
