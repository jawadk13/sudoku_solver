# program to solve Sudoku - wave function collapse algorithm

def is_move_valid(grid, row, col, num):
    # check every row
    for i in range(0,9):
        if grid[row][i] == num:
            return False

    # check every column
    for i in range(0,9):
        if grid[i][col] == num:
            return False

    # check every 3x3 square
    corner_row = row - row % 3 # gives top left row of square
    corner_col = col - col % 3 # gives top left column of square
    for x in range (0,3):
        for y in range (0,3):
            if grid[corner_row + x][corner_col + y] == num:
                return False

    return True

def solve(grid, row, col):
    # check if Sudoku is solved
    if col == 9:
        if row == 8:
            return True # end has been reached 
        # else if row != 8 (moves on to the next row if row 8 hasn't been reached yet)
        row += 1
        col = 0

    # if the spot if filled, move on to the next one
    if grid[row][col] > 0:
        return solve(grid, row, col + 1)

    # try all individual possibilities
    for num in range (1, 10): # numbers 1 through 9
        # check if move is valid
        if is_move_valid(grid, row, col, num):
            grid[row][col] = num
            
            if solve(grid, row, col + 1):
                return True
        
        # else if move is invalid, leave spot unfilled
        grid[row][col] = 0

    return False

# grids used from Sudoku.com's Evil difficulty 
grid = [[0, 0, 9, 0, 4, 0, 8, 0, 0],
        [0, 6, 0, 5, 0, 8, 0, 0, 2],
        [5, 0, 0, 0, 3, 0, 0, 0, 0],
        [0, 4, 0, 0, 0, 0, 0, 7, 0],
        [7, 0, 0, 2, 0, 5, 9, 0, 0],
        [0, 0, 0, 3, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0, 6],
        [4, 0, 0, 7, 0, 9, 2, 0, 0],
        [0, 0, 0, 0, 8, 0, 0, 0, 0]]

if solve (grid, 0, 0):
    for x in range(0,9):
        for y in range(0,9):
            print(grid[x][y], end = " ")
        print()
else:
    print("No solution for this Sudoku!")