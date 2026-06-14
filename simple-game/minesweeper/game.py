import os
import random

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def make_board(rows, cols, mines):
    board = [[0] * cols for _ in range(rows)]
    positions = [(r, c) for r in range(rows) for c in range(cols)]
    for r, c in random.sample(positions, mines):
        board[r][c] = -1
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] != -1:
                    board[nr][nc] += 1
    return board

def reveal(board, shown, r, c):
    if not (0 <= r < len(board) and 0 <= c < len(board[0])) or shown[r][c]:
        return
    shown[r][c] = True
    if board[r][c] == 0:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                reveal(board, shown, r + dr, c + dc)

def display(board, shown, flags):
    clear()
    print(" Minesweeper\n")
    rows, cols = len(board), len(board[0])
    print("    " + " ".join(f"{c:2}" for c in range(cols)))
    for r in range(rows):
        print(f" {r:2} ", end="")
        for c in range(cols):
            if (r, c) in flags:
                print(" F ", end="")
            elif not shown[r][c]:
                print(" . ", end="")
            elif board[r][c] == -1:
                print(" * ", end="")
            else:
                print(f" {board[r][c] or ' '} ", end="")
        print()
    print()

def main():
    rows, cols, mine_count = 9, 9, 10
    board = make_board(rows, cols, mine_count)
    shown = [[False] * cols for _ in range(rows)]
    flags = set()
    first = True

    while True:
        display(board, shown, flags)
        print("Commands: r row col (reveal) | f row col (flag) | q (quit)")
        cmd = input("\n> ").strip().split()
        if not cmd:
            continue
        if cmd[0] == "q":
            break
        if len(cmd) != 3:
            continue
        try:
            r, c = int(cmd[1]), int(cmd[2])
        except ValueError:
            continue

        if cmd[0] == "f":
            if (r, c) in flags:
                flags.remove((r, c))
            else:
                flags.add((r, c))
            continue

        if cmd[0] != "r":
            continue
        if not (0 <= r < rows and 0 <= c < cols):
            continue

        if first:
            while board[r][c] == -1:
                board = make_board(rows, cols, mine_count)
            first = False

        if board[r][c] == -1:
            shown[r][c] = True
            display(board, shown, flags)
            print("  BOOM! You hit a mine.\n")
            break

        reveal(board, shown, r, c)

        if sum(sum(1 for c in range(cols) if not shown[r][c]) for r in range(rows)) == mine_count:
            display(board, shown, flags)
            print("  You win!\n")
            break

if __name__ == "__main__":
    main()
