# Sudoku solver with two algorithms: backtracking and wave function collapse.
# All code written by Jawad Kazma

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass

Grid = list[list[int]]

DIGITS = frozenset(range(1, 10))

def parse_grid(text: str) -> Grid:
    # turn an 81-character puzzle string into a 9x9 grid of ints (0 = empty)
    cells = []
    for ch in text:
        if ch.isdigit():
            cells.append(int(ch))
        elif ch == ".":
            cells.append(0)
        elif ch.isspace() or ch in "|-+":
            continue  # ignore layout characters
        else:
            raise ValueError(f"unexpected character {ch!r} in puzzle")
    if len(cells) != 81:
        raise ValueError(f"a puzzle needs 81 cells, got {len(cells)}")
    return [cells[r * 9:(r + 1) * 9] for r in range(9)]


def format_grid(grid: Grid) -> str:
    # return the grid as text with lines between the 3x3 boxes
    lines = []
    for r in range(9):
        if r in (3, 6):
            lines.append("------+-------+------")
        row = []
        for c in range(9):
            if c in (3, 6):
                row.append("|")
            row.append(str(grid[r][c]) if grid[r][c] else ".")
        lines.append(" ".join(row))
    return "\n".join(lines)


def find_conflicts(grid: Grid) -> list[str]:
    # list any rule breaks in the given numbers (Ex: two 5s in one row)
    problems = []
    units = (
        [("row", r + 1, [(r, c) for c in range(9)]) for r in range(9)]
        + [("column", c + 1, [(r, c) for r in range(9)]) for c in range(9)]
        + [("box", b + 1, [(b // 3 * 3 + i, b % 3 * 3 + j)
                           for i in range(3) for j in range(3)]) for b in range(9)]
    )
    for kind, number, cells in units:
        seen = set()
        for r, c in cells:
            value = grid[r][c]
            if value in seen:
                problems.append(f"{value} appears more than once in {kind} {number}")
            elif value:
                seen.add(value)
    return problems


def check_grid(grid: Grid) -> None:
    # raise ValueError if the grid has the wrong shape, bad values or conflicts
    if len(grid) != 9 or any(len(row) != 9 for row in grid):
        raise ValueError("the grid must be 9 rows of 9 cells")
    if any(value not in range(10) for row in grid for value in row):
        raise ValueError("cells must contain 0-9")
    conflicts = find_conflicts(grid)
    if conflicts:
        raise ValueError("invalid puzzle: " + "; ".join(conflicts))


def is_solved(grid: Grid) -> bool:
    # true if every cell is filled and no rule is broken
    return all(all(row) for row in grid) and not find_conflicts(grid)


@dataclass
class Stats:
    # counts how much work a solver did.

    # guesses: numbers the solver tried placing without being sure
    # backtracks: guesses that led to a dead end and had to be undone
    # max_guesses: optional limit; the solver stops with SearchLimitReached once it has made this many guesses

    guesses: int = 0
    backtracks: int = 0
    max_guesses: int | None = None

    def count_guess(self) -> None:
        self.guesses += 1
        if self.max_guesses is not None and self.guesses > self.max_guesses:
            raise SearchLimitReached(self.max_guesses)


class SearchLimitReached(Exception):
    """Raised when a solver goes past Stats.max_guesses"""


# solver 1: backtracking (the original approach)
# ---------------------------------------------------------------------------------
# visit the cells in reading order
# in each empty cell, try 1 to 9 and keep the first number that doesn't break a rule, then move on to the next cell
# if a cell has no number that fits, go back and change the previous guess.

def is_move_valid(grid: Grid, row: int, col: int, num: int) -> bool:
    # check whether num can go at (row, col) without breaking a rule
    # check this row
    for i in range(9):
        if grid[row][i] == num:
            return False

    # check this column
    for i in range(9):
        if grid[i][col] == num:
            return False

    # check this 3x3 box
    corner_row = row - row % 3  # top-left row of the box
    corner_col = col - col % 3  # top-left column of the box
    for x in range(3):
        for y in range(3):
            if grid[corner_row + x][corner_col + y] == num:
                return False

    return True


def _backtrack(grid: Grid, row: int, col: int, stats: Stats) -> bool:
    # past the last column: move to the next row, or stop if this was the last row
    if col == 9:
        if row == 8:
            return True  # every cell is filled
        row += 1
        col = 0

    # if the cell is already filled, move on to the next one
    if grid[row][col] > 0:
        return _backtrack(grid, row, col + 1, stats)

    # try every number in this cell
    for num in range(1, 10):
        if is_move_valid(grid, row, col, num):
            stats.count_guess()
            grid[row][col] = num
            if _backtrack(grid, row, col + 1, stats):
                return True
            # the guess led to a dead end: undo it and try the next number
            grid[row][col] = 0
            stats.backtracks += 1

    return False


def solve_backtracking(grid: Grid, stats: Stats | None = None) -> Grid | None:
    # solve with plain backtracking; returns a solved copy, or none if impossible
    check_grid(grid)
    stats = stats if stats is not None else Stats()
    work = [row[:] for row in grid]  # don't change the caller's grid
    return work if _backtrack(work, 0, 0, stats) else None


# solver 2: wave function collapse
# ---------------------------------------------------------------------------
# every cell starts out as "any of 1-9" (its superposition)
# the solver keeps that set of possible numbers (cell's candidates) for all 81 cells

# observe: pick unsolved cell with fewest candidates (lowest entropy) b/c it is the least risky guess
# collapse: fix that cell to one of its candidates
# propagate: 
#   - remove that number from every cell in the same row, column and box
#   - if that leaves a cell with one candidate, it is solved too, so propagate from it as well
#   - repeat until every cell has one candidate (solved), or a cell runs out of candidates (a contradiction)
#   - on a contradiction, undo the last collapse and try that cell's next candidate

# cells are numbered 0-80 in reading order, so cell = row * 9 + col.

def _peers(cell: int) -> frozenset[int]:
    # all cells sharing a row, column or box with this cell (not itself)
    row, col = divmod(cell, 9)
    box_row, box_col = row - row % 3, col - col % 3
    same_row = {row * 9 + c for c in range(9)}
    same_col = {r * 9 + col for r in range(9)}
    same_box = {(box_row + i) * 9 + box_col + j for i in range(3) for j in range(3)}
    return frozenset((same_row | same_col | same_box) - {cell})


PEERS = [_peers(cell) for cell in range(81)]

Wave = list[frozenset]  # the candidates of each of the 81 cells


def _collapse(wave: Wave, cell: int, value: int) -> bool:
    # fix cell to value and propagate; returns false on a contradiction
    # the candidate sets are frozensets that are replaced, never changed in place, so a shallow copy of the wave is enough to undo a guess later

    if value not in wave[cell]:
        return False
    wave[cell] = frozenset([value])
    to_propagate = [cell]
    while to_propagate:
        solved = to_propagate.pop()
        (number,) = wave[solved]
        for peer in PEERS[solved]:
            if number in wave[peer]:
                wave[peer] = wave[peer] - {number}
                if not wave[peer]:
                    return False  # this peer has no options left
                if len(wave[peer]) == 1:
                    to_propagate.append(peer)  # the peer collapsed on its own
    return True


def _initial_wave(grid: Grid) -> Wave | None:
    # start every cell as 1-9, then collapse the given numbers
    wave: Wave = [DIGITS] * 81
    for cell in range(81):
        value = grid[cell // 9][cell % 9]
        if value and not _collapse(wave, cell, value):
            return None
    return wave


def _lowest_entropy_cell(wave: Wave) -> int | None:
    # the unsolved cell with the fewest candidates, or none if all are solved
    best = None
    for cell, candidates in enumerate(wave):
        if len(candidates) > 1 and (best is None or len(candidates) < len(wave[best])):
            best = cell
            if len(candidates) == 2:
                break  # can't do better than two options
    return best


def _search(wave: Wave, stats: Stats) -> Wave | None:
    cell = _lowest_entropy_cell(wave)
    if cell is None:
        return wave  # every cell has exactly one candidate
    for value in sorted(wave[cell]):
        stats.count_guess()
        trial = wave.copy()
        if _collapse(trial, cell, value):
            result = _search(trial, stats)
            if result is not None:
                return result
        stats.backtracks += 1  # contradiction: try the next candidate
    return None


def solve_wfc(grid: Grid, stats: Stats | None = None) -> Grid | None:
    # solve with wave function collapse; returns a solved grid, or none if impossible
    check_grid(grid)
    stats = stats if stats is not None else Stats()
    wave = _initial_wave(grid)
    if wave is None:
        return None
    solved = _search(wave, stats)
    if solved is None:
        return None
    return [[next(iter(solved[r * 9 + c])) for c in range(9)] for r in range(9)]


def count_solutions(grid: Grid, limit: int = 2) -> int:
    # count solutions up to limit (a proper Sudoku has exactly one)
    check_grid(grid)
    wave = _initial_wave(grid)
    if wave is None:
        return 0
    found = 0

    def search(wave: Wave) -> None:
        nonlocal found
        cell = _lowest_entropy_cell(wave)
        if cell is None:
            found += 1
            return
        for value in sorted(wave[cell]):
            if found >= limit:
                return
            trial = wave.copy()
            if _collapse(trial, cell, value):
                search(trial)

    search(wave)
    return found


SOLVERS = {"wfc": solve_wfc, "backtracking": solve_backtracking}

# command line

def _run(name: str, grid: Grid) -> Grid | None:
    stats = Stats()
    start = time.perf_counter()
    solution = SOLVERS[name](grid, stats)
    elapsed = time.perf_counter() - start
    print(f"{name}: {elapsed:.4f} s, {stats.guesses:,} guesses, "
          f"{stats.backtracks:,} backtracks")
    return solution


def main(argv: list[str] | None = None) -> int:
    from puzzles import PUZZLES

    parser = argparse.ArgumentParser(description="Solve a Sudoku puzzle.")
    parser.add_argument("puzzle", nargs="?",
                        help="81 characters, 1-9 for givens and 0 or . for blanks")
    parser.add_argument("-f", "--file", help="read the puzzle from a text file")
    parser.add_argument("-e", "--example", choices=sorted(PUZZLES),
                        help="solve one of the bundled puzzles")
    parser.add_argument("-m", "--method", choices=["wfc", "backtracking", "both"],
                        default="wfc", help="which solver to use (default: wfc)")
    args = parser.parse_args(argv)

    try:
        if args.file:
            with open(args.file, encoding="utf-8") as f:
                grid = parse_grid(f.read())
        elif args.puzzle:
            grid = parse_grid(args.puzzle)
        else:
            grid = parse_grid(PUZZLES[args.example or "evil"].grid)
        check_grid(grid)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    print("Puzzle:")
    print(format_grid(grid))
    print()

    methods = ["backtracking", "wfc"] if args.method == "both" else [args.method]
    solution = None
    for name in methods:
        solution = _run(name, grid)

    print()
    if solution is None:
        print("No solution for this Sudoku!")
        return 1
    print("Solution:")
    print(format_grid(solution))
    return 0


if __name__ == "__main__":
    sys.exit(main())