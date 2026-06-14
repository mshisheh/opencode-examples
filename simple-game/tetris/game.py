import pygame
import random

pygame.init()

COLS, ROWS = 10, 20
CELL = 30
W, H = COLS * CELL, ROWS * CELL
FPS = 10

BLACK = (0, 0, 0)
COLORS = [(0, 255, 255), (0, 0, 255), (255, 128, 0),
          (255, 255, 0), (0, 255, 0), (128, 0, 128), (255, 0, 0)]

SHAPES = [
    [[1, 1, 1, 1]],
    [[1, 1], [1, 1]],
    [[1, 0, 0], [1, 1, 1]],
    [[0, 0, 1], [1, 1, 1]],
    [[0, 1, 1], [1, 1, 0]],
    [[1, 1, 0], [0, 1, 1]],
    [[0, 1, 0], [1, 1, 1]],
]

def rotate(shape):
    return [list(row) for row in zip(*shape[::-1])]

def collide(board, shape, x, y):
    for r in range(len(shape)):
        for c in range(len(shape[0])):
            if shape[r][c]:
                nx, ny = x + c, y + r
                if nx < 0 or nx >= COLS or ny >= ROWS or (ny >= 0 and board[ny][nx]):
                    return True
    return False

def merge(board, shape, x, y, color):
    for r in range(len(shape)):
        for c in range(len(shape[0])):
            if shape[r][c]:
                board[y + r][x + c] = color

def clear_lines(board):
    cleared = 0
    new_board = [row for row in board if any(c == 0 for c in row)]
    cleared = ROWS - len(new_board)
    while len(new_board) < ROWS:
        new_board.insert(0, [0] * COLS)
    return new_board, cleared

def draw(screen, board, score):
    screen.fill(BLACK)
    for r in range(ROWS):
        for c in range(COLS):
            color = board[r][c]
            if color:
                rect = (c * CELL, r * CELL, CELL - 1, CELL - 1)
                pygame.draw.rect(screen, COLORS[color - 1], rect)
    font = pygame.font.SysFont("monospace", 24)
    text = font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(text, (10, 10))

def main():
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Tetris")
    clock = pygame.time.Clock()

    board = [[0] * COLS for _ in range(ROWS)]
    score = 0
    piece = random.choice(SHAPES)
    color = random.randint(1, 7)
    x, y = COLS // 2 - len(piece[0]) // 2, 0
    fall_time = 0
    running = True

    while running:
        fall_time += clock.get_rawtime()
        clock.tick()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and not collide(board, piece, x - 1, y):
                    x -= 1
                if event.key == pygame.K_RIGHT and not collide(board, piece, x + 1, y):
                    x += 1
                if event.key == pygame.K_DOWN and not collide(board, piece, x, y + 1):
                    y += 1
                if event.key == pygame.K_UP:
                    rotated = rotate(piece)
                    if not collide(board, rotated, x, y):
                        piece = rotated
                if event.key == pygame.K_SPACE:
                    while not collide(board, piece, x, y + 1):
                        y += 1

        if fall_time >= 500:
            if not collide(board, piece, x, y + 1):
                y += 1
            else:
                merge(board, piece, x, y, color)
                board, cleared = clear_lines(board)
                score += cleared * 100
                piece = random.choice(SHAPES)
                color = random.randint(1, 7)
                x, y = COLS // 2 - len(piece[0]) // 2, 0
                if collide(board, piece, x, y):
                    break
            fall_time = 0

        draw(screen, board, score)
        for r in range(len(piece)):
            for c in range(len(piece[0])):
                if piece[r][c]:
                    px, py = (x + c) * CELL, (y + r) * CELL
                    pygame.draw.rect(screen, COLORS[color - 1], (px, py, CELL - 1, CELL - 1))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
