import pygame
from settings import *
import random
from attack import Attack, SwingAttack
import os

class Player(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__()
        self.game = game
        # --- Анимация кролика ---
        # Загружаем кадры анимации ходьбы вправо
        self.walk_right_frames = [
            pygame.image.load(os.path.join("assets", "bunny", "bunny_walk1.png")).convert_alpha(),
            pygame.image.load(os.path.join("assets", "bunny", "bunny_walk2.png")).convert_alpha(),
            pygame.image.load(os.path.join("assets", "bunny", "bunny_walk3.png")).convert_alpha(),
        ]
        # Создаём зеркальные кадры для ходьбы влево
        self.walk_left_frames = [
            pygame.transform.flip(frame, True, False) for frame in self.walk_right_frames
        ]
        # Начальный кадр
        self.image = self.walk_right_frames[0]
        self.rect = self.image.get_rect()
        self.x = x * TILE_SIZE
        self.y = y * TILE_SIZE
        self.rect.x = self.x
        self.rect.y = self.y
        # Переменные анимации
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 0.12  # секунд на кадр
        self.direction = "right"  # "right" или "left"
        self.is_moving = False
        # --- Анимация атаки ---
        # Загружаем кадры анимации атаки вправо
        self.attack_frames_right = [
            pygame.image.load(os.path.join("assets", "bunny", "bunny_attack1.png")).convert_alpha(),
            pygame.image.load(os.path.join("assets", "bunny", "bunny_attack2.png")).convert_alpha(),
            pygame.image.load(os.path.join("assets", "bunny", "bunny_attack3.png")).convert_alpha(),
        ]
        # Создаём зеркальные кадры для атаки влево
        self.attack_frames_left = [
            pygame.transform.flip(frame, True, False) for frame in self.attack_frames_right
        ]
        self.is_attacking = False
        self.attack_anim_timer = 0
        self.attack_anim_speed = 0.08  # скорость переключения кадров атаки
        self.attack_frame = 0  # текущий кадр атаки
        
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
        dx, dy = 0, 0
        if keys[pygame.K_w]:
            dy = -1
        if keys[pygame.K_s]:
            dy = 1
        if keys[pygame.K_a]:
            dx = -1
        if keys[pygame.K_d]:
            dx = 1
        self.is_moving = dx != 0 or dy != 0
        # Определяем направление
        if dx > 0:
            self.direction = "right"
        elif dx < 0:
            self.direction = "left"
        # Движение
        if self.is_moving:
            self.move(dx, dy)
        # --- Анимация ---
        dt = 1 / 60  # Предполагаем 60 FPS, если dt не передаётся
        
        # Обработка анимации атаки
        if self.is_attacking:
            self.attack_anim_timer += dt
            # Переключаем кадры атаки
            if self.attack_anim_timer >= self.attack_anim_speed:
                self.attack_anim_timer = 0
                self.attack_frame += 1
                # Если анимация атаки закончилась
                if self.attack_frame >= len(self.attack_frames_right):
                    self.is_attacking = False
                    self.attack_frame = 0
            # Показываем текущий кадр атаки
            if self.direction == "right":
                self.image = self.attack_frames_right[self.attack_frame]
            else:
                self.image = self.attack_frames_left[self.attack_frame]
        else:
            # Обычная анимация ходьбы (только если не атакуем)
            self.animation_timer += dt if self.is_moving else 0
            if self.is_moving and self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.walk_right_frames)
            # Выбор кадра ходьбы
            if self.direction == "right":
                self.image = self.walk_right_frames[self.current_frame] if self.is_moving else self.walk_right_frames[0]
            else:
                self.image = self.walk_left_frames[self.current_frame] if self.is_moving else self.walk_left_frames[0]
        # Обновляем позицию rect
        self.rect.x = self.x
        self.rect.y = self.y
    
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
        # Включаем анимацию атаки
        self.is_attacking = True
        self.attack_anim_timer = 0
        self.attack_frame = 0 # Сбрасываем кадр атаки при новом ударе
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
        # Определяем направление атаки для анимации
        if direction[0] > 0:
            self.direction = "right"
        elif direction[0] < 0:
            self.direction = "left"
        # Создаём SwingAttack
        attack = SwingAttack(self.game, self, direction)
        if random.random() < self.critical_chance:
            attack.damage *= 2
        attack.size_multiplier = self.attack_size_multiplier
        if self.explosive_attack:
            attack.explosive = True
        return attack