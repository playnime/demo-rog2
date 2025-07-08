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
        
        # Base attributes
        self.max_health = PLAYER_HEALTH
        self.health = self.max_health
        self.speed = PLAYER_SPEED
        self.attack_damage = 20
        self.attack_cooldown = 500  # milliseconds
        self.attack_size_multiplier = 1.0
        
        # Special abilities
        self.vampirism = 0
        self.critical_chance = 0
        self.dodge_chance = 0
        self.explosive_attack = False
        
        # Last attack time
        self.last_attack_time = 0

    def move(self, dx=0, dy=0):
        new_x = self.x + dx * self.speed
        new_y = self.y + dy * self.speed

        # Get map size in tiles
        map_width = self.game.map.width
        map_height = self.game.map.height

        # Check boundaries (in pixels)
        min_x = 0
        min_y = 0
        max_x = (map_width - 1) * TILE_SIZE
        max_y = (map_height - 1) * TILE_SIZE

        # Clamp coordinates
        if min_x <= new_x <= max_x:
            self.x = new_x
        if min_y <= new_y <= max_y:
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
    
    def attack(self):
        """Perform attack"""
        if not self.can_attack():
            return None
        
        self.last_attack_time = pygame.time.get_ticks()
        
        # Create attack with upgrades
        attack = Attack(self.game, self)
        
        # Apply critical hit
        if random.random() < self.critical_chance:
            attack.damage *= 2
        
        # Apply attack size
        attack.size_multiplier = self.attack_size_multiplier
        
        # Apply explosive attack
        if self.explosive_attack:
            attack.explosive = True
        
        return attack