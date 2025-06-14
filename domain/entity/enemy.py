import pygame
import math
import random

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, iso_utils):
        super().__init__()
        self.iso_utils = iso_utils
        self.grid_x = x
        self.grid_y = y
        self.z = 0
        self.animation_frame = 0
        self.move_timer = 0
        self.create_sprite()

    def create_sprite(self):
        self.image = self.iso_utils.create_character_sprite((200, 50, 50))
        self.rect = self.image.get_rect()
        self.update_position()

    def update_position(self):
        screen_x, screen_y = self.iso_utils.grid_to_screen(self.grid_x, self.grid_y, self.z)
        offset_x, offset_y = self.iso_utils.get_tile_center_offset()
        # Add floating animation
        float_offset = math.sin(self.animation_frame) * 3
        self.rect.centerx = screen_x + offset_x
        self.rect.bottom = screen_y + offset_y - float_offset

    def update(self, game_map, grid_width, grid_height):
        self.animation_frame += 0.2
        self.move_timer += 1

        if self.move_timer > 60:
            self.move_timer = 0
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            dx, dy = random.choice(directions)
            new_x = self.grid_x + dx
            new_y = self.grid_y + dy

            if (0 <= new_x < grid_width and 0 <= new_y < grid_height and
                    game_map[new_y, new_x] == 0):
                self.grid_x = new_x
                self.grid_y = new_y

        self.update_position()
