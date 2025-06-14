import pygame

class SpriteSheet:
    """Třída pro práci se sprite sheety"""
    
    def __init__(self, image_path):
        """Načte sprite sheet ze souboru"""
        try:
            self.sheet = pygame.image.load(image_path)
        except pygame.error:
            print(f"Nelze načíst sprite sheet: {image_path}")
            # Vytvoř prázdný surface jako fallback
            self.sheet = pygame.Surface((32, 32))
            self.sheet.fill((255, 0, 255))  # Magenta jako chyba
    
    def get_sprite(self, x, y, width, height, scale=1):
        """Extrahuje sprite z sheet na dané pozici"""
        sprite = pygame.Surface((width, height), pygame.SRCALPHA)
        sprite.blit(self.sheet, (0, 0), (x, y, width, height))
        
        if scale != 1:
            sprite = pygame.transform.scale(sprite, (int(width * scale), int(height * scale)))
        
        return sprite
    
    def get_sprites_row(self, y, width, height, count, scale=1):
        """Extrahuje řadu sprite ze stejného řádku"""
        sprites = []
        for i in range(count):
            sprite = self.get_sprite(i * width, y, width, height, scale)
            sprites.append(sprite)
        return sprites
    
    def get_sprites_grid(self, start_x, start_y, width, height, cols, rows, scale=1):
        """Extrahuje mřížku sprite"""
        sprites = []
        for row in range(rows):
            for col in range(cols):
                x = start_x + col * width
                y = start_y + row * height
                sprite = self.get_sprite(x, y, width, height, scale)
                sprites.append(sprite)
        return sprites