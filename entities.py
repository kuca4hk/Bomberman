import pygame
import math
import random
from isometric_utils import IsometricUtils


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, iso_utils):
        super().__init__()
        self.iso_utils = iso_utils
        self.grid_x = x
        self.grid_y = y
        self.z = 0
        self.animation_frame = 0
        self.animation_timer = 0
        self.facing_direction = 1  # 1 for right, -1 for left
        self.create_sprite()
        
    def create_sprite(self):
        self.image = self.iso_utils.create_character_sprite((0, 150, 255))
        if self.facing_direction == -1:
            self.image = pygame.transform.flip(self.image, True, False)
        self.rect = self.image.get_rect()
        self.update_position()
        
    def update_position(self):
        screen_x, screen_y = self.iso_utils.grid_to_screen(self.grid_x, self.grid_y, self.z)
        offset_x, offset_y = self.iso_utils.get_tile_center_offset()
        self.rect.centerx = screen_x + offset_x
        self.rect.bottom = screen_y + offset_y
        
    def move(self, dx, dy, game_map, grid_width, grid_height):
        new_x = max(0, min(grid_width - 1, self.grid_x + dx))
        new_y = max(0, min(grid_height - 1, self.grid_y + dy))
        
        if game_map[new_y, new_x] == 0:
            self.grid_x = new_x
            self.grid_y = new_y
            # Update facing direction
            if dx != 0:
                self.facing_direction = 1 if dx > 0 else -1
                self.create_sprite()
            self.update_position()
            return True
        return False
        
    def animate(self, moving):
        self.animation_timer += 1
        if moving and self.animation_timer > 5:
            self.animation_frame = (self.animation_frame + 1) % 4
            self.animation_timer = 0
            
    def set_facing_direction(self, direction):
        if self.facing_direction != direction:
            self.facing_direction = direction
            self.create_sprite()


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


class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, iso_utils):
        super().__init__()
        self.iso_utils = iso_utils
        self.grid_x = x
        self.grid_y = y
        self.z = 0
        self.timer = 30
        self.max_timer = 30
        self.create_sprite()
        
    def create_sprite(self):
        frame = self.max_timer - self.timer
        self.image = self.iso_utils.create_explosion_sprite(frame, self.max_timer)
        self.rect = self.image.get_rect()
        self.update_position()
        
    def update_position(self):
        screen_x, screen_y = self.iso_utils.grid_to_screen(self.grid_x, self.grid_y, self.z)
        offset_x, offset_y = self.iso_utils.get_tile_center_offset()
        self.rect.centerx = screen_x + offset_x
        self.rect.bottom = screen_y + offset_y
        
    def update(self):
        self.timer -= 1
        self.create_sprite()
        return self.timer <= 0