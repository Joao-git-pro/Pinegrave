import pygame
import sys



pygame.init()



WIDTH = 320
HEIGHT = 180
SCALE = 3
WORLD_WIDTH = 2000



screen = pygame.display.set_mode((WIDTH * SCALE, HEIGHT * SCALE))
pygame.display.set_caption("Pinegrave")



game = pygame.Surface((WIDTH, HEIGHT))
clock = pygame.time.Clock()



sky_top = (91, 57, 83)
sky_bottom = (242, 150, 137)
dark = (25, 24, 30)
tree_color = (39, 34, 39)
ground_color = (28, 36, 31)
player_color = (139, 105, 70)
player_light = (184, 140, 80)



sky_surface = pygame.Surface((WIDTH, HEIGHT))
for y in range(HEIGHT):
    t = y / HEIGHT
    r = int(sky_top[0] + (sky_bottom[0] - sky_top[0]) * t)
    g = int(sky_top[1] + (sky_bottom[1] - sky_top[1]) * t)
    b = int(sky_top[2] + (sky_bottom[2] - sky_top[2]) * t)
    pygame.draw.line(sky_surface, (r, g, b), (0, y), (WIDTH, y))



mountains = [
    (0, 125), (20, 113), (35, 118), (50, 108), (65, 116), (82, 106),
    (100, 117), (120, 109), (140, 116), (160, 105), (180, 115),
    (200, 107), (220, 116), (245, 104), (270, 116), (295, 108),
    (320, 115), (320, 150), (0, 150)
]



def draw_background(camera_x):
    game.blit(sky_surface, (0, 0))
    offset = int(camera_x * 0.2)
    points = [(x - offset, y) for x, y in mountains]
    pygame.draw.polygon(game, (70, 68, 63), points)



def draw_trees(camera_x):
    tree_x = 55 - int(camera_x * 0.5)
    pygame.draw.line(game, tree_color, (tree_x, 125), (tree_x + 3, 50), 5)
    pygame.draw.line(game, tree_color, (tree_x + 2, 75), (tree_x - 23, 52), 3)
    pygame.draw.line(game, tree_color, (tree_x + 1, 80), (tree_x + 27, 58), 3)
    pygame.draw.line(game, tree_color, (tree_x + 1, 65), (tree_x - 12, 40), 2)
    pygame.draw.line(game, tree_color, (tree_x + 5, 68), (tree_x + 27, 45), 2)



    tree_x = 275 - int(camera_x * 0.5)
    pygame.draw.line(game, tree_color, (tree_x, 115), (tree_x - 2, 45), 6)
    pygame.draw.circle(game, dark, (tree_x, 30), 30)
    pygame.draw.circle(game, dark, (tree_x + 25, 35), 25)
    pygame.draw.circle(game, dark, (tree_x - 25, 38), 22)



def draw_ground(camera_x):
    ground = [
        (-camera_x, 135), (25 - camera_x, 131), (50 - camera_x, 136),
        (75 - camera_x, 130), (100 - camera_x, 135), (125 - camera_x, 131),
        (150 - camera_x, 137), (175 - camera_x, 132), (200 - camera_x, 136),
        (225 - camera_x, 130), (250 - camera_x, 134), (280 - camera_x, 129),
        (300 - camera_x, 133), (WORLD_WIDTH - camera_x, 130),
        (WORLD_WIDTH - camera_x, 180), (-camera_x, 180)
    ]
    pygame.draw.polygon(game, ground_color, ground)



platforms = [
    pygame.Rect(0, 155, WORLD_WIDTH, 25),
    pygame.Rect(70, 125, 55, 8),
    pygame.Rect(150, 105, 50, 8),
    pygame.Rect(240, 130, 80, 8),
    pygame.Rect(400, 120, 70, 8),
    pygame.Rect(550, 100, 60, 8),
    pygame.Rect(720, 130, 100, 8),
    pygame.Rect(950, 110, 70, 8),
    pygame.Rect(1150, 130, 100, 8),
    pygame.Rect(1400, 105, 70, 8),
    pygame.Rect(1650, 125, 100, 8),
]



