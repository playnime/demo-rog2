import pygame
from settings import *
import random
import math

def create_enemy_image(color, size=TILE_SIZE):
    """Creates an enemy image of the given color"""
    image = pygame.Surface((size, size))
    image.fill(color)
    # Add simple details
    pygame.draw.circle(image, (255, 255, 255), (size//4, size//4), size//8)  # eye
    pygame.draw.circle(image, (255, 255, 255), (3*size//4, size//4), size//8)  # eye
    pygame.draw.rect(image, (100, 0, 0), (size//3, 2*size//3, size//3, size//6))  # mouth
    return image

def tint_image(image, color):
    """Changes the hue of the image"""
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
            # If color is provided, create image
            self.image = create_enemy_image(image_path)
        
        self.rect = self.image.get_rect()
        self.x = x * TILE_SIZE
        self.y = y * TILE_SIZE
        self.speed = speed
        self.health = health
        self.damage = damage
        self.attack_cooldown = attack_cooldown
        self.last_attack_time = 0
        # Flash effect
        self.flash_time = 0
        self.flash_duration = 100  # ms
        self.base_image = self.image.copy()

    def update(self):
        # Simple behavior: move toward player
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

        # Soft push when colliding with other enemies
        for other in self.game.enemies:
            if other is not self and self.rect.colliderect(other.rect):
                # Vector between centers
                ox, oy = other.rect.centerx, other.rect.centery
                sx, sy = self.rect.centerx, self.rect.centery
                vec_x = sx - ox
                vec_y = sy - oy
                dist = max(1, (vec_x**2 + vec_y**2)**0.5)
                # Move by a small distance (e.g., 2 pixels)
                push_strength = 2
                self.x += (vec_x / dist) * push_strength
                self.y += (vec_y / dist) * push_strength
                self.rect.x = int(self.x)
                self.rect.y = int(self.y)
                # Optionally: also move 'other' a bit for smoother effect

        # Check collision with player for damage
        if self.rect.colliderect(self.game.player.rect):
            now = pygame.time.get_ticks()
            if now - self.last_attack_time > self.attack_cooldown:
                self.game.player.take_damage(self.damage)
                self.last_attack_time = now

        # Check collision with player (don't allow passing through)
        if self.rect.colliderect(self.game.player.rect):
            self.x, self.y = old_x, old_y
            self.rect.x = int(self.x)
            self.rect.y = int(self.y)

        # Flash effect update
        if self.flash_time > 0:
            if pygame.time.get_ticks() - self.flash_time < self.flash_duration:
                self.image.fill((255, 255, 255))
            else:
                self.image = self.base_image.copy()
                self.flash_time = 0

    def take_damage(self, amount):
        self.health -= amount
        # Flash effect
        self.flash_time = pygame.time.get_ticks()
        # Damage number
        DamageNumber.spawn(self.game, self.rect.centerx, self.rect.top, amount)
        if self.health <= 0:
            self.kill()

# Enemy types
class BasicEnemy(Enemy):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, "assets/basic_gryavol.png", 1.5, 50, 10, 500, (255, 255, 255))  # Normal (white tint)

class FastEnemy(Enemy):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, "assets/basic_gryavol.png", 3.0, 30, 5, 300, (100, 255, 100))  # Green tint

class StrongEnemy(Enemy):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, "assets/basic_gryavol.png", 0.8, 100, 20, 800, (255, 100, 100))  # Red tint

class BossEnemy(Enemy):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, "assets/basic_yeti.png", 1.2, 200, 30, 1000)  # Boss (no tint)

class DamageNumber(pygame.sprite.Sprite):
    def __init__(self, game, x, y, value):
        super().__init__(game.all_sprites)
        self.game = game
        self.value = value
        self.font = pygame.font.SysFont(None, 28)
        self.image = self.font.render(str(value), True, (255, 220, 80))
        self.rect = self.image.get_rect(center=(x, y))
        # Случайное направление
        angle = random.uniform(-0.7, 0.7)
        speed = random.uniform(2, 4)
        self.vx = math.cos(angle) * speed
        self.vy = -abs(math.sin(angle)) * speed - 1  # всегда вверх
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 700  # ms
    def update(self):
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)
        # Fade out
        elapsed = pygame.time.get_ticks() - self.spawn_time
        if elapsed > self.lifetime:
            self.kill()
        else:
            alpha = max(0, 255 - int(255 * (elapsed / self.lifetime)))
            self.image.set_alpha(alpha)
    @staticmethod
    def spawn(game, x, y, value):
        dmg = DamageNumber(game, x, y, value)
        game.all_sprites.add(dmg)