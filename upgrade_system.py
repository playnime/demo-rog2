import pygame
import random
from settings import *

class Upgrade:
    def __init__(self, name, description, effect_type, effect_value, rarity="common"):
        self.name = name
        self.description = description
        self.effect_type = effect_type
        self.effect_value = effect_value
        self.rarity = rarity
        self.color = self.get_rarity_color()
    
    def get_rarity_color(self):
        colors = {
            "common": (200, 200, 200),    # Серый
            "uncommon": (100, 255, 100),  # Зеленый
            "rare": (100, 100, 255),      # Синий
            "epic": (200, 100, 255),      # Фиолетовый
            "legendary": (255, 200, 100)  # Оранжевый
        }
        return colors.get(self.rarity, (200, 200, 200))

class UpgradeManager:
    def __init__(self):
        self.available_upgrades = self.create_upgrade_pool()
        self.player_upgrades = []
        self.kills_until_upgrade = 5
        self.current_kills = 0
        self.showing_upgrade_screen = False
        self.upgrade_options = []
        self.level = 1
        self.boss_spawned = False
        
    def create_upgrade_pool(self):
        """Создает пул всех возможных улучшений"""
        upgrades = [
            # Улучшения здоровья
            Upgrade("Железное Сердце", "Увеличивает максимальное здоровье на 25", "max_health", 25, "common"),
            Upgrade("Титановое Сердце", "Увеличивает максимальное здоровье на 50", "max_health", 50, "uncommon"),
            Upgrade("Божественное Сердце", "Увеличивает максимальное здоровье на 100", "max_health", 100, "rare"),
            
            # Улучшения скорости
            Upgrade("Быстрые Ноги", "Увеличивает скорость движения на 0.5", "speed", 0.5, "common"),
            Upgrade("Скорость Ветра", "Увеличивает скорость движения на 1.0", "speed", 1.0, "uncommon"),
            Upgrade("Молния", "Увеличивает скорость движения на 2.0", "speed", 2.0, "rare"),
            
            # Улучшения атаки
            Upgrade("Острый Меч", "Увеличивает урон атаки на 5", "attack_damage", 5, "common"),
            Upgrade("Кровавый Клинок", "Увеличивает урон атаки на 10", "attack_damage", 10, "uncommon"),
            Upgrade("Экскалибур", "Увеличивает урон атаки на 20", "attack_damage", 20, "rare"),
            
            # Улучшения скорости атаки
            Upgrade("Быстрая Рука", "Уменьшает задержку атаки на 100мс", "attack_speed", 100, "common"),
            Upgrade("Мастер Меча", "Уменьшает задержку атаки на 200мс", "attack_speed", 200, "uncommon"),
            Upgrade("Берсерк", "Уменьшает задержку атаки на 300мс", "attack_speed", 300, "rare"),
            
            # Улучшения размера атаки
            Upgrade("Длинный Меч", "Увеличивает размер атаки на 10%", "attack_size", 0.1, "common"),
            Upgrade("Гигантский Клинок", "Увеличивает размер атаки на 20%", "attack_size", 0.2, "uncommon"),
            Upgrade("Космический Меч", "Увеличивает размер атаки на 50%", "attack_size", 0.5, "rare"),
            
            # Специальные улучшения
            Upgrade("Вампиризм", "Восстанавливает 5 здоровья за убийство", "vampirism", 5, "epic"),
            Upgrade("Критический Удар", "20% шанс нанести двойной урон", "critical_chance", 0.2, "epic"),
            Upgrade("Бессмертие", "Шанс 10% не получить урон при атаке", "dodge_chance", 0.1, "legendary"),
            Upgrade("Взрывная Атака", "Атаки взрываются, нанося урон врагам поблизости", "explosive_attack", 1, "legendary"),
        ]
        return upgrades
    
    def on_enemy_killed(self):
        """Вызывается при убийстве врага"""
        self.current_kills += 1
        if self.current_kills >= self.kills_until_upgrade:
            self.level += 1
            self.show_upgrade_screen()
            self.current_kills = 0
            # Увеличиваем количество убийств для следующего улучшения
            self.kills_until_upgrade = min(self.kills_until_upgrade + 2, 20)
            
            # Проверяем, нужно ли спавнить босса
            if self.level == 5 and not self.boss_spawned:
                self.boss_spawned = True
                return "spawn_boss"
        return None
    
    def show_upgrade_screen(self):
        """Показывает экран выбора улучшений"""
        self.showing_upgrade_screen = True
        self.upgrade_options = self.get_random_upgrades(3)
    
    def get_random_upgrades(self, count):
        """Возвращает случайные улучшения для выбора"""
        # Фильтруем улучшения, которые еще не взяты
        available = [upgrade for upgrade in self.available_upgrades 
                    if upgrade not in self.player_upgrades]
        
        if len(available) < count:
            # Если доступных улучшений мало, добавляем уже взятые
            available = self.available_upgrades.copy()
        
        return random.sample(available, min(count, len(available)))
    
    def select_upgrade(self, upgrade_index):
        """Выбирает улучшение и применяет его к игроку"""
        if 0 <= upgrade_index < len(self.upgrade_options):
            selected_upgrade = self.upgrade_options[upgrade_index]
            self.player_upgrades.append(selected_upgrade)
            self.showing_upgrade_screen = False
            self.upgrade_options = []
            return selected_upgrade
        return None
    
    def apply_upgrade_to_player(self, player, upgrade):
        """Применяет улучшение к игроку"""
        if upgrade.effect_type == "max_health":
            player.max_health += upgrade.effect_value
            player.health = min(player.health + upgrade.effect_value, player.max_health)
        elif upgrade.effect_type == "speed":
            player.speed += upgrade.effect_value
        elif upgrade.effect_type == "attack_damage":
            player.attack_damage += upgrade.effect_value
        elif upgrade.effect_type == "attack_speed":
            player.attack_cooldown = max(100, player.attack_cooldown - upgrade.effect_value)
        elif upgrade.effect_type == "attack_size":
            player.attack_size_multiplier += upgrade.effect_value
        elif upgrade.effect_type == "vampirism":
            player.vampirism = upgrade.effect_value
        elif upgrade.effect_type == "critical_chance":
            player.critical_chance += upgrade.effect_value
        elif upgrade.effect_type == "dodge_chance":
            player.dodge_chance += upgrade.effect_value
        elif upgrade.effect_type == "explosive_attack":
            player.explosive_attack = True
    
    def draw_upgrade_screen(self, screen):
        """Отрисовывает экран выбора улучшений"""
        if not self.showing_upgrade_screen:
            return
        
        # Затемнение фона
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Заголовок
        font_large = pygame.font.SysFont(None, 48)
        title = font_large.render("CHOOSE AN UPGRADE", True, (255, 255, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
        
        # Инструкция
        font_small = pygame.font.SysFont(None, 24)
        instruction = font_small.render("Press 1, 2 or 3 to choose", True, (200, 200, 200))
        screen.blit(instruction, (WIDTH // 2 - instruction.get_width() // 2, 100))
        
        # Отображение улучшений
        for i, upgrade in enumerate(self.upgrade_options):
            self.draw_upgrade_option(screen, upgrade, i, WIDTH // 2, 150 + i * 120)
    
    def draw_upgrade_option(self, screen, upgrade, index, center_x, y):
        """Отрисовывает одно улучшение"""
        font_name = pygame.font.SysFont(None, 32)
        font_desc = pygame.font.SysFont(None, 20)
        font_key = pygame.font.SysFont(None, 24)
        
        # Фон карточки
        card_width = 300
        card_height = 100
        card_rect = pygame.Rect(center_x - card_width // 2, y, card_width, card_height)
        pygame.draw.rect(screen, (50, 50, 50), card_rect)
        pygame.draw.rect(screen, upgrade.color, card_rect, 3)
        
        # Название
        name_text = font_name.render(upgrade.name, True, upgrade.color)
        screen.blit(name_text, (center_x - name_text.get_width() // 2, y + 10))
        
        # Описание
        desc_text = font_desc.render(upgrade.description, True, (200, 200, 200))
        screen.blit(desc_text, (center_x - desc_text.get_width() // 2, y + 40))
        
        # Клавиша выбора
        key_text = font_key.render(f"{index + 1}", True, (255, 255, 255))
        key_rect = pygame.Rect(center_x - card_width // 2 - 30, y + 35, 20, 20)
        pygame.draw.rect(screen, (100, 100, 100), key_rect)
        pygame.draw.rect(screen, (255, 255, 255), key_rect, 2)
        screen.blit(key_text, (key_rect.x + 5, key_rect.y + 2))
    
    def draw_progress(self, screen):
        """Отрисовывает прогресс до следующего улучшения"""
        if self.showing_upgrade_screen:
            return
        
        font = pygame.font.SysFont(None, 24)
        progress_text = font.render(f"Level: {self.level} | Kills to upgrade: {self.current_kills}/{self.kills_until_upgrade}", True, (255, 255, 255))
        screen.blit(progress_text, (10, 60))
        
        # Прогресс-бар
        bar_width = 200
        bar_height = 10
        bar_x, bar_y = 10, 90
        
        # Фон прогресс-бара
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        
        # Заполнение прогресс-бара
        progress = self.current_kills / self.kills_until_upgrade
        fill_width = int(bar_width * progress)
        pygame.draw.rect(screen, (100, 255, 100), (bar_x, bar_y, fill_width, bar_height))
        
        # Рамка прогресс-бара
        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1) 