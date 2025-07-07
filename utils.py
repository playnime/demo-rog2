import pygame


def draw_health_bar(surface, x, y, health, max_health):
    ratio = health / max_health
    pygame.draw.rect(surface, (255, 0, 0), (x, y, 100, 10))
    pygame.draw.rect(surface, (0, 255, 0), (x, y, 100 * ratio, 10))