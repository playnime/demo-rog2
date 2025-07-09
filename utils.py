import pygame


def draw_health_bar(surface, x, y, health, max_health, width=100, height=10):
    ratio = health / max_health
    pygame.draw.rect(surface, (255, 0, 0), (x, y, width, height))
    pygame.draw.rect(surface, (0, 255, 0), (x, y, width * ratio, height))