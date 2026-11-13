"""Sudoku generation and thermal-printer rendering."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from PIL import Image, ImageDraw

from ..i18n import Translator
from ..rendering import (
    Page,
    draw_text_center,
    draw_text_left,
    draw_text_right,
    load_font,
)

Grid = list[list[int]]

# Target number of clues for each 1..5 difficulty level. A puzzle is accepted
# when digging reaches the target or gets within one clue of it.
TARGET_CLUES = {1: 40, 2: 36, 3: 32, 4: 28, 5: 25}
MIN_CLUES = {1: 38, 2: 34, 3: 30, 4: 26, 5: 23}

_ALL = 0x1FF


@dataclass(frozen=True)
class SudokuPuzzle:
    puzzle: Grid
    solution: Grid
    level: int

    @property
    def clues(self) -> int:
        return sum(1 for row in self.puzzle for value in row if value)


def _empty_grid() -> Grid:
    return [[0] * 9 for _ in range(9)]


def _candidates(rows: list[int], cols: list[int], boxes: list[int], row: int, col: int) -> int:
    return _ALL & ~(rows[row] | cols[col] | boxes[(row // 3) * 3 + col // 3])


def generate_full_grid(rng: random.Random) -> Grid:
    """Return a random, fully solved 9x9 grid."""
    grid = _empty_grid()
    rows = [0] * 9
    cols = [0] * 9
    boxes = [0] * 9

    def fill(index: int) -> bool:
        if index == 81:
            return True
        row, col = divmod(index, 9)
        box = (row // 3) * 3 + col // 3
        mask = _candidates(rows, cols, boxes, row, col)
        values = [value for value in range(1, 10) if mask & (1 << (value - 1))]
        rng.shuffle(values)
        for value in values:
            bit = 1 << (value - 1)
            grid[row][col] = value
            rows[row] |= bit
            cols[col] |= bit
            boxes[box] |= bit
            if fill(index + 1):
                return True
            grid[row][col] = 0
            rows[row] &= ~bit
            cols[col] &= ~bit
            boxes[box] &= ~bit
        return False

    if not fill(0):
        raise RuntimeError("failed to generate a sudoku solution")
    return grid


def count_solutions(grid: Grid, limit: int = 2) -> int:
    """Count solutions up to ``limit``; stops as soon as the limit is reached."""
    work = [row[:] for row in grid]
    rows = [0] * 9
    cols = [0] * 9
    boxes = [0] * 9
    for row in range(9):
        for col in range(9):
            value = work[row][col]
            if not value:
                continue
            bit = 1 << (value - 1)
            box = (row // 3) * 3 + col // 3
            if rows[row] & bit or cols[col] & bit or boxes[box] & bit:
                return 0
            rows[row] |= bit
            cols[col] |= bit
            boxes[box] |= bit

    count = 0

    def search() -> bool:
        nonlocal count
        best: Optional[tuple[int, int]] = None
        best_mask = 0
        best_count = 10
        for row in range(9):
            for col in range(9):
                if work[row][col]:
                    continue
                mask = _candidates(rows, cols, boxes, row, col)
                available = mask.bit_count()
                if available == 0:
                    return False
                if available < best_count:
                    best = (row, col)
                    best_mask = mask
                    best_count = available
                    if available == 1:
                        break
            if best_count == 1:
                break
        if best is None:
            count += 1
            return count >= limit
        row, col = best
        box = (row // 3) * 3 + col // 3
        mask = best_mask
        while mask:
            bit = mask & -mask
            value = bit.bit_length()
            work[row][col] = value
            rows[row] |= bit
            cols[col] |= bit
            boxes[box] |= bit
            if search():
                return True
            rows[row] &= ~bit
            cols[col] &= ~bit
            boxes[box] &= ~bit
            work[row][col] = 0
            mask &= ~bit
        return False

    search()
    return count


def generate_puzzle(level: int, rng: random.Random, *, attempts: int = 40) -> SudokuPuzzle:
    """Generate a puzzle with a unique solution for difficulty ``level`` 1..5."""
    if level not in TARGET_CLUES:
        raise ValueError("difficulty must be between 1 and 5")
    target = TARGET_CLUES[level]
    minimum = MIN_CLUES[level]
    best: Optional[SudokuPuzzle] = None
    best_clues = 82

    for _ in range(attempts):
        solution = generate_full_grid(rng)
        puzzle = [row[:] for row in solution]
        cells = list(range(81))
        rng.shuffle(cells)
        clues = 81

        for index in cells:
            if clues <= target:
                break
            row, col = divmod(index, 9)
            value = puzzle[row][col]
            puzzle[row][col] = 0
            if count_solutions(puzzle) == 1:
                clues -= 1
            else:
                puzzle[row][col] = value

        candidate = SudokuPuzzle(puzzle=puzzle, solution=solution, level=level)
        if clues < best_clues:
            best = candidate
            best_clues = clues
        if minimum <= clues <= target:
            return candidate

    if best is None:
        raise RuntimeError("failed to generate a sudoku puzzle")
    return best


def ascii_preview(puzzle: Grid) -> str:
    separator = "+-------+-------+-------+"
    lines = [separator]
    for row in range(9):
        if row and row % 3 == 0:
            lines.append(separator)
        parts = ["|"]
        for col in range(9):
            value = puzzle[row][col]
            parts.append(f" {value if value else '.'}")
            if col in (2, 5, 8):
                parts.append(" |")
        lines.append("".join(parts))
    lines.append(separator)
    return "\n".join(lines)


def render_sudoku(
    puzzle: SudokuPuzzle,
    *,
    width: int,
    number: int,
    t: Translator,
) -> Page:
    """Render one sudoku page at exactly ``width`` pixels."""
    margin = max(6, width // 32)
    available = width - 2 * margin
    cell = max(20, available // 9)
    grid_size = cell * 9
    grid_left = (width - grid_size) // 2

    title_size = max(16, int(cell * 0.56))
    subtitle_size = max(11, int(cell * 0.33))
    digit_size = max(16, int(cell * 0.68))

    title_font = load_font(title_size)
    subtitle_font = load_font(subtitle_size)
    digit_font = load_font(digit_size)

    header_height = max(38, int(cell * 1.2))
    top = margin
    grid_top = top + header_height
    height = grid_top + grid_size + margin

    image = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(image)

    draw_text_left(draw, (margin, top), t("sudoku_title"), title_font)
    subtitle = f"{t('sudoku_number', number=number)} · {t.level(puzzle.level)}"
    draw_text_right(draw, (width - margin, top + 2), subtitle, subtitle_font)

    # Thin cell lines first, then the heavier 3x3 block borders.
    for index in range(1, 9):
        if index % 3 == 0:
            continue
        x = grid_left + index * cell
        y = grid_top + index * cell
        draw.line((x, grid_top, x, grid_top + grid_size), fill=0, width=max(2, cell // 20))
        draw.line((grid_left, y, grid_left + grid_size, y), fill=0, width=max(2, cell // 20))

    block_width = max(3, cell // 10)
    for index in (3, 6):
        x = grid_left + index * cell
        y = grid_top + index * cell
        draw.line((x, grid_top, x, grid_top + grid_size), fill=0, width=block_width)
        draw.line((grid_left, y, grid_left + grid_size, y), fill=0, width=block_width)

    outer_width = max(4, cell // 8)
    draw.rectangle(
        (grid_left, grid_top, grid_left + grid_size, grid_top + grid_size),
        outline=0,
        width=outer_width,
    )

    for row in range(9):
        for col in range(9):
            value = puzzle.puzzle[row][col]
            if not value:
                continue
            x = grid_left + col * cell + cell / 2
            y = grid_top + row * cell + cell / 2
            draw_text_center(draw, (x, y), str(value), digit_font)

    label = f"{t('sudoku_number', number=number)} · {t.level(puzzle.level)}"
    return Page(image=image, label=label, ascii_preview=ascii_preview(puzzle.puzzle))


def build_sudoku_pages(
    *,
    width: int,
    level: int,
    count: int,
    t: Translator,
    rng: Optional[random.Random] = None,
) -> list[Page]:
    rng = rng or random.Random()
    pages: list[Page] = []
    for number in range(1, count + 1):
        puzzle = generate_puzzle(level, rng)
        pages.append(render_sudoku(puzzle, width=width, number=number, t=t))
    return pages


__all__ = [
    "SudokuPuzzle",
    "ascii_preview",
    "build_sudoku_pages",
    "count_solutions",
    "generate_full_grid",
    "generate_puzzle",
    "render_sudoku",
]
