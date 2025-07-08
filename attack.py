import pygame
import math
import random
from settings import *

class Attack(pygame.sprite.Sprite):
    def __init__(self, game, player):
        super().__init__()
        self.game = game
        self.player = player
        
        # Базовые характеристики
        self.damage = player.attack_damage
        self.size_multiplier = 1.0
        self.explosive = False
        self.explosion_radius = TILE_SIZE * 3
        
        # Создаем изображение атаки с учетом размера
        base_size = TILE_SIZE * 2
        attack_size = int(base_size * self.size_multiplier)
        self.image = pygame.Surface((attack_size, attack_size))
        self.image.fill((255, 0, 0))
        self.image.set_alpha(100)
        
        # Если взрывная атака, делаем её круглой
        if self.explosive:
            self.image = pygame.Surface((attack_size, attack_size), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (255, 0, 0, 100), (attack_size//2, attack_size//2), attack_size//2)
        
        self.rect = self.image.get_rect()
        self.rect.center = player.rect.center
        self.duration = 200  # мс
        self.spawn_time = pygame.time.get_ticks()
        self.hit_enemies = set()

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.spawn_time > self.duration:
            self.kill()
            return
        
        # Проверка столкновений с врагами
        for enemy in self.game.enemies:
            if enemy not in self.hit_enemies:
                if self.explosive:
                    # Взрывная атака - проверяем расстояние
                    distance = math.sqrt((enemy.rect.centerx - self.rect.centerx)**2 + 
                                       (enemy.rect.centery - self.rect.centery)**2)
                    if distance <= self.explosion_radius:
                        enemy.take_damage(self.damage)
                        self.hit_enemies.add(enemy)
                        # Вызываем метод убийства врага для системы прокачки
                        if enemy.health <= 0:
                            self.player.on_kill_enemy()
                            result = self.game.upgrade_manager.on_enemy_killed()
                            if result == "spawn_boss":
                                self.game.spawn_boss()
                else:
                    # Обычная атака - проверяем столкновение
                    if self.rect.colliderect(enemy.rect):
                        enemy.take_damage(self.damage)
                        self.hit_enemies.add(enemy)
                        # Вызываем метод убийства врага для системы прокачки
                        if enemy.health <= 0:
                            self.player.on_kill_enemy()
                            result = self.game.upgrade_manager.on_enemy_killed()
                            if result == "spawn_boss":
                                self.game.spawn_boss()

class SwingAttack(pygame.sprite.Sprite):
    def __init__(self, game, player, direction):
        super().__init__()
        self.game = game
        self.player = player
        self.damage = player.attack_damage
        self.size_multiplier = player.attack_size_multiplier
        self.explosive = player.explosive_attack
        self.explosion_radius = TILE_SIZE * 3 * self.size_multiplier
        self.critical_chance = player.critical_chance
        self.duration = 180  # мс
        self.spawn_time = pygame.time.get_ticks()
        self.hit_enemies = set()
        self.direction = direction  # (dx, dy) нормализованный вектор
        # Параметры дуги
        self.arc_angle = math.radians(90)  # угол дуги (90 градусов)
        self.arc_radius = int(TILE_SIZE * 2 * self.size_multiplier)
        self.arc_width = int(TILE_SIZE * 0.7 * self.size_multiplier)
        # Центр дуги = центр игрока
        px, py = player.rect.center
        # Размер изображения
        img_size = self.arc_radius * 2
        self.image = pygame.Surface((img_size, img_size), pygame.SRCALPHA)
        # Нарисовать дугу (меч) — центр surface совпадает с px, py
        dx, dy = direction
        swing_dir_angle = -math.atan2(dy, dx)
        # В pygame.draw.arc 0 — вправо, против часовой стрелки
        # Центр окружности: (img_size//2, img_size//2)
        arc_rect = (0, 0, img_size, img_size)
        start_angle = swing_dir_angle - self.arc_angle / 2
        end_angle = swing_dir_angle + self.arc_angle / 2
        pygame.draw.arc(
            self.image,
            (0, 180, 255, 180),
            arc_rect,
            start_angle,
            end_angle,
            self.arc_width
        )
        self.rect = self.image.get_rect()
        self.rect.center = (px, py)

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.spawn_time > self.duration:
            self.kill()
            return
        px, py = self.player.rect.center
        self.rect.center = (px, py)
        dx, dy = self.direction
        swing_dir_angle = -math.atan2(dy, dx)
        # Проверка попадания по дуге
        for enemy in self.game.enemies:
            if enemy not in self.hit_enemies:
                ex, ey = enemy.rect.center
                vx = ex - px
                vy = ey - py
                dist = math.hypot(vx, vy)
                if dist > self.arc_radius or dist < TILE_SIZE * 0.5:
                    continue
                angle_to_enemy = -math.atan2(vy, vx)
                delta_angle = (angle_to_enemy - swing_dir_angle + math.pi * 3) % (2 * math.pi) - math.pi
                if abs(delta_angle) > self.arc_angle / 2:
                    continue
                # Попадание!
                dmg = self.damage
                if self.critical_chance > 0 and random.random() < self.critical_chance:
                    dmg *= 2
                enemy.take_damage(dmg)
                if self.explosive:
                    for other in self.game.enemies:
                        if other is not enemy and math.hypot(other.rect.centerx-ex, other.rect.centery-ey) < self.explosion_radius:
                            other.take_damage(dmg//2)
                if self.player.knockback_attack:
                    knockback_strength = 30 * self.size_multiplier
                    enemy.x += dx * knockback_strength
                    enemy.y += dy * knockback_strength
                    enemy.rect.x = int(enemy.x)
                    enemy.rect.y = int(enemy.y)
                self.hit_enemies.add(enemy)
                if enemy.health <= 0:
                    self.player.on_kill_enemy()
                    result = self.game.upgrade_manager.on_enemy_killed()
                    if result == "spawn_boss":
                        self.game.spawn_boss()