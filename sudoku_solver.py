# Sudoku solver with two algorithms: backtracking and wave function collapse.
# All code written by Jawad Kazma

import argparse
import time

from puzzles import PUZZLES     # dictionary of bundled puzzles from puzzles.py


# reading, checking and printing grids
# ---------------------------------------------------------------------------

def parse_grid(text):
    # turn an 81-character puzzle string into a 9x9 grid of ints (0 = empty)
    numbers = []
    for char in text:
        if char.isdigit():
            numbers.append(int(char))
        elif char == ".":                       # dot also means empty cell
            numbers.append(0)
        elif char.isspace() or char in "|-+":   # space, line break, or grid line
            continue                            # skip and go to next character
        else:
            raise ValueError("unexpected character '" + char + "' in puzzle")
    if len(numbers) != 81:
        raise ValueError("a puzzle needs 81 cells, got " + str(len(numbers)))
    return [numbers[i:i + 9] for i in range(0, 81, 9)]


def format_grid(grid):
    # return the grid as text with lines between the 3x3 boxes
    lines = []
    for row in range(9):
        if row in (3, 6):
            lines.append("------+-------+------")   # divider line
        row_text = []
        for col in range(9):
            if col in (3, 6):
                row_text.append("|")                # add a divider
            if grid[row][col] > 0:
                row_text.append(str(grid[row][col]))
            else:
                row_text.append(".")                # dot for empty cell
        lines.append(" ".join(row_text))
    return "\n".join(lines)


def duplicates_in(grid, cells, name):
    # check one row, column or box for repeated numbers
    problems = []
    seen = []
    for row, col in cells:
        num = grid[row][col]
        if num in seen:
            problems.append(str(num) + " appears more than once in " + name)
        elif num > 0:
            seen.append(num)
    return problems


def find_conflicts(grid):
    # list any rule breaks in the given numbers (Ex: two 5s in one row)
    problems = []

    # check every row
    for row in range(9):
        cells = []
        for col in range(9):
            cells.append((row, col))
        problems += duplicates_in(grid, cells, "row " + str(row + 1))

    # check every column
    for col in range(9):
        cells = []
        for row in range(9):
            cells.append((row, col))
        problems += duplicates_in(grid, cells, "column " + str(col + 1))

    # check every 3x3 box
    box = 1
    for corner_row in range(0, 9, 3):
        for corner_col in range(0, 9, 3):
            cells = []
            for i in range(3):
                for j in range(3):
                    cells.append((corner_row + i, corner_col + j))
            problems += duplicates_in(grid, cells, "box " + str(box))
            box += 1

    return problems


def check_grid(grid):
    # raise ValueError if two given numbers break a rule
    conflicts = find_conflicts(grid)
    if conflicts:
        raise ValueError("invalid puzzle: " + "; ".join(conflicts))


def new_stats(max_guesses=None):
    # keeps count of how much work a solver did
    return {
        "guesses": 0,               # numbers placed without being sure
        "backtracks": 0,            # guesses that hit a dead end and were undone
        "max_guesses": max_guesses  # optional limit on guesses
    }


def count_guess(stats):
    stats["guesses"] += 1
    if stats["max_guesses"] is not None and stats["guesses"] > stats["max_guesses"]:
        raise RuntimeError("reached the guess limit")


# solver 1: backtracking (the original approach)
# ---------------------------------------------------------------------------
# visit the cells in reading order
# in each empty cell, try 1 to 9 and keep the first number that doesn't break a rule
# if a cell has no number that fits, go back and change the previous guess

def is_move_valid(grid, row, col, num):
    # check this row
    for i in range(9):
        if grid[row][i] == num:
            return False

    # check this column
    for i in range(9):
        if grid[i][col] == num:
            return False

    # check this 3x3 box
    corner_row = row - row % 3  # top left row of the box
    corner_col = col - col % 3  # top left column of the box
    for i in range(3):
        for j in range(3):
            if grid[corner_row + i][corner_col + j] == num:
                return False

    return True


def backtrack(grid, row, col, stats):
    # past the last column: move to the next row, or stop if this was the last row
    if col == 9:
        if row == 8:
            return True  # every cell is filled
        row += 1
        col = 0

    # if the cell is already filled, move on to the next one
    if grid[row][col] > 0:
        return backtrack(grid, row, col + 1, stats)

    # try every number in this cell
    for num in range(1, 10):
        if is_move_valid(grid, row, col, num):
            count_guess(stats)
            grid[row][col] = num
            if backtrack(grid, row, col + 1, stats):
                return True
            # the guess led to a dead end: undo it and try the next number
            grid[row][col] = 0
            stats["backtracks"] += 1

    return False


def solve_backtracking(grid, stats=None):
    # returns a solved copy of the grid, or None if it's impossible
    check_grid(grid)
    if stats is None:
        stats = new_stats()
    solution = [row[:] for row in grid]  # don't change the caller's grid
    if backtrack(solution, 0, 0, stats):
        return solution
    return None


# solver 2: wave function collapse
# ---------------------------------------------------------------------------
# candidates[row][col] is the list of numbers that cell could still be
# (its superposition); every cell starts out as 1-9

