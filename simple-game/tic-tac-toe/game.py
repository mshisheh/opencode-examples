import os

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def print_board(board):
    clear()
    print(" Tic-Tac-Toe\n")
    for i in range(3):
        row = " | ".join(board[i * 3:(i + 1) * 3])
        print(f"  {row}")
        if i < 2:
            print("  ---------")

def check_winner(board, player):
    lines = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],
        [0, 3, 6], [1, 4, 7], [2, 5, 8],
        [0, 4, 8], [2, 4, 6],
    ]
    return any(all(board[i] == player for i in line) for line in lines)

def is_draw(board):
    return all(c != " " for c in board)

def get_move(player):
    while True:
        try:
            n = int(input(f"\n Player {player}, pick 1-9: "))
            if 1 <= n <= 9:
                return n - 1
            print(" Must be 1-9.")
        except ValueError:
            print(" Enter a number.")

def main():
    board = [" "] * 9
    player = "X"

    while True:
        print_board(board)
        idx = get_move(player)
        if board[idx] != " ":
            print(" Spot taken, try again.")
            continue
        board[idx] = player
        if check_winner(board, player):
            print_board(board)
            print(f"\n  Player {player} wins!\n")
            break
        if is_draw(board):
            print_board(board)
            print("\n  It's a draw!\n")
            break
        player = "O" if player == "X" else "X"

if __name__ == "__main__":
    main()
