"""
Tile Pyramid - Pre-computed multi-resolution tile system for fast zoom rendering
Generates and caches image tiles at multiple zoom levels to eliminate per-frame scaling
"""
import pygame
import os
import pickle
import hashlib
from typing import Optional, Tuple, List


class TilePyramid:
    """Manages multi-resolution tile pyramid for an image"""
    
    # Default pyramid levels (zoom factors)
    DEFAULT_LEVELS = [1.0, 2.0, 4.0, 8.0]
    TILE_SIZE = 512
    
    def __init__(self, original_surface: pygame.Surface, image_path: str, 
                 viewport_dims: Tuple[int, int], base_scale: float):
        """
        Initialize tile pyramid
        
        Args:
            original_surface: High-resolution original image
            image_path: Path to source image (for cache key)
            viewport_dims: Viewport dimensions (width, height)
            base_scale: Scale factor that was used to fit image to viewport
        """
        self.original = original_surface
        self.image_path = image_path
        self.viewport_dims = viewport_dims
        self.base_scale = base_scale
        
        # Calculate base size (image scaled to fit viewport)
        self.base_width = int(original_surface.get_width() * base_scale)
        self.base_height = int(original_surface.get_height() * base_scale)
        
        # Pyramid storage: level -> list of tile surfaces
        self.pyramid = {}
        self.levels = self.DEFAULT_LEVELS.copy()
        
        # Cache metadata
        self.cache_dir = os.path.join(os.path.dirname(image_path), ".tile_cache")
        self.cache_key = self._generate_cache_key()
        
    def _generate_cache_key(self) -> str:
        """Generate unique cache key based on image and viewport"""
        # Hash image path, file mod time, and viewport dims
        try:
            mod_time = os.path.getmtime(self.image_path)
            key_data = f"{self.image_path}_{mod_time}_{self.viewport_dims}_{self.base_scale}"
            return hashlib.md5(key_data.encode()).hexdigest()
        except:
            # Fallback if file operations fail
            return hashlib.md5(self.image_path.encode()).hexdigest()
    
    def _get_cache_path(self) -> str:
        """Get path to cache file for this pyramid"""
        os.makedirs(self.cache_dir, exist_ok=True)
        return os.path.join(self.cache_dir, f"{self.cache_key}.pkl")
    
    def load_or_generate(self) -> None:
        """Load pyramid from cache or generate if not exists"""
        cache_path = self._get_cache_path()
        
        # Try to load from cache
        if os.path.exists(cache_path):
            try:
                if self._load_from_cache(cache_path):
                    print(f"Loaded tile pyramid from cache: {os.path.basename(self.image_path)}")
                    return
            except Exception as e:
                print(f"Cache load failed, regenerating: {e}")
        
        # Generate new pyramid
        print(f"Generating tile pyramid for {os.path.basename(self.image_path)}...")
        self._generate_pyramid()
        
        # Save to cache
        try:
            self._save_to_cache(cache_path)
        except Exception as e:
            print(f"Warning: Failed to cache tiles: {e}")
    
    def _generate_pyramid(self) -> None:
        """Generate all pyramid levels"""
        for level in self.levels:
            self.pyramid[level] = self._generate_level(level)
    
    def _generate_level(self, level: float) -> List[pygame.Surface]:
        """Generate tiles for a specific zoom level"""
        # Calculate dimensions at this level
        level_width = int(self.base_width * level)
        level_height = int(self.base_height * level)
        
        # Scale entire image to this level
        level_surface = pygame.transform.smoothscale(
            self.original, 
            (level_width, level_height)
        )
        
        # Create tiles from the scaled surface
        tiles = []
        for y in range(0, level_height, self.TILE_SIZE):
            for x in range(0, level_width, self.TILE_SIZE):
                tile_width = min(self.TILE_SIZE, level_width - x)
                tile_height = min(self.TILE_SIZE, level_height - y)
                
                # Create tile as subsurface
                tile = level_surface.subsurface(
                    pygame.Rect(x, y, tile_width, tile_height)
                ).copy()  # Copy to own surface
                
                tiles.append((x, y, tile))
        
        return tiles
    
    def _save_to_cache(self, cache_path: str) -> None:
        """Save pyramid to disk cache"""
        cache_data = {
            'levels': self.levels,
            'base_width': self.base_width,
            'base_height': self.base_height,
            'pyramid': {}
        }
        
        # Convert surfaces to image strings for pickling
        for level, tiles in self.pyramid.items():
            cache_data['pyramid'][level] = [
                (x, y, pygame.image.tostring(tile, 'RGBA'), tile.get_size())
                for x, y, tile in tiles
            ]
        
        with open(cache_path, 'wb') as f:
            pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)
    
    def _load_from_cache(self, cache_path: str) -> bool:
        """Load pyramid from disk cache. Returns True if successful."""
        with open(cache_path, 'rb') as f:
            cache_data = pickle.load(f)
        
        # Validate cache data
        if (cache_data['base_width'] != self.base_width or 
            cache_data['base_height'] != self.base_height):
            return False
        
        self.levels = cache_data['levels']
        self.pyramid = {}
        
        # Reconstruct surfaces from image strings
        for level, tile_data in cache_data['pyramid'].items():
            tiles = []
            for x, y, img_string, size in tile_data:
                tile = pygame.image.fromstring(img_string, size, 'RGBA')
                tiles.append((x, y, tile))
            self.pyramid[level] = tiles
        
        return True
    
    def get_scaled_surface(self, zoom: float, crop_rect: Optional[pygame.Rect] = None) -> Tuple[pygame.Surface, Tuple[int, int]]:
        """
        Get scaled surface at specified zoom level, optionally cropped
        
        Args:
            zoom: Zoom factor (relative to base_scale, e.g., 1.0 = base, 2.0 = 2x zoom)
            crop_rect: Optional rect in base-scaled coordinates to crop to
            
        Returns:
            (surface, offset) - Scaled/cropped surface and position offset for rendering
        """
        # Find best pyramid level for this zoom
        best_level = self._find_best_level(zoom)
        
        if crop_rect:
            return self._get_cropped_surface(zoom, best_level, crop_rect)
        else:
            return self._get_full_surface(zoom, best_level)
    
    def _find_best_level(self, zoom: float) -> float:
        """Find the pyramid level closest to requested zoom (prefer higher resolution)"""
        if zoom <= self.levels[0]:
            return self.levels[0]
        if zoom >= self.levels[-1]:
            return self.levels[-1]
        
        # Find bracketing levels
        for i in range(len(self.levels) - 1):
            if self.levels[i] <= zoom <= self.levels[i + 1]:
                # Use higher resolution level for better quality
                return self.levels[i + 1]
        
        return self.levels[-1]
    
    def _get_full_surface(self, zoom: float, level: float) -> Tuple[pygame.Surface, Tuple[int, int]]:
        """Get full image at zoom level"""
        # Calculate target size
        target_width = int(self.base_width * zoom)
        target_height = int(self.base_height * zoom)
        
        # Get level dimensions
        level_width = int(self.base_width * level)
        level_height = int(self.base_height * level)
        
        # Composite all tiles for this level
        level_surface = pygame.Surface((level_width, level_height), pygame.SRCALPHA)
        for x, y, tile in self.pyramid[level]:
            level_surface.blit(tile, (x, y))
        
        # Scale to exact zoom if needed
        if zoom != level:
            result = pygame.transform.smoothscale(level_surface, (target_width, target_height))
        else:
            result = level_surface
        
        return result, (0, 0)
    
    def _get_cropped_surface(self, zoom: float, level: float, crop_rect: pygame.Rect) -> Tuple[pygame.Surface, Tuple[int, int]]:
        """Get cropped region at zoom level"""
        # Calculate crop rect at pyramid level coordinates
        level_crop = pygame.Rect(
            int(crop_rect.x * level),
            int(crop_rect.y * level),
            int(crop_rect.width * level),
            int(crop_rect.height * level)
        )
        
        # Calculate target size at zoom
        target_width = int(crop_rect.width * zoom)
        target_height = int(crop_rect.height * zoom)
        
        # Find which tiles overlap with crop rect
        relevant_tiles = self._find_overlapping_tiles(level, level_crop)
        
        if not relevant_tiles:
            # Fallback: create empty surface
            return pygame.Surface((target_width, target_height), pygame.SRCALPHA), (0, 0)
        
        # Create surface for cropped region at level scale
        crop_surface = pygame.Surface((level_crop.width, level_crop.height), pygame.SRCALPHA)
        
        # Composite relevant tiles
        for x, y, tile in relevant_tiles:
            # Calculate position relative to crop rect
            rel_x = x - level_crop.x
            rel_y = y - level_crop.y
            
            # Calculate which part of tile to use
            tile_rect = pygame.Rect(x, y, tile.get_width(), tile.get_height())
            overlap = tile_rect.clip(level_crop)
            
            if overlap.width > 0 and overlap.height > 0:
                # Source rect within tile
                src_x = overlap.x - x
                src_y = overlap.y - y
                src_rect = pygame.Rect(src_x, src_y, overlap.width, overlap.height)
                
                # Destination in crop surface
                dst_x = overlap.x - level_crop.x
                dst_y = overlap.y - level_crop.y
                
                crop_surface.blit(tile, (dst_x, dst_y), src_rect)
        
        # Scale to exact zoom if needed
        if zoom != level:
            result = pygame.transform.smoothscale(crop_surface, (target_width, target_height))
        else:
            result = crop_surface
        
        return result, (0, 0)
    
    def _find_overlapping_tiles(self, level: float, rect: pygame.Rect) -> List[Tuple[int, int, pygame.Surface]]:
        """Find tiles that overlap with given rect at pyramid level"""
        overlapping = []
        
        for x, y, tile in self.pyramid[level]:
            tile_rect = pygame.Rect(x, y, tile.get_width(), tile.get_height())
            if tile_rect.colliderect(rect):
                overlapping.append((x, y, tile))
        
        return overlapping
    
    def has_level(self, zoom: float) -> bool:
        """Check if pyramid has been generated"""
        return bool(self.pyramid)
    
    def get_memory_usage(self) -> int:
        """Estimate memory usage in bytes"""
        total = 0
        for tiles in self.pyramid.values():
            for _, _, tile in tiles:
                total += tile.get_width() * tile.get_height() * 4  # RGBA
        return total
