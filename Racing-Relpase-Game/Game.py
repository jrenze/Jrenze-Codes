import pygame, random, sys, subprocess

pygame.init()

w, h = 500, 700
screen = pygame.display.set_mode((w, h))
clock = pygame.time.Clock()

car = pygame.Rect(w//2 - 20, h - 100, 40, 80)
road_lines = [pygame.Rect(w//2 - 5, i, 10, 40) for i in range(0, h, 100)]
pygame.display.set_caption("Joke lang po ito")

enemy_cars = []
speed = 3
distance = 0
score = 0
font = pygame.font.SysFont("Courier", 30, bold=True)
retro_font = pygame.font.SysFont("Courier", 60, bold=True)

game_over = False
video_played = False
running = True

lanes = [80, 160, 240, 320, 400]
last_spawn_lane = None

def draw_tv_effect():
    for y in range(0, h, 4):
        pygame.draw.line(screen, (10, 10, 10), (0, y), (w, y))

def play_game_over_video():
    path = "Your File Path Here"
    subprocess.Popen([
        "ffplay",
        "-autoexit",
        "-loglevel", "quiet",
        path
    ])

while running:
    screen.fill((0, 0, 0))
    pygame.draw.rect(screen, (20, 20, 20), (50, 0, 400, h))
    for line in road_lines:
        pygame.draw.rect(screen, (180, 180, 180), line)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if game_over and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                enemy_cars.clear()
                distance = 0
                score = 0
                speed = 3
                car.x, car.y = w//2 - 20, h - 100
                game_over = False
                video_played = False

    if not game_over:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and car.left > 60:
            car.x -= 7
        if keys[pygame.K_RIGHT] and car.right < 440:
            car.x += 7

        distance += speed / 10
        score = int(distance)
        speed = 3 + distance / 150

        if random.randint(1, 40) == 1:
            lane = random.choice(lanes)
            if lane != last_spawn_lane:
                enemy_cars.append(pygame.Rect(lane, -100, 40, 80))

        new_enemies = []
        occupied_lanes = []
        for enemy in enemy_cars:
            enemy.y += speed
            if enemy.y < h:
                if enemy.x not in occupied_lanes:
                    new_enemies.append(enemy)
                    occupied_lanes.append(enemy.x)
        enemy_cars = new_enemies

        for enemy in enemy_cars:
            pygame.draw.rect(screen, (150, 150, 0), enemy)
            pygame.draw.rect(screen, (0, 0, 0), (enemy.x-8, enemy.y+20, 12, 15))
            pygame.draw.rect(screen, (0, 0, 0), (enemy.x+36, enemy.y+20, 12, 15))
            pygame.draw.rect(screen, (0, 0, 0), (enemy.x-8, enemy.y+50, 12, 15))
            pygame.draw.rect(screen, (0, 0, 0), (enemy.x+36, enemy.y+50, 12, 15))

            if enemy.colliderect(car):
                game_over = True

        pygame.draw.rect(screen, (0, 200, 150), car)
        pygame.draw.rect(screen, (0, 0, 0), (car.x-8, car.y+20, 12, 15))
        pygame.draw.rect(screen, (0, 0, 0), (car.x+36, car.y+20, 12, 15))
        pygame.draw.rect(screen, (0, 0, 0), (car.x-8, car.y+50, 12, 15))
        pygame.draw.rect(screen, (0, 0, 0), (car.x+36, car.y+50, 12, 15))

        for line in road_lines:
            line.y += speed
            if line.y > h:
                line.y = -100

        score_text = font.render(f"SCORE: {score}", True, (255, 255, 0))
        screen.blit(score_text, (10, 10))

        draw_tv_effect()

    else:
        if not video_played:
            play_game_over_video()
            video_played = True
        over_text = retro_font.render("GAME OVER", True, (255, 255, 0))
        retry_text = font.render("Press ENTER to Retry", True, (200, 200, 200))
        screen.blit(over_text, (w//2 - over_text.get_width()//2, h//2 - 60))
        screen.blit(retry_text, (w//2 - retry_text.get_width()//2, h//2 + 20))
        draw_tv_effect()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
