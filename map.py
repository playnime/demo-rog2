import pygame
from settings import *
from tilemap import load_tilemap

class Tile(pygame.sprite.Sprite):
    def __init__(self, game, x, y, image):
        self.groups = game.all_sprites
        super().__init__(self.groups)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x * TILE_SIZE
        self.rect.y = y * TILE_SIZE

class Map:
    def __init__(self, game, level_data, tileset_path):
        self.game = game
        self.tileset = load_tilemap(tileset_path)
        self.tiles = []

        for y, row in enumerate(level_data):
            for x, tile_id in enumerate(row):
                if tile_id >= 0:
                    Tile(game, x, y, self.tileset[tile_id][0])