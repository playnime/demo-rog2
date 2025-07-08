import pygame
from settings import *
import random
from attack import Attack, SwingAttack

class Player(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.x = x * TILE_SIZE
        self.y = y * TILE_SIZE
        self.rect.x = self.x
        self.rect.y = self.y
        
        # Base attributes
        self.max_health = PLAYER_HEALTH
        self.health = self.max_health
        self.speed = PLAYER_SPEED
        self.attack_damage = 20
        self.attack_cooldown = 500  # milliseconds
        self.attack_size_multiplier = 2.0  # Было 1.0, теперь радиус атаки в 2 раза больше
        
        # Special abilities
        self.vampirism = 0
        self.critical_chance = 0
        self.dodge_chance = 0
        self.explosive_attack = False
        self.knockback_attack = False
        
        # Last attack time
        self.last_attack_time = 0

    def move(self, dx=0, dy=0):
        # Новые координаты после перемещения
        new_x = self.x + dx * self.speed
        new_y = self.y + dy * self.speed

        # Получаем размеры карты
        map_width = self.game.map.width * TILE_SIZE
        map_height = self.game.map.height * TILE_SIZE

        # Ограничиваем координаты, чтобы не выйти за границы карты
        new_x = max(0, min(new_x, map_width - TILE_SIZE))
        new_y = max(0, min(new_y, map_height - TILE_SIZE))

        # Устанавливаем новые координаты
        self.x = new_x
        self.y = new_y

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
        """Take damage with dodge chance"""
        if random.random() < self.dodge_chance:
            return  # Dodge the attack
        self.health -= amount
        self.health = max(0, self.health)
    
    def heal(self, amount):
        """Restore health"""
        self.health = min(self.health + amount, self.max_health)
    
    def on_kill_enemy(self):
        """Called when an enemy is killed"""
        # Vampirism
        if self.vampirism > 0:
            self.heal(self.vampirism)
    
    def can_attack(self):
        """Check if player can attack"""
        current_time = pygame.time.get_ticks()
        return current_time - self.last_attack_time >= self.attack_cooldown
    
    def attack(self, direction=None):
        """Perform attack. Если direction не задан — вычислить по мыши."""
        if not self.can_attack():
            return None
        self.last_attack_time = pygame.time.get_ticks()
        # Если направление не задано — вычислить по мыши (в мировых координатах)
        if direction is None:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            # Получаем scale и surf_rect из main.py через game
            scale = self.game.get_scale() if self.game.fullscreen else 1.0
            screen_rect = self.game.screen.get_rect()
            surf_w, surf_h = int(WIDTH * scale), int(HEIGHT * scale)
            surf_rect = pygame.Rect(0, 0, surf_w, surf_h)
            surf_rect.center = screen_rect.center
            # Переводим координаты мыши в координаты игрового поля
            rel_x = (mouse_x - surf_rect.x) / scale
            rel_y = (mouse_y - surf_rect.y) / scale
            cam = self.game.camera
            # Переводим в мировые координаты
            world_mouse_x = rel_x - cam.offset.x
            world_mouse_y = rel_y - cam.offset.y
            px, py = self.rect.center
            dx = world_mouse_x - px
            dy = world_mouse_y - py
            length = (dx ** 2 + dy ** 2) ** 0.5
            if length == 0:
                direction = (1, 0)
            else:
                direction = (dx / length, dy / length)
        # Создаём SwingAttack
        attack = SwingAttack(self.game, self, direction)
        if random.random() < self.critical_chance:
            attack.damage *= 2
        attack.size_multiplier = self.attack_size_multiplier
        if self.explosive_attack:
            attack.explosive = True
        return attack