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
        # Загружаем все тайлы из png tileset
        self.tilemap = load_tilemap(tileset_path)
        self.tiles = []
        if lua_map_path:
            self.load_lua_map(lua_map_path)
        elif level_data:
            self.load_from_data(level_data)
        else:
            self.create_default_map()

    def load_lua_map(self, lua_map_path):
        loader = LuaMapLoader()
        map_data = loader.load_map_from_lua(lua_map_path)
        if map_data:
            self.width = map_data['width']
            self.height = map_data['height']
            self.tile_width = map_data['tile_width']
            self.tile_height = map_data['tile_height']
            for layer in map_data['layers']:
                if layer.get('data') and len(layer['data']) > 0:
                    self.load_layer(layer)
        else:
            print("Error loading Lua map, creating default map")
            self.create_default_map()

    def load_layer(self, layer_data):
        data = layer_data['data']
        for y, row in enumerate(data):
            for x, tile_id in enumerate(row):
                if tile_id >= 0:
                    # tile_id соответствует индексу в tileset (0-индексация)
                    tile_image = self.get_tile_image(tile_id)
                    tile = Tile(self.game, x, y, tile_image)
                    self.tiles.append(tile)

    def get_tile_image(self, tile_id):
        # tile_id: 0-индексация, tileset 8x8 (64 тайла)
        columns = 8
        row = tile_id // columns
        col = tile_id % columns
        try:
            return self.tilemap[row][col]
        except IndexError:
            # Если вдруг tile_id вне диапазона, возвращаем пустой тайл
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
            surf.fill((255, 0, 255))
            return surf

    def load_from_data(self, level_data):
        for y, row in enumerate(level_data):
            for x, tile_id in enumerate(row):
                if tile_id >= 0:
                    tile_image = self.get_tile_image(tile_id)
                    Tile(self.game, x, y, tile_image)

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

    def is_solid_tile(self, x, y):
        for tile in self.tiles:
            if tile.rect.x // TILE_SIZE == x and tile.rect.y // TILE_SIZE == y:
                return getattr(tile, 'is_solid', False)
        return False

    def is_water_tile(self, x, y):
        for tile in self.tiles:
            if tile.rect.x // TILE_SIZE == x and tile.rect.y // TILE_SIZE == y:
                return getattr(tile, 'is_water', False)
        return False