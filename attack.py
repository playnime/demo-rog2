import pygame
import math
import random
import os
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
        
        # --- Анимация атаки ---
        # Загружаем кадры анимации атаки
        self.attack_frames = [
            pygame.image.load(os.path.join("assets", "sword_effect", "attack1.png")).convert_alpha(),
            pygame.image.load(os.path.join("assets", "sword_effect", "attack2.png")).convert_alpha(),
            pygame.image.load(os.path.join("assets", "sword_effect", "attack3.png")).convert_alpha(),
        ]
        # Масштабируем кадры под размер атаки
        attack_size = int(TILE_SIZE * 1.5 * self.size_multiplier)  # уменьшили с *3 до *1.5
        self.attack_frames = [
            pygame.transform.scale(frame, (attack_size, attack_size)) for frame in self.attack_frames
        ]
        # Создаём кадры для всех 4 направлений
        self.attack_frames_right = self.attack_frames  # оригинальные кадры для атаки вправо
        self.attack_frames_left = [
            pygame.transform.flip(frame, True, False) for frame in self.attack_frames
        ]  # зеркальные для атаки влево
        self.attack_frames_down = [
            pygame.transform.rotate(frame, -90) for frame in self.attack_frames
        ]  # повёрнутые на 90° для атаки вниз
        self.attack_frames_up = [
            pygame.transform.rotate(frame, 90) for frame in self.attack_frames
        ]  # повёрнутые на -90° для атаки вверх
        
        # Переменные анимации
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 0.06  # скорость переключения кадров (60мс на кадр)
        
        # Определяем направление атаки
        dx, dy = direction
        # Определяем основное направление по наибольшей компоненте
        if abs(dx) > abs(dy):
            # Горизонтальное движение
            self.attack_direction = "right" if dx > 0 else "left"
        else:
            # Вертикальное движение
            self.attack_direction = "down" if dy > 0 else "up"
        
        # Начальный кадр
        if self.attack_direction == "right":
            self.image = self.attack_frames_right[0]
        elif self.attack_direction == "left":
            self.image = self.attack_frames_left[0]
        elif self.attack_direction == "down":
            self.image = self.attack_frames_down[0]
        else:  # up
            self.image = self.attack_frames_up[0]
        
        self.rect = self.image.get_rect()
        # Позиционируем атаку так, чтобы край был привязан к персонажу
        px, py = player.rect.center
        if self.attack_direction == "right":
            # Для атаки вправо - левый край анимации у персонажа
            self.rect.midleft = (px, py)
        elif self.attack_direction == "left":
            # Для атаки влево - правый край анимации у персонажа
            self.rect.midright = (px, py)
        elif self.attack_direction == "down":
            # Для атаки вниз - верхний край анимации у персонажа
            self.rect.midtop = (px, py)
        else:  # up
            # Для атаки вверх - нижний край анимации у персонажа
            self.rect.midbottom = (px, py)
        
        # Параметры дуги для проверки попадания (оставляем для логики)
        self.arc_angle = math.radians(90)  # угол дуги (90 градусов)
        self.arc_radius = int(TILE_SIZE * 2 * self.size_multiplier)

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.spawn_time > self.duration:
            self.kill()
            return
        
        # --- Анимация атаки ---
        dt = 1 / 60  # Предполагаем 60 FPS
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.current_frame += 1
            # Если анимация закончилась, останавливаемся на последнем кадре
            if self.current_frame >= len(self.attack_frames):
                self.current_frame = len(self.attack_frames) - 1
        
        # Обновляем кадр анимации
        if self.attack_direction == "right":
            self.image = self.attack_frames_right[self.current_frame]
        elif self.attack_direction == "left":
            self.image = self.attack_frames_left[self.current_frame]
        elif self.attack_direction == "down":
            self.image = self.attack_frames_down[self.current_frame]
        else:  # up
            self.image = self.attack_frames_up[self.current_frame]
        
        # Обновляем позицию атаки относительно игрока
        px, py = self.player.rect.center
        if self.attack_direction == "right":
            # Для атаки вправо - левый край анимации у персонажа
            self.rect.midleft = (px, py)
        elif self.attack_direction == "left":
            # Для атаки влево - правый край анимации у персонажа
            self.rect.midright = (px, py)
        elif self.attack_direction == "down":
            # Для атаки вниз - верхний край анимации у персонажа
            self.rect.midtop = (px, py)
        else:  # up
            # Для атаки вверх - нижний край анимации у персонажа
            self.rect.midbottom = (px, py)
        
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