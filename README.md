# Sudoku Solver

A Python Sudoku solver with two algorithms side by side:

- **Backtracking**: tries numbers cell by cell and backs up when it gets stuck.
- **Wave function collapse (WFC)**: tracks every cell's possible numbers, always fills the most constrained cell first, and rules out impossible numbers as it goes.

Both solve everyday puzzles instantly. On the hardest puzzles, wave function collapse finishes in about a tenth of a second, while backtracking still hasn't finished after 5 million guesses. The [comparison table](#what-it-can-solve) below shows the difference.

No extra packages are needed, just Python 3.9 or newer.

## Quick start

```
python sudoku_solver.py
```

```
Puzzle:
. . 9 | . 4 . | 8 . .
. 6 . | 5 . 8 | . . 2
5 . . | . 3 . | . . .
------+-------+------
. 4 . | . . . | . 7 .
7 . . | 2 . 5 | 9 . .
. . . | 3 . . | . . .
------+-------+------
. . 1 | . . . | . . 6
4 . . | 7 . 9 | 2 . .
. . . | . 8 . | . . .

wfc: 0.0006 s, 24 guesses, 15 backtracks

Solution:
1 2 9 | 6 4 7 | 8 3 5
3 6 7 | 5 1 8 | 4 9 2
5 8 4 | 9 3 2 | 1 6 7
------+-------+------
6 4 2 | 8 9 1 | 5 7 3
7 1 3 | 2 6 5 | 9 8 4
9 5 8 | 3 7 4 | 6 2 1
------+-------+------
8 9 1 | 4 2 3 | 7 5 6
4 3 6 | 7 5 9 | 2 1 8
2 7 5 | 1 8 6 | 3 4 9
```

More ways to run it:

```
python sudoku_solver.py                     # solve the built-in example
python sudoku_solver.py --example inkala    # solve one of the bundled puzzles
python sudoku_solver.py "530070000600195..."  # solve your own puzzle (81 digits)
python sudoku_solver.py --file puzzle.txt   # read the puzzle from a file
python sudoku_solver.py --method both       # compare the two solvers
```

A puzzle is 81 characters read left to right, top to bottom: `1`-`9` for given numbers and `0` or `.` for empty cells. Spaces, line breaks and the characters `| - +` are ignored, so you can also paste a grid drawn like the one above.

Before solving, the program checks the puzzle. If two of the same number already share a row, column or box, it says so straight away (for example `5 appears more than once in row 1`) instead of searching forever. If the puzzle is valid but has no solution, it prints `No solution for this Sudoku!`.

## How Sudoku works

A Sudoku is a 9x9 grid split into nine 3x3 boxes. Some cells start filled in (the **clues**). The goal is to fill every empty cell with a number from 1 to 9 so that each **row**, each **column** and each **3x3 box** contains every number exactly once. A proper puzzle has exactly one solution.

## How the solvers work

### Backtracking

This is the original algorithm in this repo, a depth-first search:

1. Go to the first empty cell, reading left to right and top to bottom.
2. Try 1, then 2, then 3, and so on, and place the first number that doesn't clash with its row, column or box.
3. Move to the next empty cell and repeat.
4. If a cell has no number that fits, an earlier guess was wrong. Go back to the previous cell, erase it and try its next number.
5. When the last cell is filled, the puzzle is solved.

It's simple and always finds the answer eventually. Its weakness is that it fills cells in a fixed order and only notices a bad guess when it reaches a cell that can't be filled, which may be dozens of cells later. A wrong guess near the top of the grid can mean millions of wasted guesses before it's undone.

### Wave function collapse

