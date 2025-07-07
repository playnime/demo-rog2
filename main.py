import pygame
import sys
from settings import *
from player import Player
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
        self.player = Player(self, 3, 3)
        self.map = Map(self, level_data, "GAME/roguelike/assets/tiles.png")
        self.camera = Camera(WIDTH, HEIGHT)

    def run(self):
        running = True
        while running:
            dt = clock.tick(FPS) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        attack = Attack(self.player)
                        self.all_sprites.add(attack)

            self.all_sprites.update()

            self.camera.update(self.player)

            screen.fill((0, 0, 0))
            for sprite in self.all_sprites:
                screen.blit(sprite.image, self.camera.apply(sprite))

            draw_health_bar(screen, 10, 10, self.player.health, PLAYER_HEALTH)

            pygame.display.flip()

if __name__ == '__main__':
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()