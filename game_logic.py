import numpy as np
import pygame
import random
from entities import Explosion
from isometric_utils import IsometricUtils


def create_game_map(grid_width, grid_height):
    """Vytvoří herní mapu s stěnami a zničitelnými objekty"""
    game_map = np.zeros((grid_height, grid_width), dtype=int)
    
    # 0 = prázdné, 1 = stěna, 2 = zničitelná stěna
    # Okraje jsou stěny
    game_map[0, :] = 1
    game_map[-1, :] = 1
    game_map[:, 0] = 1
    game_map[:, -1] = 1
    
    # Vnitřní stěny (každý druhý sudý řádek a sloupec)
    for i in range(2, grid_height-1, 2):
        for j in range(2, grid_width-1, 2):
            game_map[i, j] = 1
    
    # Náhodné zničitelné stěny
    for i in range(1, grid_height-1):
        for j in range(1, grid_width-1):
            if game_map[i, j] == 0 and np.random.random() < 0.3:
                # Nechat volné místo kolem hráče
                if not (i <= 2 and j <= 2):
                    game_map[i, j] = 2
    
    return game_map


def create_isometric_sprites(iso_utils):
    """Vytvoří isometrické sprite objekty pro různé herní prvky"""
    sprites = {}
    
    # Stěna - kamenný blok
    sprites['wall'] = iso_utils.create_isometric_cube((120, 120, 120), 1)
    
    # Zničitelná stěna - cihlový blok
    sprites['brick'] = iso_utils.create_isometric_cube((139, 69, 19), 1)
    
    # Bomba pro dekorace
    sprites['bomb'] = iso_utils.create_bomb_sprite()
    
    # Podlaha
    sprites['floor'] = iso_utils.create_isometric_tile((60, 80, 40), 1, False)
    
    return sprites


def create_isometric_background(screen_width, screen_height):
    """Vytvoří isometrické pozadí"""
    bg_surface = pygame.Surface((screen_width, screen_height))
    # Gradient background
    for y in range(screen_height):
        color_val = int(30 + (y / screen_height) * 40)
        color = (color_val//2, color_val, color_val//3)
        pygame.draw.line(bg_surface, color, (0, y), (screen_width, y))
    return bg_surface


def explode_bomb(bomb, game_map, grid_width, grid_height, iso_utils, explosions_group, all_sprites_group):
    """Zpracuje explozi bomby a vytvoří exploze ve všech směrech"""
    x, y = bomb.grid_x, bomb.grid_y
    power = bomb.power
    explosion_particles = []
    score_gained = 0
    
    # Střed exploze
    explosion = Explosion(x, y, iso_utils)
    explosions_group.add(explosion)
    all_sprites_group.add(explosion)
    
    # Exploze ve všech směrech
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    for dx, dy in directions:
        for i in range(1, power + 1):
            nx, ny = x + dx * i, y + dy * i
            if 0 <= nx < grid_width and 0 <= ny < grid_height:
                if game_map[ny, nx] == 1:  # Neznič. stěna
                    break
                if game_map[ny, nx] == 2:  # Zničitelná stěna
                    game_map[ny, nx] = 0
                    score_gained += 10
                    # Isometrické částice při destrukci
                    screen_x, screen_y = iso_utils.grid_to_screen(nx, ny)
                    for _ in range(8):
                        explosion_particles.append({
                            'x': screen_x + random.randint(-20, 20),
                            'y': screen_y + random.randint(-20, 20),
                            'vx': random.uniform(-4, 4),
                            'vy': random.uniform(-6, 2),
                            'life': 40,
                            'color': (139, 69, 19)
                        })
                    break
                explosion = Explosion(nx, ny, iso_utils)
                explosions_group.add(explosion)
                all_sprites_group.add(explosion)
    
    return explosion_particles, score_gained


def check_collisions(player, enemies, explosions, lives, score):
    """Zkontroluje kolize mezi hráčem a nepřáteli/explozemi"""
    collision_occurred = False
    
    # Kolize s nepřáteli
    for enemy in enemies:
        if player.grid_x == enemy.grid_x and player.grid_y == enemy.grid_y:
            lives -= 1
            collision_occurred = True
            break
    
    # Kolize s explozemi
    if not collision_occurred:
        for explosion in explosions:
            if player.grid_x == explosion.grid_x and player.grid_y == explosion.grid_y:
                lives -= 1
                collision_occurred = True
                break
    
    # Reset pozice hráče při kolizi
    if collision_occurred and lives > 0:
        player.grid_x, player.grid_y = 1, 1
        player.update_position()
    
    return lives, collision_occurred


def check_enemy_explosions(enemies, explosions, score):
    """Zkontroluje kolize nepřátel s explozemi"""
    enemies_hit = []
    
    for enemy in enemies.copy():
        for explosion in explosions:
            if enemy.grid_x == explosion.grid_x and enemy.grid_y == explosion.grid_y:
                enemy.kill()
                enemies_hit.append(enemy)
                score += 100
                break
    
    return score, enemies_hit