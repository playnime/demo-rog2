import pygame
from settings import *
import random
from attack import Attack

class Player(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__(game.all_sprites)
        self.game = game
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.x = x * TILE_SIZE
        self.y = y * TILE_SIZE
        self.rect.x = self.x
        self.rect.y = self.y
        
        # Базовые характеристики
        self.max_health = PLAYER_HEALTH
        self.health = self.max_health
        self.speed = PLAYER_SPEED
        self.attack_damage = 20
        self.attack_cooldown = 500  # миллисекунды
        self.attack_size_multiplier = 1.0
        
        # Специальные способности
        self.vampirism = 0
        self.critical_chance = 0
        self.dodge_chance = 0
        self.explosive_attack = False
        
        # Время последней атаки
        self.last_attack_time = 0

    def move(self, dx=0, dy=0):
        self.x += dx * self.speed
        self.y += dy * self.speed
        self.rect.x = self.x
        self.rect.y = self.y

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.move(dy=-1)
        if keys[pygame.K_s]:
            self.move(dy=1)
        if keys[pygame.K_a]:
            self.move(dx=-1)
        if keys[pygame.K_d]:
            self.move(dx=1)
    
    def take_damage(self, amount):
        """Получение урона с учетом уклонения"""
        if random.random() < self.dodge_chance:
            return  # Уклонение от атаки
        self.health -= amount
        self.health = max(0, self.health)
    
    def heal(self, amount):
        """Восстановление здоровья"""
        self.health = min(self.health + amount, self.max_health)
    
    def on_kill_enemy(self):
        """Вызывается при убийстве врага"""
        # Вампиризм
        if self.vampirism > 0:
            self.heal(self.vampirism)
    
    def can_attack(self):
        """Проверяет, может ли игрок атаковать"""
        current_time = pygame.time.get_ticks()
        return current_time - self.last_attack_time >= self.attack_cooldown
    
    def attack(self):
        """Выполняет атаку"""
        if not self.can_attack():
            return None
        
        self.last_attack_time = pygame.time.get_ticks()
        
        # Создаем атаку с учетом улучшений
        attack = Attack(self.game, self)
        
        # Применяем критический удар
        if random.random() < self.critical_chance:
            attack.damage *= 2
        
        # Применяем размер атаки
        attack.size_multiplier = self.attack_size_multiplier
        
        # Применяем взрывную атаку
        if self.explosive_attack:
            attack.explosive = True
        
        return attack