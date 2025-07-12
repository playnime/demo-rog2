import pygame
import sys
import random
import math
from settings import *
from player import Player
from enemy import BasicEnemy, FastEnemy, StrongEnemy, BossEnemy, FoxEnemy, BlackFoxEnemy, RedFoxEnemy, BoarEnemy, ChickenEnemy, CowEnemy, LamaEnemy, PigEnemy, SheepEnemy
from map import Map
from camera import Camera
from attack import Attack, PiercingCarrot, LightningAttack
from utils import draw_health_bar
from upgrade_system import UpgradeManager
from experience_orb import ExperienceOrb, Carrot
from sound_settings import apply_volume_to_sounds, get_effects_volume, get_volume_multiplier

pygame.init()
pygame.mixer.init()  # Инициализация звуковой системы
screen = pygame.display.set_mode((WIDTH, HEIGHT))
fullscreen = False
# Surface for the game field
GAME_SIZE = (WIDTH, HEIGHT)
game_surface = pygame.Surface(GAME_SIZE)
font_fps = pygame.font.SysFont(None, 24)

# Загрузка изображений меню
try:
    menu_background = pygame.image.load("assets/menu/menu_background.jpg").convert()
    menu_title = pygame.image.load("assets/menu/menu_game_title.png").convert_alpha()
    menu_start_btn = pygame.image.load("assets/menu/menu_start.png").convert_alpha()
    menu_settings_btn = pygame.image.load("assets/menu/menu_settings.png").convert_alpha()
    menu_leave_btn = pygame.image.load("assets/menu/menu_leave.png").convert_alpha()
    menu_back_btn = pygame.image.load("assets/menu/button_back.png").convert_alpha()
except pygame.error as e:
    print(f"Ошибка загрузки изображений меню: {e}")
    # Создаём заглушки если изображения не найдены
    menu_background = pygame.Surface((WIDTH, HEIGHT))
    menu_background.fill((50, 50, 100))
    menu_title = pygame.Surface((300, 100))
    menu_title.fill((255, 255, 255))
    menu_start_btn = pygame.Surface((200, 60))
    menu_start_btn.fill((0, 255, 0))
    menu_settings_btn = pygame.Surface((200, 60))
    menu_settings_btn.fill((255, 255, 0))
    menu_leave_btn = pygame.Surface((200, 60))
    menu_leave_btn.fill((255, 0, 0))
    menu_back_btn = pygame.Surface((200, 60))
    menu_back_btn.fill((100, 100, 100))

# Загрузка звука наведения на кнопки меню
try:
    menu_hover_sound = pygame.mixer.Sound("assets/sounds/menu_hover_sound.wav")
    menu_hover_sound.set_volume(0.3)
except pygame.error as e:
    print(f"Ошибка загрузки звука наведения меню: {e}")
    menu_hover_sound = None

# Масштабирование изображений под размер экрана
def scale_menu_images():
    global menu_background, menu_title, menu_start_btn, menu_settings_btn, menu_leave_btn, menu_back_btn
    # Масштабируем фоновое изображение
    menu_background = pygame.transform.scale(menu_background, (WIDTH, HEIGHT))
    # Масштабируем заголовок (примерно 1/3 ширины экрана)
    title_width = WIDTH // 3
    title_height = int(title_width * menu_title.get_height() / menu_title.get_width())
    menu_title = pygame.transform.scale(menu_title, (title_width, title_height))
    # Масштабируем кнопки (примерно 1/4 ширины экрана)
    btn_width = WIDTH // 4
    btn_height = int(btn_width * menu_start_btn.get_height() / menu_start_btn.get_width())
    menu_start_btn = pygame.transform.scale(menu_start_btn, (btn_width, btn_height))
    menu_settings_btn = pygame.transform.scale(menu_settings_btn, (btn_width, btn_height))
    menu_leave_btn = pygame.transform.scale(menu_leave_btn, (btn_width, btn_height))
    menu_back_btn = pygame.transform.scale(menu_back_btn, (btn_width, btn_height))

scale_menu_images()

