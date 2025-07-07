import pygame
from settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__(game.all_sprites)
        self.game = game
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.x = x * TILE_SIZE
        self.y = y * TILE_SIZE
        self.rect.x = self.x
        self.rect.y = self.y
        self.health = PLAYER_HEALTH

    def move(self, dx=0, dy=0):
        self.x += dx * PLAYER_SPEED
        self.y += dy * PLAYER_SPEED
        self.rect.x = self.x
        self.rect.y = self.y

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.move(dy=-1)
        if keys[pygame.K_s]:
            self.move(dy=1)
        if keys[pygame.K_a]:
            self.move(dx=-1)
        if keys[pygame.K_d]:
            self.move(dx=1)