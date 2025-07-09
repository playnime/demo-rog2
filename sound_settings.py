# Настройки звука
EFFECTS_VOLUME_PERCENT = 70  # Громкость эффектов в процентах (0-100)

def apply_volume_to_sounds(volume_percent):
    """Применяет громкость ко всем звуковым эффектам (0-100%)"""
    global EFFECTS_VOLUME_PERCENT
    EFFECTS_VOLUME_PERCENT = max(0, min(100, int(volume_percent)))

def get_effects_volume():
    """Возвращает текущую громкость эффектов в процентах"""
    return EFFECTS_VOLUME_PERCENT

def get_volume_multiplier():
    """Возвращает коэффициент громкости (0.0 - 1.0) для умножения на звуки"""
    return EFFECTS_VOLUME_PERCENT / 100.0 