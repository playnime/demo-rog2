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
    def __init__(self, game, level_data=None, tileset_path="assets/tiles.png", lua_map_path=None):
        self.game = game
        # Try to load ground.jpg with diagnostics
        try:
            ground_img = pygame.transform.scale(pygame.image.load(os.path.join('assets', 'ground.jpg')).convert(), (TILE_SIZE, TILE_SIZE))
            print("ground.jpg loaded successfully")
        except Exception as e:
            print(f"Error loading ground.jpg: {e}")
            ground_img = pygame.Surface((TILE_SIZE, TILE_SIZE))
            ground_img.fill((255, 0, 255))
        self.tile_images = {
            'ground': ground_img,
            'water': pygame.transform.scale(pygame.image.load(os.path.join('assets', 'water.jpg')).convert(), (TILE_SIZE, TILE_SIZE)),
            'sand beach': pygame.transform.scale(pygame.image.load(os.path.join('assets', 'sand_beach.jpg')).convert(), (TILE_SIZE, TILE_SIZE)),
            'stone beach': pygame.transform.scale(pygame.image.load(os.path.join('assets', 'stone_beach.jpg')).convert(), (TILE_SIZE, TILE_SIZE)),
        }
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
            # Sort layers: first water, then ground, then others
            water_layers = [layer for layer in map_data['layers'] if 'water' in layer.get('name', '').lower()]
            ground_layers = [layer for layer in map_data['layers'] if 'ground' in layer.get('name', '').lower()]
            other_layers = [layer for layer in map_data['layers'] if layer not in water_layers + ground_layers]
            # New order: water -> ground -> others
            sorted_layers = water_layers + ground_layers + other_layers
            for layer in sorted_layers:
                if layer.get('data') and len(layer['data']) > 0:
                    self.load_layer(layer)
        else:
            print("Error loading Lua map, creating default map")
            self.create_default_map()

    def load_layer(self, layer_data):
        data = layer_data['data']
        layer_name = layer_data.get('name', '').lower()
        # Determine image for layer
        if 'water' in layer_name:
            tile_image = self.tile_images['water']
        elif 'sand' in layer_name:
            tile_image = self.tile_images['sand beach']
        elif 'stone' in layer_name:
            tile_image = self.tile_images['stone beach']
        else:
            tile_image = self.tile_images['ground']
        ground_count = 0
        for y, row in enumerate(data):
            for x, tile_id in enumerate(row):
                if tile_id >= 0:
                    tile = Tile(self.game, x, y, tile_image)
                    self.tiles.append(tile)
                    if tile_image == self.tile_images['ground']:
                        ground_count += 1
        if tile_image == self.tile_images['ground']:
            print(f"Created ground tiles: {ground_count}")

    def load_from_data(self, level_data):
        for y, row in enumerate(level_data):
            for x, tile_id in enumerate(row):
                if tile_id >= 0:
                    Tile(self.game, x, y, self.tile_images['ground'])

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