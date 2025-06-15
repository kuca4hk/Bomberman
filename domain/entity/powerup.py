import pygame
import math
import random
from enum import Enum


class PowerUpType(Enum):
    UNLIMITED_BOMBS = "unlimited_bombs"  # Neomezené bomby na 5 sekund
    EXTRA_BOMB = "extra_bomb"           # +1 bomba permanentně
    SPEED_BOOST = "speed_boost"         # Rychlejší pohyb na 5 sekund
    BIGGER_EXPLOSION = "bigger_explosion"  # Větší exploze na 5 sekund


class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, iso_utils, powerup_type=None):
        super().__init__()
        self.iso_utils = iso_utils
        self.grid_x = x
        self.grid_y = y
        self.z = 0
        self.animation_frame = 0
        self.lifetime = 450  # 30 sekund při 15 FPS
        
        # Náhodný typ pokud není zadaný
        if powerup_type is None:
            self.powerup_type = random.choice(list(PowerUpType))
        else:
            self.powerup_type = powerup_type
            
        self.create_sprite()

    def create_sprite(self):
        """Vytvoří sprite pro powerup"""
        # Různé barvy pro různé typy
        colors = {
            PowerUpType.UNLIMITED_BOMBS: (255, 255, 0),    # Žlutá
            PowerUpType.EXTRA_BOMB: (255, 100, 100),       # Červená
            PowerUpType.SPEED_BOOST: (100, 255, 100),      # Zelená
            PowerUpType.BIGGER_EXPLOSION: (255, 100, 255)  # Růžová
        }
        
        color = colors[self.powerup_type]
        
        # Vytvoř základní sprite - malý krystal/diamant
        size = 20
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Pulsování podle animace
        pulse = math.sin(self.animation_frame * 0.2) * 0.2 + 1
        current_size = int(size * pulse)
        
        # Nakresli diamant
        center = size // 2
        points = [
            (center, 2),                    # Top
            (current_size - 2, center),     # Right
            (center, current_size - 2),     # Bottom
            (2, center)                     # Left
        ]
        
        pygame.draw.polygon(self.image, color, points)
        pygame.draw.polygon(self.image, (255, 255, 255), points, 2)  # Bílý okraj
        
        self.rect = self.image.get_rect()
        self.update_position()

    def update_position(self):
        screen_x, screen_y = self.iso_utils.grid_to_screen(self.grid_x, self.grid_y, self.z)
        offset_x, offset_y = self.iso_utils.get_tile_center_offset()
        
        # Levitace efekt
        float_offset = math.sin(self.animation_frame * 0.15) * 5
        
        self.rect.centerx = screen_x + offset_x
        self.rect.bottom = screen_y + offset_y - int(float_offset)

    def update(self):
        """Update powerup animace a lifetime"""
        self.animation_frame += 1
        self.lifetime -= 1
        
        # Blikání pokud končí lifetime
        if self.lifetime < 90:  # Posledních 6 sekund
            if (self.lifetime // 5) % 2:  # Blikání
                self.create_sprite()
        else:
            self.create_sprite()
        
        return self.lifetime <= 0  # Vrací True pokud má zmizet

    def get_effect_description(self):
        """Vrátí popis efektu powerupu"""
        descriptions = {
            PowerUpType.UNLIMITED_BOMBS: "Neomezené bomby (5s)",
            PowerUpType.EXTRA_BOMB: "Extra bomba",
            PowerUpType.SPEED_BOOST: "Rychlost (5s)",
            PowerUpType.BIGGER_EXPLOSION: "Větší exploze (5s)"
        }
        return descriptions[self.powerup_type]