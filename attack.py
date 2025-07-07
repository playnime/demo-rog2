import pygame
from settings import *

class Attack(pygame.sprite.Sprite):
    def __init__(self, game, player):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((TILE_SIZE * 2, TILE_SIZE * 2))
        self.image.fill((255, 0, 0))
        self.image.set_alpha(100)
        self.rect = self.image.get_rect()
        self.rect.center = player.rect.center
        self.duration = 200  # мс
        self.spawn_time = pygame.time.get_ticks()
        self.damage = 20
        self.hit_enemies = set()

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.spawn_time > self.duration:
            self.kill()
        # Проверка столкновений с врагами
        for enemy in self.game.enemies:
            if self.rect.colliderect(enemy.rect) and enemy not in self.hit_enemies:
                enemy.take_damage(self.damage)
                self.hit_enemies.add(enemy)