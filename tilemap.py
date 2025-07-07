import pygame
from settings import TILE_SIZE

def load_tilemap(path):
    try:
        sheet = pygame.image.load(path).convert_alpha()
    except pygame.error as e:
        print(f"Не удалось загрузить файл изображения: {e}")
        raise SystemExit(e)

    tilemap = []
    sheet_width, sheet_height = sheet.get_size()

    for y in range(0, sheet_height, TILE_SIZE):
        row = []
        for x in range(0, sheet_width, TILE_SIZE):
            # Проверяем, не выходим ли мы за границу изображения
            if x + TILE_SIZE > sheet_width or y + TILE_SIZE > sheet_height:
                continue  # пропускаем неполные тайлы
            tile = sheet.subsurface(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))
            row.append(tile)
        if row:
            tilemap.append(row)
    return tilemap