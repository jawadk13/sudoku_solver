"""Tests for the Sudoku solvers. Run with:  python -m unittest"""

import io
import os
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from puzzles import PUZZLES  # noqa: E402
from sudoku_solver import (  # noqa: E402
    new_stats,
    check_grid,
    collapse,
    fewest_candidates,
    initial_candidates,
    find_conflicts,
    format_grid,
    main,
    parse_grid,
    solve_backtracking,
    solve_wfc,
)

# no conflicting givens, but cell (row 1, col 9) can't hold anything:
# its row already has 1-8 and its column already has the 9
UNSOLVABLE = "123456780" + "000000009" + "0" * 63

# puzzles both solvers finish quickly (backtracking is too slow on the others)
FAST_FOR_BOTH = ["easy", "evil", "inkala"]


def keeps_givens(puzzle, solution):
    return all(puzzle[r][c] in (0, solution[r][c]) for r in range(9) for c in range(9))


def is_solved(grid):
    return all(all(row) for row in grid) and not find_conflicts(grid)


def count_solutions(grid, limit=2):
    # count solutions up to limit (a proper Sudoku has exactly one)
    candidates = initial_candidates(grid)
    if candidates is None:
        return 0
    return count_from(candidates, limit)


def count_from(candidates, limit):
    cell = fewest_candidates(candidates)
    if cell is None:
        return 1
    row, col = cell
    found = 0
    for num in candidates[row][col]:
        if found >= limit:
            break
        trial = [[options[:] for options in cells] for cells in candidates]
        if collapse(trial, row, col, num):
            found += count_from(trial, limit - found)
    return found


class TestParsing(unittest.TestCase):
    def test_digits_and_dots(self):
        grid = parse_grid("." * 80 + "5")
        self.assertEqual(grid[8][8], 5)
        self.assertEqual(sum(map(sum, grid)), 5)

    def test_ignores_layout_characters(self):
        drawn = format_grid(parse_grid(PUZZLES["easy"].grid))
        self.assertEqual(parse_grid(drawn), parse_grid(PUZZLES["easy"].grid))

    def test_wrong_length(self):
        with self.assertRaises(ValueError):
            parse_grid("123")

    def test_bad_character(self):
        with self.assertRaises(ValueError):
            parse_grid("x" + "0" * 80)


class TestChecking(unittest.TestCase):
    def test_valid_puzzle_has_no_conflicts(self):
        self.assertEqual(find_conflicts(parse_grid(PUZZLES["evil"].grid)), [])

    def test_duplicate_in_row(self):
        grid = parse_grid("55" + "0" * 79)
        self.assertIn("5 appears more than once in row 1", find_conflicts(grid))

    def test_duplicate_in_column(self):
        grid = parse_grid("7" + "0" * 8 + "7" + "0" * 71)
        self.assertIn("7 appears more than once in column 1", find_conflicts(grid))

    def test_duplicate_in_box(self):
        grid = parse_grid("3" + "0" * 9 + "3" + "0" * 70)  # (1,1) and (2,2)
        self.assertIn("3 appears more than once in box 1", find_conflicts(grid))

    def test_check_grid_rejects_conflicts(self):
        with self.assertRaises(ValueError):
            check_grid(parse_grid("55" + "0" * 79))



class TestSolvers(unittest.TestCase):
    def test_wfc_solves_every_bundled_puzzle(self):
        for name, puzzle in PUZZLES.items():
            with self.subTest(name):
                grid = parse_grid(puzzle.grid)
                solution = solve_wfc(grid)
                self.assertIsNotNone(solution)
                self.assertTrue(is_solved(solution))
                self.assertTrue(keeps_givens(grid, solution))

    def test_backtracking_solves_fast_puzzles(self):
        for name in FAST_FOR_BOTH:
            with self.subTest(name):
                grid = parse_grid(PUZZLES[name].grid)
                solution = solve_backtracking(grid)
                self.assertTrue(is_solved(solution))
                self.assertTrue(keeps_givens(grid, solution))

    def test_both_solvers_agree(self):
        for name in FAST_FOR_BOTH:
            with self.subTest(name):
                grid = parse_grid(PUZZLES[name].grid)
                self.assertEqual(solve_wfc(grid), solve_backtracking(grid))

    def test_input_grid_is_not_changed(self):
        grid = parse_grid(PUZZLES["evil"].grid)
        before = [row[:] for row in grid]
        solve_wfc(grid)
        solve_backtracking(grid)
        self.assertEqual(grid, before)

    def test_every_bundled_puzzle_has_one_solution(self):
        for name, puzzle in PUZZLES.items():
            with self.subTest(name):
                self.assertEqual(count_solutions(parse_grid(puzzle.grid)), 1)

    def test_unsolvable_puzzle(self):
        grid = parse_grid(UNSOLVABLE)
        self.assertEqual(find_conflicts(grid), [])
        self.assertIsNone(solve_wfc(grid))
        self.assertIsNone(solve_backtracking(grid))
        self.assertEqual(count_solutions(grid), 0)

    def test_conflicting_puzzle_is_rejected_quickly(self):
        grid = parse_grid("55" + "0" * 79)
        with self.assertRaises(ValueError):
            solve_wfc(grid)
        with self.assertRaises(ValueError):
            solve_backtracking(grid)

    def test_empty_grid(self):
        grid = parse_grid("0" * 81)
        self.assertTrue(is_solved(solve_wfc(grid)))
        self.assertEqual(count_solutions(grid, limit=5), 5)

    def test_easy_puzzle_needs_no_guesses_with_wfc(self):
        stats = new_stats()
        solve_wfc(parse_grid(PUZZLES["easy"].grid), stats)
        self.assertEqual(stats["guesses"], 0)

    def test_guess_limit(self):
        grid = parse_grid(PUZZLES["anti_backtracking"].grid)
        with self.assertRaises(RuntimeError):
            solve_backtracking(grid, new_stats(1000))


class TestCommandLine(unittest.TestCase):
    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_default_example(self):
        code, out, _ = self.run_main()
        self.assertEqual(code, 0)
        self.assertIn("Solution:", out)

    def test_both_methods(self):
        code, out, _ = self.run_main("--example", "inkala", "--method", "both")
        self.assertEqual(code, 0)
        self.assertIn("backtracking:", out)
        self.assertIn("wfc:", out)

    def test_unsolvable(self):
        code, out, _ = self.run_main(UNSOLVABLE)
        self.assertEqual(code, 1)
        self.assertIn("No solution", out)

    def test_invalid_input(self):
        code, out, _ = self.run_main("123")
        self.assertEqual(code, 2)
        self.assertIn("Error", out)


if __name__ == "__main__":
    unittest.main()
