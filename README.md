# README.md

## Project Overview

This is a Boomer Man game built with Python using pygame. The game features a player navigating a grid-based map in **isometric 3D view**, placing bombs to destroy walls and enemies. The game now uses advanced isometric rendering with proper depth sorting.

## Development Commands

### Running the Game
```bash
python main.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Development Environment
- Python 3.12+ required
- Dependencies: pygame 2.6.1, numpy 2.3.0

## Architecture

### Modular Structure
- `main.py`: Entry point that imports and runs the game
- `game.py`: Main game controller (`BoomerManGame` class) with isometric rendering
- `entities.py`: Game entities (Player, Enemy, Bomb, Explosion classes) with isometric positioning
- `ui_components.py`: UI elements (Button class, GameState enum)
- `game_logic.py`: Game logic functions (map generation, collision detection, isometric sprite creation)
- `isometric_utils.py`: Isometric utilities for 3D coordinate conversion and sprite generation

### Core Game Structure
- **Modular architecture**: Code split into logical modules for maintainability
- **Isometric 3D rendering**: Uses isometric projection for pseudo-3D view
- **Sprite-based system**: Uses pygame sprite groups for game objects with depth sorting
- **Grid-based movement**: All entities move on a tile-based grid with isometric coordinates
- **State machine**: Game uses `GameState` enum for different screens (INTRO, MENU_SCREEN, PLAYING, GAME_OVER)

### Key Classes and Modules
- `BoomerManGame` (game.py): Main game controller with isometric rendering pipeline
- `Player` (entities.py): Player character with isometric sprite and directional facing
- `Enemy` (entities.py): AI-controlled enemies with floating animation in isometric space
- `Bomb` (entities.py): 3D isometric bombs with pulsing animation
- `Explosion` (entities.py): Isometric explosion effects with proper depth
- `Button` (ui_components.py): UI button class for menu interactions
- `GameState` (ui_components.py): Enum for game states
- `IsometricUtils` (isometric_utils.py): Core isometric conversion and sprite generation utilities

### Isometric System
- **Coordinate conversion**: Grid coordinates to isometric screen coordinates
- **Depth sorting**: Proper rendering order for 3D appearance
- **Tile generation**: Creates isometric cubes, tiles, and character sprites
- **Camera system**: Configurable camera offset for proper view positioning
- **3D effects**: Height layers, shadows, and perspective

### Game Map System
- Uses numpy 2D array for map representation
- Values: 0=empty (floor), 1=indestructible wall, 2=destructible brick wall
- Map generation creates perimeter walls, grid pattern walls, and random destructible walls
- Isometric tile rendering with proper depth and occlusion

### Rendering Pipeline
- **Isometric background**: Gradient background for depth perception
- **Depth-sorted rendering**: All objects sorted by their grid position for proper layering
- **3D sprite rendering**: Isometric sprites with proper positioning and shadows
- **Particle system**: 3D-aware explosion debris with gravity
- **Screen shake effects**: Enhanced with isometric camera movement
- **Mock sound visualization**: Visual indicators for audio feedback

### Game Mechanics
- Grid-based collision detection (unchanged)
- Bomb explosion spreads in 4 directions with isometric visualization
- Player has multiple lives and respawns on damage
- Score increases from destroying walls and enemies
- Enhanced visual feedback with 3D effects