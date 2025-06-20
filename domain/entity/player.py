import pygame


class Player(pygame.sprite.Sprite):
    """
    Class for player sprite

    player has x, y, can have imunity after hit, has max_boms meaning how many bombs he can place
    also has animation
    player is controlled by the user
    """
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
        self.bomb_placed_position = None  # Pozice kde hráč položil bombu (může z ní odejít)
        self.max_bombs = 1  # Počet bomb které může hráč mít současně
        self.current_bomb_count = 0  # Aktuální počet položených bomb
        
        # Powerup efekty
        self.active_powerups = {}  # Slovník aktivních powerupů s časem konce
        self.unlimited_bombs_timer = 0  # Časovač pro neomezené bomby
        self.speed_boost_timer = 0      # Časovač pro rychlost
        self.bigger_explosion_timer = 0  # Časovač pro větší exploze
        
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

    def move(self, dx, dy, game_map, grid_width, grid_height, bombs=None):
        """
        Function for moving the player.
        It checks if the move is valid.
        Player cannot walk out of the map, through the wall and through the bomb

        Inputs:
        -------
        dx : int
            x change from current position
        dy : int
            y change from current position
        game_map : 2d array
            map of the game, used for determining valid moves
        grid_width : int
            width of the map, used for determining valid moves
        grid_height : int
            height of the map, used for determining valid moves
        bombs, default None
            bombs placed on the map
        """
        new_x = max(0, min(grid_width - 1, self.grid_x + dx))
        new_y = max(0, min(grid_height - 1, self.grid_y + dy))

        # Kontrola stěn
        if game_map[new_y, new_x] != 0:
            return False
            
        # Kontrola bomb
        if bombs:
            for bomb in bombs:
                if bomb.grid_x == new_x and bomb.grid_y == new_y:
                    # Pokud se snažíme jít na bombu a není to ta bomba kterou jsme právě položili
                    if self.bomb_placed_position != (new_x, new_y):
                        return False
        
        # Pokud se pohybujeme, zkontroluj jestli opouštíme pozici s bombou
        if self.bomb_placed_position and (self.grid_x, self.grid_y) == self.bomb_placed_position:
            # Opouštíme pozici s bombou - už se na ni nemůžeme vrátit
            self.bomb_placed_position = None
        
        self.grid_x = new_x
        self.grid_y = new_y
        # Update facing direction
        if dx != 0:
            self.facing_direction = 1 if dx > 0 else -1
            self.create_sprite()
        self.update_position()
        return True

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
            
        # Update powerup timery
        if self.unlimited_bombs_timer > 0:
            self.unlimited_bombs_timer -= 1
        if self.speed_boost_timer > 0:
            self.speed_boost_timer -= 1
        if self.bigger_explosion_timer > 0:
            self.bigger_explosion_timer -= 1

    def set_facing_direction(self, direction):
        """
        Function for setting the direction the player is facing.
        variable facing_direction is then used for animation
        """
        if self.facing_direction != direction:
            self.facing_direction = direction
            self.create_sprite()
    
    def set_bomb_placed_position(self, x, y):
        """Nastaví pozici kde hráč položil bombu"""
        self.bomb_placed_position = (x, y)
    
    def can_place_bomb(self):
        """Zkontroluje zda může hráč položit bombu"""
        # Pokud má unlimited bombs, může vždy
        if self.unlimited_bombs_timer > 0:
            return True
        return self.current_bomb_count < self.max_bombs
    
    def add_bomb(self):
        """Zvýší počet položených bomb"""
        # Pokud má unlimited bombs, nezvyšuj počítadlo
        if self.unlimited_bombs_timer > 0:
            return True
        if self.current_bomb_count < self.max_bombs:
            self.current_bomb_count += 1
            return True
        return False
    
    def remove_bomb(self):
        """Sníží počet bomb po explozi"""
        # Pokud má unlimited bombs, nesniž počítadlo
        if self.unlimited_bombs_timer > 0:
            return
        if self.current_bomb_count > 0:
            self.current_bomb_count -= 1
    
    def set_max_bombs_for_level(self, level):
        """Nastaví maximální počet bomb podle levelu"""
        self.max_bombs = min(5, level)  # Level 1: 1 bomba, Level 2: 2 bomby, Level 3: 3 bomby, atd. max 5
    
    def apply_powerup(self, powerup_type):
        """Aplikuje efekt powerupu"""
        from domain.entity.powerup import PowerUpType
        
        if powerup_type == PowerUpType.UNLIMITED_BOMBS:
            self.unlimited_bombs_timer = 75  # 5 sekund při 15 FPS
        elif powerup_type == PowerUpType.EXTRA_BOMB:
            self.max_bombs += 1  # Permanentní zvýšení
        elif powerup_type == PowerUpType.SPEED_BOOST:
            self.speed_boost_timer = 75  # 5 sekund při 15 FPS
        elif powerup_type == PowerUpType.BIGGER_EXPLOSION:
            self.bigger_explosion_timer = 75  # 5 sekund při 15 FPS
    
    def get_bomb_power(self):
        """Vrátí sílu bomb (základní nebo s bonusem)"""
        base_power = 2
        if self.bigger_explosion_timer > 0:
            return base_power + 2  # Větší exploze
        return base_power
    
    def get_move_speed(self):
        """Vrátí rychlost pohybu (pro budoucí použití)"""
        if self.speed_boost_timer > 0:
            return 2  # 2x rychlejší
        return 1  # Normální rychlost