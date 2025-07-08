import pygame
import os
from settings import TILE_SIZE

class ExperienceOrb(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__(game.experience_orbs)
        self.game = game
        # Загружаем текстуру морковки вместо создания круга
        self.image = pygame.image.load(os.path.join("assets", "carrot.png")).convert_alpha()
        # Масштабируем морковку до подходящего размера
        orb_size = TILE_SIZE // 1  # размер сферы опыта (увеличили с //2 до //1.5)
        self.image = pygame.transform.scale(self.image, (orb_size, orb_size))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 2

    def update(self):
        # Магнит: если игрок близко, сфера летит к нему
        player = self.game.player
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = (dx ** 2 + dy ** 2) ** 0.5
        if dist < TILE_SIZE * 2:
            if dist > 1:
                self.rect.x += int(self.speed * dx / dist)
                self.rect.y += int(self.speed * dy / dist) 