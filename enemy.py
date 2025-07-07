import pygame
from settings import *

class Enemy(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__(game.all_sprites)
        self.game = game
        self.image = pygame.image.load("assets/enemy.png").convert_alpha()
        scaled_image = pygame.transform.scale(self.image, (TILE_SIZE, TILE_SIZE))
        self.image = scaled_image
        
        self.rect = self.image.get_rect()
        self.x = x * TILE_SIZE
        self.y = y * TILE_SIZE
        self.speed = 1.5
        self.health = 50

    def update(self):
        # Простое поведение: двигаемся к игроку
        dx = self.game.player.x - self.x
        dy = self.game.player.y - self.y
        dist = max(1, (dx**2 + dy**2)**0.5)

        dx = dx / dist
        dy = dy / dist

        self.x += dx * self.speed
        self.y += dy * self.speed

        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

        # Проверка столкновения с игроком
        if self.rect.colliderect(self.game.player.rect):
            self.game.player.health -= 0.5  # Наносим маленький урон постепенно

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.kill()