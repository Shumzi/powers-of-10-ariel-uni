import pygame
import json
import os
from urllib.parse import unquote

def ease_in_out_cubic(x):
    if x < 0.5:
        return 4 * x * x * x
    return 1 - pow(-2 * x + 2, 3) / 2

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
        self.continuous_zoom_speed = 0.02  # Speed factor for continuous zooming
        
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
                # Use the first dimension (width) of the rectangle to determine zoom scale
                # This ensures the zoomed view matches the rectangle's width
                width_scale = 1/rect[2] if isinstance(rect[2], float) else original.get_width() / rect[2]
                height_scale = 1/rect[3] if isinstance(rect[3], float) else original.get_height() / rect[3]
                max_scale = min(width_scale, height_scale)
            self.images[-1]['max_scale'] = max_scale

        self.current_img = self.images[self.current_index]  # Reset to first image


    def get_rect(self, img_config):
        # Check for pixel coordinates first
        pixel_rect = img_config.get('nextPixelRect')
        if pixel_rect and len(pixel_rect) == 4:
            px, py, pw, ph = pixel_rect
            img = self.current_img['original']
            return [px/img.get_width(), py/img.get_height(), 
                   pw/img.get_width(), ph/img.get_height()]
        
        # Fall back to relative coordinates
        rect = img_config.get('nextRect')
        if rect and len(rect) == 4:
            return rect
            
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
            zoom_progress = (self.scale - self.min_scale) / (self.current_img['max_scale'] - self.min_scale)
            # Calculate center of the target rectangle
            cx = rect[0] + rect[2]/2
            cy = rect[1] + rect[3]/2
            # Calculate scaled dimensions
            scaled_width = img_width * self.scale
            scaled_height = img_height * self.scale
            # Calculate position to center the rectangle in the viewport
            x = rect[0] * scaled_width * zoom_progress
            y = rect[1] * scaled_height * zoom_progress
            scaled_surface = pygame.transform.smoothscale(self.current_img['surface'], 
                                                          (scaled_width, scaled_height))
            
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

        # Draw outline if rect exists
        if rect:
            # Get outline color
            default_color = self.config.get('defaultOutlineColor', '#00ff88')
            outline_color = img_config.get('outlineColor', default_color)
            
            # Convert hex color to RGB
            if outline_color.startswith('#'):
                outline_color = outline_color[:7]  # Remove alpha if present
                r = int(outline_color[1:3], 16)
                g = int(outline_color[3:5], 16)
                b = int(outline_color[5:7], 16)
                outline_color = (r, g, b)
            
            # Calculate outline rectangle position and size
            rx, ry, rw, rh = rect
            outline_x = x + rx * scaled_width
            outline_y = y + ry * scaled_height
            outline_w = rw * scaled_width
            outline_h = rh * scaled_height
            
            # Draw rectangle outline
            pygame.draw.rect(self.viewport, outline_color, 
                           (outline_x, outline_y, outline_w, outline_h), 2)
            self.screen.blit(self.viewport, self.viewport_rect)
        
        # Blit viewport to main screen
        self.screen.blit(self.viewport, self.viewport_rect)
        
        # Draw caption
        caption = img_config['caption']
        caption_surface = self.font.render(caption, True, (238, 238, 238))
        caption_x = (self.width - caption_surface.get_width()) / 2
        self.screen.blit(caption_surface, (caption_x, self.height - 40))
        
        # Draw instructions
        instructions = "⬆ Zoom In    ⬇ Zoom Out"
        instr_surface = self.font.render(instructions, True, (153, 153, 153))
        instr_x = (self.width - instr_surface.get_width()) / 2
        self.screen.blit(instr_surface, (instr_x, self.height - 20))
        
        # Update display
        pygame.display.flip()

    def zoom_image(self, direction, scale_step=0.05):
        """
        Initiate zoom animation in the specified direction ('in' or 'out')."""
        if direction == 'in':
            new_scale = self.scale + (self.current_img['max_scale'] - self.min_scale) * scale_step
        elif direction == 'out':
            new_scale = self.scale - (self.current_img['max_scale'] - self.min_scale) * scale_step
        self.start_zoom_animation(new_scale)

    def handle_step_animation(self):
        """
        Handle automatic scaling for a single pressed key event.
        """
        if not self.is_animating:
            return
        
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.animation_start_time
        progress = min(1.0, elapsed / self.animation_duration)
        
        # # Apply easing function
        # eased_progress = ease_in_out_cubic(progress)
        
        # Calculate current scale
        self.scale = self.start_scale + (self.target_scale - self.start_scale) * progress
        
        if progress >= 1.0:
            # Animation complete
            self.is_animating = False
            self.scale = self.target_scale  # Ensure we're exactly at target
            
            self.swap_image_if_exceeded_zoom_boundaries()
        
    def swap_image_if_exceeded_zoom_boundaries(self):
        if self.scale > self.current_img['max_scale']:
            if self.current_index < len(self.images) - 1: # check if next image exists
                self.current_index += 1
                self.current_img = self.images[self.current_index]
                self.scale = self.min_scale  # Reset scale before next animation
            else:
                self.scale = self.min_scale  # stay at min scale, nothing to zoom into anymore.
        elif self.scale < self.min_scale:
            # Check if we can go to previous image
            if self.current_index > 0:
                self.current_index -= 1
                self.current_img = self.images[self.current_index]
                self.scale = self.current_img['max_scale']  # Set to max scale for previous image
            else:
                # If we can't go to previous image, stay at min scale
                self.scale = self.min_scale
        elif self.current_index == len(self.images) - 1:
            self.scale = self.min_scale  # stay at min scale, nowhere to zoom into...

    def start_zoom_animation(self, target, start=None):
        """
        Start a zoom animation towards the target scale.
        If already animating, just update the target.
        """
        self.is_animating = True
        self.animation_start_time = pygame.time.get_ticks()
        self.target_scale = target
        self.start_scale = start if start is not None else self.scale

    def handle_continuous_zoom(self):
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_UP]:  # Continuous zoom in
            self.scale = self.scale + self.continuous_zoom_speed

        elif keys[pygame.K_DOWN]:  # Continuous zoom out
            self.scale = self.scale - self.continuous_zoom_speed

        self.swap_image_if_exceeded_zoom_boundaries()


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