# observe: pick the unsolved cell with the fewest candidates (lowest entropy)
# collapse: fix that cell to one of its candidates
# propagate:
#   - remove that number from every cell in the same row, column and box
#   - if that leaves a cell with one candidate, it is solved too, so propagate from it as well
#   - repeat until every cell has one candidate (solved), or a cell runs out (a contradiction)
#   - on a contradiction, go back and try that cell's next candidate

def get_peers(row, col):
    # all cells sharing a row, column or box with this cell (not itself)
    peers = []
    corner_row = row - row % 3
    corner_col = col - col % 3
    for i in range(9):
        peers.append((row, i))
        peers.append((i, col))
    for i in range(3):
        for j in range(3):
            peers.append((corner_row + i, corner_col + j))
    peers = list(set(peers))  # remove duplicates (sets drop repeats automatically)
    peers.remove((row, col))  # remove cell from own peer list
    return peers


# work out every cell's peers once, so they're never recalculated
all_peers = [[get_peers(row, col) for col in range(9)] for row in range(9)]


def collapse(candidates, row, col, num):
    # place num in a cell and update its peers; returns False on a contradiction
    if num not in candidates[row][col]:
        return False
    candidates[row][col] = [num]

    for peer_row, peer_col in all_peers[row][col]:
        peer_candidates = candidates[peer_row][peer_col]
        if num in peer_candidates:
            peer_candidates.remove(num)
            if len(peer_candidates) == 0:
                return False  # this peer has no options left
            if len(peer_candidates) == 1:
                # the peer is solved too, so collapse it the same way
                if not collapse(candidates, peer_row, peer_col, peer_candidates[0]):
                    return False

    return True


def initial_candidates(grid):
    # start every cell as 1-9, then collapse the given numbers
    candidates = [[list(range(1, 10)) for col in range(9)] for row in range(9)]
    for row in range(9):
        for col in range(9):
            if grid[row][col] > 0:
                if not collapse(candidates, row, col, grid[row][col]):
                    return None
    return candidates


def fewest_candidates(candidates):
    # the unsolved cell with the fewest candidates, or None if all are solved
    best = None
    fewest = 10
    for row in range(9):
        for col in range(9):
            count = len(candidates[row][col])
            if count > 1 and count < fewest:
                best = (row, col)
                fewest = count
                if count == 2:
                    return best  # can't do better than two options
    return best


def search(candidates, stats):
    cell = fewest_candidates(candidates)
    if cell is None:
        return candidates  # every cell has exactly one candidate
    row, col = cell
    for num in candidates[row][col]:
        count_guess(stats)
        trial = [[options[:] for options in cells] for cells in candidates]  # try the guess on a copy
        if collapse(trial, row, col, num):
            result = search(trial, stats)
            if result is not None:
                return result
        stats["backtracks"] += 1  # contradiction: try the next candidate
    return None


def solve_wfc(grid, stats=None):
    # returns a solved grid, or None if it's impossible
    check_grid(grid)
    if stats is None:
        stats = new_stats()
    candidates = initial_candidates(grid)
    if candidates is None:
        return None
    solved = search(candidates, stats)
    if solved is None:
        return None
    return [[solved[row][col][0] for col in range(9)] for row in range(9)]


# command line
# ---------------------------------------------------------------------------

def run_solver(name, solver, grid):
    stats = new_stats()
    start = time.perf_counter()
    solution = solver(grid, stats)
    elapsed = time.perf_counter() - start
    print(name + ": " + str(round(elapsed, 4)) + " s, " + str(stats["guesses"]) + " guesses, "
          + str(stats["backtracks"]) + " backtracks")
    return solution


def main(argv=None):
    parser = argparse.ArgumentParser(description="Solve a Sudoku puzzle.")
    parser.add_argument("puzzle", nargs="?", help="81 characters, 1-9 for givens and 0 or . for blanks")
    parser.add_argument("--file", help="read the puzzle from a text file")
    parser.add_argument("--example", choices=sorted(PUZZLES), default="evil", help="solve one of the bundled puzzles")
    parser.add_argument("--method", choices=["wfc", "backtracking", "both"], default="wfc", help="which solver to use")
    args = parser.parse_args(argv)

    try:
        if args.file:
            with open(args.file, encoding="utf-8") as f:
                grid = parse_grid(f.read())
        elif args.puzzle:
            grid = parse_grid(args.puzzle)
        else:
            grid = parse_grid(PUZZLES[args.example].grid)
        check_grid(grid)
    except (OSError, ValueError) as error:
        print("Error: " + str(error))
        return 2

    print("Puzzle:")
    print(format_grid(grid))
    print()

    if args.method in ("backtracking", "both"):
        solution = run_solver("backtracking", solve_backtracking, grid)
    if args.method in ("wfc", "both"):
        solution = run_solver("wfc", solve_wfc, grid)

    print()
    if solution is None:
        print("No solution for this Sudoku!")
        return 1
    print("Solution:")
    print(format_grid(solution))
    return 0


if __name__ == "__main__":
    main()
