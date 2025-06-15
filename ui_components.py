import pygame
import math
import time
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
        self.hover_color = (min(255, color[0] + 40), min(255, color[1] + 40), min(255, color[2] + 40))
        self.is_hovered = False
        self.click_time = 0
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.click_time = time.time()
                return True
        return False
        
    def draw(self, screen):
        # Animace při kliknutí
        click_scale = 1.0
        if time.time() - self.click_time < 0.2:
            click_scale = 0.95 + (time.time() - self.click_time) * 0.25
        
        # Pulsování při hoveru
        hover_pulse = 1.0
        if self.is_hovered:
            hover_pulse = 1.0 + math.sin(time.time() * 8) * 0.05
        
        # Výpočet finální velikosti
        final_scale = click_scale * hover_pulse
        scaled_width = int(self.rect.width * final_scale)
        scaled_height = int(self.rect.height * final_scale)
        scaled_rect = pygame.Rect(
            self.rect.centerx - scaled_width // 2,
            self.rect.centery - scaled_height // 2,
            scaled_width,
            scaled_height
        )
        
        # Hlavní barva tlačítka
        base_color = self.hover_color if self.is_hovered else self.color
        
        # Gradient efekt - více vrstev pro hloubku
        for i in range(8, 0, -1):
            shadow_rect = pygame.Rect(
                scaled_rect.x + i,
                scaled_rect.y + i,
                scaled_rect.width,
                scaled_rect.height
            )
            shadow_alpha = 30 - i * 3
            shadow_color = (0, 0, 0, shadow_alpha)
            
            # Vytvoření povrchu se stínem
            shadow_surface = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surface, shadow_color, (0, 0, shadow_rect.width, shadow_rect.height), border_radius=8)
            screen.blit(shadow_surface, shadow_rect)
        
        # Gradient na tlačítku
        gradient_surface = pygame.Surface((scaled_rect.width, scaled_rect.height), pygame.SRCALPHA)
        
        # Horní světlejší část
        top_color = (min(255, base_color[0] + 30), min(255, base_color[1] + 30), min(255, base_color[2] + 30))
        # Dolní tmavší část  
        bottom_color = (max(0, base_color[0] - 20), max(0, base_color[1] - 20), max(0, base_color[2] - 20))
        
        # Vytvoření gradientu
        for y in range(scaled_rect.height):
            ratio = y / scaled_rect.height
            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
            pygame.draw.line(gradient_surface, (r, g, b), (0, y), (scaled_rect.width, y))
        
        # Zaoblené rohy
        pygame.draw.rect(gradient_surface, (0, 0, 0, 0), (0, 0, scaled_rect.width, scaled_rect.height), border_radius=8)
        mask = pygame.mask.from_surface(gradient_surface)
        gradient_surface = mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
        
        # Překreslení gradientu s správnými barvami
        for y in range(scaled_rect.height):
            ratio = y / scaled_rect.height
            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
            for x in range(scaled_rect.width):
                if gradient_surface.get_at((x, y))[3] > 0:  # Pokud pixel není průhledný
                    gradient_surface.set_at((x, y), (r, g, b, 255))
        
        screen.blit(gradient_surface, scaled_rect)
        
        # Světlý okraj nahoře pro 3D efekt
        if self.is_hovered:
            highlight_color = (min(255, base_color[0] + 60), min(255, base_color[1] + 60), min(255, base_color[2] + 60))
            pygame.draw.line(screen, highlight_color, 
                           (scaled_rect.left + 8, scaled_rect.top + 2), 
                           (scaled_rect.right - 8, scaled_rect.top + 2), 2)
        
        # Vnější okraj
        border_color = (255, 255, 255, 180) if self.is_hovered else (180, 180, 180, 120)
        pygame.draw.rect(screen, border_color[:3], scaled_rect, 3, border_radius=8)
        
        # Text s efekty
        text_surface = self.font.render(self.text, True, self.text_color)
        
        # Stín textu
        shadow_text = self.font.render(self.text, True, (0, 0, 0))
        shadow_rect = shadow_text.get_rect(center=(scaled_rect.centerx + 2, scaled_rect.centery + 2))
        shadow_surface = pygame.Surface(shadow_text.get_size(), pygame.SRCALPHA)
        shadow_surface.blit(shadow_text, (0, 0))
        shadow_surface.set_alpha(100)
        screen.blit(shadow_surface, shadow_rect)
        
        # Hlavní text
        text_rect = text_surface.get_rect(center=scaled_rect.center)
        screen.blit(text_surface, text_rect)