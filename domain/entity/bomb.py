import pygame
import math


class Bomb(pygame.sprite.Sprite):
    def __init__(self, x, y, iso_utils, power=2):
        super().__init__()
        self.iso_utils = iso_utils
        self.grid_x = x
        self.grid_y = y
        self.z = 0
        self.timer = 180
        self.power = power
        self.pulse_timer = 0
        self.pulse_scale = 1.0
        self.create_sprite()

    def create_sprite(self):
        self.image = self.iso_utils.create_bomb_sprite(self.pulse_scale)
        self.rect = self.image.get_rect()
        self.update_position()

    def update_position(self):
        screen_x, screen_y = self.iso_utils.grid_to_screen(self.grid_x, self.grid_y, self.z)
        offset_x, offset_y = self.iso_utils.get_tile_center_offset()
        self.rect.centerx = screen_x + offset_x
        self.rect.bottom = screen_y + offset_y

    def update(self):
        self.timer -= 1
        self.pulse_timer += 1

        # Pulsing animation
        time_factor = self.timer / 180.0
        pulse_speed = 10 - time_factor * 8
        self.pulse_scale = 0.8 + math.sin(self.pulse_timer / pulse_speed) * 0.3

        self.create_sprite()
        return self.timer <= 0
