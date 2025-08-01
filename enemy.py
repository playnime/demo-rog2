import pygame
from settings import *
import random
import math
from experience_orb import ExperienceOrb, Carrot
import os
from sound_settings import get_volume_multiplier

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
    """Tints an image with a color"""
    tinted = image.copy()
    tinted.fill(color, special_flags=pygame.BLEND_MULT)
    return tinted

class Enemy(pygame.sprite.Sprite):
    def __init__(self, game, x, y, image_path, speed, health, damage, attack_cooldown, tint_color=None, animation_frames=None, animation_speed=200):
        super().__init__(game.all_sprites)
        self.game = game
        
        # --- Загрузка звука получения урона ---
        try:
            self.hit_sound = pygame.mixer.Sound(os.path.join("assets", "sounds", "hit_sound.wav"))
            self.hit_sound.set_volume(0.1)  # Устанавливаем громкость на 10%
        except:
            self.hit_sound = None
            print("Не удалось загрузить звук получения урона")
        
        self.animation_frames = animation_frames
        self.animation_speed = animation_speed
        self.current_frame = 0
        self.last_animation_time = pygame.time.get_ticks()
        self.facing_right = True  # Направление взгляда лисы
        
        if animation_frames:
            # Загружаем все кадры анимации
            self.frames = []
            self.frames_flipped = []  # Перевернутые кадры для движения влево
            for frame_path in animation_frames:
                frame = pygame.image.load(frame_path).convert_alpha()
                # Увеличиваем размер для лис (1.5x больше стандартного тайла)
                scaled_frame = pygame.transform.scale(frame, (int(TILE_SIZE * 1.5), int(TILE_SIZE * 1.5)))
                if tint_color:
                    scaled_frame = tint_image(scaled_frame, tint_color)
                self.frames.append(scaled_frame)
                # Создаем перевернутую версию
                flipped_frame = pygame.transform.flip(scaled_frame, True, False)
                self.frames_flipped.append(flipped_frame)
            self.image = self.frames[0]
        elif isinstance(image_path, str):
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
        self._update_base_image()

    def update(self):
        # Simple behavior: move toward player
        dx = self.game.player.x - self.x
        dy = self.game.player.y - self.y
        dist = max(1, (dx**2 + dy**2)**0.5)

        dx = dx / dist
        dy = dy / dist

        # Обновляем направление взгляда лисы
        if self.animation_frames:
            if dx > 0 and not self.facing_right:
                self.facing_right = True
            elif dx < 0 and self.facing_right:
                self.facing_right = False

        old_x, old_y = self.x, self.y
        self.x += dx * self.speed
        self.y += dy * self.speed

        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        
        # Обновление анимации
        if self.animation_frames:
            now = pygame.time.get_ticks()
            if now - self.last_animation_time > self.animation_speed:
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                # Выбираем правильное направление анимации
                if self.facing_right:
                    self.image = self.frames[self.current_frame]
                else:
                    self.image = self.frames_flipped[self.current_frame]
                self.last_animation_time = now
                # Обновляем базовое изображение для эффекта вспышки
                self._update_base_image()

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

        # Check collision with player (don't allow passing through)
        if self.rect.colliderect(self.game.player.rect):
            self.x, self.y = old_x, old_y
            self.rect.x = int(self.x)
            self.rect.y = int(self.y)
            # --- Наносим урон игроку ---
            now = pygame.time.get_ticks()
            if now - self.last_attack_time > self.attack_cooldown:
                self.game.player.take_damage(self.damage)
                self.last_attack_time = now

        # Flash effect update
        if self.flash_time > 0:
            if pygame.time.get_ticks() - self.flash_time < self.flash_duration:
                # Создаем эффект засветления
                if self.animation_frames:
                    if self.facing_right:
                        base_frame = self.frames[self.current_frame]
                    else:
                        base_frame = self.frames_flipped[self.current_frame]
                else:
                    base_frame = self.base_image
                
                # Создаем засвеченную версию, смешивая с белым
                flash_surface = base_frame.copy()
                white_overlay = pygame.Surface(flash_surface.get_size())
                white_overlay.fill((255, 255, 255))
                flash_surface.blit(white_overlay, (0, 0), special_flags=pygame.BLEND_ADD)
                self.image = flash_surface
            else:
                # Возвращаем нормальное изображение с правильным направлением
                if self.animation_frames:
                    if self.facing_right:
                        self.image = self.frames[self.current_frame]
                    else:
                        self.image = self.frames_flipped[self.current_frame]
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
        if self.hit_sound:
            # Применяем коэффициент громкости
            volume_multiplier = get_volume_multiplier()
            self.hit_sound.set_volume(0.1 * volume_multiplier)
            self.hit_sound.play()

    def _update_base_image(self):
        """Обновляет базовое изображение для эффекта вспышки"""
        if self.animation_frames:
            if self.facing_right:
                self.base_image = self.frames[self.current_frame].copy()
            else:
                self.base_image = self.frames_flipped[self.current_frame].copy()
        else:
            self.base_image = self.image.copy()

