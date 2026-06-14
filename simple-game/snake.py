import curses
import random
import time

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(100)

    sh, sw = stdscr.getmaxyx()
    snake = [[sh // 2, sw // 2]]
    dirs = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}
    direction = dirs["RIGHT"]
    food = [random.randint(1, sh - 2), random.randint(1, sw - 2)]
    score = 0

    while True:
        key = stdscr.getch()
        if key == curses.KEY_UP and direction != dirs["DOWN"]:
            direction = dirs["UP"]
        elif key == curses.KEY_DOWN and direction != dirs["UP"]:
            direction = dirs["DOWN"]
        elif key == curses.KEY_LEFT and direction != dirs["RIGHT"]:
            direction = dirs["LEFT"]
        elif key == curses.KEY_RIGHT and direction != dirs["LEFT"]:
            direction = dirs["RIGHT"]
        elif key == ord("q"):
            break

        head = [snake[0][0] + direction[0], snake[0][1] + direction[1]]
        if (head in snake or head[0] <= 0 or head[0] >= sh - 1 or
                head[1] <= 0 or head[1] >= sw - 1):
            break

        snake.insert(0, head)

        if head == food:
            score += 1
            while True:
                food = [random.randint(1, sh - 2), random.randint(1, sw - 2)]
                if food not in snake:
                    break
        else:
            snake.pop()

        stdscr.clear()
        stdscr.border(0)
        stdscr.addstr(0, 2, f" Score: {score} ")
        for y, x in snake:
            stdscr.addch(y, x, curses.ACS_BLOCK)
        stdscr.addch(food[0], food[1], curses.ACS_PI)

    stdscr.clear()
    msg = f"Game Over! Score: {score}"
    stdscr.addstr(sh // 2, (sw - len(msg)) // 2, msg)
    stdscr.nodelay(0)
    stdscr.getch()

if __name__ == "__main__":
    curses.wrapper(main)
