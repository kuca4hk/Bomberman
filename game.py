import pygame
import time
import math
import random

from domain.entity.bomb import Bomb
from domain.entity.enemy import Enemy
from domain.entity.player import Player
from ui_components import GameState, Button
from utils.isometric_utils import IsometricUtils
from game_logic import (create_game_map, create_isometric_sprites, create_sounds, create_isometric_background, 
                       explode_bomb, check_collisions, check_enemy_explosions, count_destructible_blocks,
                       create_story_map, STORY_TOTAL_LEVELS)
from domain.entity.biome import Biome

class BoomerManGame:
    """
    Main class containing the game
    """
    def __init__(self):
        """
        Iniitializes the game
        prepares map width and height, fps, wellcome screen (with buttons)
        """
        pygame.init()
        self.WIDTH = 1000
        self.HEIGHT = 700
        self.FPS = 15
        
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Boomer Man - Isometric 3D")
        self.clock = pygame.time.Clock()
        
        # Isometric setup
        self.iso_utils = IsometricUtils(tile_width=64, tile_height=32)
        self.camera_offset_x = self.WIDTH // 2
        self.camera_offset_y = 100
        
        self.game_state = GameState.INTRO
        self.menu_screen_clicked = False
        self.intro_start_time = time.time()
        self.score = 0
        self.lives = 3
        self.high_score = self.load_high_score()
        
        # Story mode
        self.story_level = 1
        self.story_high_score = self.load_story_high_score()
        self.is_story_mode = False
        self.biome = None

        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)
        
        self.running = True
        self.keys_pressed = set()
        
        # Sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.players = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bombs = pygame.sprite.Group()
        self.explosions = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        
        # UI tlačítka pro menu - barevné gradientové tlačítka
        self.play_button = Button(self.WIDTH//2 - 100, self.HEIGHT//2 - 30, 200, 50,
                                 "HRÁT", self.font, (34, 139, 34), (255, 255, 255))  # Zelená
        self.story_button = Button(self.WIDTH//2 - 100, self.HEIGHT//2 + 30, 200, 50,
                                  "STORY", self.font, (138, 43, 226), (255, 255, 255))  # Fialová
        
        # Victory screen tlačítka - barevné
        self.play_again_button = Button(self.WIDTH//2 - 200, self.HEIGHT//2 + 50, 180, 50, 
                                       "Hrát znova", self.font, (34, 139, 34), (255, 255, 255))  # Zelená
        self.menu_button = Button(self.WIDTH//2 + 20, self.HEIGHT//2 + 50, 180, 50, 
                                 "Menu", self.font, (30, 144, 255), (255, 255, 255))  # Modrá
        
        # Game over screen tlačítka - barevné
        self.restart_button = Button(self.WIDTH//2 - 200, self.HEIGHT//2 + 50, 180, 50, 
                                    "Restart", self.font, (220, 20, 60), (255, 255, 255))  # Červená
        self.game_over_menu_button = Button(self.WIDTH//2 + 20, self.HEIGHT//2 + 50, 180, 50, 
                                           "Menu", self.font, (70, 130, 180), (255, 255, 255))  # Ocelová modrá
        
        self.sprites_collection = create_isometric_sprites(self.iso_utils)
        self.bg_surface_collection = create_isometric_background(self.WIDTH, self.HEIGHT)
        self.sounds = create_sounds()
        self.init_game_world()
        
        self.sounds['background'].play(loops=-1).set_volume(0.1)
    
    def init_game_world(self):
        """
        generates the game map via create_game_map, adds player and adds enemy/ies
        """
        self.grid_width = 15
        self.grid_height = 11
        
        # Vytvoření herního pole
        self.game_map = create_game_map(self.grid_width, self.grid_height)
        
        # Vytvoření hráče a nepřátel jako sprite objekty
        self.player = Player(1, 1, self.iso_utils)
        # Nastaví 3 bomby pro normální high-score mód
        self.player.max_bombs = 3
        self.all_sprites.add(self.player)
        self.players.add(self.player)
        
        # Nepřátelé - 3 v rozích pro normální mód
        enemy_positions = [(self.grid_width-2, self.grid_height-2),
                          (self.grid_width-2, 2), (2, self.grid_height-2)]
        
        for x, y in enemy_positions:
            enemy = Enemy(x, y, self.iso_utils)
            self.all_sprites.add(enemy)
            self.enemies.add(enemy)
        
        # Animace a efekty
        self.bomb_pulse_timer = 0
        self.explosion_particles = []
        self.screen_shake = 0
        
        # Mock zvukové efekty (pouze vizuální indikace)
        self.sound_effects = {
            'bomb_place': {'active': False, 'timer': 0},
            'explosion': {'active': False, 'timer': 0},
            'enemy_hit': {'active': False, 'timer': 0},
            'player_hit': {'active': False, 'timer': 0}
        }
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.game_state == GameState.INTRO:
                    self.game_state = GameState.MENU_SCREEN
                elif self.game_state == GameState.MENU_SCREEN:
                    if self.play_button.handle_event(event):
                        self.restart_game()
                    elif self.story_button.handle_event(event):
                        self.start_story_mode()
                elif self.game_state == GameState.VICTORY:
                    if self.play_again_button.handle_event(event):
                        self.restart_game()
                    elif self.menu_button.handle_event(event):
                        self.game_state = GameState.MENU_SCREEN
                elif self.game_state == GameState.GAME_OVER:
                    if self.restart_button.handle_event(event):
                        self.restart_game()
                    elif self.game_over_menu_button.handle_event(event):
                        self.game_state = GameState.MENU_SCREEN
                elif self.game_state == GameState.STORY_COMPLETE:
                    if self.play_again_button.handle_event(event):
                        self.start_story_mode()
                    elif self.menu_button.handle_event(event):
                        self.game_state = GameState.MENU_SCREEN
            elif event.type == pygame.MOUSEMOTION:
                if self.game_state == GameState.MENU_SCREEN:
                    self.play_button.handle_event(event)
                    self.story_button.handle_event(event)
                elif self.game_state == GameState.VICTORY:
                    self.play_again_button.handle_event(event)
                    self.menu_button.handle_event(event)
                elif self.game_state == GameState.GAME_OVER:
                    self.restart_button.handle_event(event)
                    self.game_over_menu_button.handle_event(event)
                elif self.game_state == GameState.STORY_COMPLETE:
                    self.play_again_button.handle_event(event)
                    self.menu_button.handle_event(event)
            elif event.type == pygame.KEYDOWN:
                self.keys_pressed.add(event.key)
                if self.game_state == GameState.MENU and event.key == pygame.K_SPACE:
                    self.game_state = GameState.PLAYING
                elif (self.game_state == GameState.PLAYING or self.game_state == GameState.STORY_PLAYING) and event.key == pygame.K_SPACE:
                    self.place_bomb()
            elif event.type == pygame.KEYUP:
                self.keys_pressed.discard(event.key)
    
    def update(self):
        # Update mock sound effects
        for effect in self.sound_effects.values():
            if effect['active']:
                effect['timer'] -= 1
                if effect['timer'] <= 0:
                    effect['active'] = False
        
        if self.game_state == GameState.INTRO:
            if time.time() - self.intro_start_time > 3:
                self.game_state = GameState.MENU_SCREEN
        
        elif self.game_state == GameState.PLAYING or self.game_state == GameState.STORY_PLAYING:
            self.update_player()
            self.update_sprites()
            self.check_game_collisions()
    
    def update_player(self):
        """
        Processes the movements of the player.
        """
        moving = False
        
        # Update hráče (pro imunitu)
        self.player.update()
        
        if pygame.K_LEFT in self.keys_pressed or pygame.K_a in self.keys_pressed:
            if self.player.move(-1, 0, self.game_map, self.grid_width, self.grid_height, self.bombs):
                moving = True
                self.player.set_facing_direction(-1)
        elif pygame.K_RIGHT in self.keys_pressed or pygame.K_d in self.keys_pressed:
            if self.player.move(1, 0, self.game_map, self.grid_width, self.grid_height, self.bombs):
                moving = True
                self.player.set_facing_direction(1)
        elif pygame.K_UP in self.keys_pressed or pygame.K_w in self.keys_pressed:
            if self.player.move(0, -1, self.game_map, self.grid_width, self.grid_height, self.bombs):
                moving = True
        elif pygame.K_DOWN in self.keys_pressed or pygame.K_s in self.keys_pressed:
            if self.player.move(0, 1, self.game_map, self.grid_width, self.grid_height, self.bombs):
                moving = True
        
        self.player.animate(moving)
    
    def place_bomb(self):
        """
        Processe the bomb placement.
        Checks whether the player can place another bomb.
        Creates new sprite for the bomb.
        """
        # Zkontroluj, jestli hráč může položit bombu (limit podle levelu)
        if not self.player.can_place_bomb():
            return

        bomb_pos = (self.player.grid_x, self.player.grid_y)
        # Zkontroluj, jestli na pozici už není bomba
        bomb_exists = any(bomb.grid_x == bomb_pos[0] and bomb.grid_y == bomb_pos[1] 
                         for bomb in self.bombs)
        
        if not bomb_exists:
            # Použij sílu bomb z hráče (může být zvýšená powerupem)
            bomb_power = self.player.get_bomb_power()
            bomb = Bomb(bomb_pos[0], bomb_pos[1], self.iso_utils, power=bomb_power)
            self.bombs.add(bomb)
            self.all_sprites.add(bomb)
            # Přidej bombu do počítadla hráče
            self.player.add_bomb()
            # Nastav pozici bomby pro bomb passing mechanismus
            self.player.set_bomb_placed_position(bomb_pos[0], bomb_pos[1])
            # Mock zvukový efekt
            self.sound_effects['bomb_place']['active'] = True
            self.sound_effects['bomb_place']['timer'] = 20
            self.sounds['bomb_place'].play()
    
    def update_sprites(self):
        """
        Processes the bombs, explosions and enemies sprites.
        Processes whether the bomb should explode and removes the bomb sprite and adds the corresponding explosion sprites.
        Procecces the explosions and removes them when they should be removed.
        Processes the enemies and their moves.
        """
        # Update bomb sprites
        for bomb in self.bombs.copy():
            if bomb.update():  # Vrací True pokud má explodovat
                particles, score_gain, spawned_powerups = explode_bomb(bomb, self.game_map, self.grid_width, 
                                                   self.grid_height, self.iso_utils, 
                                                   self.explosions, self.all_sprites, self.powerups)
                self.explosion_particles.extend(particles)
                self.score += score_gain
                self.screen_shake = 8
                self.sound_effects['explosion']['active'] = True
                self.sound_effects['explosion']['timer'] = 30
                self.sounds['explosion'].play()
                # Sníž počítadlo bomb u hráče po explozi
                self.player.remove_bomb()
                bomb.kill()
        
        # Update explosion sprites
        for explosion in self.explosions.copy():
            if explosion.update():  # Vrací True pokud má zmizet
                explosion.kill()
        
        # Update powerup sprites
        for powerup in self.powerups.copy():
            if powerup.update():  # Vrací True pokud má zmizet
                powerup.kill()
        
        # Update enemy sprites
        for enemy in self.enemies:
            enemy.update(self.game_map, self.grid_width, self.grid_height, self.player, pygame.sprite.Group(self.bombs, self.explosions))
    
    def check_game_collisions(self):
        """
        Processes collisions.
        If the player is hit by explosion or by the enemy he loses a live.
        If the player has 0 lives, the game and, player lost.
        If there are no destroyable blocks, player won.
        """
        # Kolize hráče
        self.lives, player_hit = check_collisions(self.player, self.enemies, 
                                                 self.explosions, self.lives, self.score)
        if player_hit:
            self.sound_effects['player_hit']['active'] = True
            self.sound_effects['player_hit']['timer'] = 20
            self.sounds['player_hit'].play()
            if self.lives <= 0:
                self.game_state = GameState.GAME_OVER
        
        # Sbírání powerupů
        collected_powerups = pygame.sprite.spritecollide(self.player, self.powerups, True)
        for powerup in collected_powerups:
            self.player.apply_powerup(powerup.powerup_type)
            # Zvukový efekt pro powerup (můžeme použít bomb_place sound)
            self.sounds['bomb_place'].play()
        
        # Kolize nepřátel s explozemi
        self.score, enemies_hit = check_enemy_explosions(self.enemies, self.explosions, self.score)
        if enemies_hit:
            self.sound_effects['enemy_hit']['active'] = True
            self.sound_effects['enemy_hit']['timer'] = 20
            self.sounds['enemy_hit'].play()
        
        # Kontrola vítězství - žádné zničitelné bloky
        if count_destructible_blocks(self.game_map) == 0:
            if self.game_state == GameState.STORY_PLAYING:
                # Story mode - pokračuj na další level nebo ukonči
                self.story_level += 1
                if self.story_level > STORY_TOTAL_LEVELS:
                    # Dokončena celá story
                    if self.score > self.story_high_score:
                        self.story_high_score = self.score
                        self.save_story_high_score()
                    self.game_state = GameState.STORY_COMPLETE
                else:
                    # Pokračuj na další level
                    self.biome = None
                    self.clear_sprites()
                    self.init_story_level()
            else:
                # Normální mode
                if self.score > self.high_score:
                    self.high_score = self.score
                    self.save_high_score()
                self.game_state = GameState.VICTORY
    
    def update_explosions(self):
        """Explosion animation"""
        # Update částic
        for particle in self.explosion_particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vy'] += 0.2  # Gravitace
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.explosion_particles.remove(particle)
        
        # Kreslení částic
        for particle in self.explosion_particles:
            alpha = max(0, particle['life'] * 8)
            if alpha > 0:
                color = (*particle['color'], min(255, alpha))
                size = max(1, particle['life'] // 10)
                pygame.draw.circle(self.screen, color[:3], (int(particle['x']), int(particle['y'])), size)
    
    def draw(self):
        """Function drawing screen content according to the state of the game (level, wellcome screen, gamover etc.)"""
        self.screen.fill((0, 0, 0))
        
        if self.game_state == GameState.INTRO:
            self.draw_intro()
        elif self.game_state == GameState.MENU_SCREEN:
            self.draw_menu_screen()
        elif self.game_state == GameState.MENU:
            self.draw_menu()
        elif self.game_state == GameState.PLAYING or self.game_state == GameState.STORY_PLAYING:
            self.draw_game()
        elif self.game_state == GameState.GAME_OVER:
            self.draw_game_over()
        elif self.game_state == GameState.VICTORY:
            self.draw_victory()
        elif self.game_state == GameState.STORY_COMPLETE:
            self.draw_story_complete()

        pygame.display.flip()
    
    def draw_intro(self):
        """Draws wellcome screen of the game"""
        # Fancy gradient background
        for y in range(self.HEIGHT):
            color_val = int(50 + (math.sin(y * 0.01 + time.time()) + 1) * 25)
            pygame.draw.line(self.screen, (0, 0, color_val), (0, y), (self.WIDTH, y))
        
        # Pulsující title
        pulse = math.sin(time.time() * 3) * 0.2 + 1
        font_size = int(72 * pulse)
        pulse_font = pygame.font.Font(None, font_size)
        
        # Stín
        shadow = pulse_font.render("BOOMER MAN", True, (100, 0, 0))
        shadow_rect = shadow.get_rect(center=(self.WIDTH//2 + 3, self.HEIGHT//2 + 3))
        self.screen.blit(shadow, shadow_rect)
        
        # Hlavní text
        title = pulse_font.render("BOOMER MAN", True, (255, 200, 0))
        rect = title.get_rect(center=(self.WIDTH//2, self.HEIGHT//2))
        self.screen.blit(title, rect)
        
        # Jiskry kolem
        for i in range(10):
            angle = time.time() * 2 + i * math.pi / 5
            x = self.WIDTH//2 + math.cos(angle) * 150
            y = self.HEIGHT//2 + math.sin(angle) * 80
            pygame.draw.circle(self.screen, (255, 255, 0), (int(x), int(y)), 3)
            
        # Pokyn pro kliknutí
        click_text = self.font.render("Klikni kamkoliv pro pokračování", True, (255, 255, 255))
        click_rect = click_text.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 + 150))
        
        # Blikání textu
        if int(time.time() * 2) % 2:
            self.screen.blit(click_text, click_rect)

    def change_used_sprites(self, is_menu = False):
        if is_menu:
            self.biome = None
            self.sprites = self.sprites_collection[0]
            self.bg_surface = self.bg_surface_collection[0]
            return

        if self.biome is None:
            self.biome = random.choice(list(Biome))
            self.sprites = self.sprites_collection[self.biome.value]
            self.bg_surface = self.bg_surface_collection[self.biome.value + 1]

    def draw_menu_screen(self):
        """
        Draws menu screen, where the user can choose game mode.
        Score game mode is one level, player must destroy the most destroyable blocks.
        Story mode is several levels the user must pass to win the game.
        """
        self.change_used_sprites(is_menu=True)

        # Dynamické pozadí s gradientem a efekty
        for y in range(self.HEIGHT):
            # Více vrstev gradientu pro bohatší vzhled
            wave1 = math.sin(y * 0.008 + time.time() * 0.5) * 20 + 20
            wave2 = math.cos(y * 0.012 + time.time() * 0.3) * 15 + 15
            wave3 = math.sin(y * 0.005 + time.time() * 0.8) * 10 + 10
            
            # Tmavší základní barva s jemnými vlnami
            color_r = int(10 + wave1 * 0.4)
            color_g = int(15 + wave2 * 0.3) 
            color_b = int(25 + wave3 * 0.6)
            
            pygame.draw.line(self.screen, (color_r, color_g, color_b), (0, y), (self.WIDTH, y))
        
        # Překrytí isometrického pozadí s průhledností
        bg_overlay = self.bg_surface.copy()
        bg_overlay.set_alpha(120)
        self.screen.blit(bg_overlay, (0, 0))
        
        # Jemné světelné efekty v pozadí
        for i in range(15):
            angle = time.time() * 0.3 + i * math.pi / 7.5
            x = self.WIDTH//2 + math.cos(angle) * (200 + i * 10)
            y = self.HEIGHT//2 + math.sin(angle) * (100 + i * 5)
            alpha = int((math.sin(time.time() * 2 + i) + 1) * 15)
            if alpha > 0:
                glow_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255, 255, 200, alpha), (10, 10), 10)
                self.screen.blit(glow_surf, (int(x) - 10, int(y) - 10))
        
        # Vylepšený title s více efekty
        pulse = math.sin(time.time() * 1.5) * 0.1 + 1
        
        # Více vrstev stínu pro hloubku
        for i in range(5, 0, -1):
            shadow_alpha = 150 - i * 25
            shadow_color = (50 - i * 8, 0, 0)
            shadow = self.big_font.render("BOOMER MAN", True, shadow_color)
            shadow_rect = shadow.get_rect(center=(self.WIDTH//2 + i * 2, self.HEIGHT//2 - 150 + i * 2))
            shadow_surface = pygame.Surface(shadow.get_size(), pygame.SRCALPHA)
            shadow_surface.blit(shadow, (0, 0))
            shadow_surface.set_alpha(shadow_alpha)
            self.screen.blit(shadow_surface, shadow_rect)
        
        # Hlavní titul s gradientovým efektem
        title_surface = pygame.Surface((600, 100), pygame.SRCALPHA)
        title_text = self.big_font.render("BOOMER MAN", True, (255, 220, 50))
        title_rect = title_text.get_rect(center=(300, 50))
        
        # Přidat záři kolem textu
        glow_surface = pygame.Surface((600, 100), pygame.SRCALPHA)
        for offset in range(1, 4):
            glow_text = self.big_font.render("BOOMER MAN", True, (255, 200, 0, 80 - offset * 20))
            for dx in [-offset, 0, offset]:
                for dy in [-offset, 0, offset]:
                    if dx != 0 or dy != 0:
                        glow_surface.blit(glow_text, (title_rect.x + dx, title_rect.y + dy))
        
        title_surface.blit(glow_surface, (0, 0))
        title_surface.blit(title_text, title_rect)
        
        # Aplikovat pulsování
        scaled_size = (int(600 * pulse), int(100 * pulse))
        scaled_title = pygame.transform.scale(title_surface, scaled_size)
        final_rect = scaled_title.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 150))
        self.screen.blit(scaled_title, final_rect)
        
        # Kreslení tlačítek
        self.play_button.draw(self.screen)
        self.story_button.draw(self.screen)

        # Ovládání
        controls = self.font.render("WASD/šipky - pohyb, MEZERNÍK - bomba", True, (200, 200, 200))
        controls_rect = controls.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 + 100))
        self.screen.blit(controls, controls_rect)
        
        # Dekorativní bomby v rozích
        bomb_positions = [(50, 50), (self.WIDTH-50, 50), (50, self.HEIGHT-50), (self.WIDTH-50, self.HEIGHT-50)]
        for pos in bomb_positions:
            bomb_sprite = self.sprites['bomb'].copy()
            pulse_bomb = math.sin(time.time() * 2 + pos[0] * 0.01) * 10 + 40
            scaled_bomb = pygame.transform.scale(bomb_sprite, (int(pulse_bomb), int(pulse_bomb)))
            bomb_rect = scaled_bomb.get_rect(center=pos)
            self.screen.blit(scaled_bomb, bomb_rect)
        
        # Autoři - levý dolní roh
        authors = [
            ("Karel Vrablik", "Game Developer & Game Design"),
            ("Iurii Pavlov", "Game Design & Quality Tester"),
            ("Enriko Hrcik", "Quality Tester & Game Director"),
            ("Jiri Kerner", "Game Director & Graphics Design"),
            ("Jakub Kucera", "Game Developer & Quality Tester")
        ]
        
        small_font = pygame.font.Font(None, 20)
        y_offset = self.HEIGHT - 120
        for author, roles in authors:
            author_text = small_font.render(f"{author}: {roles}", True, (150, 150, 150))
            self.screen.blit(author_text, (80, y_offset))
            y_offset += 22
    
    def draw_game(self):
        """Draws current level with its items."""
        # Screen shake efekt
        shake_x = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        shake_y = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        
        self.change_used_sprites()

        # Isometrické pozadí
        self.screen.blit(self.bg_surface, (shake_x, shake_y))
        
        # Render floor tiles and walls in isometric view
        render_list = []
        
        # Collect all tiles and objects for proper depth sorting
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                screen_x, screen_y = self.iso_utils.grid_to_screen(x, y)
                screen_x += self.camera_offset_x + shake_x
                screen_y += self.camera_offset_y + shake_y
                
                # Floor tile (always render)
                if self.game_map[y, x] == 0:
                    floor_rect = self.sprites['floor'].get_rect()
                    floor_rect.centerx = screen_x + self.iso_utils.half_tile_width
                    floor_rect.bottom = screen_y + self.iso_utils.tile_height + 40
                    render_list.append((y + x, 'floor', floor_rect))
                
                # Walls and destructible blocks
                if self.game_map[y, x] == 1:  # Stěna
                    wall_rect = self.sprites['wall'].get_rect()
                    wall_rect.centerx = screen_x + self.iso_utils.half_tile_width
                    wall_rect.bottom = screen_y + self.iso_utils.tile_height + 24
                    render_list.append((y + x, 'wall', wall_rect))
                elif self.game_map[y, x] == 2:  # Zničitelná stěna
                    brick_rect = self.sprites['brick'].get_rect()
                    brick_rect.centerx = screen_x + self.iso_utils.half_tile_width
                    brick_rect.bottom = screen_y + self.iso_utils.tile_height + 32
                    render_list.append((y + x, 'brick', brick_rect))
        
        # Add sprites to render list with proper sorting
        all_entities = list(self.all_sprites)
        sorted_entities = self.iso_utils.get_render_order(all_entities)
        
        for sprite in sorted_entities:
            adjusted_rect = sprite.rect.copy()
            adjusted_rect.x += self.camera_offset_x + shake_x
            adjusted_rect.y += self.camera_offset_y + shake_y
            render_depth = sprite.grid_y + sprite.grid_x + 0.5  # Slightly higher than tiles
            render_list.append((render_depth, 'sprite', sprite, adjusted_rect))
        
        # Sort and render everything
        render_list.sort(key=lambda item: item[0])
        
        for item in render_list:
            if item[1] == 'sprite':
                sprite, rect = item[2], item[3]
                self.screen.blit(sprite.image, rect)
            else:
                sprite_type, rect = item[1], item[2]
                self.screen.blit(self.sprites[sprite_type], rect)
        
        # Kreslení částic
        self.update_explosions()
        
        # Vylepšený UI panel s moderním designem
        powerups_active = (self.player.speed_boost_timer > 0 or self.player.bigger_explosion_timer > 0)
        story_mode = (self.game_state == GameState.STORY_PLAYING)
        immunity_active = (self.player.immunity_timer > 0)
        
        # Výpočet výšky panelu podle obsahu - reaktivní design
        base_height = 130  # Základní výška pro skóre, životy, bomby
        
        # Přidat místo pro bomb progress bar
        if len(self.bombs) > 0:
            base_height += 45  # Label + progress bar + spacing
            
        if story_mode:
            base_height += 30
            
        if powerups_active:
            base_height += 25 * (int(self.player.speed_boost_timer > 0) + int(self.player.bigger_explosion_timer > 0))
            
        if immunity_active:
            base_height += 50  # Text + progress bar + spacing
        
        ui_width = 280
        ui_height = base_height
        
        # Gradientní pozadí panelu
        ui_bg = pygame.Surface((ui_width, ui_height), pygame.SRCALPHA)
        
        # Vytvoření gradientu (tmavší nahoře, světlejší dole)
        for y in range(ui_height):
            alpha = 180 - (y * 40 // ui_height)  # Gradient průhlednosti
            color_intensity = 20 + (y * 15 // ui_height)  # Gradient barvy
            pygame.draw.line(ui_bg, (color_intensity, color_intensity, color_intensity + 10, alpha), 
                           (0, y), (ui_width, y))
        
        # Fancy okraje s více vrstvami pro 3D efekt
        # Vnější světlý okraj
        pygame.draw.rect(ui_bg, (200, 200, 220, 100), (0, 0, ui_width, ui_height), 3, border_radius=12)
        # Střední okraj
        pygame.draw.rect(ui_bg, (150, 150, 170, 150), (2, 2, ui_width-4, ui_height-4), 2, border_radius=10)
        # Vnitřní tmavý okraj
        pygame.draw.rect(ui_bg, (80, 80, 90, 200), (4, 4, ui_width-8, ui_height-8), 1, border_radius=8)
        
        # Přidat jemný glow efekt kolem panelu
        glow_surface = pygame.Surface((ui_width + 20, ui_height + 20), pygame.SRCALPHA)
        for i in range(10, 0, -1):
            glow_alpha = 15 - i
            pygame.draw.rect(glow_surface, (100, 150, 255, glow_alpha), 
                           (10-i, 10-i, ui_width + i*2, ui_height + i*2), border_radius=12+i)
        
        self.screen.blit(glow_surface, (5, 5))
        self.screen.blit(ui_bg, (15, 15))
        
        # Pozice pro obsah
        x_margin = 25
        y_pos = 25
        
        # Skóre s textem
        score_text = self.font.render(f"Skóre: {self.score}", True, (255, 215, 0))  # Zlatá
        self.screen.blit(score_text, (x_margin, y_pos))
        y_pos += 30
        
        # Životy s textem  
        lives_text = self.font.render(f"Životy: {self.lives}", True, (255, 100, 100))
        self.screen.blit(lives_text, (x_margin, y_pos))
        y_pos += 30
        
        # Bomby s lepším zobrazením
        if self.player.unlimited_bombs_timer > 0:
            bombs_text = self.font.render(f"Bomby: ∞ ({self.player.unlimited_bombs_timer // 15 + 1}s)", True, (255, 255, 0))
        else:
            bombs_text = self.font.render(f"Bomby: {self.player.current_bomb_count}/{self.player.max_bombs}", True, (255, 200, 100))
        self.screen.blit(bombs_text, (x_margin, y_pos))
        y_pos += 30
        
        # Progress bar pro bomby (uvnitř panelu)
        if len(self.bombs) > 0:
            bomb_label = self.font.render("Bomba:", True, (200, 200, 200))
            self.screen.blit(bomb_label, (x_margin, y_pos))
            y_pos += 20
            
            bomb_timer = min(bomb.timer for bomb in self.bombs)
            progress = bomb_timer / 75.0
            # Pozadí progress baru
            pygame.draw.rect(self.screen, (60, 20, 20), (x_margin, y_pos, 180, 12), border_radius=6)
            # Aktivní část
            pygame.draw.rect(self.screen, (255, 80, 80), (x_margin, y_pos, int(180 * progress), 12), border_radius=6)
            # Okraj
            pygame.draw.rect(self.screen, (200, 200, 200), (x_margin, y_pos, 180, 12), 2, border_radius=6)
            y_pos += 25
        
        # Level info pro story mode
        if story_mode:
            level_text = self.font.render(f"Level: {self.story_level}/{STORY_TOTAL_LEVELS}", True, (150, 255, 150))
            self.screen.blit(level_text, (x_margin, y_pos))
            y_pos += 30
        
        # Powerupy
        if self.player.speed_boost_timer > 0:
            speed_text = self.font.render(f"Rychlost: ({self.player.speed_boost_timer // 15 + 1}s)", True, (100, 255, 100))
            self.screen.blit(speed_text, (x_margin, y_pos))
            y_pos += 25
            
        if self.player.bigger_explosion_timer > 0:
            explosion_text = self.font.render(f"Velká exploze: ({self.player.bigger_explosion_timer // 15 + 1}s)", True, (255, 100, 255))
            self.screen.blit(explosion_text, (x_margin, y_pos))
            y_pos += 25
        
        # Imunita s progress barem
        if immunity_active:
            immunity_text = self.font.render("Imunita:", True, (100, 200, 255))
            self.screen.blit(immunity_text, (x_margin, y_pos))
            y_pos += 20
            
            # Progress bar pro imunitu
            immunity_progress = self.player.immunity_timer / 120.0
            pygame.draw.rect(self.screen, (20, 40, 80), (x_margin, y_pos, 180, 10), border_radius=5)
            pygame.draw.rect(self.screen, (100, 200, 255), (x_margin, y_pos, int(180 * immunity_progress), 10), border_radius=5)
            pygame.draw.rect(self.screen, (200, 200, 200), (x_margin, y_pos, 180, 10), 1, border_radius=5)
        
        
        # Snížení screen shake
        if self.screen_shake > 0:
            self.screen_shake -= 1
    
    def load_high_score(self):
        """Načte nejlepší skóre ze souboru"""
        try:
            with open('high_score.txt', 'r') as f:
                return int(f.read().strip())
        except:
            return 0
    
    def save_high_score(self):
        """Uloží nejlepší skóre do souboru"""
        try:
            with open('high_score.txt', 'w') as f:
                f.write(str(self.high_score))
        except:
            pass
    
    def load_story_high_score(self):
        """Načte nejlepší story skóre ze souboru"""
        try:
            with open('story_high_score.txt', 'r') as f:
                return int(f.read().strip())
        except:
            return 0

    def save_story_high_score(self):
        """Uloží nejlepší story skóre do souboru"""
        try:
            with open('story_high_score.txt', 'w') as f:
                f.write(str(self.story_high_score))
        except:
            pass

    def clear_sprites(self):
        """Vymaže všechny sprite skupiny"""
        self.all_sprites.empty()
        self.players.empty()
        self.enemies.empty()
        self.bombs.empty()
        self.explosions.empty()
        self.powerups.empty()
        self.explosion_particles = []
        self.screen_shake = 0

    def restart_game(self):
        """Restartuje hru"""
        self.score = 0
        self.lives = 3
        self.clear_sprites()
        self.biome = None
        self.init_game_world()
        self.game_state = GameState.PLAYING

    def start_story_mode(self):
        """Začne Story mode"""
        self.score = 0
        self.lives = 3
        self.story_level = 1
        self.is_story_mode = True
        self.all_sprites.empty()
        self.players.empty()
        self.enemies.empty()
        self.bombs.empty()
        self.explosions.empty()
        self.powerups.empty()
        self.explosion_particles = []
        self.screen_shake = 0
        self.biome = None
        self.init_story_level()
        self.game_state = GameState.STORY_PLAYING

    def init_story_level(self):
        """Inicializuje nový level pro Story mode"""
        self.grid_width = 15
        self.grid_height = 11

        # Vytvoření story mapy podle levelu
        self.game_map = create_story_map(self.story_level, self.grid_width, self.grid_height)

        # Vytvoření hráče
        self.player = Player(1, 1, self.iso_utils)
        # Nastaví počet bomb podle levelu + 1 jako default
        self.player.set_max_bombs_for_level(self.story_level)
        self.player.max_bombs += 1  # +1 bomba navíc
        self.all_sprites.add(self.player)
        self.players.add(self.player)

        # Nepřátelé - počet se zvyšuje s levelem
        enemy_count = min(3, 1 + (self.story_level - 1) // 2)
        enemy_positions = [(self.grid_width-2, self.grid_height-2),
                          (self.grid_width-2, 2), (2, self.grid_height-2)]

        for i in range(enemy_count):
            if i < len(enemy_positions):
                x, y = enemy_positions[i]
                enemy = Enemy(x, y, self.iso_utils)
                self.all_sprites.add(enemy)
                self.enemies.add(enemy)

        # Inicializace efektů
        self.bomb_pulse_timer = 0
        self.explosion_particles = []
        self.screen_shake = 0

        # Mock zvukové efekty
        self.sound_effects = {
            'bomb_place': {'active': False, 'timer': 0},
            'explosion': {'active': False, 'timer': 0},
            'enemy_hit': {'active': False, 'timer': 0},
            'player_hit': {'active': False, 'timer': 0}
        }
    
    def draw_game_over(self):
        """Draws game over screen. Used when player loses. User can go back to menu or restart the game."""
        # Tmavé pozadí s červenými blesky
        for y in range(self.HEIGHT):
            color_val = int(20 + (math.sin(y * 0.03 + time.time() * 3) + 1) * 15)
            color = (color_val + 30, color_val//3, color_val//3)
            pygame.draw.line(self.screen, color, (0, y), (self.WIDTH, y))
        
        # Padající "slzy" efekt
        for i in range(30):
            x = (i * 97 + int(time.time() * 60)) % self.WIDTH
            y = (i * 51 + int(time.time() * 120)) % self.HEIGHT
            size = (i % 3) + 1
            color = (100, 100, 150)
            pygame.draw.circle(self.screen, color, (x, y), size)
        
        # Pulsující game over text
        pulse = math.sin(time.time() * 2) * 0.2 + 1
        font_size = int(72 * pulse)
        pulse_font = pygame.font.Font(None, font_size)
        
        # Stín
        shadow = pulse_font.render("GAME OVER", True, (100, 0, 0))
        shadow_rect = shadow.get_rect(center=(self.WIDTH//2 + 3, self.HEIGHT//2 - 97))
        self.screen.blit(shadow, shadow_rect)
        
        # Hlavní text
        game_over_text = pulse_font.render("GAME OVER", True, (255, 50, 50))
        game_over_rect = game_over_text.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 100))
        self.screen.blit(game_over_text, game_over_rect)
        
        # Skóre s rámečkem
        score_bg = pygame.Surface((350, 80), pygame.SRCALPHA)
        score_bg.fill((50, 50, 50, 200))
        pygame.draw.rect(score_bg, (255, 50, 50), (0, 0, 350, 80), 3)
        score_bg_rect = score_bg.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 20))
        self.screen.blit(score_bg, score_bg_rect)
        
        # Aktuální skóre
        current_score_text = self.font.render(f"Vaše skóre: {self.score}", True, (255, 255, 255))
        current_score_rect = current_score_text.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 35))
        self.screen.blit(current_score_text, current_score_rect)
        
        # Nejlepší skóre
        high_score_text = self.font.render(f"Nejlepší: {self.high_score}", True, (200, 200, 200))
        high_score_rect = high_score_text.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 5))
        self.screen.blit(high_score_text, high_score_rect)
        
        # Kreslení tlačítek
        self.restart_button.draw(self.screen)
        self.game_over_menu_button.draw(self.screen)
        
        # Motivační text
        failure_text = self.font.render("Zkuste to znovu!", True, (255, 255, 255))
        failure_rect = failure_text.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 + 120))
        self.screen.blit(failure_text, failure_rect)
    
    def draw_victory(self):
        """Draws Win screen after scoremode. Used when player destroys all blocks in score mode."""
        # Zlaté pozadí s konfety efektem
        for y in range(self.HEIGHT):
            color_val = int(80 + (math.sin(y * 0.02 + time.time() * 2) + 1) * 30)
            color = (color_val, color_val//2, 0)
            pygame.draw.line(self.screen, color, (0, y), (self.WIDTH, y))
        
        # Konfety částice
        for i in range(50):
            x = (i * 73 + int(time.time() * 100)) % self.WIDTH
            y = (i * 47 + int(time.time() * 80)) % self.HEIGHT
            size = (i % 5) + 2
            colors = [(255, 255, 0), (255, 100, 100), (100, 255, 100), (100, 100, 255), (255, 255, 255)]
            color = colors[i % len(colors)]
            pygame.draw.circle(self.screen, color, (x, y), size)
        
        # Pulsující victory text
        pulse = math.sin(time.time() * 2) * 0.3 + 1
        font_size = int(72 * pulse)
        pulse_font = pygame.font.Font(None, font_size)
        
        # Stín
        shadow = pulse_font.render("VÍTĚZSTVÍ!", True, (100, 50, 0))
        shadow_rect = shadow.get_rect(center=(self.WIDTH//2 + 3, self.HEIGHT//2 - 97))
        self.screen.blit(shadow, shadow_rect)
        
        # Hlavní text
        victory_text = pulse_font.render("VÍTĚZSTVÍ!", True, (255, 215, 0))
        victory_rect = victory_text.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 100))
        self.screen.blit(victory_text, victory_rect)
        
        # Skóre s rámečkem
        score_bg = pygame.Surface((350, 80), pygame.SRCALPHA)
        score_bg.fill((50, 50, 50, 200))
        pygame.draw.rect(score_bg, (255, 215, 0), (0, 0, 350, 80), 3)
        score_bg_rect = score_bg.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 20))
        self.screen.blit(score_bg, score_bg_rect)
        
        # Aktuální skóre
        current_score_text = self.font.render(f"Vaše skóre: {self.score}", True, (255, 255, 255))
        current_score_rect = current_score_text.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 35))
        self.screen.blit(current_score_text, current_score_rect)
        
        # Nejlepší skóre
        if self.score == self.high_score and self.score > 0:
            high_score_text = self.font.render("🏆 NOVÝ REKORD! 🏆", True, (255, 215, 0))
        else:
            high_score_text = self.font.render(f"Nejlepší: {self.high_score}", True, (200, 200, 200))
        high_score_rect = high_score_text.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 5))
        self.screen.blit(high_score_text, high_score_rect)
        
        # Kreslení tlačítek
        self.play_again_button.draw(self.screen)
        self.menu_button.draw(self.screen)
        
        # Gratuláční text
        congrats_text = self.font.render("Zničili jste všechny překážky!", True, (255, 255, 255))
        congrats_rect = congrats_text.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 + 120))
        self.screen.blit(congrats_text, congrats_rect)

    def draw_story_complete(self):
        """Draws Win screen after story mode. Used when player sucessfully passes all levels."""
        # Úžasné pozadí s duhovými vlnami
        for y in range(self.HEIGHT):
            wave1 = math.sin(y * 0.01 + time.time() * 2) * 30 + 30
            wave2 = math.cos(y * 0.015 + time.time() * 1.5) * 20 + 20
            color_r = int(100 + wave1)
            color_g = int(50 + wave2)
            color_b = int(150 + math.sin(y * 0.02 + time.time()) * 50)
            pygame.draw.line(self.screen, (color_r, color_g, color_b), (0, y), (self.WIDTH, y))

        # Padající hvězdy efekt
        for i in range(100):
            x = (i * 37 + int(time.time() * 80)) % self.WIDTH
            y = (i * 71 + int(time.time() * 60)) % self.HEIGHT
            size = (i % 4) + 2
            brightness = (math.sin(i + time.time() * 3) + 1) * 127.5
            color = (int(brightness), int(brightness), 255)
            pygame.draw.circle(self.screen, color, (x, y), size)

        # Pulsující story complete text
        pulse = math.sin(time.time() * 2) * 0.4 + 1
        font_size = int(72 * pulse)
        pulse_font = pygame.font.Font(None, font_size)

        # Stín
        shadow = pulse_font.render("STORY DOKONČENA!", True, (50, 0, 100))
        shadow_rect = shadow.get_rect(center=(self.WIDTH//2 + 3, self.HEIGHT//2 - 97))
        self.screen.blit(shadow, shadow_rect)

        # Hlavní text
        complete_text = pulse_font.render("STORY DOKONČENA!", True, (200, 100, 255))
        complete_rect = complete_text.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 100))
        self.screen.blit(complete_text, complete_rect)

        # Skóre s rámečkem
        score_bg = pygame.Surface((350, 80), pygame.SRCALPHA)
        score_bg.fill((50, 50, 50, 200))
        pygame.draw.rect(score_bg, (200, 100, 255), (0, 0, 350, 80), 3)
        score_bg_rect = score_bg.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 20))
        self.screen.blit(score_bg, score_bg_rect)

        # Finální skóre
        final_score_text = self.font.render(f"Finální skóre: {self.score}", True, (255, 255, 255))
        final_score_rect = final_score_text.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 35))
        self.screen.blit(final_score_text, final_score_rect)

        # Story nejlepší skóre
        if self.score == self.story_high_score and self.score > 0:
            high_score_text = self.font.render("🏆 NOVÝ STORY REKORD! 🏆", True, (200, 100, 255))
        else:
            high_score_text = self.font.render(f"Story rekord: {self.story_high_score}", True, (200, 200, 200))
        high_score_rect = high_score_text.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 5))
        self.screen.blit(high_score_text, high_score_rect)

        # Kreslení tlačítek
        self.play_again_button.draw(self.screen)
        self.menu_button.draw(self.screen)

        # Gratuláční text
        congrats_text = self.font.render(f"Prošli jste všech {STORY_TOTAL_LEVELS} levelů!", True, (255, 255, 255))
        congrats_rect = congrats_text.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 + 120))
        self.screen.blit(congrats_text, congrats_rect)

    def run(self):
        """
        Main loop of the game.

        1. events are handled.
        2. all sprites are updated
        3. screen is redrawn
        4. fixed FPS
        """
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.FPS)
        
        pygame.quit()