# Enemy types
class BasicEnemy(Enemy):
    def __init__(self, game, x, y):
        level = getattr(game.upgrade_manager, 'level', 1)
        # Старые статы коровы - теперь для гремлинов
        hp = 400 + int(level * 20)
        dmg = (40 + int(level * 4)) // 2  # Уменьшаем урон в 2 раза
        super().__init__(game, x, y, "assets/basic_gryavol.png", 1.8 / 2, hp, dmg, 900, (255, 255, 255))  # Уменьшаем скорость в 2 раза

    def kill(self):
        # Спавним морковки на позиции врага
        for _ in range(5):  # 5 морковок для сильных гремлинов
            offset_x = random.randint(-20, 20)
            offset_y = random.randint(-20, 20)
            carrot = Carrot(self.game, self.rect.centerx + offset_x, self.rect.centery + offset_y)
            self.game.carrots.add(carrot)
        super().kill()

class FastEnemy(Enemy):
    def __init__(self, game, x, y):
        level = getattr(game.upgrade_manager, 'level', 1)
        # Старые статы коровы - теперь для быстрых гремлинов
        hp = 400 + int(level * 20)
        dmg = (40 + int(level * 4)) // 2  # Уменьшаем урон в 2 раза
        super().__init__(game, x, y, "assets/basic_yeti.png", 2.5 / 2, hp, dmg, 900, (100, 200, 255))  # Уменьшаем скорость в 2 раза

    def kill(self):
        # Спавним морковки на позиции врага
        for _ in range(5):  # 5 морковок для сильных гремлинов
            offset_x = random.randint(-20, 20)
            offset_y = random.randint(-20, 20)
            carrot = Carrot(self.game, self.rect.centerx + offset_x, self.rect.centery + offset_y)
            self.game.carrots.add(carrot)
        super().kill()

class StrongEnemy(Enemy):
    def __init__(self, game, x, y):
        level = getattr(game.upgrade_manager, 'level', 1)
        hp = 120 + int(level * 6)
        dmg = (10 + int(level * 1.0)) // 2  # Уменьшаем урон в 2 раза
        super().__init__(game, x, y, "assets/basic_gryavol.png", 1.0 / 2, hp, dmg, 700, (255, 100, 100))  # Уменьшаем скорость в 2 раза

    def kill(self):
        # Спавним морковки на позиции врага
        for _ in range(1):  # 1 морковка для остальных врагов
            offset_x = random.randint(-10, 10)
            offset_y = random.randint(-10, 10)
            carrot = Carrot(self.game, self.rect.centerx + offset_x, self.rect.centery + offset_y)
            self.game.carrots.add(carrot)
        super().kill()

class BossEnemy(Enemy):
    def __init__(self, game, x, y):
        level = getattr(game.upgrade_manager, 'level', 1)
        hp = 500 + int(level * 30)
        dmg = (20 + int(level * 2.5)) // 2  # Уменьшаем урон в 2 раза
        super().__init__(game, x, y, "assets/basic_yeti.png", 0.7 / 2, hp, dmg, 1200, (255, 255, 0))  # Уменьшаем скорость в 2 раза

    def kill(self):
        # Спавним морковки на позиции врага
        for _ in range(1):  # 1 морковка для остальных врагов
            offset_x = random.randint(-10, 10)
            offset_y = random.randint(-10, 10)
            carrot = Carrot(self.game, self.rect.centerx + offset_x, self.rect.centery + offset_y)
            self.game.carrots.add(carrot)
        super().kill()

