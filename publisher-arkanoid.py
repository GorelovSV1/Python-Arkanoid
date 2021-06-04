import pygame
from random import randrange as rnd
import paho.mqtt.client as mqtt
from random import uniform
import time

client = mqtt.Client("Publisher")  # создание клиента
client.connect("127.0.0.1", 1883, 60)  # подключение к брокеру
print('connected')
client.loop_start()

# -----------------------------------------ARKANOID-------------------------------------------
WIDTH, HEIGHT = 1200, 800
fps = 60
# paddle settings
paddle_w = 320
paddle_h = 35
paddle_speed = 15
paddle = pygame.Rect(WIDTH // 2 - paddle_w // 2, HEIGHT - paddle_h - 10, paddle_w, paddle_h)

# ball settings
ball_radius = 20
ball_speed = 6
ball_rect = int(ball_radius * 2 ** 0.5)
ball = pygame.Rect(rnd(ball_rect, WIDTH - ball_rect), HEIGHT // 2, ball_rect, ball_rect)
dx, dy = 1, -1
# blocks settings
block_list = [pygame.Rect(10 + 120 * i, 10 + 70 * j, 100, 50) for i in range(10) for j in range(4)]
color_list = [(rnd(30, 256), rnd(30, 256), rnd(30, 256)) for i in range(10) for j in range(4)]

pygame.init()
sc = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

print ('paddle', '    ball')
print('Х', 'X', 'Y')
paddle_cx = paddle.centerx
paddle_cy = paddle.centery
ball_cx = ball.center


def detect_collision(dx, dy, ball, rect):
    if dx > 0:
        delta_x = ball.right - rect.left
    else:
        delta_x = rect.right - ball.left
    if dy > 0:
        delta_y = ball.bottom - rect.top
    else:
        delta_y = rect.bottom - ball.top

    if abs(delta_x - delta_y) < 10:
        dx, dy = -dx, -dy
    elif delta_x > delta_y:
        dy = -dy
    elif delta_y > delta_x:
        dx = -dx
    return dx, dy


def send_ball_coords_to_topic(ball_coords: tuple) -> None:
    print('отправка координат в топик')
    client.publish("coords/ball", str(ball_coords[0]) + ',' + str(ball_coords[1]))


def send_paddle_coord_to_topic(paddle_x: int) -> None:
    print('отправка координат в топик')
    client.publish("coords/paddle", paddle_x)


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()

    # drawing world
    [pygame.draw.rect(sc, color_list[color], block) for color, block in enumerate(block_list)]
    pygame.draw.rect(sc, pygame.Color('red'), paddle)
    pygame.draw.circle(sc, pygame.Color('white'), ball.center, ball_radius)
    # ball movement
    ball.x += ball_speed * dx
    ball.y += ball_speed * dy
    # collision left right
    if ball.centerx < ball_radius or ball.centerx > WIDTH - ball_radius:
        dx = -dx
        ball_cx = ball.center
        send_ball_coords_to_topic(ball_cx)
        send_paddle_coord_to_topic(paddle_cx)
        print(paddle_cx, ball_cx)

    # collision top
    if ball.centery < ball_radius:
        dy = -dy
        ball_cx = ball.center
        send_ball_coords_to_topic(ball_cx)
        send_paddle_coord_to_topic(paddle_cx)
        print(paddle_cx, ball_cx)

    # collision paddle
    if ball.colliderect(paddle) and dy > 0:
        dx, dy = detect_collision(dx, dy, ball, paddle)
        ball_cx = ball.center
        send_ball_coords_to_topic(ball_cx)
        send_paddle_coord_to_topic(paddle_cx)
        print(paddle_cx, ball_cx)

    # collision blocks
    hit_index = ball.collidelist(block_list)
    if hit_index != -1:
        hit_rect = block_list.pop(hit_index)
        hit_color = color_list.pop(hit_index)
        dx, dy = detect_collision(dx, dy, ball, hit_rect)
        # special effect
        hit_rect.inflate_ip(ball.width * 3, ball.height * 3)
        pygame.draw.rect(sc, hit_color, hit_rect)
        fps += 2
    # win, game over
    if ball.bottom > HEIGHT:
        print('GAME OVER')
        exit()
    elif not len(block_list):
        print('WIN')
        exit()
    # control
    key = pygame.key.get_pressed()
    if key[pygame.K_LEFT] and paddle.left > 0:
        paddle.left -= paddle_speed
        paddle_cx = paddle.centerx
        paddle_cy = paddle.centery
        send_paddle_coord_to_topic(paddle_cx)
        print(paddle_cx)
    if key[pygame.K_RIGHT] and paddle.right < WIDTH:
        paddle.right += paddle_speed
        paddle_cx = paddle.centerx
        paddle_cy = paddle.centery
        send_paddle_coord_to_topic(paddle_cx)
        print(paddle_cx)
    # update screen
    pygame.display.flip()
    clock.tick(fps)
