import pygame

pygame.init()

W, H = 800, 600
PADDLE_W, PADDLE_H = 15, 100
BALL_SIZE = 15
FPS = 60
SPEED = 7

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Pong")
clock = pygame.time.Clock()
font = pygame.font.SysFont("monospace", 36)

def draw(p1_y, p2_y, ball, score1, score2):
    screen.fill(BLACK)
    pygame.draw.rect(screen, WHITE, (20, p1_y, PADDLE_W, PADDLE_H))
    pygame.draw.rect(screen, WHITE, (W - 20 - PADDLE_W, p2_y, PADDLE_W, PADDLE_H))
    pygame.draw.ellipse(screen, WHITE, (ball[0], ball[1], BALL_SIZE, BALL_SIZE))
    pygame.draw.line(screen, WHITE, (W // 2, 0), (W // 2, H), 2)
    s1 = font.render(str(score1), True, WHITE)
    s2 = font.render(str(score2), True, WHITE)
    screen.blit(s1, (W // 2 - 50, 20))
    screen.blit(s2, (W // 2 + 30, 20))
    pygame.display.flip()

def main():
    p1_y = p2_y = H // 2 - PADDLE_H // 2
    ball = [W // 2 - BALL_SIZE // 2, H // 2 - BALL_SIZE // 2]
    dx, dy = SPEED, SPEED
    score1 = score2 = 0
    running = True

    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] and p1_y > 0:
            p1_y -= 8
        if keys[pygame.K_s] and p1_y < H - PADDLE_H:
            p1_y += 8
        if keys[pygame.K_UP] and p2_y > 0:
            p2_y -= 8
        if keys[pygame.K_DOWN] and p2_y < H - PADDLE_H:
            p2_y += 8

        ball[0] += dx
        ball[1] += dy

        if ball[1] <= 0 or ball[1] >= H - BALL_SIZE:
            dy = -dy

        bx, by = ball
        if (bx <= 20 + PADDLE_W and p1_y <= by + BALL_SIZE // 2 <= p1_y + PADDLE_H
                and ball[0] <= 20 + PADDLE_W):
            dx = -dx
            ball[0] = 20 + PADDLE_W
        if (bx >= W - 20 - PADDLE_W - BALL_SIZE
                and p2_y <= by + BALL_SIZE // 2 <= p2_y + PADDLE_H
                and ball[0] >= W - 20 - PADDLE_W - BALL_SIZE):
            dx = -dx
            ball[0] = W - 20 - PADDLE_W - BALL_SIZE

        if ball[0] < 0:
            score2 += 1
            ball = [W // 2 - BALL_SIZE // 2, H // 2 - BALL_SIZE // 2]
            dx = SPEED * (-1 if dx > 0 else 1)
        elif ball[0] > W:
            score1 += 1
            ball = [W // 2 - BALL_SIZE // 2, H // 2 - BALL_SIZE // 2]
            dx = SPEED * (-1 if dx > 0 else 1)

        draw(p1_y, p2_y, ball, score1, score2)

    pygame.quit()

if __name__ == "__main__":
    main()
