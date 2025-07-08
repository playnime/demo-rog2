import pygame
import sys
import random
import math
from settings import *
from player import Player
from enemy import BasicEnemy, FastEnemy, StrongEnemy, BossEnemy
from map import Map
from camera import Camera
from attack import Attack
from utils import draw_health_bar
from upgrade_system import UpgradeManager

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

class Game:
    def __init__(self):
        self.state = 'menu'  # 'menu' или 'playing'
        self.upgrade_manager = UpgradeManager()
        self.reset_game()
        self.last_spawn_time = pygame.time.get_ticks()
        self.spawn_interval = 5000  # 5 секунд в миллисекундах
        self.spawn_distance = 200  # Расстояние от игрока для спавна
        self.notification_text = ""
        self.notification_time = 0
        self.notification_duration = 3000  # 3 секунды

    def reset_game(self):
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        # Получаем размеры карты (по умолчанию 8x6)
        map_width, map_height = 8, 6
        if hasattr(self, 'map') and hasattr(self.map, 'width') and hasattr(self.map, 'height'):
            map_width = self.map.width
            map_height = self.map.height
        elif hasattr(self, 'map') and hasattr(self.map, 'tiles') and self.map.tiles:
            # Если есть тайлы, определяем размеры по ним
            max_x = max(tile.rect.x for tile in self.map.tiles) // TILE_SIZE
            max_y = max(tile.rect.y for tile in self.map.tiles) // TILE_SIZE
            map_width = max_x + 1
            map_height = max_y + 1
        # Центр карты
        player_x = map_width // 2
        player_y = map_height // 2
        self.player = Player(self, player_x, player_y)
        # Загружаем карту из Lua файла
        self.map = Map(self, lua_map_path="assets/map.lua")
        self.camera = Camera(WIDTH, HEIGHT)
        self.enemy = BasicEnemy(self, 5, 5)
        self.all_sprites.add(self.enemy)
        self.enemies.add(self.enemy)
        self.last_spawn_time = pygame.time.get_ticks()
        self.camera.update(self.player)
        # Сбрасываем систему прокачки
        self.upgrade_manager = UpgradeManager()

    def spawn_enemy(self):
        # Генерируем случайный угол
        angle = random.uniform(0, 2 * 3.14159)
        # Генерируем случайное расстояние в пределах spawn_distance
        distance = random.uniform(100, self.spawn_distance)
        
        # Вычисляем позицию относительно игрока
        spawn_x = self.player.x + distance * math.cos(angle)
        spawn_y = self.player.y + distance * math.sin(angle)
        
        # Случайно выбираем тип врага
        enemy_types = [BasicEnemy, FastEnemy, StrongEnemy, BossEnemy]
        enemy_class = random.choice(enemy_types)
        
        # Создаем врага в этой позиции
        enemy = enemy_class(self, spawn_x // TILE_SIZE, spawn_y // TILE_SIZE)
        self.all_sprites.add(enemy)
        self.enemies.add(enemy)

    def spawn_boss(self):
        """Спавнит босса на 5-м уровне"""
        # Генерируем позицию для босса (дальше от игрока)
        angle = random.uniform(0, 2 * 3.14159)
        distance = self.spawn_distance * 1.5  # Босс появляется дальше
        
        spawn_x = self.player.x + distance * math.cos(angle)
        spawn_y = self.player.y + distance * math.sin(angle)
        
        # Создаем босса
        boss = BossEnemy(self, spawn_x // TILE_SIZE, spawn_y // TILE_SIZE)
        self.all_sprites.add(boss)
        self.enemies.add(boss)
        
        # Показываем сообщение о появлении босса
        self.show_notification("БОСС ПОЯВИЛСЯ!")

    def show_notification(self, text):
        """Показывает уведомление на экране"""
        self.notification_text = text
        self.notification_time = pygame.time.get_ticks()

    def draw_notification(self, screen):
        """Отрисовывает уведомление"""
        if self.notification_text and pygame.time.get_ticks() - self.notification_time < self.notification_duration:
            font = pygame.font.SysFont(None, 36)
            text_surface = font.render(self.notification_text, True, (255, 0, 0))
            text_rect = text_surface.get_rect(center=(WIDTH // 2, 100))
            
            # Фон для текста
            bg_rect = text_rect.inflate(20, 10)
            pygame.draw.rect(screen, (0, 0, 0), bg_rect)
            pygame.draw.rect(screen, (255, 0, 0), bg_rect, 2)
            
            screen.blit(text_surface, text_rect)
        elif self.notification_text:
            self.notification_text = ""

    def run(self):
        running = True
        while running:
            dt = clock.tick(FPS) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if self.state == 'menu':
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                        self.reset_game()
                        self.state = 'playing'
                elif self.state == 'playing':
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            attack = self.player.attack()
                            if attack:
                                self.all_sprites.add(attack)
                        
                        # Обработка выбора улучшений
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

            # --- ВСЕГДА обновляем и отрисовываем сцену ---
            if self.state == 'playing' and not self.upgrade_manager.showing_upgrade_screen:
                self.all_sprites.update()
                # Спавн врагов: интервал уменьшается с уровнем
                current_time = pygame.time.get_ticks()
                # Новый интервал: минимум 1 секунда
                level = self.upgrade_manager.level
                self.spawn_interval = max(1000, 5000 - (level - 1) * 400)
                if current_time - self.last_spawn_time > self.spawn_interval:
                    self.spawn_enemy()
                    self.last_spawn_time = current_time

            self.camera.update(self.player)

            screen.fill((0, 0, 0))
            # Сначала рисуем тайлы карты
            for tile in self.map.tiles:
                screen.blit(tile.image, self.camera.apply(tile))
            # Затем рисуем всех спрайтов, кроме игрока
            for sprite in self.all_sprites:
                if sprite is not self.player:
                    screen.blit(sprite.image, self.camera.apply(sprite))
            # В самом конце рисуем игрока поверх всех
            screen.blit(self.player.image, self.camera.apply(self.player))

            # Отрисовка UI
            draw_health_bar(screen, 10, 10, self.player.health, self.player.max_health)
            self.upgrade_manager.draw_progress(screen)
            
            # Отрисовка экрана улучшений
            self.upgrade_manager.draw_upgrade_screen(screen)
            
            # Отрисовка уведомлений
            self.draw_notification(screen)

            # --- Если меню, рисуем затемнение и текст поверх ---
            if self.state == 'menu':
                s = pygame.Surface((WIDTH, HEIGHT))
                s.set_alpha(180)
                s.fill((30, 30, 30))
                screen.blit(s, (0, 0))
                draw_menu()
            else:
                pygame.display.flip()

            # Проверка смерти игрока
            if self.state == 'playing' and self.player.health <= 0:
                self.state = 'menu'

def draw_menu():
    screen.fill((30, 30, 30))
    font = pygame.font.SysFont(None, 60)
    text = font.render('ROG DEMO', True, (255, 255, 255))
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 100))
    font_small = pygame.font.SysFont(None, 40)
    play_text = font_small.render('Нажмите ENTER чтобы начать', True, (200, 200, 200))
    screen.blit(play_text, (WIDTH // 2 - play_text.get_width() // 2, HEIGHT // 2))
    pygame.display.flip()

if __name__ == '__main__':
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()