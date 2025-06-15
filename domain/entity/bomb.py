import pygame
import math


class Bomb(pygame.sprite.Sprite):
    """
    Class for bomb sprite

    bomb has x, y and timer that says how long from placing it takes the bomb to explode
    it also has an animation
    """
    def __init__(self, x, y, iso_utils, power=2):
        super().__init__()
        self.iso_utils = iso_utils
        self.grid_x = x
        self.grid_y = y
        self.z = 0
        self.timer = 75  # 5 sekund při 15 FPS
        self.power = power
        self.animation_frame = 0
        self.create_sprite()

    def create_sprite(self):
        # Použij animation_frame pro smooth animaci místo skákání
        self.image = self.iso_utils.create_bomb_sprite(self.animation_frame)
        self.rect = self.image.get_rect()
        self.update_position()

    def update_position(self):
        screen_x, screen_y = self.iso_utils.grid_to_screen(self.grid_x, self.grid_y, self.z)
        offset_x, offset_y = self.iso_utils.get_tile_center_offset()
        
        # Jemné pulsování místo skákání
        time_left = self.timer / 75.0
        pulse_intensity = (1.0 - time_left) * 0.5  # Čím méně času, tím větší pulsování
        pulse = math.sin(self.animation_frame * 0.3) * pulse_intensity
        
        self.rect.centerx = screen_x + offset_x
        self.rect.bottom = screen_y + offset_y + int(pulse * 2)  # Jemné vertikální pulsování

    def update(self):
        self.timer -= 1
        self.animation_frame += 1

        # Aktualizuj sprite
        self.create_sprite()
        return self.timer <= 0
