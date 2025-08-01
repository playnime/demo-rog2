import pygame
import os
from settings import *
from sound_settings import get_volume_multiplier

class ExperienceOrb(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__()
        self.game = game
        self.image = pygame.image.load(os.path.join("assets", "carrot.png")).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.lifetime = 10000  # 10 seconds
        self.spawn_time = pygame.time.get_ticks()

    def update(self):
        # Remove after lifetime
        if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
            self.kill()
            return
        
        # Check collision with player
        if self.rect.colliderect(self.game.player.rect):
            self.game.upgrade_manager.on_experience_orb_collected()
            self.kill()

class Carrot(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__()
        self.game = game
        
        # --- Загрузка звука получения опыта ---
        try:
            self.exp_sound = pygame.mixer.Sound(os.path.join("assets", "sounds", "exp_sound.wav"))
            self.exp_sound.set_volume(0.3)  # Устанавливаем громкость на 30%
        except:
            self.exp_sound = None
            print("Не удалось загрузить звук получения опыта")
        
        self.image = pygame.image.load(os.path.join("assets", "carrot.png")).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        # Убираем ограничение времени жизни для морковок
        # self.lifetime = 10000  # 10 seconds
        # self.spawn_time = pygame.time.get_ticks()

    def update(self):
        # Убираем проверку времени жизни - морковки не исчезают автоматически
        # if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
        #     self.kill()
        #     return
        
        # Check collision with player
        if self.rect.colliderect(self.game.player.rect):
            if self.exp_sound:
                # Применяем коэффициент громкости
                volume_multiplier = get_volume_multiplier()
                self.exp_sound.set_volume(0.3 * volume_multiplier)
                self.exp_sound.play()
            self.game.upgrade_manager.on_experience_orb_collected()
            self.kill() 