import pygame
from settings import *

class Camera:
    def __init__(self, width, height):
        self.offset = pygame.Vector2(0, 0)
        self.width = width
        self.height = height

    def apply(self, target):
        return target.rect.move(self.offset.x, self.offset.y)

    def update(self, target):
        x = -target.rect.x + WIDTH // 2
        y = -target.rect.y + HEIGHT // 2
        self.offset = pygame.Vector2(x, y)