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

pygame.init()
pygame.mixer.init()  # Инициализация звуковой системы
screen = pygame.display.set_mode((WIDTH, HEIGHT))
fullscreen = False
# Surface for the game field
GAME_SIZE = (WIDTH, HEIGHT)
game_surface = pygame.Surface(GAME_SIZE)
font_fps = pygame.font.SysFont(None, 24)

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
        self.enemy = BasicEnemy(self, 5, 5)
        self.all_sprites.add(self.enemy)
        self.enemies.add(self.enemy)
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
            enemy_types = [BasicEnemy, FastEnemy]
        elif level == 2:
            enemy_types = [BasicEnemy, FastEnemy, FoxEnemy, SheepEnemy]
        elif level == 3 or level == 4:
            enemy_types = [BasicEnemy, FastEnemy, FoxEnemy, SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy]
        elif level == 5:
            enemy_types = [BasicEnemy, FastEnemy, FoxEnemy, SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy, RedFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 2)]
        elif level == 6:
            enemy_types = [BasicEnemy, FastEnemy, FoxEnemy, SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy, RedFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 2), BlackFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 1), lambda g, x, y: LamaEnemy(g, x, y, 0)]
        elif level == 7:
            enemy_types = [BasicEnemy, FastEnemy, FoxEnemy, SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy, RedFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 2), BlackFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 1), lambda g, x, y: LamaEnemy(g, x, y, 0), lambda g, x, y: LamaEnemy(g, x, y, 2)]
        elif level == 8:
            enemy_types = [BasicEnemy, FastEnemy, FoxEnemy, SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy, RedFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 2), BlackFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 1), lambda g, x, y: LamaEnemy(g, x, y, 0), lambda g, x, y: LamaEnemy(g, x, y, 2)]
        elif level == 9:
            enemy_types = [BasicEnemy, FastEnemy, FoxEnemy, SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy, RedFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 2), BlackFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 1), lambda g, x, y: LamaEnemy(g, x, y, 0), lambda g, x, y: LamaEnemy(g, x, y, 2), lambda g, x, y: LamaEnemy(g, x, y, 1)]
        elif level == 10:
            enemy_types = [BasicEnemy, FastEnemy, FoxEnemy, SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy, RedFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 2), BlackFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 1), lambda g, x, y: LamaEnemy(g, x, y, 0), lambda g, x, y: LamaEnemy(g, x, y, 2), lambda g, x, y: LamaEnemy(g, x, y, 1)]
        elif level == 11:
            enemy_types = [BasicEnemy, FastEnemy, FoxEnemy, SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy, RedFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 2), BlackFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 1), lambda g, x, y: LamaEnemy(g, x, y, 0), lambda g, x, y: LamaEnemy(g, x, y, 2), lambda g, x, y: LamaEnemy(g, x, y, 1), lambda g, x, y: BoarEnemy(g, x, y, 0)]
        elif level == 12:
            enemy_types = [BasicEnemy, FastEnemy, FoxEnemy, SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy, RedFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 2), BlackFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 1), lambda g, x, y: LamaEnemy(g, x, y, 0), lambda g, x, y: LamaEnemy(g, x, y, 2), lambda g, x, y: LamaEnemy(g, x, y, 1), lambda g, x, y: BoarEnemy(g, x, y, 0)]
        elif level == 13:
            enemy_types = [FoxEnemy, SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy, RedFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 2), BlackFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 1), lambda g, x, y: LamaEnemy(g, x, y, 0), lambda g, x, y: LamaEnemy(g, x, y, 2), lambda g, x, y: LamaEnemy(g, x, y, 1), lambda g, x, y: BoarEnemy(g, x, y, 0), lambda g, x, y: BoarEnemy(g, x, y, 1), lambda g, x, y: BoarEnemy(g, x, y, 2)]
        elif level == 14:
            enemy_types = [SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy, RedFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 2), BlackFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 1), lambda g, x, y: LamaEnemy(g, x, y, 0), lambda g, x, y: LamaEnemy(g, x, y, 2), lambda g, x, y: LamaEnemy(g, x, y, 1), lambda g, x, y: BoarEnemy(g, x, y, 0), lambda g, x, y: BoarEnemy(g, x, y, 1), lambda g, x, y: BoarEnemy(g, x, y, 2)]
        elif level == 15:
            enemy_types = [SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy, RedFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 2), BlackFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 1), lambda g, x, y: LamaEnemy(g, x, y, 0), lambda g, x, y: LamaEnemy(g, x, y, 2), lambda g, x, y: LamaEnemy(g, x, y, 1), lambda g, x, y: BoarEnemy(g, x, y, 0), lambda g, x, y: BoarEnemy(g, x, y, 1), lambda g, x, y: BoarEnemy(g, x, y, 2)]
        elif level == 16:
            enemy_types = [SheepEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 0), PigEnemy, RedFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 2), BlackFoxEnemy, lambda g, x, y: ChickenEnemy(g, x, y, 1), lambda g, x, y: LamaEnemy(g, x, y, 0), lambda g, x, y: LamaEnemy(g, x, y, 2), lambda g, x, y: LamaEnemy(g, x, y, 1), lambda g, x, y: BoarEnemy(g, x, y, 0), lambda g, x, y: BoarEnemy(g, x, y, 1), lambda g, x, y: BoarEnemy(g, x, y, 2), lambda g, x, y: CowEnemy(g, x, y, 0), lambda g, x, y: CowEnemy(g, x, y, 1), lambda g, x, y: CowEnemy(g, x, y, 2)]
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
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                        self.reset_game()
                        self.state = 'playing'
                elif self.state == 'playing':
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            attack = self.player.attack()
                            if attack:
                                self.all_sprites.add(attack)
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
                        attack = self.player.attack()
                        if attack:
                            self.all_sprites.add(attack)
                elif self.state == 'paused':
                    # В паузе можно только выйти из паузы (по P)
                    pass
                elif self.state == 'game_over':
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                        self.state = 'menu'

            # --- ALWAYS update and draw the scene ---
            if self.state == 'playing' and not self.upgrade_manager.showing_upgrade_screen:
                self.all_sprites.update()
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
                s = pygame.Surface(GAME_SIZE)
                s.set_alpha(180)
                s.fill((30, 30, 30))
                game_surface.blit(s, (0, 0))
                draw_menu()
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

def draw_menu():
    game_surface.fill((30, 30, 30))
    font = pygame.font.SysFont(None, 60)
    text = font.render('ДЕМО ROG', True, (255, 255, 255))
    game_surface.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 100))
    font_small = pygame.font.SysFont(None, 40)
    play_text = font_small.render('Нажмите ENTER для начала', True, (200, 200, 200))
    game_surface.blit(play_text, (WIDTH // 2 - play_text.get_width() // 2, HEIGHT // 2))
    # Controls
    font_ctrl = pygame.font.SysFont(None, 28)
    controls = [
        'WASD — движение',
        'ЛКМ или ПРОБЕЛ — атака',
        '1, 2, 3 — выбор улучшения',
        'P — пауза',
        'F11 — полноэкранный режим',
        'ESC — выйти'
    ]
    for i, ctrl in enumerate(controls):
        ctrl_text = font_ctrl.render(ctrl, True, (180, 180, 180))
        game_surface.blit(ctrl_text, (WIDTH // 2 - ctrl_text.get_width() // 2, HEIGHT // 2 + 50 + i * 28))

if __name__ == '__main__':
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()