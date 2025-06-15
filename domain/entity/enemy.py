import traceback

import pygame
import math
import random

import domain.entity.bomb
from utils.astar import AStar


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
        # Použij animaci frame pro sprite
        frame = int(self.animation_frame) % 4
        self.image = self.iso_utils.create_enemy_sprite(enemy_type=0, frame=frame)
        self.rect = self.image.get_rect()
        self.update_position()

    def update_position(self):
        screen_x, screen_y = self.iso_utils.grid_to_screen(self.grid_x, self.grid_y, self.z)
        offset_x, offset_y = self.iso_utils.get_tile_center_offset()
        # Add floating animation
        float_offset = math.sin(self.animation_frame) * 3
        self.rect.centerx = screen_x + offset_x
        self.rect.bottom = screen_y + offset_y - float_offset

    def update(self, game_map, grid_width, grid_height, player, dangers):
        self.animation_frame += 0.2
        self.move_timer += 1

        if self.move_timer > 10:
            self.move_timer = 0
            bomb_proximity = 4
            explosion_proximity = 1
            danger_proximity = 4
            dx = 0
            dy = 0


            # pronásledování hráče
            try:
                astar=AStar(game_map)
                path=astar.find_path((self.grid_x,self.grid_y),(player.grid_x,player.grid_y))
            except :
                traceback.print_exc()
                path=[]
            if len(path)>1:
                print(path[1],self.grid_x,self.grid_y)
                print(path[1][0],path[1][1])
                dx=path[1][0]-self.grid_x
                dy=path[1][1]-self.grid_y
            else:#není li cesta
                if random.random() < 0.5:
                    if self.grid_x - player.grid_x > 0:
                        dx = -1
                    else:
                        dx = 1
                else:
                    if self.grid_y - player.grid_y > 0:
                        dy = -1
                    else:
                        dy = 1




            for danger in dangers:#TODO seřadit nebezpečí od nejbližšího
                if type(danger) == domain.entity.bomb.Bomb:
                    danger_proximity=bomb_proximity
                if type(danger) == domain.entity.explosion.Explosion:
                    danger_proximity=explosion_proximity

                # jestli utíkat
                d_x_dist=self.grid_x - danger.grid_x
                d_y_dist=self.grid_y - danger.grid_y
                if abs(d_x_dist) < danger_proximity and abs(d_y_dist) < danger_proximity:
                    # kudy utíkat
                    if abs(d_x_dist) > abs(d_y_dist):
                        if d_x_dist > 0:
                            dx = 1
                        else:
                            dx = -1
                        break
                    else:
                        if d_y_dist > 0:
                            dy = 1
                        else:
                            dy = -1
                        break

            new_x = self.grid_x + dx
            new_y = self.grid_y + dy

            if (0 <= new_x < grid_width and 0 <= new_y < grid_height and
                    game_map[new_y, new_x] == 0):
                self.grid_x = new_x
                self.grid_y = new_y

        # Aktualizuj sprite pro animaci
        self.create_sprite()
