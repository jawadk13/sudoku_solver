# example puzzles (from easy to extreme) used by the command line, tests and benchmark

# each puzzle is 81 characters read left to right, top to bottom (0 = empty)
# every puzzle here has exactly one solution (checked in the tests)


from dataclasses import dataclass


@dataclass(frozen=True)
class Puzzle:
    title: str
    difficulty: str
    source: str
    grid: str

    @property
    def clues(self) -> int:
        return sum(ch != "0" for ch in self.grid)


PUZZLES = {
    "easy": Puzzle(
        title="Wikipedia example",
        difficulty="Easy",
        source="The example puzzle from Wikipedia's Sudoku article",
        grid="530070000600195000098000060800060003400803001700020006060000280000419005000080079",
    ),
    "evil": Puzzle(
        title="Sudoku.com Evil",
        difficulty="Evil (hardest level on Sudoku.com)",
        source="Sudoku.com, Evil difficulty",
        grid="009040800060508002500030000040000070700205900000300000001000006400709200000080000",
    ),
    "inkala": Puzzle(
        title='Arto Inkala\'s "world\'s hardest Sudoku"',
        difficulty="Extreme",
        source="Published by mathematician Arto Inkala in 2012",
        grid="800000000003600000070090200050007000000045700000100030001000068008500010090000400",
    ),
    "seventeen": Puzzle(
        title="17-clue puzzle",
        difficulty="Extreme (minimum possible clues)",
        source="Gordon Royle's collection of 17-clue puzzles; 17 is the fewest "
               "clues a Sudoku can have and still have one solution",
        grid="000000010400000000020000000000050407008000300001090000300400200050100000000806000",
    ),
    "anti_backtracking": Puzzle(
        title="Anti-backtracking puzzle",
        difficulty="Built to defeat brute force",
        source="Wikipedia's 'Sudoku solving algorithms' article: designed so a "
               "solver that tries 1-9 in reading order makes as many wrong guesses as possible",
        grid="000000000000003085001020000000507000004000100090000000500000073002010000000040009",
    ),
}
