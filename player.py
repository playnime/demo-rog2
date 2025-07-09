import pygame
from settings import *
import random
from attack import Attack, SwingAttack, PiercingCarrot
import os
import math

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
        self.attack_direction = "right"  # направление атаки (не меняется при движении)
        
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
        self.piercing_carrot = False  # Новое улучшение
        self.lightning = False  # Бонус молнии
        
        # --- Magic Carrots ---
        self.magic_carrots_active = False
        self.magic_carrots_timer = 0
        self.magic_carrots_cooldown = 10000  # 10 секунд
        self.magic_carrots_duration = 3000   # 3 секунды
        self.magic_carrots_last_time = 0
        self.magic_carrots_angle = 0
        self.has_magic_carrots = False
        self.magic_carrots_count = 0  # начальное количество морковок
        self.magic_carrots_image = None
        try:
            img = pygame.image.load(os.path.join("assets", "blue_carrot.png")).convert_alpha()
            self.magic_carrots_image = pygame.transform.scale(img, (img.get_width()*2, img.get_height()*2))
        except Exception:
            self.magic_carrots_image = pygame.Surface((48, 48), pygame.SRCALPHA)
            pygame.draw.ellipse(self.magic_carrots_image, (80, 180, 255), (0, 0, 48, 24))
        
        # --- Piercing Carrot ---
        self.piercing_carrot_last_time = 0
        self.piercing_carrot_cooldown = 2000  # 2 секунды
        self.piercing_carrot_count = 0  # Счетчик пронзающих морковок
        self.piercing_carrot_image = None
        
        # --- Lightning ---
        self.lightning_last_time = 0
        self.lightning_cooldown = 5000  # 5 секунд
        try:
            img = pygame.image.load(os.path.join("assets", "carrot.png")).convert_alpha()
            self.piercing_carrot_image = pygame.transform.scale(img, (img.get_width()//2, img.get_height()//2))
        except Exception:
            self.piercing_carrot_image = pygame.Surface((16, 16), pygame.SRCALPHA)
            pygame.draw.ellipse(self.piercing_carrot_image, (150, 150, 150), (0, 0, 16, 8))
        
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
        # Если игрок мёртв — ничего не делаем
        if self.health <= 0:
            if self.game.state != 'game_over':
                self.game.last_level = self.game.upgrade_manager.level
                self.game.state = 'game_over'
            return
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
            # Показываем текущий кадр атаки (используем attack_direction)
            if self.attack_direction == "right":
                self.image = self.attack_frames_right[self.attack_frame]
            else:
                self.image = self.attack_frames_left[self.attack_frame]
        else:
            # Обычная анимация ходьбы (только если не атакуем)
            self.animation_timer += dt if self.is_moving else 0
            if self.is_moving and self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.walk_right_frames)
            # Выбор кадра ходьбы (используем direction для движения)
            if self.direction == "right":
                self.image = self.walk_right_frames[self.current_frame] if self.is_moving else self.walk_right_frames[0]
            else:
                self.image = self.walk_left_frames[self.current_frame] if self.is_moving else self.walk_left_frames[0]
        # --- Magic Carrots update ---
        if self.has_magic_carrots:
            now = pygame.time.get_ticks()
            if self.magic_carrots_active:
                if now - self.magic_carrots_last_time > self.magic_carrots_duration:
                    self.magic_carrots_active = False
                    self.magic_carrots_last_time = now
            else:
                if now - self.magic_carrots_last_time > self.magic_carrots_cooldown:
                    self.magic_carrots_active = True
                    self.magic_carrots_last_time = now
            if self.magic_carrots_active:
                self.magic_carrots_angle += 0.12  # скорость вращения
                if self.magic_carrots_angle > 2 * 3.14159:
                    self.magic_carrots_angle -= 2 * 3.14159
                # --- Проверка столкновений с врагами для каждой морковки ---
                px, py = self.rect.center
                radius = 120
                for i in range(self.magic_carrots_count):
                    angle = self.magic_carrots_angle + i * (2 * math.pi / self.magic_carrots_count)
                    carrot_x = px + radius * math.cos(angle)
                    carrot_y = py + radius * math.sin(angle)
                    carrot_rect = self.magic_carrots_image.get_rect(center=(carrot_x, carrot_y))
                    for enemy in self.game.enemies:
                        if carrot_rect.colliderect(enemy.rect):
                            if not hasattr(enemy, f'carrot_last_hit_{i}') or now - getattr(enemy, f'carrot_last_hit_{i}', 0) > 300:
                                enemy.take_damage(5)
                                setattr(enemy, f'carrot_last_hit_{i}', now)
        
        # --- Piercing Carrot update ---
        if self.piercing_carrot:
            now = pygame.time.get_ticks()
            if now - self.piercing_carrot_last_time > self.piercing_carrot_cooldown:
                # Стреляем морковками в направлении курсора
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
                if length > 0:
                    direction = (dx / length, dy / length)
                    # Создаем несколько пронзающих морковок в зависимости от количества бонусов
                    for i in range(self.piercing_carrot_count):
                        # Добавляем небольшое отклонение для каждой морковки
                        angle_offset = (i - (self.piercing_carrot_count - 1) / 2) * 0.2  # 0.2 радиан = ~11 градусов
                        cos_offset = math.cos(angle_offset)
                        sin_offset = math.sin(angle_offset)
                        # Поворачиваем направление
                        rotated_dx = direction[0] * cos_offset - direction[1] * sin_offset
                        rotated_dy = direction[0] * sin_offset + direction[1] * cos_offset
                        rotated_direction = (rotated_dx, rotated_dy)
                        # Создаем пронзающую морковку
                        piercing_carrot = PiercingCarrot(self.game, self, rotated_direction)
                        self.game.all_sprites.add(piercing_carrot)
                self.piercing_carrot_last_time = now
        
        # --- Lightning update ---
        if self.lightning:
            now = pygame.time.get_ticks()
            if now - self.lightning_last_time > self.lightning_cooldown:
                # Ищем случайного врага в кадре
                visible_enemies = []
                for enemy in self.game.enemies:
                    # Проверяем, что враг видим на экране
                    enemy_screen_pos = self.game.camera.apply(enemy)
                    if (0 <= enemy_screen_pos.x <= WIDTH and 
                        0 <= enemy_screen_pos.y <= HEIGHT):
                        visible_enemies.append(enemy)
                
                if visible_enemies:
                    # Выбираем случайного врага
                    target_enemy = random.choice(visible_enemies)
                    # Создаем молнию
                    from attack import LightningAttack
                    lightning = LightningAttack(self.game, self, target_enemy)
                    self.game.all_sprites.add(lightning)
                self.lightning_last_time = now
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
            self.attack_direction = "right"
        elif direction[0] < 0:
            self.attack_direction = "left"
        # Создаём SwingAttack
        attack = SwingAttack(self.game, self, direction)
        if random.random() < self.critical_chance:
            attack.damage *= 2
        attack.size_multiplier = self.attack_size_multiplier
        if self.explosive_attack:
            attack.explosive = True
        return attack

    def draw(self, surface, camera):
        # Сначала рисуем морковки, если активны
        if self.has_magic_carrots and self.magic_carrots_active and self.magic_carrots_image:
            px, py = self.rect.center
            radius = 120
            for i in range(self.magic_carrots_count):
                angle = self.magic_carrots_angle + i * (2 * math.pi / self.magic_carrots_count)
                carrot_x = px + radius * math.cos(angle) + camera.offset.x
                carrot_y = py + radius * math.sin(angle) + camera.offset.y
                rect = self.magic_carrots_image.get_rect(center=(carrot_x, carrot_y))
                surface.blit(self.magic_carrots_image, rect)
        # Затем рисуем самого игрока
        player_rect_on_screen = camera.apply(self)
        surface.blit(self.image, player_rect_on_screen)
        # Рисуем полосу здоровья под игроком
        from utils import draw_health_bar
        bar_width = 40
        bar_height = 6
        bar_x = player_rect_on_screen.centerx - bar_width // 2
        bar_y = player_rect_on_screen.bottom + 4  # чуть ниже спрайта
        draw_health_bar(surface, bar_x, bar_y, self.health, self.max_health, width=bar_width, height=bar_height)

    def apply_upgrade(self, upgrade):
        if upgrade.effect_type == "magic_carrots":
            self.has_magic_carrots = True
            self.magic_carrots_count = min(self.magic_carrots_count + 1, 5)
        elif upgrade.effect_type == "piercing_carrot":
            self.piercing_carrot = True
            self.piercing_carrot_count = min(self.piercing_carrot_count + 1, 3)  # Максимум 3 морковки
        elif upgrade.effect_type == "lightning":
            self.lightning = True