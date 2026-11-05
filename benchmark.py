"""Time both solvers on every bundled puzzle and print a Markdown table.

    python benchmark.py

Backtracking is stopped after MAX_GUESSES guesses so the run doesn't take forever.
"""

import time

from puzzles import PUZZLES
from sudoku_solver import SearchLimitReached, Stats, parse_grid, solve_backtracking, solve_wfc

MAX_GUESSES = 5_000_000


def run(solver, grid, max_guesses=None):
    stats = Stats(max_guesses=max_guesses)
    start = time.perf_counter()
    try:
        solver(grid, stats)
        finished = True
    except SearchLimitReached:
        finished = False
    return finished, time.perf_counter() - start, stats


def describe(finished, seconds, stats):
    if not finished:
        return f"gave up after {stats.max_guesses:,} guesses ({seconds:.0f} s)"
    return f"{seconds:.4f} s, {stats.guesses:,} guesses"


def main():
    print("| Puzzle | Difficulty | Clues | Backtracking | Wave function collapse |")
    print("|---|---|---|---|---|")
    for puzzle in PUZZLES.values():
        grid = parse_grid(puzzle.grid)
        backtracking = describe(*run(solve_backtracking, grid, MAX_GUESSES))
        wfc = describe(*run(solve_wfc, grid))
        print(f"| {puzzle.title} | {puzzle.difficulty} | {puzzle.clues} "
              f"| {backtracking} | {wfc} |", flush=True)


if __name__ == "__main__":
    main()