[Wave function collapse](https://en.wikipedia.org/wiki/Model_synthesis) is a constraint-solving algorithm best known for generating game levels and textures. Its terms come from quantum physics, and Sudoku maps onto it neatly:

| WFC term | In Sudoku |
|---|---|
| **Superposition** | An empty cell could still be several numbers. At the start, every empty cell is "any of 1-9". |
| **Entropy** | How uncertain a cell is, meaning how many numbers it could still be. |
| **Collapse** | Fixing a cell to a single number. |
| **Propagation** | Removing that number from every other cell in the same row, column and box. |
| **Contradiction** | A cell runs out of possible numbers, so an earlier choice was wrong. |

The solver keeps a set of possible numbers (candidates) for each of the 81 cells and repeats these steps:

1. **Start.** Every cell begins with candidates 1-9. Each clue is collapsed and propagated, which already rules out many candidates.
2. **Observe.** Pick the unsolved cell with the **fewest candidates** (lowest entropy). It's the safest place to guess: with two options there's a 50% chance of being right, and with nine options only an 11% chance.
3. **Collapse.** Fix that cell to one of its candidates.
4. **Propagate.** Remove that number from all its peers. If a peer is left with one candidate, it has collapsed by itself, so propagate from it as well. One guess can solve a whole chain of cells.
5. **Repeat** until every cell has exactly one candidate (solved).
6. **Backtrack on contradiction.** If any cell ends up with zero candidates, undo the last collapse and try that cell's next candidate.

Here's an example. If a cell's row already has 1, 2, 5 and 8, its column has 3 and 9, and its box has 4 and 6, the only candidate left is 7. WFC fills it in without guessing, exactly like a person writing pencil marks. On the easy puzzle below, propagation alone solves the whole grid with **zero guesses**.

### Why WFC is so much faster on hard puzzles

- **It finds mistakes immediately.** Propagation spots a contradiction the moment a guess makes some cell impossible, instead of discovering it many cells later.
- **It guesses where it's safest.** Choosing the cell with the fewest candidates keeps the number of branches to explore small.
- **It solves cells for free.** Every collapse ripples out, so many cells are filled by deduction rather than by guessing.

Backtracking is still part of WFC (step 6). The difference is that WFC needs it far less often.

## What it can solve

All five bundled puzzles have exactly one solution, which the tests confirm. Results from `python benchmark.py`:

| Puzzle | Difficulty | Clues | Backtracking | Wave function collapse |
|---|---|---|---|---|
| Wikipedia example | Easy | 30 | 0.02 s, 4,208 guesses | 0.0004 s, **0 guesses** |
| Sudoku.com Evil | Evil (hardest level on Sudoku.com) | 23 | 0.02 s, 4,669 guesses | 0.0006 s, 24 guesses |
| Arto Inkala's "world's hardest Sudoku" | Extreme | 21 | 0.25 s, 49,558 guesses | 0.02 s, 1,850 guesses |
| 17-clue puzzle | Extreme (fewest clues possible) | 17 | not solved: stopped after 5,000,000 guesses (27 s) | 0.01 s, 1,456 guesses |
| Anti-backtracking puzzle | Built to defeat brute force | 17 | not solved: stopped after 5,000,000 guesses (25 s) | 0.13 s, 12,094 guesses |

Times will vary by computer, but the guess counts are always the same.

What the difficulty levels mean:

- **Easy to Evil** covers the puzzles you find in newspapers and apps. Both solvers handle them instantly. For WFC, easy puzzles need no guessing at all, because propagation solves them.
- **Extreme** puzzles, like Inkala's, were designed for people to need long chains of reasoning. Backtracking slows down but still finishes. WFC stays well under a second.
- **17 clues** is the fewest a Sudoku can have and still have only one solution (proven in 2012). With so few clues, backtracking has a huge number of wrong paths to explore.
- **The anti-backtracking puzzle** has an empty first row and an answer that starts 9-8-7…, so a solver that tries 1 to 9 in reading order makes as many wrong early guesses as possible. WFC doesn't care what order the cells are in, so it isn't affected.

In general, wave function collapse can solve any valid 9x9 Sudoku: any difficulty, any number of clues, even a completely empty grid. It also reliably reports puzzles that have no solution.

## Project structure

```
sudoku_solver.py              both solvers, input checking and the command line
puzzles.py                    the bundled example puzzles
benchmark.py                  times both solvers on every puzzle
tests/test_sudoku_solver.py   tests (24 of them)
```

Using it from your own code:

```python
from sudoku_solver import parse_grid, solve_wfc, format_grid

grid = parse_grid("530070000600195000098000060800060003400803001700020006060000280000419005000080079")
print(format_grid(solve_wfc(grid)))
```

## Running the tests

```
python -m unittest
```

The tests check parsing, conflict detection, that both solvers produce valid solutions that keep the original clues, that they agree with each other, that unsolvable and invalid puzzles are handled, and that every bundled puzzle has exactly one solution.

## Further reading

- [Wave function collapse / model synthesis](https://en.wikipedia.org/wiki/Model_synthesis)
- [Sudoku solving algorithms](https://en.wikipedia.org/wiki/Sudoku_solving_algorithms)
- [Mathematics of Sudoku](https://en.wikipedia.org/wiki/Mathematics_of_Sudoku) (including the 17-clue result)
