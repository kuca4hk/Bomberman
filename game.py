import pygame
import time
import math
import random

from domain.entity.bomb import Bomb
from domain.entity.enemy import Enemy
from domain.entity.player import Player
from ui_components import GameState, Button
from utils.isometric_utils import IsometricUtils
from game_logic import (create_game_map, create_isometric_sprites, create_isometric_background, 
                       explode_bomb, check_collisions, check_enemy_explosions, count_destructible_blocks,
                       create_story_map, STORY_TOTAL_LEVELS)


class BoomerManGame:
    def __init__(self):
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
        
        # UI tlačítka pro menu
        self.play_button = Button(self.WIDTH//2 - 100, self.HEIGHT//2 - 30, 200, 50, 
                                 "HRÁT", self.font, (50, 100, 50), (255, 255, 255))
        self.story_button = Button(self.WIDTH//2 - 100, self.HEIGHT//2 + 30, 200, 50, 
                                  "STORY", self.font, (100, 50, 150), (255, 255, 255))
        
        # Victory screen tlačítka
        self.play_again_button = Button(self.WIDTH//2 - 200, self.HEIGHT//2 + 50, 180, 50, 
                                       "Hrát znova", self.font, (50, 150, 50), (255, 255, 255))
        self.menu_button = Button(self.WIDTH//2 + 20, self.HEIGHT//2 + 50, 180, 50, 
                                 "Menu", self.font, (150, 50, 50), (255, 255, 255))
        
        # Game over screen tlačítka
        self.restart_button = Button(self.WIDTH//2 - 200, self.HEIGHT//2 + 50, 180, 50, 
                                    "Restart", self.font, (150, 50, 50), (255, 255, 255))
        self.game_over_menu_button = Button(self.WIDTH//2 + 20, self.HEIGHT//2 + 50, 180, 50, 
                                           "Menu", self.font, (100, 100, 100), (255, 255, 255))
        
        self.sprites = create_isometric_sprites(self.iso_utils)
        self.bg_surface = create_isometric_background(self.WIDTH, self.HEIGHT)
        self.init_game_world()
    
    def init_game_world(self):
        self.grid_width = 15
        self.grid_height = 11
        
        # Vytvoření herního pole
        self.game_map = create_game_map(self.grid_width, self.grid_height)
        
        # Vytvoření hráče a nepřátel jako sprite objekty
        self.player = Player(1, 1, self.iso_utils)
        self.all_sprites.add(self.player)
        self.players.add(self.player)
        
        # Nepřátelé
        enemy = Enemy(self.grid_width-2, self.grid_height-2, self.iso_utils)
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
        bomb_pos = (self.player.grid_x, self.player.grid_y)
        # Zkontroluj, jestli na pozici už není bomba
        bomb_exists = any(bomb.grid_x == bomb_pos[0] and bomb.grid_y == bomb_pos[1] 
                         for bomb in self.bombs)
        
        if not bomb_exists:
            bomb = Bomb(bomb_pos[0], bomb_pos[1], self.iso_utils)
            self.bombs.add(bomb)
            self.all_sprites.add(bomb)
            # Nastav pozici bomby pro bomb passing mechanismus
            self.player.set_bomb_placed_position(bomb_pos[0], bomb_pos[1])
            # Mock zvukový efekt
            self.sound_effects['bomb_place']['active'] = True
            self.sound_effects['bomb_place']['timer'] = 20
    
    def update_sprites(self):
        # Update bomb sprites
        for bomb in self.bombs.copy():
            if bomb.update():  # Vrací True pokud má explodovat
                particles, score_gain = explode_bomb(bomb, self.game_map, self.grid_width, 
                                                   self.grid_height, self.iso_utils, 
                                                   self.explosions, self.all_sprites)
                self.explosion_particles.extend(particles)
                self.score += score_gain
                self.screen_shake = 8
                self.sound_effects['explosion']['active'] = True
                self.sound_effects['explosion']['timer'] = 30
                bomb.kill()
        
        # Update explosion sprites
        for explosion in self.explosions.copy():
            if explosion.update():  # Vrací True pokud má zmizet
                explosion.kill()
        
        # Update enemy sprites
        for enemy in self.enemies:
            enemy.update(self.game_map, self.grid_width, self.grid_height, self.player, pygame.sprite.Group(self.bombs, self.explosions))
    
    def check_game_collisions(self):
        # Kolize hráče
        self.lives, player_hit = check_collisions(self.player, self.enemies, 
                                                 self.explosions, self.lives, self.score)
        if player_hit:
            self.sound_effects['player_hit']['active'] = True
            self.sound_effects['player_hit']['timer'] = 20
            if self.lives <= 0:
                self.game_state = GameState.GAME_OVER
        
        # Kolize nepřátel s explozemi
        self.score, enemies_hit = check_enemy_explosions(self.enemies, self.explosions, self.score)
        if enemies_hit:
            self.sound_effects['enemy_hit']['active'] = True
            self.sound_effects['enemy_hit']['timer'] = 20
        
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
                    self.clear_sprites()
                    self.init_story_level()
            else:
                # Normální mode
                if self.score > self.high_score:
                    self.high_score = self.score
                    self.save_high_score()
                self.game_state = GameState.VICTORY
    
    def update_explosions(self):
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
    
    def draw_menu_screen(self):
        # Isometrické pozadí
        self.screen.blit(self.bg_surface, (0, 0))
        
        # Stín pro title
        shadow = self.big_font.render("BOOMER MAN", True, (100, 0, 0))
        shadow_rect = shadow.get_rect(center=(self.WIDTH//2 + 3, self.HEIGHT//2 - 147))
        self.screen.blit(shadow, shadow_rect)
        
        # Gradient title
        title = self.big_font.render("BOOMER MAN", True, (255, 200, 0))
        title_rect = title.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 150))
        self.screen.blit(title, title_rect)
        
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
    
    def draw_menu(self):
        pass  # Nepoužívá se
    
    def draw_game(self):
        # Screen shake efekt
        shake_x = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        shake_y = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        
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
                    floor_rect.bottom = screen_y + self.iso_utils.tile_height
                    render_list.append((y + x, 'floor', floor_rect))
                
                # Walls and destructible blocks
                if self.game_map[y, x] == 1:  # Stěna
                    wall_rect = self.sprites['wall'].get_rect()
                    wall_rect.centerx = screen_x + self.iso_utils.half_tile_width
                    wall_rect.bottom = screen_y + self.iso_utils.tile_height
                    render_list.append((y + x, 'wall', wall_rect))
                elif self.game_map[y, x] == 2:  # Zničitelná stěna
                    brick_rect = self.sprites['brick'].get_rect()
                    brick_rect.centerx = screen_x + self.iso_utils.half_tile_width
                    brick_rect.bottom = screen_y + self.iso_utils.tile_height
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
        
        # Fancy UI s pozadím - větší pro immunity bar
        ui_height = 125 if self.player.immunity_timer > 0 else 90
        ui_bg = pygame.Surface((200, ui_height), pygame.SRCALPHA)
        ui_bg.fill((0, 0, 0, 150))
        pygame.draw.rect(ui_bg, (100, 100, 100), (0, 0, 200, ui_height), 2)
        self.screen.blit(ui_bg, (10, 10))
        
        score_text = self.font.render(f"Skóre: {self.score}", True, (255, 255, 0))
        self.screen.blit(score_text, (20, 20))
        
        lives_text = self.font.render(f"Životy: {self.lives}", True, (255, 100, 100))
        self.screen.blit(lives_text, (20, 50))
        
        # Story mode UI - zobraz level informace
        if self.game_state == GameState.STORY_PLAYING:
            level_text = self.font.render(f"Level: {self.story_level}/{STORY_TOTAL_LEVELS}", True, (255, 255, 255))
            self.screen.blit(level_text, (220, 20))
        
        # Progress bar pro bomby
        if len(self.bombs) > 0:
            bomb_timer = min(bomb.timer for bomb in self.bombs)
            progress = bomb_timer / 180.0
            pygame.draw.rect(self.screen, (100, 0, 0), (20, 75, 160, 10))
            pygame.draw.rect(self.screen, (255, 0, 0), (20, 75, int(160 * progress), 10))
        
        # Progress bar pro imunitu hráče
        if self.player.immunity_timer > 0:
            immunity_progress = self.player.immunity_timer / 120.0
            pygame.draw.rect(self.screen, (0, 0, 100), (20, 90, 160, 10))
            pygame.draw.rect(self.screen, (0, 150, 255), (20, 90, int(160 * immunity_progress), 10))
            
            # Text pro imunitu
            immunity_text = self.font.render("Imunita", True, (0, 150, 255))
            self.screen.blit(immunity_text, (20, 105))
        
        # Mock vizuální indikace zvukových efektů
        effect_y = 130 if self.player.immunity_timer > 0 else 95
        for effect_name, effect in self.sound_effects.items():
            if effect['active']:
                alpha = min(255, effect['timer'] * 12)
                color_map = {
                    'bomb_place': (0, 255, 0),
                    'explosion': (255, 100, 0),
                    'enemy_hit': (255, 255, 0),
                    'player_hit': (255, 0, 0)
                }
                color = color_map.get(effect_name, (255, 255, 255))
                text = self.font.render(f"♪ {effect_name}", True, (*color, alpha))
                self.screen.blit(text, (220, effect_y))
                effect_y += 25
        
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
        self.explosion_particles = []
        self.screen_shake = 0

    def restart_game(self):
        """Restartuje hru"""
        self.score = 0
        self.lives = 3
        self.clear_sprites()
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
        self.explosion_particles = []
        self.screen_shake = 0
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
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.FPS)
        
        pygame.quit()