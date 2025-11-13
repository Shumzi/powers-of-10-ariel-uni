import pygame
import json
import os
from urllib.parse import unquote

class ZoomViewer:
    def __init__(self):
        pygame.init()
        
        # Initialize display
        self.width = 1600
        self.height = 919
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Powers of Ten Viewer")
        
        self.viewport_dims = (720,720)
        self.viewport = pygame.Surface(self.viewport_dims) 
        self.viewport_rect = pygame.Rect(812, 76, *self.viewport_dims)
        # Font setup
        self.font = pygame.font.SysFont('Arial', 16)
        
        # Load configuration
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
            
        # Initialize variables
        self.current_index = 0
        
        self.scale = 1.0
        self.min_scale = 1.0
        
        # Animation properties
        self.animation_duration = 300  # milliseconds
        self.target_scale = 1.0
        self.start_scale = 1.0
        self.animation_start_time = None
        self.is_animating = False
        self.continuous_zoom_speed = 0.0005  # Speed factor per frame for continuous zooming (at 60 FPS)
        
        # Load images
        self.images = []
        self.load_images()
        
        # Clock for controlling frame rate
        self.clock = pygame.time.Clock()
        self.FPS = 60

    def load_images(self):
        for img_config in self.config['images']:
            # Load image from file
            image_path = img_config['src']
            if image_path.startswith('http'):
                # Extract filename from URL and look for local file
                filename = unquote(os.path.basename(image_path))
                image_path = f"sample photos/{filename}"
            image_path_bg = f"sample bg/{img_config.get('bg')}"
            # Load and scale image
            original = pygame.image.load(image_path).convert_alpha()
            bg = pygame.image.load(image_path_bg).convert_alpha()
            # Calculate scaling to fit screen size while maintaining aspect ratio
            scale = min(self.viewport.get_width() / original.get_width(), 
                       self.viewport.get_height()/ original.get_height())
            
            new_size = (int(original.get_width() * scale),
                       int(original.get_height() * scale))
            
            scaled = pygame.transform.smoothscale(original, new_size)
            
            self.images.append({
                'config': img_config,
                'original': original,
                'surface': scaled, # scaled to fit viewport. all zooming done from this base.
                'scale': scale,
                'bg': bg,
            })

            # Calculate max scale based on the rectangle dimensions
            self.current_img = self.images[-1]  # Set the current image temporarily
            rect = self.get_rect(img_config)
            max_scale = 1.0
            if rect:
                # Calculate max scale so rect fills viewport when positioned at top-left
                # At max_scale, rect dimensions should equal viewport dimensions
                width_scale = self.viewport.get_width() / rect.width
                height_scale = self.viewport.get_height() / rect.height
                max_scale = min(width_scale, height_scale)
            self.images[-1]['max_scale'] = max_scale

        self.current_img = self.images[self.current_index]  # Reset to first image

    def blit_image(self, rect):
        """
        Zoom using relative anchor points based on rect position in the image.
        The anchor point is determined by where the rect is positioned,
        ensuring the rect stays in view throughout the zoom.
        """

        # Scale the image
        image_scaled = pygame.transform.smoothscale_by(self.current_img['surface'], self.scale)
        # progress from min_scale to max_scale.
        normalized_zoom = (self.scale - self.min_scale) / (self.current_img['max_scale'] - self.min_scale)
        
        img_surface = self.current_img['surface']
        
        # Calculate rect's relative position in the image (0 to 1)
        rect_center_x = rect.x + rect.width / 2
        rect_center_y = rect.y + rect.height / 2
        relative_x = rect_center_x / img_surface.get_width()
        relative_y = rect_center_y / img_surface.get_height()
        
        # At zoom start: position image so the relative_x/y point on the image is at relative_x/y in viewport
        # At zoom end: position image so the relative_x/y point on the RECT is at relative_x/y in viewport
        
        # The point at relative position in the image
        img_point_x = img_surface.get_width() * relative_x
        img_point_y = img_surface.get_height() * relative_y
        
        # The corresponding point at relative position WITHIN the rect
        # (e.g., if rect is at 10% of image, use 10% point within rect too)
        rect_local_x = rect.width * relative_x
        rect_local_y = rect.height * relative_y
        rect_point_x = rect.x + rect_local_x
        rect_point_y = rect.y + rect_local_y
        
        # Viewport position where we anchor
        viewport_anchor_x = self.viewport.get_width() * relative_x
        viewport_anchor_y = self.viewport.get_height() * relative_y
        
        # Interpolate between image point and rect point
        focus_x = img_point_x + (rect_point_x - img_point_x) * normalized_zoom
        focus_y = img_point_y + (rect_point_y - img_point_y) * normalized_zoom
        
        # Position scaled image so that focus point is at viewport anchor
        image_pos_x = viewport_anchor_x - focus_x * self.scale
        image_pos_y = viewport_anchor_y - focus_y * self.scale

        # Draw the scaled rect at its position on the scaled image
        rect_viewport_x = rect.x * self.scale + image_pos_x
        rect_viewport_y = rect.y * self.scale + image_pos_y
        rect_viewport_w = rect.width * self.scale
        rect_viewport_h = rect.height * self.scale
        
        # Draw
        self.viewport.fill((0, 0, 0))
        self.viewport.blit(image_scaled, (image_pos_x, image_pos_y))
        pygame.draw.rect(self.viewport, 'red', 
                        (rect_viewport_x, rect_viewport_y, rect_viewport_w, rect_viewport_h), 2)
        # Blit to screen occurs in main draw function.

    def get_rect(self, img_config):
        # Check for pixel coordinates first
        pixel_rect = img_config.get('nextPixelRect')
        if pixel_rect and len(pixel_rect) == 4:
            px, py, pw, ph = pixel_rect
            # Scale from original image coordinates to scaled surface coordinates
            scale_factor = self.current_img['scale']
            return pygame.Rect(
                px * scale_factor,
                py * scale_factor,
                pw * scale_factor,
                ph * scale_factor
            )
        
        # Fall back to relative coordinates
        rect = img_config.get('nextRect')
        if rect and len(rect) == 4:
            # Use scaled surface dimensions, not original
            img = self.current_img['surface']
            return pygame.Rect(
                img.get_width() * rect[0],
                img.get_height() * rect[1],
                img.get_width() * rect[2],
                img.get_height() * rect[3]
            )
            
        return None

    def draw(self):
        # Fill background
        self.screen.fill((17, 17, 17))  # #111111 in RGB
        # Draw background image
        current_bg = self.current_img['bg']
        self.screen.blit(current_bg, (0,0))

        img_config = self.current_img['config']
        rect = self.get_rect(img_config)
        
        # Get the original surface dimensions
        img_width = self.current_img['surface'].get_width()
        img_height = self.current_img['surface'].get_height()
        
        if rect:
            self.blit_image(rect)
            
        else:
            # No zoom, just center the image
            x = self.viewport.get_width()/2 - img_width/2
            y = self.viewport.get_height()/2 - img_height/2
            scaled_surface = self.current_img['surface']
            scaled_width = img_width
            scaled_height = img_height
        
            # Draw the image
            self.viewport.fill((0, 0, 0))  # Clear canvas
            self.viewport.blit(scaled_surface, (x,y))

        # Blit viewport to main screen
        self.screen.blit(self.viewport, self.viewport_rect)
        
        # Draw instructions
        instructions = "⬆ Zoom In    ⬇ Zoom Out"
        instr_surface = self.font.render(instructions, True, (153, 153, 153))
        instr_x = (self.width - instr_surface.get_width()) / 2
        self.screen.blit(instr_surface, (instr_x, self.height - 20))
        
        # Update display
        pygame.display.flip()

    def zoom_image(self, direction, zoom_factor=1.3):
        """
        Initiate zoom animation in the specified direction ('in' or 'out').
        Uses multiplicative zoom for consistent feel at all zoom levels.
        """
        if direction == 'in':
            new_scale = self.scale * zoom_factor
        elif direction == 'out':
            new_scale = self.scale / zoom_factor
        self.start_zoom_animation(new_scale)

    def swap_image_if_exceeded_zoom_boundaries(self):
        if self.scale > self.current_img['max_scale']:
            if self.current_index < len(self.images) - 1: # check if next image exists
                self.current_index += 1
                self.current_img = self.images[self.current_index]
                self.scale = self.min_scale  # Reset scale before next animation
            else:
                self.scale = 1.0  # stay at min scale, nothing to zoom into anymore.
            return True
        elif self.scale < self.min_scale:
            # Check if we can go to previous image
            if self.current_index > 0:
                self.current_index -= 1
                self.current_img = self.images[self.current_index]
                self.scale = self.current_img['max_scale']  # Set to max scale for previous image
            else:
                # If we can't go to previous image, stay at min scale
                self.scale = self.min_scale
            return True
        return False

    def start_zoom_animation(self, target, start=None):
        """
        Start a zoom animation towards the target scale.
        If already animating, just update the target.
        """
        self.is_animating = True
        self.animation_start_time = pygame.time.get_ticks()
        self.target_scale = target
        self.start_scale = start if start is not None else self.scale

    def handle_step_animation(self):
        """
        Handle automatic scaling for a single pressed key event.
        """
        if not self.is_animating:
            return
        
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.animation_start_time
        animation_progress = min(1.0, elapsed / self.animation_duration)
        
        if animation_progress >= 1.0:
            # Animation complete
            self.is_animating = False
            self.scale = self.target_scale  # Ensure we're exactly at target
            animation_progress = 1.0
        else:
            self.scale = self.start_scale + (self.target_scale - self.start_scale) * animation_progress
            swapped = self.swap_image_if_exceeded_zoom_boundaries()          
            if swapped:
                self.is_animating = False
                animation_progress = 1.0
        
    def handle_continuous_zoom(self):
        keys = pygame.key.get_pressed()
        
        # Use multiplicative zoom for consistent feel at all zoom levels
        zoom_factor = 1.01  # 1% change per frame
        
        if keys[pygame.K_UP]:  # Continuous zoom in
            self.scale = self.scale * zoom_factor

        elif keys[pygame.K_DOWN]:  # Continuous zoom out
            self.scale = self.scale / zoom_factor

        swapped = self.swap_image_if_exceeded_zoom_boundaries()


    def run(self):
        running = True
        last_key_time = {}  # Track last key press time for each key
        key_delay = 200  # Milliseconds to wait before starting continuous zoom
        
        while running:
            current_time = pygame.time.get_ticks()
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_UP, pygame.K_DOWN]:
                        last_key_time[event.key] = current_time
                        # Initial key press handles single step zoom
                        if event.key == pygame.K_UP:  # Zoom in
                            self.zoom_image('in')                        

                        elif event.key == pygame.K_DOWN:  # Zoom out
                            self.zoom_image('out')
                
                elif event.type == pygame.KEYUP:
                    if event.key in last_key_time:
                        del last_key_time[event.key]
            
            # Handle continuous zoom after initial delay
            keys = pygame.key.get_pressed()
            for key in [pygame.K_UP, pygame.K_DOWN]:
                if (key in last_key_time and 
                    current_time - last_key_time[key] > key_delay and 
                    keys[key]):
                    self.handle_continuous_zoom()

            # Handle animation
            self.handle_step_animation()
            
            # Draw everything
            self.draw()
            
            # Control frame rate
            self.clock.tick(self.FPS)

        pygame.quit()

if __name__ == "__main__":
    viewer = ZoomViewer()
    viewer.run()