# Fox enemies - три версии лисы с анимацией
class FoxEnemy(Enemy):
    def __init__(self, game, x, y):
        level = getattr(game.upgrade_manager, 'level', 1)
        hp = 40 + int(level * 2.5)
        dmg = (4 + int(level * 0.4)) // 2  # Уменьшаем урон в 2 раза
        animation_frames = ["assets/fox_anim1.png", "assets/fox_anim2.png", "assets/fox_anim3.png"]
        super().__init__(game, x, y, None, 1.8 / 2, hp, dmg, 450, None, animation_frames, 300)  # Уменьшаем скорость в 2 раза

    def kill(self):
        # Спавним морковки на позиции врага
        for _ in range(1):  # 1 морковка для обычных лис
            offset_x = random.randint(-15, 15)
            offset_y = random.randint(-15, 15)
            carrot = Carrot(self.game, self.rect.centerx + offset_x, self.rect.centery + offset_y)
            self.game.carrots.add(carrot)
        super().kill()

class BlackFoxEnemy(Enemy):
    def __init__(self, game, x, y):
        level = getattr(game.upgrade_manager, 'level', 1)
        hp = 80 + int(level * 4)
        dmg = (12 + int(level * 1.2)) // 2  # Уменьшаем урон в 2 раза
        animation_frames = ["assets/fox_anim1.png", "assets/fox_anim2.png", "assets/fox_anim3.png"]
        super().__init__(game, x, y, None, 0.8 / 2, hp, dmg, 800, (50, 50, 50), animation_frames, 400)  # Уменьшаем скорость в 2 раза

    def kill(self):
        # Спавним морковки на позиции врага
        for _ in range(2):  # 2 морковки для черных животных
            offset_x = random.randint(-15, 15)
            offset_y = random.randint(-15, 15)
            carrot = Carrot(self.game, self.rect.centerx + offset_x, self.rect.centery + offset_y)
            self.game.carrots.add(carrot)
        super().kill()

class RedFoxEnemy(Enemy):
    def __init__(self, game, x, y):
        level = getattr(game.upgrade_manager, 'level', 1)
        hp = 25 + int(level * 1.5)
        dmg = (2 + int(level * 0.2)) // 2  # Уменьшаем урон в 2 раза
        animation_frames = ["assets/fox_anim1.png", "assets/fox_anim2.png", "assets/fox_anim3.png"]
        super().__init__(game, x, y, None, 3.2 / 2, hp, dmg, 300, (255, 100, 100), animation_frames, 200)  # Уменьшаем скорость в 2 раза

    def kill(self):
        # Спавним морковки на позиции врага
        for _ in range(2):  # 2 морковки для красных лис
            offset_x = random.randint(-15, 15)
            offset_y = random.randint(-15, 15)
            carrot = Carrot(self.game, self.rect.centerx + offset_x, self.rect.centery + offset_y)
            self.game.carrots.add(carrot)
        super().kill()

class BoarEnemy(Enemy):
    def __init__(self, game, x, y, color_variant=0):
        # Цветовые варианты: 0 — обычный, 1 — тёмный, 2 — красный
        level = getattr(game.upgrade_manager, 'level', 1)
        # На порядок сильнее остальных врагов
        hp = 400 + int(level * 20)
        dmg = (40 + int(level * 4)) // 2  # Уменьшаем урон в 2 раза
        speed = 1.2 / 2  # Уменьшаем скорость в 2 раза
        animation_frames = [
            "assets/boar_anim1.png",
            "assets/boar_anim2.png",
            "assets/boar_anim3.png"
        ]
        # Цвета для трёх вариантов
        tints = [None, (60, 60, 60), (200, 50, 50)]
        tint = tints[color_variant % 3]
        super().__init__(game, x, y, None, speed, hp, dmg, 900, tint, animation_frames, 250)

    def kill(self):
        # Спавним морковки на позиции врага
        for _ in range(5):  # 5 морковок для кабанов и коров
            offset_x = random.randint(-20, 20)
            offset_y = random.randint(-20, 20)
            carrot = Carrot(self.game, self.rect.centerx + offset_x, self.rect.centery + offset_y)
            self.game.carrots.add(carrot)
        super().kill()

