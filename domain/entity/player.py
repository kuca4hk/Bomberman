import pygame


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
        self.immunity_timer = 0  # Imunita po zásahu
        self.create_sprite()

    def create_sprite(self):
        # Změna barvy při immunitě (blikání)
        if self.immunity_timer > 0 and (self.immunity_timer // 5) % 2:
            # Blikání - průhlednější barva
            self.image = self.iso_utils.create_character_sprite((0, 100, 200))
        else:
            # Normální barva
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
    
    def update(self):
        if self.immunity_timer > 0:
            self.immunity_timer -= 1
            # Aktualizuj sprite pro blikání
            self.create_sprite()
            # Debug výpis každých 30 framů
            if self.immunity_timer % 30 == 0:
                print(f"Imunita zbývá: {self.immunity_timer} framů")

    def set_facing_direction(self, direction):
        if self.facing_direction != direction:
            self.facing_direction = direction
            self.create_sprite()