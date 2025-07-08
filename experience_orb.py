import pygame
from settings import TILE_SIZE

class ExperienceOrb(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__(game.experience_orbs)
        self.game = game
        self.image = pygame.Surface((TILE_SIZE // 3, TILE_SIZE // 3), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (50, 150, 255), (TILE_SIZE // 6, TILE_SIZE // 6), TILE_SIZE // 6)
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