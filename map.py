import pygame
from settings import *
from tilemap import load_tilemap
from lua_map_loader import LuaMapLoader
import os

class Tile(pygame.sprite.Sprite):
    def __init__(self, game, x, y, image):
        super().__init__(game.all_sprites)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x * TILE_SIZE
        self.rect.y = y * TILE_SIZE
        self.is_solid = False
        self.is_water = False

class Map:
    def __init__(self, game, level_data=None, tileset_path="assets/map/TXTilesetGrass.png", lua_map_path=None):
        self.game = game
        self.tilemap = load_tilemap(tileset_path)
        self.tile_ids = []  # двумерный массив tile_id
        self.width = 0
        self.height = 0
        if lua_map_path:
            self.load_lua_map(lua_map_path)
        elif level_data:
            self.load_from_data(level_data)
        else:
            self.create_default_map()
        # Один экземпляр Tile для отрисовки (не спрайт)
        self._draw_tile = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

    def load_lua_map(self, lua_map_path):
        loader = LuaMapLoader()
        map_data = loader.load_map_from_lua(lua_map_path)
        if map_data:
            self.width = map_data['width']
            self.height = map_data['height']
            self.tile_width = map_data['tile_width']
            self.tile_height = map_data['tile_height']
            # Берём только первый слой
            if map_data['layers']:
                self.tile_ids = map_data['layers'][0]['data']
        else:
            print("Ошибка загрузки Lua карты, создается карта по умолчанию")
            self.create_default_map()

    def load_from_data(self, level_data):
        self.tile_ids = [row[:] for row in level_data]
        self.height = len(self.tile_ids)
        self.width = len(self.tile_ids[0]) if self.height > 0 else 0

    def create_default_map(self):
        default_map = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, -1, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, -1, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ]
        self.load_from_data(default_map)

    def get_tile_id(self, x, y):
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.tile_ids[y][x]
        return -1

    def get_tile_image(self, tile_id):
        columns = 8
        row = tile_id // columns
        col = tile_id % columns
        try:
            return self.tilemap[row][col]
        except IndexError:
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
            surf.fill((255, 0, 255))
            return surf

    def is_solid_tile(self, x, y):
        # Можно добавить отдельную логику для solid-тайлов
        return False

    def is_water_tile(self, x, y):
        return False