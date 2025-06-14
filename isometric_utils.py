import math
import pygame


class IsometricUtils:
    """Utility class for isometric coordinate conversions and rendering"""
    
    def __init__(self, tile_width=64, tile_height=32):
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.half_tile_width = tile_width // 2
        self.half_tile_height = tile_height // 2
        
    def grid_to_screen(self, grid_x, grid_y, z=0):
        """Convert grid coordinates to screen coordinates"""
        screen_x = (grid_x - grid_y) * self.half_tile_width
        screen_y = (grid_x + grid_y) * self.half_tile_height - z * self.half_tile_height
        return int(screen_x), int(screen_y)
    
    def screen_to_grid(self, screen_x, screen_y):
        """Convert screen coordinates to grid coordinates"""
        grid_x = (screen_x / self.half_tile_width + screen_y / self.half_tile_height) / 2
        grid_y = (screen_y / self.half_tile_height - screen_x / self.half_tile_width) / 2
        return int(grid_x), int(grid_y)
    
    def create_isometric_tile(self, color, height=1, with_sides=True):
        """Create an isometric tile sprite"""
        # Calculate total height including 3D effect
        total_height = self.tile_height + (height - 1) * self.half_tile_height
        surface = pygame.Surface((self.tile_width, total_height), pygame.SRCALPHA)
        
        # Top face (diamond shape)
        top_points = [
            (self.half_tile_width, 0),  # top
            (self.tile_width, self.half_tile_height),  # right
            (self.half_tile_width, self.tile_height),  # bottom
            (0, self.half_tile_height)  # left
        ]
        
        # Draw top face
        pygame.draw.polygon(surface, color, top_points)
        
        if with_sides and height > 1:
            # Left side
            left_color = tuple(max(0, c - 40) for c in color[:3])
            left_points = [
                (0, self.half_tile_height),
                (self.half_tile_width, self.tile_height),
                (self.half_tile_width, total_height),
                (0, total_height - self.half_tile_height)
            ]
            pygame.draw.polygon(surface, left_color, left_points)
            
            # Right side
            right_color = tuple(max(0, c - 60) for c in color[:3])
            right_points = [
                (self.tile_width, self.half_tile_height),
                (self.half_tile_width, self.tile_height),
                (self.half_tile_width, total_height),
                (self.tile_width, total_height - self.half_tile_height)
            ]
            pygame.draw.polygon(surface, right_color, right_points)
        
        # Add outline
        pygame.draw.polygon(surface, (0, 0, 0), top_points, 2)
        
        return surface
    
    def create_isometric_cube(self, color, size=1):
        """Create a 3D cube in isometric view"""
        cube_height = size * self.tile_height
        surface = pygame.Surface((self.tile_width, cube_height + self.half_tile_height), pygame.SRCALPHA)
        
        # Top face
        top_points = [
            (self.half_tile_width, 0),
            (self.tile_width, self.half_tile_height),
            (self.half_tile_width, self.tile_height),
            (0, self.half_tile_height)
        ]
        pygame.draw.polygon(surface, color, top_points)
        
        # Left side
        left_color = tuple(max(0, c - 40) for c in color[:3])
        left_points = [
            (0, self.half_tile_height),
            (self.half_tile_width, self.tile_height),
            (self.half_tile_width, cube_height + self.half_tile_height),
            (0, cube_height)
        ]
        pygame.draw.polygon(surface, left_color, left_points)
        
        # Right side
        right_color = tuple(max(0, c - 60) for c in color[:3])
        right_points = [
            (self.tile_width, self.half_tile_height),
            (self.half_tile_width, self.tile_height),
            (self.half_tile_width, cube_height + self.half_tile_height),
            (self.tile_width, cube_height)
        ]
        pygame.draw.polygon(surface, right_color, right_points)
        
        # Outlines
        pygame.draw.polygon(surface, (0, 0, 0), top_points, 2)
        pygame.draw.polygon(surface, (0, 0, 0), left_points, 2)
        pygame.draw.polygon(surface, (0, 0, 0), right_points, 2)
        
        return surface
    
    def create_character_sprite(self, base_color, height=1):
        """Create an isometric character sprite"""
        char_width = self.tile_width // 2
        char_height = int(self.tile_height * 1.5)
        surface = pygame.Surface((char_width, char_height), pygame.SRCALPHA)
        
        # Body (ellipse)
        body_rect = pygame.Rect(char_width//4, char_height//3, char_width//2, char_height//2)
        pygame.draw.ellipse(surface, base_color, body_rect)
        
        # Head
        head_radius = char_width // 6
        head_center = (char_width//2, char_height//4)
        pygame.draw.circle(surface, base_color, head_center, head_radius)
        
        # Simple face
        eye_size = 2
        pygame.draw.circle(surface, (255, 255, 255), (head_center[0] - 3, head_center[1] - 2), eye_size)
        pygame.draw.circle(surface, (255, 255, 255), (head_center[0] + 3, head_center[1] - 2), eye_size)
        pygame.draw.circle(surface, (0, 0, 0), (head_center[0] - 3, head_center[1] - 2), 1)
        pygame.draw.circle(surface, (0, 0, 0), (head_center[0] + 3, head_center[1] - 2), 1)
        
        # Outline
        pygame.draw.ellipse(surface, (0, 0, 0), body_rect, 2)
        pygame.draw.circle(surface, (0, 0, 0), head_center, head_radius, 2)
        
        return surface
    
    def create_bomb_sprite(self, pulse_scale=1.0):
        """Create an isometric bomb sprite"""
        bomb_size = int(self.tile_width * 0.4 * pulse_scale)
        surface = pygame.Surface((bomb_size, bomb_size), pygame.SRCALPHA)
        
        center = bomb_size // 2
        
        # Bomb body (sphere)
        pygame.draw.circle(surface, (40, 40, 40), (center, center), center - 2)
        pygame.draw.circle(surface, (60, 60, 60), (center, center), center - 4)
        
        # Fuse
        fuse_length = bomb_size // 4
        pygame.draw.line(surface, (139, 69, 19), 
                        (center, 2), (center, fuse_length), 3)
        
        # Spark
        spark_size = max(2, int(3 * pulse_scale))
        pygame.draw.circle(surface, (255, 255, 0), (center, 2), spark_size)
        pygame.draw.circle(surface, (255, 200, 0), (center, 2), spark_size - 1)
        
        return surface
    
    def create_explosion_sprite(self, frame=0, max_frames=30):
        """Create an isometric explosion sprite"""
        progress = frame / max_frames
        explosion_size = int(self.tile_width * (0.5 + progress * 1.5))
        surface = pygame.Surface((explosion_size, explosion_size), pygame.SRCALPHA)
        
        center = explosion_size // 2
        
        # Multiple explosion rings
        for i in range(5):
            radius = int((center - i * 5) * (1 - progress * 0.3))
            if radius > 0:
                color_intensity = int(255 * (1 - i * 0.2) * (1 - progress))
                color = (color_intensity, color_intensity // 2, 0)
                pygame.draw.circle(surface, color, (center, center), radius)
        
        # Sparks around explosion
        num_sparks = 8
        for i in range(num_sparks):
            angle = i * 2 * math.pi / num_sparks
            spark_dist = center * (0.8 + progress * 0.4)
            spark_x = center + math.cos(angle) * spark_dist
            spark_y = center + math.sin(angle) * spark_dist
            spark_size = max(1, int(4 * (1 - progress)))
            pygame.draw.circle(surface, (255, 255, 0), (int(spark_x), int(spark_y)), spark_size)
        
        return surface
    
    def get_render_order(self, entities):
        """Sort entities by their render order (back to front)"""
        def sort_key(entity):
            # Sort by grid_y first (back to front), then by grid_x, then by z if available
            z = getattr(entity, 'z', 0)
            return (entity.grid_y + entity.grid_x, -z)
        
        return sorted(entities, key=sort_key)
    
    def get_tile_center_offset(self):
        """Get offset to center objects on tiles"""
        return self.half_tile_width, self.tile_height