import pygame

class Explosion(pygame.sprite.Sprite):
    """
    Class for the explosion sprite(s)

    when bomb explodes the bomb sprite is deleted and several explosion sprites appear
    explosion sprites delete destroyable barriers and are harmful to the player and to enemies
    they have animation and timer, that determines, how long the explosion takes
    """
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