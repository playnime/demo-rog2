import pygame
import math
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