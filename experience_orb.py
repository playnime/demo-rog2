import pygame
import os
from settings import *

class ExperienceOrb(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__()
        self.game = game
        self.image = pygame.image.load(os.path.join("assets", "carrot.png")).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.lifetime = 10000  # 10 seconds
        self.spawn_time = pygame.time.get_ticks()

    def update(self):
        # Remove after lifetime
        if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
            self.kill()
            return
        
        # Check collision with player
        if self.rect.colliderect(self.game.player.rect):
            self.game.upgrade_manager.on_experience_orb_collected()
            self.kill()

class Carrot(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__()
        self.game = game
        self.image = pygame.image.load(os.path.join("assets", "carrot.png")).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        # Убираем ограничение времени жизни для морковок
        # self.lifetime = 10000  # 10 seconds
        # self.spawn_time = pygame.time.get_ticks()

    def update(self):
        # Убираем проверку времени жизни - морковки не исчезают автоматически
        # if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
        #     self.kill()
        #     return
        
        # Check collision with player
        if self.rect.colliderect(self.game.player.rect):
            self.game.upgrade_manager.on_experience_orb_collected()
            self.kill() 