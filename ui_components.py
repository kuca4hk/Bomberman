import pygame
from enum import Enum


class GameState(Enum):
    INTRO = 1
    MENU_SCREEN = 2
    MENU = 3
    PLAYING = 4
    GAME_OVER = 5
    VICTORY = 6
    STORY_PLAYING = 7
    STORY_COMPLETE = 8
    STORY_GAME_OVER = 9


class Button:
    def __init__(self, x, y, width, height, text, font, color=(100, 100, 100), text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.text_color = text_color
        self.hover_color = (150, 150, 150)
        self.is_hovered = False
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False
        
    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2)
        
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)