class ChickenEnemy(Enemy):
    def __init__(self, game, x, y, color_variant=0):
        # color_variant: 0 — обычная, 1 — тёмная, 2 — красная
        level = getattr(game.upgrade_manager, 'level', 1)
        # Характеристики можно варьировать по аналогии с другими врагами
        hp_list = [35 + int(level * 2), 60 + int(level * 3.5), 20 + int(level * 1.2)]
        dmg_list = [(4 + int(level * 0.4)) // 2, (8 + int(level * 0.8)) // 2, (2 + int(level * 0.2)) // 2]  # Уменьшаем урон в 2 раза
        speed_list = [2.0 / 2, 1.2 / 2, 3.0 / 2]  # Уменьшаем скорость в 2 раза
        animation_frames = [
            "assets/chicken_anim1.png",
            "assets/chicken_anim2.png",
            "assets/chicken_anim3.png",
            "assets/chicken_anim4.png"
        ]
        # Цветовые оттенки для трёх вариантов
        tints = [None, (60, 60, 60), (200, 50, 50)]
        tint = tints[color_variant % 3]
        hp = hp_list[color_variant % 3]
        dmg = dmg_list[color_variant % 3]
        speed = speed_list[color_variant % 3]
        super().__init__(game, x, y, None, speed, hp, dmg, 500, tint, animation_frames, 220)
        self.color_variant = color_variant  # Сохраняем color_variant как атрибут

    def kill(self):
        # Спавним морковки на позиции врага
        if self.color_variant == 1:  # черная курица
            for _ in range(2):  # 2 морковки для черных животных
                offset_x = random.randint(-15, 15)
                offset_y = random.randint(-15, 15)
                carrot = Carrot(self.game, self.rect.centerx + offset_x, self.rect.centery + offset_y)
                self.game.carrots.add(carrot)
        else:  # обычная и красная курица
            for _ in range(1):  # 1 морковка для обычных и красных животных
                offset_x = random.randint(-15, 15)
                offset_y = random.randint(-15, 15)
                carrot = Carrot(self.game, self.rect.centerx + offset_x, self.rect.centery + offset_y)
                self.game.carrots.add(carrot)
        super().kill()

class CowEnemy(Enemy):
    def __init__(self, game, x, y, color_variant=0):
        # color_variant: 0 — обычная, 1 — тёмная, 2 — красная
        level = getattr(game.upgrade_manager, 'level', 1)
        # Старые статы гремлинов - теперь для коров
        hp = 50 + int(level * 3)
        dmg = (5 + int(level * 0.5)) // 2  # Уменьшаем урон в 2 раза
        speed = 1.5 / 2  # Уменьшаем скорость в 2 раза
        animation_frames = [
            "assets/cow-anim1.png",
            "assets/cow-anim2.png", 
            "assets/cow-anim3.png"
        ]
        # Цветовые оттенки для трёх вариантов
        tints = [None, (60, 60, 60), (200, 50, 50)]
        tint = tints[color_variant % 3]
        super().__init__(game, x, y, None, speed, hp, dmg, 500, tint, animation_frames, 250)

    def kill(self):
        # Спавним морковки на позиции врага
        for _ in range(1):  # 1 морковка для слабых коров
            offset_x = random.randint(-10, 10)
            offset_y = random.randint(-10, 10)
            carrot = Carrot(self.game, self.rect.centerx + offset_x, self.rect.centery + offset_y)
            self.game.carrots.add(carrot)
        super().kill()

class LamaEnemy(Enemy):
    def __init__(self, game, x, y, color_variant=0):
        # color_variant: 0 — обычная, 1 — тёмная, 2 — красная
        level = getattr(game.upgrade_manager, 'level', 1)
        # Характеристики для трёх видов ламы
        hp_list = [50 + int(level * 3), 80 + int(level * 4), 35 + int(level * 2)]
        dmg_list = [(5 + int(level * 0.5)) // 2, (8 + int(level * 0.8)) // 2, (3 + int(level * 0.3)) // 2]  # Уменьшаем урон в 2 раза
        speed_list = [1.5 / 2, 1.1 / 2, 2.2 / 2]  # Уменьшаем скорость в 2 раза
        animation_frames = [
            "assets/lama_anim1.png",
            "assets/lama_anim2.png",
            "assets/lama_anim3.png",
            "assets/lama_anim4.png"
        ]
        # Цветовые оттенки для трёх вариантов
        tints = [None, (60, 60, 60), (200, 50, 50)]
        tint = tints[color_variant % 3]
        hp = hp_list[color_variant % 3]
        dmg = dmg_list[color_variant % 3]
        speed = speed_list[color_variant % 3]
        super().__init__(game, x, y, None, speed, hp, dmg, 500, tint, animation_frames, 220)
        self.color_variant = color_variant  # Сохраняем color_variant как атрибут

    def kill(self):
        # Спавним морковки на позиции врага
        if self.color_variant == 1:  # черная лама
            for _ in range(2):  # 2 морковки для черных животных
                offset_x = random.randint(-15, 15)
                offset_y = random.randint(-15, 15)
                carrot = Carrot(self.game, self.rect.centerx + offset_x, self.rect.centery + offset_y)
                self.game.carrots.add(carrot)
        else:  # обычная и красная лама
            for _ in range(1):  # 1 морковка для обычных и красных животных
                offset_x = random.randint(-15, 15)
                offset_y = random.randint(-15, 15)
                carrot = Carrot(self.game, self.rect.centerx + offset_x, self.rect.centery + offset_y)
                self.game.carrots.add(carrot)
        super().kill()

class PigEnemy(Enemy):
    def __init__(self, game, x, y):
        # Характеристики как у FastEnemy (yeti)
        level = getattr(game.upgrade_manager, 'level', 1)
        hp = 30 + int(level * 2)
        dmg = (3 + int(level * 0.3)) // 2  # Уменьшаем урон в 2 раза
        speed = 2.5 / 2  # Уменьшаем скорость в 2 раза
        animation_frames = [
            "assets/pig_anim1.png",
            "assets/pig_anim2.png",
            "assets/pig_anim3.png",
            "assets/pig_anim4.png"
        ]
        super().__init__(game, x, y, None, speed, hp, dmg, 400, None, animation_frames, 220)
        # Делаем свинью шире
        self.image = pygame.transform.scale(self.image, (int(TILE_SIZE * 1.6), int(TILE_SIZE * 1.6)))
        self.rect = self.image.get_rect()
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def kill(self):
        # Спавним морковки на позиции врага
        for _ in range(1):  # 1 морковка для остальных врагов
            offset_x = random.randint(-10, 10)
            offset_y = random.randint(-10, 10)
            carrot = Carrot(self.game, self.rect.centerx + offset_x, self.rect.centery + offset_y)
            self.game.carrots.add(carrot)
        super().kill()

class SheepEnemy(Enemy):
    def __init__(self, game, x, y):
        # Овца: быстрая, наносит много урона, но умирает с одного удара
        level = getattr(game.upgrade_manager, 'level', 1)
        hp = 1  # Умирает с одного удара
        dmg = (15 + int(level * 1.5)) // 2  # Уменьшаем урон в 2 раза
        # Анимация овцы
        animation_frames = [
            "assets/sheep-anim1.png",
            "assets/sheep-anim2.png", 
            "assets/sheep-anim3.png",
            "assets/sheep-anim4.png"
        ]
        super().__init__(game, x, y, None, 3.5 / 2, hp, dmg, 300, (255, 255, 255), animation_frames, 150)  # Уменьшаем скорость в 2 раза

    def kill(self):
        # Спавним морковки на позиции врага
        for _ in range(1):  # 1 морковка для остальных врагов
            offset_x = random.randint(-10, 10)
            offset_y = random.randint(-10, 10)
            carrot = Carrot(self.game, self.rect.centerx + offset_x, self.rect.centery + offset_y)
            self.game.carrots.add(carrot)
        super().kill()

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