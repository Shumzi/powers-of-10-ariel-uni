"""
Image Manager - Handles loading and managing images with their metadata
"""
import pygame
import os


class ImageData:
    """Encapsulates all data for a single image"""
    def __init__(self, config, original, surface, scale, bg, max_scale):
        self.config = config
        self.original = original  # High-res original
        self.surface = surface    # Pre-scaled to fit viewport
        self.scale = scale        # Scale factor used to create surface
        self.bg = bg             # Background image
        self.max_scale = max_scale  # Maximum zoom level for this image


class ImageManager:
    """Manages loading and accessing images"""
    
    def __init__(self, config, viewport_dims):
        self.config = config
        self.viewport_dims = viewport_dims
        self.images = []
        self.current_index = 0
        
    def load_images(self):
        """Load all images from config"""
        for img_config in self.config['images']:
            # Load image from file
            image_path = img_config['src']
            image_path_bg = img_config.get('bg')
            
            original = pygame.image.load(image_path).convert_alpha()
            bg = pygame.image.load(image_path_bg).convert_alpha()
            
            # Calculate scaling to fit viewport while maintaining aspect ratio
            scale = min(self.viewport_dims[0] / original.get_width(), 
                       self.viewport_dims[1] / original.get_height())
            
            new_size = (int(original.get_width() * scale),
                       int(original.get_height() * scale))
            
            scaled = pygame.transform.smoothscale(original, new_size)
            
            # Calculate max scale based on rectangle dimensions
            max_scale = self._calculate_max_scale(img_config, scaled, scale)
            
            image_data = ImageData(img_config, original, scaled, scale, bg, max_scale)
            self.images.append(image_data)
    
    def _calculate_max_scale(self, img_config, scaled_surface, scale_factor):
        """Calculate maximum zoom level based on rect dimensions"""
        rect = self._get_rect(img_config, scaled_surface, scale_factor)
        max_scale = 1.0
        
        if rect:
            # Calculate max scale so rect fills viewport
            width_scale = self.viewport_dims[0] / rect.width
            height_scale = self.viewport_dims[1] / rect.height
            max_scale = min(width_scale, height_scale)
        
        return max_scale
    
    def _get_rect(self, img_config, surface, scale_factor):
        """Get rect from config (pixel or relative coordinates)"""
        # Check for pixel coordinates first
        pixel_rect = img_config.get('nextPixelRect')
        if pixel_rect and len(pixel_rect) == 4:
            px, py, pw, ph = pixel_rect
            return pygame.Rect(
                px * scale_factor,
                py * scale_factor,
                pw * scale_factor,
                ph * scale_factor
            )
        
        # Fall back to relative coordinates
        rect = img_config.get('nextRect')
        if rect and len(rect) == 4:
            return pygame.Rect(
                surface.get_width() * rect[0],
                surface.get_height() * rect[1],
                surface.get_width() * rect[2],
                surface.get_height() * rect[3]
            )
        
        return None
    
    def get_current_image(self):
        """Get the current image data"""
        return self.images[self.current_index]
    
    def get_rect(self, image_data):
        """Get rect for a specific image"""
        return self._get_rect(image_data.config, image_data.surface, image_data.scale)
    
    def next_image(self):
        """Move to next image if available"""
        if self.current_index < len(self.images) - 1:
            self.current_index += 1
            return True
        return False
    
    def previous_image(self):
        """Move to previous image if available"""
        if self.current_index > 0:
            self.current_index -= 1
            return True
        return False
    
    def can_go_next(self):
        """Check if can move to next image"""
        return self.current_index < len(self.images) - 1
    
    def can_go_previous(self):
        """Check if can move to previous image"""
        return self.current_index > 0
