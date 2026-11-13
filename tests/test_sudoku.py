from __future__ import annotations

import random

import pytest

from printplay.games.sudoku import (
    MIN_CLUES,
    TARGET_CLUES,
    ascii_preview,
    count_solutions,
    generate_full_grid,
    generate_puzzle,
)


def _assert_valid_solution(grid: list[list[int]]) -> None:
    expected = set(range(1, 10))
    for row in grid:
        assert set(row) == expected
    for col in range(9):
        assert {grid[row][col] for row in range(9)} == expected
    for box_row in range(0, 9, 3):
        for box_col in range(0, 9, 3):
            values = {
                grid[row][col]
                for row in range(box_row, box_row + 3)
                for col in range(box_col, box_col + 3)
            }
            assert values == expected


def test_generate_full_grid_is_valid() -> None:
    for seed in range(20):
        _assert_valid_solution(generate_full_grid(random.Random(seed)))


@pytest.mark.parametrize("level", range(1, 6))
def test_puzzle_has_unique_solution_and_expected_clues(level: int) -> None:
    for seed in range(10):
        puzzle = generate_puzzle(level, random.Random(seed))
        _assert_valid_solution(puzzle.solution)
        assert count_solutions(puzzle.puzzle) == 1
        assert MIN_CLUES[level] <= puzzle.clues <= TARGET_CLUES[level]
        for row in range(9):
            for col in range(9):
                if puzzle.puzzle[row][col]:
                    assert puzzle.puzzle[row][col] == puzzle.solution[row][col]


def test_count_solutions_stops_at_two() -> None:
    empty = [[0] * 9 for _ in range(9)]
    assert count_solutions(empty, limit=2) == 2


def test_ascii_preview_shape() -> None:
    puzzle = generate_puzzle(3, random.Random(1))
    lines = ascii_preview(puzzle.puzzle).splitlines()
    assert len(lines) == 13
    assert lines[0] == "+-------+-------+-------+"
    assert all(len(line) == 25 for line in lines)
