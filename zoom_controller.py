"""
Zoom Controller - Manages zoom state and animations
"""
import pygame


class ZoomController:
    """Handles all zoom-related logic and animations"""
    
    def __init__(self, image_manager):
        self.image_manager = image_manager
        self.scale = 1.0
        self.min_scale = 1.0
        
        # Step animation properties
        self.animation_duration = 300  # milliseconds
        self.target_scale = 1.0
        self.start_scale = 1.0
        self.animation_start_time = None
        self.is_animating = False
        
        # Continuous zoom properties
        self.continuous_zoom_rate = 1.0  # 100% scale change per second
    
    def zoom_step(self, direction, zoom_factor=1.3):
        """Initiate a discrete zoom step with animation"""
        if direction == 'in':
            new_scale = self.scale * zoom_factor
        elif direction == 'out':
            new_scale = self.scale / zoom_factor
        else:
            return
        
        self.start_zoom_animation(new_scale)
    
    def zoom_continuous(self, direction, dt):
        """Apply continuous zoom based on elapsed time"""
        zoom_factor = (1 + self.continuous_zoom_rate) ** dt
        
        if direction == 'in':
            self.scale = self.scale * zoom_factor
        elif direction == 'out':
            self.scale = self.scale / zoom_factor
    
    def start_zoom_animation(self, target_scale, start_scale=None):
        """Start a zoom animation towards the target scale"""
        self.is_animating = True
        self.animation_start_time = pygame.time.get_ticks()
        self.target_scale = target_scale
        self.start_scale = start_scale if start_scale is not None else self.scale
    
    def update_step_animation(self):
        """Update step animation state and return whether image swap occurred"""
        if not self.is_animating:
            return False
        
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.animation_start_time
        animation_progress = min(1.0, elapsed / self.animation_duration)
        
        if animation_progress >= 1.0:
            # Animation complete
            self.is_animating = False
            self.scale = self.target_scale
            return self._check_boundaries()
        else:
            self.scale = self.start_scale + (self.target_scale - self.start_scale) * animation_progress
            swapped = self._check_boundaries()
            if swapped:
                self.is_animating = False
            return swapped
    
    def _check_boundaries(self):
        """Check if scale exceeded boundaries and return transition info"""
        current_img = self.image_manager.get_current_image()
        
        if self.scale > current_img.max_scale:
            if self.image_manager.can_go_next():
                return ('forward', self.image_manager.current_index + 1)
            else:
                self.scale = 1.0
            return None
        elif self.scale < self.min_scale:
            if self.image_manager.can_go_previous():
                return ('backward', self.image_manager.current_index - 1)
            else:
                self.scale = self.min_scale
            return None
        
        return None
    
    def check_boundaries_continuous(self):
        """Check boundaries for continuous zoom and return transition info"""
        return self._check_boundaries()
    
    def reset_to_min(self):
        """Reset scale to minimum (fully zoomed out)"""
        self.scale = self.min_scale
    
    def reset_to_max(self):
        """Reset scale to maximum for current image"""
        current_img = self.image_manager.get_current_image()
        self.scale = current_img.max_scale
    
    def get_normalized_zoom(self):
        """Get zoom progress from min to max (0.0 to 1.0)"""
        current_img = self.image_manager.get_current_image()
        return (self.scale - self.min_scale) / (current_img.max_scale - self.min_scale)
