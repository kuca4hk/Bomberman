import numpy as np
import pygame
import random
from domain.entity.explosion import Explosion
from utils.isometric_utils import IsometricUtils


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
    for i in range(2, grid_height - 1, 2):
        for j in range(2, grid_width - 1, 2):
            game_map[i, j] = 1

    # Náhodné zničitelné stěny
    for i in range(1, grid_height - 1):
        for j in range(1, grid_width - 1):
            if game_map[i, j] == 0 and np.random.random() < 0.3:
                # Nechat volné místo kolem hráče
                if not (i <= 2 and j <= 2):
                    game_map[i, j] = 2

    return game_map


def create_isometric_sprites(iso_utils):
    """Vytvoří isometrické sprite objekty pro různé herní prvky"""
    
    spritesheet_path = "/Users/admin/cursor/Bomberman/assets/spritesheets/tinyBlocks_NOiL_1.1update.png"
    spritesheet = pygame.image.load(spritesheet_path).convert_alpha()
    
    sprite_width = spritesheet.get_width() // 6
    sprite_height = spritesheet.get_height() // 6
    
    sprites = {}
    for row in range(6):
        for col in range(6):
            sprite = pygame.transform.scale(spritesheet.subsurface((col * sprite_width, row * sprite_height, sprite_width, sprite_height)), (sprite_width * 4, sprite_height * 4))
            sprites[(row, col)] = sprite
            
    used_sprites = {
        'wall': sprites[(5, 1)],
        'brick': sprites[(1, 1)],
        'bomb': iso_utils.create_bomb_sprite(),
        'floor': iso_utils.create_isometric_tile((60, 80, 40), 1, False)
    }

    return used_sprites


def create_isometric_background(screen_width, screen_height):
    """Vytvoří isometrické pozadí"""
    bg_surface = pygame.Surface((screen_width, screen_height))
    # Gradient background
    for y in range(screen_height):
        color_val = int(30 + (y / screen_height) * 40)
        color = (color_val // 2, color_val, color_val // 3)
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
    """Zkontroluje kolize mezi hráčem a nepřáteli/explozemi pomocí pygame.sprite.collide"""
    collision_occurred = False

    # Zkontroluj imunitu hráče
    if player.immunity_timer > 0:
        return lives, collision_occurred

    # Kolize s nepřáteli pomocí pygame.sprite.spritecollide
    collided_enemies = pygame.sprite.spritecollide(player, enemies, False, pygame.sprite.collide_rect)
    if collided_enemies:
        lives -= 1
        collision_occurred = True
        player.immunity_timer = 120  # 8 sekund imunity při 15 FPS

    # Kolize s explozemi pomocí pygame.sprite.spritecollide
    if not collision_occurred:
        collided_explosions = pygame.sprite.spritecollide(player, explosions, False, pygame.sprite.collide_rect)
        if collided_explosions:
            lives -= 1
            collision_occurred = True
            player.immunity_timer = 120  # 8 sekund imunity při 15 FPS

    # Reset pozice hráče při kolizi
    if collision_occurred and lives > 0:
        player.grid_x, player.grid_y = 1, 1
        player.update_position()

    return lives, collision_occurred


def check_enemy_explosions(enemies, explosions, score):
    """Zkontroluje kolize nepřátel s explozemi pomocí pygame.sprite.collide"""
    enemies_hit = []

    for enemy in enemies.copy():
        # Použijeme pygame.sprite.spritecollide pro přesnější kolize
        collided_explosions = pygame.sprite.spritecollide(enemy, explosions, False, pygame.sprite.collide_rect)
        if collided_explosions:
            enemy.kill()
            enemies_hit.append(enemy)
            score += 100

    return score, enemies_hit


def count_destructible_blocks(game_map):
    """Spočítá počet zbývajících zničitelných bloků (hodnota 2) na mapě"""
    return np.sum(game_map == 2)