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
fullscreen = False
# Surface for the game field
GAME_SIZE = (WIDTH, HEIGHT)
game_surface = pygame.Surface(GAME_SIZE)

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
        self.state = 'menu'  # 'menu', 'playing', 'paused'
        self.upgrade_manager = UpgradeManager()
        self.fullscreen = fullscreen
        self.screen = screen
        self.reset_game()
        self.last_spawn_time = pygame.time.get_ticks()
        self.spawn_interval = 5000  # 5 seconds in milliseconds
        self.spawn_distance = 200  # Distance from player for spawning
        self.notification_text = ""
        self.notification_time = 0
        self.notification_duration = 3000  # 3 seconds

    def reset_game(self):
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        # Get map size (default 8x6)
        map_width, map_height = 8, 6
        if hasattr(self, 'map') and hasattr(self.map, 'width') and hasattr(self.map, 'height'):
            map_width = self.map.width
            map_height = self.map.height
        elif hasattr(self, 'map') and hasattr(self.map, 'tiles') and self.map.tiles:
            # If there are tiles, determine size by them
            max_x = max(tile.rect.x for tile in self.map.tiles) // TILE_SIZE
            max_y = max(tile.rect.y for tile in self.map.tiles) // TILE_SIZE
            map_width = max_x + 1
            map_height = max_y + 1
        # Center of the map
        player_x = map_width // 2
        player_y = map_height // 2
        self.player = Player(self, player_x, player_y)
        # Load map from Lua file
        self.map = Map(self, lua_map_path="assets/map.lua")
        self.camera = Camera(WIDTH, HEIGHT)
        self.enemy = BasicEnemy(self, 5, 5)
        self.all_sprites.add(self.enemy)
        self.enemies.add(self.enemy)
        self.last_spawn_time = pygame.time.get_ticks()
        self.camera.update(self.player)
        # Reset upgrade system
        self.upgrade_manager = UpgradeManager()

    def spawn_enemy(self):
        # Generate random angle
        angle = random.uniform(0, 2 * 3.14159)
        # Generate random distance within spawn_distance
        distance = random.uniform(100, self.spawn_distance)
        
        # Calculate position relative to player
        spawn_x = self.player.x + distance * math.cos(angle)
        spawn_y = self.player.y + distance * math.sin(angle)
        
        # Randomly select enemy type
        enemy_types = [BasicEnemy, FastEnemy, StrongEnemy]  # BossEnemy removed
        enemy_class = random.choice(enemy_types)
        
        # Create enemy at this position
        enemy = enemy_class(self, spawn_x // TILE_SIZE, spawn_y // TILE_SIZE)
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
        self.show_notification("BOSS APPEARED!")

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

    def run(self):
        running = True
        while running:
            dt = clock.tick(FPS) / 1000
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

            # --- ALWAYS update and draw the scene ---
            if self.state == 'playing' and not self.upgrade_manager.showing_upgrade_screen:
                self.all_sprites.update()
                # Enemy spawn: interval decreases with level
                current_time = pygame.time.get_ticks()
                # New interval: minimum 1 second
                level = self.upgrade_manager.level
                self.spawn_interval = max(1000, 5000 - (level - 1) * 400)
                if current_time - self.last_spawn_time > self.spawn_interval:
                    self.spawn_enemy()
                    self.last_spawn_time = current_time

            self.camera.update(self.player)

            # Draw everything on game_surface
            game_surface.fill((0, 0, 0))
            # Map
            for tile in self.map.tiles:
                game_surface.blit(tile.image, self.camera.apply(tile))
            # Sprites
            for sprite in self.all_sprites:
                if sprite is not self.player:
                    game_surface.blit(sprite.image, self.camera.apply(sprite))
            game_surface.blit(self.player.image, self.camera.apply(self.player))
            # UI
            draw_health_bar(game_surface, 10, 10, self.player.health, self.player.max_health)
            self.upgrade_manager.draw_progress(game_surface)
            self.upgrade_manager.draw_upgrade_screen(game_surface)
            self.draw_notification(game_surface)
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
                text = font.render('PAUSED', True, (255, 255, 255))
                game_surface.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 40))
                # Controls in pause
                font_ctrl = pygame.font.SysFont(None, 32)
                pause_ctrls = [
                    'P — resume',
                    'F11 — fullscreen',
                    'ESC — quit'
                ]
                for i, ctrl in enumerate(pause_ctrls):
                    ctrl_text = font_ctrl.render(ctrl, True, (200, 200, 200))
                    game_surface.blit(ctrl_text, (WIDTH // 2 - ctrl_text.get_width() // 2, HEIGHT // 2 + 60 + i * 32))
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
                self.state = 'menu'

def draw_menu():
    game_surface.fill((30, 30, 30))
    font = pygame.font.SysFont(None, 60)
    text = font.render('ROG DEMO', True, (255, 255, 255))
    game_surface.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 100))
    font_small = pygame.font.SysFont(None, 40)
    play_text = font_small.render('Press ENTER to start', True, (200, 200, 200))
    game_surface.blit(play_text, (WIDTH // 2 - play_text.get_width() // 2, HEIGHT // 2))
    # Controls
    font_ctrl = pygame.font.SysFont(None, 28)
    controls = [
        'WASD — move',
        'LMB or SPACE — attack',
        '1, 2, 3 — choose upgrade',
        'P — pause',
        'F11 — fullscreen',
        'ESC — quit'
    ]
    for i, ctrl in enumerate(controls):
        ctrl_text = font_ctrl.render(ctrl, True, (180, 180, 180))
        game_surface.blit(ctrl_text, (WIDTH // 2 - ctrl_text.get_width() // 2, HEIGHT // 2 + 50 + i * 28))

if __name__ == '__main__':
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()