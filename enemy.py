import pygame
from settings import *

def create_enemy_image(color, size=TILE_SIZE):
    """Создает изображение врага заданного цвета"""
    image = pygame.Surface((size, size))
    image.fill(color)
    # Добавляем простые детали
    pygame.draw.circle(image, (255, 255, 255), (size//4, size//4), size//8)  # глаз
    pygame.draw.circle(image, (255, 255, 255), (3*size//4, size//4), size//8)  # глаз
    pygame.draw.rect(image, (100, 0, 0), (size//3, 2*size//3, size//3, size//6))  # рот
    return image

def tint_image(image, color):
    """Изменяет оттенок изображения"""
    tinted = image.copy()
    tinted.fill(color, special_flags=pygame.BLEND_MULT)
    return tinted

class Enemy(pygame.sprite.Sprite):
    def __init__(self, game, x, y, image_path, speed, health, damage, attack_cooldown, tint_color=None):
        super().__init__(game.all_sprites)
        self.game = game
        if isinstance(image_path, str):
            self.image = pygame.image.load(image_path).convert_alpha()
            scaled_image = pygame.transform.scale(self.image, (TILE_SIZE, TILE_SIZE))
            self.image = scaled_image
            if tint_color:
                self.image = tint_image(self.image, tint_color)
        else:
            # Если передается цвет, создаем изображение
            self.image = create_enemy_image(image_path)
        
        self.rect = self.image.get_rect()
        self.x = x * TILE_SIZE
        self.y = y * TILE_SIZE
        self.speed = speed
        self.health = health
        self.damage = damage
        self.attack_cooldown = attack_cooldown
        self.last_attack_time = 0

    def update(self):
        # Простое поведение: двигаемся к игроку
        dx = self.game.player.x - self.x
        dy = self.game.player.y - self.y
        dist = max(1, (dx**2 + dy**2)**0.5)

        dx = dx / dist
        dy = dy / dist

        old_x, old_y = self.x, self.y
        self.x += dx * self.speed
        self.y += dy * self.speed

        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

        # Проверка столкновения с другими врагами
        for other in self.game.enemies:
            if other is not self and self.rect.colliderect(other.rect):
                self.x, self.y = old_x, old_y
                self.rect.x = int(self.x)
                self.rect.y = int(self.y)
                break

        # Проверка столкновения с игроком для урона
        if self.rect.colliderect(self.game.player.rect):
            now = pygame.time.get_ticks()
            if now - self.last_attack_time > self.attack_cooldown:
                self.game.player.health -= self.damage
                self.last_attack_time = now

        # Проверка столкновения с игроком (не даём проходить сквозь)
        if self.rect.colliderect(self.game.player.rect):
            self.x, self.y = old_x, old_y
            self.rect.x = int(self.x)
            self.rect.y = int(self.y)

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.kill()

# Типы врагов
class BasicEnemy(Enemy):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, "assets/enemy.png", 1.5, 50, 10, 500, (255, 255, 255))  # Обычный (белый оттенок)

class FastEnemy(Enemy):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, "assets/enemy.png", 3.0, 30, 5, 300, (100, 255, 100))  # Зеленый оттенок

class StrongEnemy(Enemy):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, "assets/enemy.png", 0.8, 100, 20, 800, (255, 100, 100))  # Красный оттенок

class BossEnemy(Enemy):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, "assets/enemy2.png", 1.2, 200, 30, 1000)  # Босс (без оттенка)