def draw_platforms(camera_x):
    for platform in platforms:
        x = platform.x - camera_x
        if x + platform.width < 0 or x > WIDTH:
            continue
        pygame.draw.rect(game, (45, 35, 34), (x, platform.y, platform.width, platform.height))
        pygame.draw.rect(game, (75, 70, 45), (x, platform.y, platform.width, 3))



class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((16, 24), pygame.SRCALPHA)
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.pos = pygame.Vector2(self.rect.x, self.rect.y)
        self.speed = 90
        self.jump_force = -190
        self.gravity = 500
        self.velocity_y = 0
        self.on_ground = False
        self.frame = 0
        self.animation_time = 0
        self.direction = 1



    def input(self):
        keys = pygame.key.get_pressed()
        direction = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            direction -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            direction += 1
        if keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]:
            if self.on_ground:
                self.velocity_y = self.jump_force
                self.on_ground = False
        if direction != 0:
            self.direction = direction
        return direction



    def update(self, dt, platforms):
        direction = self.input()
        self.pos.x += direction * self.speed * dt
        self.pos.x = max(0, min(WORLD_WIDTH - self.rect.width, self.pos.x))
        self.rect.x = int(self.pos.x)



        self.velocity_y += self.gravity * dt
        self.pos.y += self.velocity_y * dt
        self.rect.y = int(self.pos.y)
        self.on_ground = False



        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.velocity_y >= 0:
                    self.rect.bottom = platform.top
                    self.pos.y = self.rect.y
                    self.velocity_y = 0
                    self.on_ground = True



        if direction != 0:
            self.animation_time += dt
            if self.animation_time >= 0.15:
                self.animation_time = 0
                self.frame = (self.frame + 1) % 2
        else:
            self.frame = 0



        self.draw_player()



    def draw_player(self):
        self.image.fill((0, 0, 0, 0))
        pygame.draw.ellipse(self.image, (20, 20, 20), (1, 20, 14, 3))



        if self.frame == 0:
            pygame.draw.rect(self.image, player_color, (5, 14, 3, 7))
            pygame.draw.rect(self.image, player_color, (9, 14, 3, 7))
        else:
            pygame.draw.rect(self.image, player_color, (3, 14, 3, 7))
            pygame.draw.rect(self.image, player_color, (10, 14, 3, 7))



        pygame.draw.rect(self.image, (75, 57, 51), (3, 8, 10, 7))
        pygame.draw.rect(self.image, player_light, (5, 3, 7, 6))
        pygame.draw.rect(self.image, (34, 30, 32), (4, 2, 9, 3))



        if self.direction >= 0:
            pygame.draw.line(self.image, (170, 166, 143), (12, 11), (16, 6), 1)
        else:
            pygame.draw.line(self.image, (170, 166, 143), (3, 11), (0, 6), 1)



class Cage:
    def __init__(self, x, y):
        self.x = x
        self.y = y



    def draw(self, camera_x):
        x = self.x - camera_x
        y = self.y
        if x < -30 or x > WIDTH + 30:
            return



        pygame.draw.line(game, (70, 75, 70), (x, 50), (x, y - 12), 1)
        pygame.draw.rect(game, (100, 105, 95), (x - 15, y - 12, 30, 3))



        for i in range(-12, 13, 6):
            pygame.draw.rect(game, (45, 50, 47), (x + i, y - 8, 2, 27))



        pygame.draw.line(game, (100, 105, 95), (x - 13, y + 20), (x + 13, y + 20), 2)



player = Player(65, 155)
player_group = pygame.sprite.GroupSingle(player)
cage = Cage(151, 72)
camera_x = 0



def update_camera():
    global camera_x
    target = player.rect.centerx - WIDTH // 2
    camera_x += (target - camera_x) * 0.1
    camera_x = max(0, min(camera_x, WORLD_WIDTH - WIDTH))



running = True
while running:
    dt = clock.tick(60) / 1000



    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False



    player_group.update(dt, platforms)
    update_camera()



    draw_background(camera_x)
    draw_trees(camera_x)
    draw_ground(camera_x)
    draw_platforms(camera_x)
    cage.draw(camera_x)
    player_group.draw(game)



    scaled = pygame.transform.scale(game, (WIDTH * SCALE, HEIGHT * SCALE))
    screen.blit(scaled, (0, 0))
    pygame.display.flip()



pygame.quit()
sys.exit()