class MenuManager:
    def __init__(self):
        self.state = 'main'  # 'main', 'settings'
        self.effects_volume_percent = 70  # Громкость эффектов в процентах (0-100)
        self.slider_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 20)
        # Инициализируем ручку слайдера в правильной позиции
        self.update_slider_handle_position()
        self.dragging_slider = False
        
        # Отслеживание наведения мыши на кнопки
        self.last_hovered_button = None
        self.hovered_button = None  # Текущая кнопка под курсором
        self.back_button_hovered = False  # Для кнопки "Назад" в настройках
    
    def update_slider_handle_position(self):
        """Обновляет позицию ручки слайдера в соответствии с текущей громкостью"""
        handle_x = self.slider_rect.left + int((self.effects_volume_percent / 100.0) * self.slider_rect.width)
        self.slider_handle_rect = pygame.Rect(handle_x - 5, self.slider_rect.centery - 15, 10, 30)
    
    def update_volume_from_mouse_pos(self, mouse_x):
        """Обновляет громкость на основе позиции мыши"""
        # Ограничиваем позицию мыши границами слайдера
        slider_x = max(self.slider_rect.left, min(self.slider_rect.right, mouse_x))
        # Вычисляем громкость в процентах (0-100)
        volume_percent = (slider_x - self.slider_rect.left) / self.slider_rect.width * 100
        self.effects_volume_percent = max(0, min(100, int(volume_percent)))
        # Обновляем позицию ручки
        self.update_slider_handle_position()
        # Применяем новую громкость
        apply_volume_to_sounds(self.effects_volume_percent)
        
    def handle_click(self, pos):
        # Преобразуем координаты мыши для полноэкранного режима
        adjusted_pos = self.adjust_mouse_pos(pos)
        
        if self.state == 'main':
            # Проверяем клики по кнопкам
            title_y = HEIGHT // 2 - 200  # Обновлено под новую позицию заголовка
            btn_y = HEIGHT // 2 + 40  # Обновлено под новую позицию кнопок
            btn_spacing = 140  # Обновлено под новое расстояние
            
            # Кнопка Start
            start_scale = 0.9 if self.hovered_button == 'start' else 1.0
            start_width = int(menu_start_btn.get_width() * start_scale)
            start_height = int(menu_start_btn.get_height() * start_scale)
            start_rect = pygame.Rect(WIDTH // 2 - start_width // 2, btn_y - start_height // 2, start_width, start_height)
            if start_rect.collidepoint(adjusted_pos):
                return 'start_game'
            
            # Кнопка Settings
            settings_scale = 0.9 if self.hovered_button == 'settings' else 1.0
            settings_width = int(menu_settings_btn.get_width() * settings_scale)
            settings_height = int(menu_settings_btn.get_height() * settings_scale)
            settings_rect = pygame.Rect(WIDTH // 2 - settings_width // 2, btn_y + btn_spacing - settings_height // 2, settings_width, settings_height)
            if settings_rect.collidepoint(adjusted_pos):
                self.state = 'settings'
                return None
            
            # Кнопка Leave (оставляем на прежнем месте)
            leave_scale = 0.9 if self.hovered_button == 'leave' else 1.0
            leave_width = int(menu_leave_btn.get_width() * leave_scale)
            leave_height = int(menu_leave_btn.get_height() * leave_scale)
            leave_rect = pygame.Rect(WIDTH // 2 - leave_width // 2, HEIGHT // 2 + 320 - leave_height // 2, leave_width, leave_height)
            if leave_rect.collidepoint(adjusted_pos):
                return 'quit_game'
                
        elif self.state == 'settings':
            # Проверяем клик по слайдеру (по ручке или по самому слайдеру)
            if self.slider_handle_rect.collidepoint(adjusted_pos) or self.slider_rect.collidepoint(adjusted_pos):
                self.dragging_slider = True
                # Если кликнули по слайдеру, а не по ручке, сразу обновляем позицию
                if not self.slider_handle_rect.collidepoint(adjusted_pos):
                    self.update_volume_from_mouse_pos(adjusted_pos[0])
            # Кнопка "Назад" (используем изображение)
            back_scale = 0.9 if self.back_button_hovered else 1.0
            back_width = int(menu_back_btn.get_width() * back_scale)
            back_height = int(menu_back_btn.get_height() * back_scale)
            back_rect = pygame.Rect(WIDTH // 2 - back_width // 2, HEIGHT // 2 + 200 - back_height // 2, back_width, back_height)
            if back_rect.collidepoint(adjusted_pos):
                self.state = 'main'
                return None
                
        return None
    
    def adjust_mouse_pos(self, pos):
        """Преобразует координаты мыши для полноэкранного режима"""
        # Получаем размеры экрана и масштаб
        screen_w, screen_h = pygame.display.get_surface().get_size()
        scale_w = screen_w / WIDTH
        scale_h = screen_h / HEIGHT
        scale = min(scale_w, scale_h)
        
        # Вычисляем отступы для центрирования
        scaled_w = int(WIDTH * scale)
        scaled_h = int(HEIGHT * scale)
        offset_x = (screen_w - scaled_w) // 2
        offset_y = (screen_h - scaled_h) // 2
        
        # Преобразуем координаты мыши
        adjusted_x = (pos[0] - offset_x) / scale
        adjusted_y = (pos[1] - offset_y) / scale
        
        return (adjusted_x, adjusted_y)
    
    def check_button_hover(self, pos):
        """Проверяет наведение мыши на кнопки и воспроизводит звук"""
        if self.state != 'main':
            return
            
        adjusted_pos = self.adjust_mouse_pos(pos)
        current_hovered = None
        
        # Проверяем наведение на кнопки (используем актуальные размеры)
        btn_y = HEIGHT // 2 + 40
        btn_spacing = 140
        
        # Кнопка Start
        start_scale = 0.9 if self.hovered_button == 'start' else 1.0
        start_width = int(menu_start_btn.get_width() * start_scale)
        start_height = int(menu_start_btn.get_height() * start_scale)
        start_rect = pygame.Rect(WIDTH // 2 - start_width // 2, btn_y - start_height // 2, start_width, start_height)
        if start_rect.collidepoint(adjusted_pos):
            current_hovered = 'start'
        
        # Кнопка Settings
        settings_scale = 0.9 if self.hovered_button == 'settings' else 1.0
        settings_width = int(menu_settings_btn.get_width() * settings_scale)
        settings_height = int(menu_settings_btn.get_height() * settings_scale)
        settings_rect = pygame.Rect(WIDTH // 2 - settings_width // 2, btn_y + btn_spacing - settings_height // 2, settings_width, settings_height)
        if settings_rect.collidepoint(adjusted_pos):
            current_hovered = 'settings'
        
        # Кнопка Leave
        leave_scale = 0.9 if self.hovered_button == 'leave' else 1.0
        leave_width = int(menu_leave_btn.get_width() * leave_scale)
        leave_height = int(menu_leave_btn.get_height() * leave_scale)
        leave_rect = pygame.Rect(WIDTH // 2 - leave_width // 2, HEIGHT // 2 + 320 - leave_height // 2, leave_width, leave_height)
        if leave_rect.collidepoint(adjusted_pos):
            current_hovered = 'leave'
        
        # Воспроизводим звук при наведении на новую кнопку
        if current_hovered != self.last_hovered_button and current_hovered is not None:
            if menu_hover_sound:
                # Применяем коэффициент громкости
                volume_multiplier = get_volume_multiplier()
                menu_hover_sound.set_volume(0.3 * volume_multiplier)
                menu_hover_sound.play()
        
        self.last_hovered_button = current_hovered
        self.hovered_button = current_hovered
    
    def handle_mouse_motion(self, pos):
        # Проверяем наведение на кнопки
        self.check_button_hover(pos)
        
        if self.state == 'settings':
            adjusted_pos = self.adjust_mouse_pos(pos)
            
            # Проверяем наведение на кнопку "Назад"
            back_scale = 0.9 if self.back_button_hovered else 1.0
            back_width = int(menu_back_btn.get_width() * back_scale)
            back_height = int(menu_back_btn.get_height() * back_scale)
            back_rect = pygame.Rect(WIDTH // 2 - back_width // 2, HEIGHT // 2 + 200 - back_height // 2, back_width, back_height)
            
            new_back_hovered = back_rect.collidepoint(adjusted_pos)
            if new_back_hovered != self.back_button_hovered:
                self.back_button_hovered = new_back_hovered
                if new_back_hovered and menu_hover_sound:
                    # Применяем коэффициент громкости
                    volume_multiplier = get_volume_multiplier()
                    menu_hover_sound.set_volume(0.3 * volume_multiplier)
                    menu_hover_sound.play()
            
            if self.dragging_slider:
                # Обновляем громкость на основе позиции мыши
                self.update_volume_from_mouse_pos(adjusted_pos[0])
    
    def handle_mouse_up(self):
        self.dragging_slider = False
    
    def draw(self, surface):
        if self.state == 'main':
            self.draw_main_menu(surface)
        elif self.state == 'settings':
            self.draw_settings_menu(surface)
    
    def draw_main_menu(self, surface):
        # Фоновое изображение
        surface.blit(menu_background, (0, 0))
        
        # Заголовок игры (подняли выше)
        title_rect = menu_title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 200))
        surface.blit(menu_title, title_rect)
        
        # Кнопки (сделали более обособленными)
        btn_y = HEIGHT // 2 + 40  # Подняли кнопки выше
        btn_spacing = 140  # Увеличили расстояние между кнопками
        
        # Кнопка Start
        start_scale = 0.9 if self.hovered_button == 'start' else 1.0
        start_scaled = pygame.transform.scale(menu_start_btn, 
            (int(menu_start_btn.get_width() * start_scale), 
             int(menu_start_btn.get_height() * start_scale)))
        start_rect = start_scaled.get_rect(center=(WIDTH // 2, btn_y))
        surface.blit(start_scaled, start_rect)
        
        # Кнопка Settings
        settings_scale = 0.9 if self.hovered_button == 'settings' else 1.0
        settings_scaled = pygame.transform.scale(menu_settings_btn, 
            (int(menu_settings_btn.get_width() * settings_scale), 
             int(menu_settings_btn.get_height() * settings_scale)))
        settings_rect = settings_scaled.get_rect(center=(WIDTH // 2, btn_y + btn_spacing))
        surface.blit(settings_scaled, settings_rect)
        
        # Кнопка Leave (оставляем на прежнем месте)
        leave_scale = 0.9 if self.hovered_button == 'leave' else 1.0
        leave_scaled = pygame.transform.scale(menu_leave_btn, 
            (int(menu_leave_btn.get_width() * leave_scale), 
             int(menu_leave_btn.get_height() * leave_scale)))
        leave_rect = leave_scaled.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 320))
        surface.blit(leave_scaled, leave_rect)
    
    def draw_settings_menu(self, surface):
        # Сначала рисуем тот же фон, что и в главном меню
        surface.blit(menu_background, (0, 0))
        # Полупрозрачный фон
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        
        # Заголовок настроек
        font = pygame.font.SysFont(None, 60)
        title = font.render('НАСТРОЙКИ', True, (255, 255, 255))
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
        surface.blit(title, title_rect)
        
        # Громкость эффектов
        font_small = pygame.font.SysFont(None, 36)
        volume_text = font_small.render('Громкость эффектов:', True, (255, 255, 255))
        volume_rect = volume_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        surface.blit(volume_text, volume_rect)
        
        # Слайдер
        # Фон слайдера
        pygame.draw.rect(surface, (80, 80, 80), self.slider_rect)
        pygame.draw.rect(surface, (120, 120, 120), self.slider_rect, 2)
        
        # Заполненная часть слайдера (показывает текущую громкость)
        filled_width = int((self.effects_volume_percent / 100.0) * self.slider_rect.width)
        filled_rect = pygame.Rect(self.slider_rect.left, self.slider_rect.top, filled_width, self.slider_rect.height)
        pygame.draw.rect(surface, (0, 150, 255), filled_rect)
        
        # Ручка слайдера
        pygame.draw.rect(surface, (255, 255, 255), self.slider_handle_rect)
        pygame.draw.rect(surface, (200, 200, 200), self.slider_handle_rect, 2)
        
        # Значение громкости
        volume_value = font_small.render(f'{self.effects_volume_percent}%', True, (255, 255, 255))
        value_rect = volume_value.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80))
        surface.blit(volume_value, value_rect)
        
        # Кнопка "Назад" (используем изображение)
        back_scale = 0.9 if self.back_button_hovered else 1.0
        back_scaled = pygame.transform.scale(menu_back_btn, 
            (int(menu_back_btn.get_width() * back_scale), 
             int(menu_back_btn.get_height() * back_scale)))
        back_rect = back_scaled.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 200))
        surface.blit(back_scaled, back_rect)

def toggle_fullscreen():
    global screen, fullscreen
    fullscreen = not fullscreen
    if fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode(GAME_SIZE)

clock = pygame.time.Clock()

class Game:
    def __init__(self):
        self.state = 'menu'  # 'menu', 'playing', 'paused', 'game_over'
        self.menu_manager = MenuManager()  # Новый менеджер меню
        self.upgrade_manager = UpgradeManager()
        self.fullscreen = fullscreen
        self.screen = screen
        self.reset_game()
        self.last_spawn_time = pygame.time.get_ticks()
        self.spawn_interval = 2000  # 2 seconds in milliseconds (раньше было 5000)
        self.spawn_distance = 200  # Distance from player for spawning
        self.notification_text = ""
        self.notification_time = 0
        self.notification_duration = 3000  # 3 seconds
        self.last_level = 1  # Для экрана Game Over

    def reset_game(self):
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.experience_orbs = pygame.sprite.Group()  # Новая группа для сфер опыта
        self.carrots = pygame.sprite.Group()  # Группа для морковок
        # Load map from Lua file
        self.map = Map(self, lua_map_path="assets/map/final_map.lua")
        map_width = self.map.width
        map_height = self.map.height
        # Center of the map
        player_x = map_width // 2
        player_y = map_height // 2
        self.player = Player(self, player_x, player_y)
        self.all_sprites.add(self.player)
        self.camera = Camera(WIDTH, HEIGHT)
        # Убираем создание гремлина при инициализации - враги будут спавниться только через spawn_enemy()
        self.last_spawn_time = pygame.time.get_ticks()
        self.camera.update(self.player)
        # Reset upgrade system
        self.upgrade_manager = UpgradeManager()

    def spawn_enemy(self):
        # Получаем границы камеры в тайлах
        cam_left = -self.camera.offset.x // TILE_SIZE
        cam_top = -self.camera.offset.y // TILE_SIZE
        cam_right = cam_left + WIDTH // TILE_SIZE
        cam_bottom = cam_top + HEIGHT // TILE_SIZE
        # Задаём минимальное и максимальное расстояние от игрока
        min_dist = max(WIDTH, HEIGHT) // TILE_SIZE // 2 + 1  # чуть за экраном
        max_dist = min(6, max(self.map.width, self.map.height) // 2)  # не дальше 6 тайлов
        for _ in range(20):  # 20 попыток найти подходящее место
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(min_dist, max_dist)
            spawn_x = int(self.player.x // TILE_SIZE + distance * math.cos(angle))
            spawn_y = int(self.player.y // TILE_SIZE + distance * math.sin(angle))
            # Проверяем, что враг вне камеры, но в пределах карты
            if (spawn_x < cam_left or spawn_x > cam_right or spawn_y < cam_top or spawn_y > cam_bottom) and \
               0 <= spawn_x < self.map.width and 0 <= spawn_y < self.map.height:
                break
        else:
            # Если не нашли — спавним как раньше
            spawn_x = self.player.x // TILE_SIZE + random.randint(-max_dist, max_dist)
            spawn_y = self.player.y // TILE_SIZE + random.randint(-max_dist, max_dist)
            spawn_x = max(0, min(self.map.width - 1, spawn_x))
            spawn_y = max(0, min(self.map.height - 1, spawn_y))
        # Выбираем тип врага в зависимости от уровня
        level = self.upgrade_manager.level
        if level == 1:
            enemy_types = [lambda g, x, y: CowEnemy(g, x, y, 0)]  # Коровы в начале
        elif level == 2:
            enemy_types = [lambda g, x, y: CowEnemy(g, x, y, 0), lambda g, x, y: CowEnemy(g, x, y, 1)]
        elif level == 3 or level == 4:
            enemy_types = [lambda g, x, y: CowEnemy(g, x, y, 0), lambda g, x, y: CowEnemy(g, x, y, 1), lambda g, x, y: CowEnemy(g, x, y, 2), FoxEnemy, SheepEnemy]
        elif level == 5:
            enemy_types = [lambda g, x, y: CowEnemy(g, x, y, 0), lambda g, x, y: CowEnemy(g, x, y, 1), lambda g, x, y: CowEnemy(g, x, y, 2), FoxEnemy, SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy]
        elif level == 6:
            enemy_types = [lambda g, x, y: CowEnemy(g, x, y, 0), lambda g, x, y: CowEnemy(g, x, y, 1), lambda g, x, y: CowEnemy(g, x, y, 2), FoxEnemy, SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy, RedFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 2)]
        elif level == 7:
            enemy_types = [lambda g, x, y: CowEnemy(g, x, y, 0), lambda g, x, y: CowEnemy(g, x, y, 1), lambda g, x, y: CowEnemy(g, x, y, 2), FoxEnemy, SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy, RedFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 2), BlackFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 1), lambda g, x, y: LamaEnemy(g, x, y, 0)]
        elif level == 8:
            enemy_types = [lambda g, x, y: CowEnemy(g, x, y, 0), lambda g, x, y: CowEnemy(g, x, y, 1), lambda g, x, y: CowEnemy(g, x, y, 2), FoxEnemy, SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy, RedFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 2), BlackFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 1), lambda g, x, y: LamaEnemy(g, x, y, 0), lambda g, x, y: LamaEnemy(g, x, y, 2)]
        elif level == 9:
            enemy_types = [lambda g, x, y: CowEnemy(g, x, y, 0), lambda g, x, y: CowEnemy(g, x, y, 1), lambda g, x, y: CowEnemy(g, x, y, 2), FoxEnemy, SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy, RedFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 2), BlackFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 1), lambda g, x, y: LamaEnemy(g, x, y, 0), lambda g, x, y: LamaEnemy(g, x, y, 2), lambda g, x, y: LamaEnemy(g, x, y, 1)]
        elif level == 10:
            enemy_types = [lambda g, x, y: CowEnemy(g, x, y, 0), lambda g, x, y: CowEnemy(g, x, y, 1), lambda g, x, y: CowEnemy(g, x, y, 2), FoxEnemy, SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy, RedFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 2), BlackFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 1), lambda g, x, y: LamaEnemy(g, x, y, 0), lambda g, x, y: LamaEnemy(g, x, y, 2), lambda g, x, y: LamaEnemy(g, x, y, 1)]
        elif level == 11:
            enemy_types = [lambda g, x, y: CowEnemy(g, x, y, 0), lambda g, x, y: CowEnemy(g, x, y, 1), lambda g, x, y: CowEnemy(g, x, y, 2), FoxEnemy, SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy, RedFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 2), BlackFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 1), lambda g, x, y: LamaEnemy(g, x, y, 0), lambda g, x, y: LamaEnemy(g, x, y, 2), lambda g, x, y: LamaEnemy(g, x, y, 1), lambda g, x, y: BoarEnemy(g, x, y, 0)]
        elif level == 12:
            enemy_types = [lambda g, x, y: CowEnemy(g, x, y, 0), lambda g, x, y: CowEnemy(g, x, y, 1), lambda g, x, y: CowEnemy(g, x, y, 2), FoxEnemy, SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy, RedFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 2), BlackFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 1), lambda g, x, y: LamaEnemy(g, x, y, 0), lambda g, x, y: LamaEnemy(g, x, y, 2), lambda g, x, y: LamaEnemy(g, x, y, 1), lambda g, x, y: BoarEnemy(g, x, y, 0)]
        elif level == 13:
            enemy_types = [lambda g, x, y: CowEnemy(g, x, y, 0), lambda g, x, y: CowEnemy(g, x, y, 1), lambda g, x, y: CowEnemy(g, x, y, 2), FoxEnemy, SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy, RedFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 2), BlackFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 1), lambda g, x, y: LamaEnemy(g, x, y, 0), lambda g, x, y: LamaEnemy(g, x, y, 2), lambda g, x, y: LamaEnemy(g, x, y, 1), lambda g, x, y: BoarEnemy(g, x, y, 0), lambda g, x, y: BoarEnemy(g, x, y, 1), lambda g, x, y: BoarEnemy(g, x, y, 2)]
        elif level == 14:
            enemy_types = [lambda g, x, y: CowEnemy(g, x, y, 0), lambda g, x, y: CowEnemy(g, x, y, 1), lambda g, x, y: CowEnemy(g, x, y, 2), SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy, RedFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 2), BlackFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 1), lambda g, x, y: LamaEnemy(g, x, y, 0), lambda g, x, y: LamaEnemy(g, x, y, 2), lambda g, x, y: LamaEnemy(g, x, y, 1), lambda g, x, y: BoarEnemy(g, x, y, 0), lambda g, x, y: BoarEnemy(g, x, y, 1), lambda g, x, y: BoarEnemy(g, x, y, 2)]
        elif level == 15:
            enemy_types = [lambda g, x, y: CowEnemy(g, x, y, 0), lambda g, x, y: CowEnemy(g, x, y, 1), lambda g, x, y: CowEnemy(g, x, y, 2), SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy, RedFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 2), BlackFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 1), lambda g, x, y: LamaEnemy(g, x, y, 0), lambda g, x, y: LamaEnemy(g, x, y, 2), lambda g, x, y: LamaEnemy(g, x, y, 1), lambda g, x, y: BoarEnemy(g, x, y, 0), lambda g, x, y: BoarEnemy(g, x, y, 1), lambda g, x, y: BoarEnemy(g, x, y, 2)]
        elif level == 16:
            # Начинаем добавлять сильных гремлинов
            enemy_types = [BasicEnemy, FastEnemy, SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy, RedFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 2), BlackFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 1), lambda g, x, y: LamaEnemy(g, x, y, 0), lambda g, x, y: LamaEnemy(g, x, y, 2), lambda g, x, y: LamaEnemy(g, x, y, 1), lambda g, x, y: BoarEnemy(g, x, y, 0), lambda g, x, y: BoarEnemy(g, x, y, 1), lambda g, x, y: BoarEnemy(g, x, y, 2)]
        else:
            # Добавляем курицу (три варианта) в пул врагов
            enemy_types = [BasicEnemy, FastEnemy, StrongEnemy, FoxEnemy, BlackFoxEnemy, RedFoxEnemy,
                          lambda g, x, y: ChickenEnemy(g, x, y, 0),
                          lambda g, x, y: ChickenEnemy(g, x, y, 1),
                          lambda g, x, y: ChickenEnemy(g, x, y, 2),
                          lambda g, x, y: LamaEnemy(g, x, y, 0),  # обычная лама
                          lambda g, x, y: LamaEnemy(g, x, y, 1),  # тёмная лама
                          lambda g, x, y: LamaEnemy(g, x, y, 2),  # красная лама
                          PigEnemy,  # свинья
                          SheepEnemy]  # овца
        enemy_class = random.choice(enemy_types)
        # Если enemy_class — функция (лямбда для ChickenEnemy), вызываем её, иначе создаём как обычно
        if callable(enemy_class) and not isinstance(enemy_class, type):
            enemy = enemy_class(self, spawn_x, spawn_y)
        else:
            enemy = enemy_class(self, spawn_x, spawn_y)
        self.all_sprites.add(enemy)
        self.enemies.add(enemy)

    def spawn_boss(self):
        """Spawns the boss at level 5"""
        # Generate boss position (further from player)
        angle = random.uniform(0, 2 * 3.14159)
        distance = self.spawn_distance * 1.5
        spawn_x = self.player.x + distance * math.cos(angle)
        spawn_y = self.player.y + distance * math.sin(angle)
        boss = BossEnemy(self, spawn_x // TILE_SIZE, spawn_y // TILE_SIZE)
        self.all_sprites.add(boss)
        self.enemies.add(boss)
        # Show notification about boss appearance
        self.show_notification("ПОЯВИЛСЯ БОСС!")

    def show_notification(self, text):
        """Shows notification on the screen"""
        self.notification_text = text
        self.notification_time = pygame.time.get_ticks()

    def draw_notification(self, screen):
        """Draws notification"""
        if self.notification_text and pygame.time.get_ticks() - self.notification_time < self.notification_duration:
            font = pygame.font.SysFont(None, 36)
            text_surface = font.render(self.notification_text, True, (255, 0, 0))
            text_rect = text_surface.get_rect(center=(WIDTH // 2, 100))
            bg_rect = text_rect.inflate(20, 10)
            pygame.draw.rect(screen, (0, 0, 0), bg_rect)
            pygame.draw.rect(screen, (255, 0, 0), bg_rect, 2)
            screen.blit(text_surface, text_rect)
        elif self.notification_text:
            self.notification_text = ""

    def get_scale(self):
        screen_w, screen_h = screen.get_size()
        scale_w = screen_w / WIDTH
        scale_h = screen_h / HEIGHT
        return min(scale_w, scale_h)

    def draw_fps(self, surface, clock):
        fps = int(clock.get_fps())
        fps_text = font_fps.render(f"FPS: {fps}", True, (255,255,0))
        surface.blit(fps_text, (surface.get_width() - fps_text.get_width() - 10, 10))

    def draw_game_over_screen(self, surface):
        """Draws the Game Over screen with the player's level (Russian text)"""
        s = pygame.Surface(GAME_SIZE)
        s.set_alpha(200)
        s.fill((0, 0, 0))
        surface.blit(s, (0, 0))
        font = pygame.font.SysFont(None, 80)
        text = font.render('ИГРА ОКОНЧЕНА', True, (255, 50, 50))
        surface.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 100))
        font2 = pygame.font.SysFont(None, 48)
        level_text = font2.render(f'Достигнут уровень: {self.last_level}', True, (255, 255, 255))
        surface.blit(level_text, (WIDTH // 2 - level_text.get_width() // 2, HEIGHT // 2))
        font3 = pygame.font.SysFont(None, 36)
        info_text = font3.render('Нажмите ENTER для возврата в меню', True, (200, 200, 200))
        surface.blit(info_text, (WIDTH // 2 - info_text.get_width() // 2, HEIGHT // 2 + 80))
        # This screen appears after the player dies
        # Shows the reached level and instruction to return to menu

    def run(self):
        running = True
        while running:
            dt = clock.tick(60) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        toggle_fullscreen()
                        self.fullscreen = fullscreen
                        self.screen = screen
                    if event.key == pygame.K_p:
                        if self.state == 'playing':
                            self.state = 'paused'
                        elif self.state == 'paused':
                            self.state = 'playing'
                if self.state == 'menu':
                    # Обработка событий мыши для меню
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        action = self.menu_manager.handle_click(event.pos)
                        if action == 'start_game':
                            self.reset_game()
                            self.state = 'playing'
                        elif action == 'quit_game':
                            running = False
                    elif event.type == pygame.MOUSEBUTTONUP:
                        self.menu_manager.handle_mouse_up()
                    elif event.type == pygame.MOUSEMOTION:
                        self.menu_manager.handle_mouse_motion(event.pos)
                elif self.state == 'playing':
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            self.player.attack()  # Атака будет создана с задержкой в update()
                        # Handle upgrade selection
                        if self.upgrade_manager.showing_upgrade_screen:
                            if event.key == pygame.K_1:
                                selected_upgrade = self.upgrade_manager.select_upgrade(0)
                                if selected_upgrade:
                                    self.upgrade_manager.apply_upgrade_to_player(self.player, selected_upgrade)
                            elif event.key == pygame.K_2:
                                selected_upgrade = self.upgrade_manager.select_upgrade(1)
                                if selected_upgrade:
                                    self.upgrade_manager.apply_upgrade_to_player(self.player, selected_upgrade)
                            elif event.key == pygame.K_3:
                                selected_upgrade = self.upgrade_manager.select_upgrade(2)
                                if selected_upgrade:
                                    self.upgrade_manager.apply_upgrade_to_player(self.player, selected_upgrade)
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.player.attack()  # Атака будет создана с задержкой в update()
                elif self.state == 'paused':
                    # В паузе можно только выйти из паузы (по P)
                    pass
                elif self.state == 'game_over':
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                        self.state = 'menu'

            # --- ALWAYS update and draw the scene ---
            if self.state == 'playing' and not self.upgrade_manager.showing_upgrade_screen:
                # Обновляем игрока отдельно, чтобы получить отложенную атаку
                delayed_attack = self.player.update()
                if delayed_attack:
                    self.all_sprites.add(delayed_attack)
                
                # Обновляем остальные спрайты
                for sprite in self.all_sprites:
                    if sprite != self.player:
                        sprite.update()
                self.experience_orbs.update()
                self.carrots.update()
                # Enemy spawn: interval decreases with level
                current_time = pygame.time.get_ticks()
                # Новый интервал: минимум 300 мс, быстрее уменьшается с уровнем
                level = self.upgrade_manager.level
                self.spawn_interval = max(300, 2000 - (level - 1) * 200)
                if current_time - self.last_spawn_time > self.spawn_interval:
                    self.spawn_enemy()
                    self.last_spawn_time = current_time

            self.camera.update(self.player)

            # Draw everything on game_surface
            game_surface.fill((0, 0, 0))
            # Map (optimized: draw from tile_ids, not sprites)
            cam_left = -self.camera.offset.x
            cam_top = -self.camera.offset.y
            cam_right = cam_left + WIDTH
            cam_bottom = cam_top + HEIGHT
            tile_left = max(0, int(cam_left // TILE_SIZE) - 1)
            tile_top = max(0, int(cam_top // TILE_SIZE) - 1)
            tile_right = min(self.map.width, int(cam_right // TILE_SIZE) + 2)
            tile_bottom = min(self.map.height, int(cam_bottom // TILE_SIZE) + 2)
            for y in range(tile_top, tile_bottom):
                for x in range(tile_left, tile_right):
                    tile_id = self.map.get_tile_id(x, y)
                    if tile_id >= 0:
                        tile_img = self.map.get_tile_image(tile_id)
                        tile_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        game_surface.blit(tile_img, self.camera.apply(type('obj', (), {'rect': tile_rect})))
            # Теперь — experience orbs (поверх карты, под врагами и игроком)
            for orb in self.experience_orbs:
                game_surface.blit(orb.image, self.camera.apply(orb))
            # Отрисовка морковок
            for carrot in self.carrots:
                game_surface.blit(carrot.image, self.camera.apply(carrot))
            # Sprites
            for sprite in self.all_sprites:
                if sprite is not self.player:
                    game_surface.blit(sprite.image, self.camera.apply(sprite))
            self.player.draw(game_surface, self.camera)
            # UI
            self.upgrade_manager.draw_progress(game_surface)
            self.upgrade_manager.draw_upgrade_screen(game_surface)
            self.draw_notification(game_surface)
            self.draw_fps(game_surface, clock)
            # Menu
            if self.state == 'menu':
                self.menu_manager.draw(game_surface)
            # Pause overlay
            if self.state == 'paused':
                s = pygame.Surface(GAME_SIZE)
                s.set_alpha(180)
                s.fill((30, 30, 30))
                game_surface.blit(s, (0, 0))
                font = pygame.font.SysFont(None, 80)
                text = font.render('ПАУЗА', True, (255, 255, 255))
                game_surface.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 40))
                # Controls in pause
                font_ctrl = pygame.font.SysFont(None, 32)
                pause_ctrls = [
                    'P — продолжить',
                    'F11 — полноэкранный режим',
                    'ESC — выйти'
                ]
                for i, ctrl in enumerate(pause_ctrls):
                    ctrl_text = font_ctrl.render(ctrl, True, (200, 200, 200))
                    game_surface.blit(ctrl_text, (WIDTH // 2 - ctrl_text.get_width() // 2, HEIGHT // 2 + 60 + i * 32))
            # Game Over overlay
            if self.state == 'game_over':
                self.draw_game_over_screen(game_surface)
            # Scale and center the final surface
            scale = self.get_scale() if fullscreen else 1.0
            scaled_surface = pygame.transform.scale(game_surface, (int(WIDTH * scale), int(HEIGHT * scale)))
            screen.fill((0, 0, 0))
            screen_rect = screen.get_rect()
            surf_rect = scaled_surface.get_rect(center=screen_rect.center)
            screen.blit(scaled_surface, surf_rect)
            pygame.display.flip()

            # Check player death
            if self.state == 'playing' and self.player.health <= 0:
                self.last_level = self.upgrade_manager.level
                self.state = 'game_over'

            # --- Новый блок: обработка сбора сфер ---
            if self.state == 'playing' and not self.upgrade_manager.showing_upgrade_screen:
                collected = pygame.sprite.spritecollide(self.player, self.experience_orbs, dokill=True)  # type: ignore
                for orb in collected:
                    self.upgrade_manager.on_experience_orb_collected()



if __name__ == '__main__':
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()