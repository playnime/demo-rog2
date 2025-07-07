import pygame
import sys
import random
import math
from settings import *
from player import Player
from enemy import Enemy
from map import Map
from camera import Camera
from attack import Attack
from utils import draw_health_bar

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Уровень (пример)
level_data = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, -1, -1, -1, -1, -1, -1, 0],
    [0, -1, -1, -1, -1, -1, -1, 0],
    [0, -1, -1, -1, -1, -1, -1, 0],
    [0, -1, -1, -1, -1, -1, -1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

class Game:
    def __init__(self):
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.player = Player(self, 3, 3)
        self.map = Map(self, level_data, "assets/tiles.png")
        self.camera = Camera(WIDTH, HEIGHT)
        self.enemy = Enemy(self, 5, 5)  # начальная позиция врага
        self.all_sprites.add(self.enemy)
        self.enemies.add(self.enemy)
        
        # Система спавна врагов
        self.last_spawn_time = pygame.time.get_ticks()
        self.spawn_interval = 5000  # 5 секунд в миллисекундах
        self.spawn_distance = 200  # Расстояние от игрока для спавна

    def spawn_enemy(self):
        # Генерируем случайный угол
        angle = random.uniform(0, 2 * 3.14159)
        # Генерируем случайное расстояние в пределах spawn_distance
        distance = random.uniform(100, self.spawn_distance)
        
        # Вычисляем позицию относительно игрока
        spawn_x = self.player.x + distance * math.cos(angle)
        spawn_y = self.player.y + distance * math.sin(angle)
        
        # Создаем врага в этой позиции
        enemy = Enemy(self, spawn_x // TILE_SIZE, spawn_y // TILE_SIZE)
        self.all_sprites.add(enemy)
        self.enemies.add(enemy)

    def run(self):
        running = True
        while running:
            dt = clock.tick(FPS) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        attack = Attack(self, self.player)
                        self.all_sprites.add(attack)

            self.all_sprites.update()

            # Спавн врагов каждые 5 секунд
            current_time = pygame.time.get_ticks()
            if current_time - self.last_spawn_time > self.spawn_interval:
                self.spawn_enemy()
                self.last_spawn_time = current_time

            self.camera.update(self.player)

            screen.fill((0, 0, 0))
            for sprite in self.all_sprites:
                screen.blit(sprite.image, self.camera.apply(sprite))

            draw_health_bar(screen, 10, 10, self.player.health, PLAYER_HEALTH)
            draw_health_bar(screen, 10, 10, self.player.health, PLAYER_HEALTH)

            pygame.display.flip()

if __name__ == '__main__':
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()