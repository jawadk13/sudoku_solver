# time both solvers on every bundled puzzle and print a Markdown table
# python benchmark.py

# backtracking is stopped after MAX_GUESSES guesses so the run doesn't take forever

import time

from puzzles import PUZZLES
from sudoku_solver import new_stats, parse_grid, solve_backtracking, solve_wfc

MAX_GUESSES = 5_000_000


def run(solver, grid, max_guesses=None):
    stats = new_stats(max_guesses)
    start = time.perf_counter()
    try:
        solver(grid, stats)
        finished = True
    except RuntimeError:
        finished = False
    return finished, time.perf_counter() - start, stats


def describe(finished, seconds, stats):
    if not finished:
        return "gave up after " + format(stats["max_guesses"], ",") + " guesses (" + str(round(seconds)) + " s)"
    return str(round(seconds, 4)) + " s, " + format(stats["guesses"], ",") + " guesses"


def main():
    print("| Puzzle | Difficulty | Clues | Backtracking | Wave function collapse |")
    print("|---|---|---|---|---|")
    for puzzle in PUZZLES.values():
        grid = parse_grid(puzzle.grid)
        backtracking = describe(*run(solve_backtracking, grid, MAX_GUESSES))
        wfc = describe(*run(solve_wfc, grid))
        print("| " + puzzle.title + " | " + puzzle.difficulty + " | " + str(puzzle.clues) + " | " + backtracking + " | " + wfc + " |", flush=True)


if __name__ == "__main__":
    main()
