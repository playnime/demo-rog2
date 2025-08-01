import pygame
import random
from settings import *
import os
from sound_settings import get_volume_multiplier

class Upgrade:
    def __init__(self, name, description, effect_type, effect_value, rarity="common", unique=False):
        self.name = name
        self.description = description
        self.effect_type = effect_type
        self.effect_value = effect_value
        self.rarity = rarity
        self.unique = unique
        self.color = self.get_rarity_color()
    
    def get_rarity_color(self):
        colors = {
            "common": (200, 200, 200),    # Gray
            "uncommon": (100, 255, 100),  # Green
            "rare": (100, 100, 255),      # Blue
            "epic": (200, 100, 255),      # Purple
            "legendary": (255, 200, 100)  # Orange
        }
        return colors.get(self.rarity, (200, 200, 200))

class UpgradeManager:
    def __init__(self):
        # --- Загрузка звука повышения уровня ---
        try:
            self.lvlup_sound = pygame.mixer.Sound(os.path.join("assets", "sounds", "lvlup_sound.mp3"))
            self.lvlup_sound.set_volume(0.1)  # Устанавливаем громкость на 10%
        except:
            self.lvlup_sound = None
            print("Не удалось загрузить звук повышения уровня")
        
        self.available_upgrades = self.create_upgrade_pool()
        self.player_upgrades = []
        self.kills_until_upgrade = 5
        self.current_kills = 0
        self.showing_upgrade_screen = False
        self.upgrade_options = []
        self.level = 1
        self.boss_spawned = False
        
    def create_upgrade_pool(self):
        """Creates the pool of all possible upgrades"""
        upgrades = [
            Upgrade("Пронзающая морковь", "Серая морковь вылетает каждые 2с\nв направлении курсора", "piercing_carrot", 1, "rare", unique=False),
            Upgrade("Молния", "Молния убивает случайного врага\nкаждые 5 секунд", "lightning", 1, "epic", unique=True),
            Upgrade("Железное сердце", "Увеличивает максимальное здоровье на 25", "max_health", 25, "common", unique=False),
            Upgrade("Быстрые ноги", "Увеличивает скорость движения на 0.5", "speed", 0.5, "common", unique=False),
            Upgrade("Острый меч", "Увеличивает урон атаки на 5", "attack_damage", 5, "common", unique=False),
            Upgrade("Быстрая рука", "Уменьшает задержку атаки\nна 100мс", "attack_speed", 100, "common", unique=False),
            Upgrade("Длинный меч", "Увеличивает размер атаки на 10%", "attack_size", 0.1, "common", unique=False),
            Upgrade("Мощный удар", "Ваши атаки отбрасывают врагов", "knockback", 1, "uncommon", unique=True),
            Upgrade("Вампиризм", "Восстанавливает 5 здоровья\nза убийство", "vampirism", 5, "epic", unique=True),
            Upgrade("Критический удар", "20% шанс нанести двойной урон", "critical_chance", 0.2, "epic", unique=True),
            Upgrade("Волшебные морковки", "Синяя морковка кружит вокруг вас\n3с каждые 10с", "magic_carrots", 1, "epic", unique=False),
        ]
        return upgrades
    
    def on_experience_orb_collected(self):
        """Вызывается при сборе сферы опыта игроком"""
        self.current_kills += 1
        if self.current_kills >= self.kills_until_upgrade:
            self.level += 1
            # Воспроизводим звук повышения уровня с небольшой задержкой
            if self.lvlup_sound:
                pygame.time.wait(50)  # Небольшая задержка в 50мс
                # Применяем коэффициент громкости
                volume_multiplier = get_volume_multiplier()
                self.lvlup_sound.set_volume(0.1 * volume_multiplier)
                self.lvlup_sound.play()
            self.show_upgrade_screen()
            self.current_kills = 0
            # Сбалансированный рост требуемого опыта
            self.kills_until_upgrade = int(self.kills_until_upgrade * 1.35)
            # Проверяем, нужно ли спавнить босса
            if self.level == 5 and not self.boss_spawned:
                self.boss_spawned = True
                return "spawn_boss"
        return None
    
    def on_enemy_killed(self):
        """Больше не начисляет опыт напрямую! Только для спавна босса."""
        # Не увеличиваем опыт! Только проверяем спавн босса
        if self.level == 5 and not self.boss_spawned:
            self.boss_spawned = True
            return "spawn_boss"
        return None
    
    def show_upgrade_screen(self):
        """Показывает экран выбора улучшений"""
        self.showing_upgrade_screen = True
        # Все бонусы выпадают случайно независимо от уровня
        self.upgrade_options = self.get_random_upgrades(3)
    
    def get_random_upgrades(self, count):
        """Возвращает случайные улучшения для выбора"""
        available = []
        for upgrade in self.available_upgrades:
            if upgrade.effect_type == 'magic_carrots':
                available.append(upgrade)
            elif upgrade.effect_type == 'piercing_carrot':
                # Ограничиваем Piercing Carrot до 3 раз
                piercing_count = sum(1 for u in self.player_upgrades if u.effect_type == 'piercing_carrot')
                if piercing_count < 3:
                    available.append(upgrade)
            elif upgrade.unique:
                if upgrade not in self.player_upgrades:
                    available.append(upgrade)
            else:
                available.append(upgrade)
        if len(available) < count:
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
        # Сначала вызываем кастомную логику игрока
        if hasattr(player, 'apply_upgrade'):
            player.apply_upgrade(upgrade)
        # Далее — стандартные параметры (на случай если что-то ещё)
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
            if player.attack_size_multiplier < 0.2:
                player.attack_size_multiplier = 0.2
        elif upgrade.effect_type == "vampirism":
            player.vampirism = upgrade.effect_value
        elif upgrade.effect_type == "critical_chance":
            player.critical_chance += upgrade.effect_value
        elif upgrade.effect_type == "dodge_chance":
            player.dodge_chance += upgrade.effect_value
        elif upgrade.effect_type == "explosive_attack":
            player.explosive_attack = True
        elif upgrade.effect_type == "knockback":
            player.knockback_attack = True
        elif upgrade.effect_type == "piercing_carrot":
            player.piercing_carrot = True
        elif upgrade.effect_type == "lightning":
            player.lightning = True
    
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
        title = font_large.render("ВЫБЕРИТЕ УЛУЧШЕНИЕ", True, (255, 255, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
        
        # Инструкция
        font_small = pygame.font.SysFont(None, 24)
        instruction = font_small.render("Нажмите 1, 2 или 3 для выбора", True, (200, 200, 200))
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
        
        # Описание (поддерживает переносы строк)
        desc_lines = upgrade.description.split('\n')
        for i, line in enumerate(desc_lines):
            desc_text = font_desc.render(line, True, (200, 200, 200))
            screen.blit(desc_text, (center_x - desc_text.get_width() // 2, y + 40 + i * 15))
        
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
        progress_text = font.render(f"Уровень: {self.level} | Морковок до улучшения: {self.current_kills}/{self.kills_until_upgrade}", True, (255, 255, 255))
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