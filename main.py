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

# Уровень (пример)
level_data = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, -1, -1, -1, -1, -1, -1, 0],
    [0, -1, -1, -1, -1, -1, -1, 0],
    [0, -1, -1, -1, -1, -1, -1, 0],
    [0, -1, -1, -1, -1, -1, -1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

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
        self.player = Player(self, 3, 3)
        self.map = Map(self, level_data, "assets/tiles.png")
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
                # Спавн врагов каждые 5 секунд
                current_time = pygame.time.get_ticks()
                if current_time - self.last_spawn_time > self.spawn_interval:
                    self.spawn_enemy()
                    self.last_spawn_time = current_time

            self.camera.update(self.player)

            screen.fill((0, 0, 0))
            for sprite in self.all_sprites:
                screen.blit(sprite.image, self.camera.apply(sprite))

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