import pygame
import json
import os
from urllib.parse import unquote
import math

def ease_in_out_cubic(x):
    if x < 0.5:
        return 4 * x * x * x
    return 1 - pow(-2 * x + 2, 3) / 2

class ZoomViewer:
    def __init__(self):
        pygame.init()
        
        # Initialize display
        self.width = 600
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Powers of Ten Viewer")
        
        # Font setup
        self.font = pygame.font.SysFont('Arial', 16)
        
        # Load configuration
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
            
        # Initialize variables
        self.current_index = 0
        self.scale = 1.0
        self.min_scale = 1.0
        self.max_scale = 2.0
        
        # Animation properties
        self.animation_duration = 300  # milliseconds
        self.target_scale = 1.0
        self.start_scale = 1.0
        self.animation_start_time = None
        self.is_animating = False
        
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
            
            # Load and scale image
            original = pygame.image.load(image_path).convert_alpha()
            
            # Calculate scaling to fit 600x600 while maintaining aspect ratio
            scale = min(self.width / original.get_width(), 
                       self.height / original.get_height())
            
            new_size = (int(original.get_width() * scale),
                       int(original.get_height() * scale))
            
            scaled = pygame.transform.smoothscale(original, new_size)
            
            self.images.append({
                'config': img_config,
                'original': original,
                'surface': scaled,
                'scale': scale
            })

    def get_rect(self, img_config):
        # Check for pixel coordinates first
        pixel_rect = img_config.get('nextPixelRect')
        if pixel_rect and len(pixel_rect) == 4:
            px, py, pw, ph = pixel_rect
            img = self.images[self.current_index]['original']
            return [px/img.get_width(), py/img.get_height(), 
                   pw/img.get_width(), ph/img.get_height()]
        
        # Fall back to relative coordinates
        rect = img_config.get('nextRect')
        if rect and len(rect) == 4:
            return rect
            
        return None

    def has_next_zoom(self):
        current_config = self.images[self.current_index]['config']
        rect = current_config.get('nextRect')
        pixel_rect = current_config.get('nextPixelRect')
        return not (rect in [None, []] and pixel_rect in [None, []])

    def draw(self):
        # Fill background
        self.screen.fill((17, 17, 17))  # #111111 in RGB
        
        current = self.images[self.current_index]
        img_config = current['config']
        rect = self.get_rect(img_config)
        
        # Get the original surface dimensions
        img_width = current['surface'].get_width()
        img_height = current['surface'].get_height()
        
        if rect and self.scale > 1.0:
            # Calculate center of the target rectangle
            cx = rect[0] + rect[2]/2
            cy = rect[1] + rect[3]/2
            
            # Calculate zoom progress
            zoom_progress = (self.scale - self.min_scale) / (self.max_scale - self.min_scale)
            
            # Interpolate between original position and zoomed position
            target_x = cx * img_width
            target_y = cy * img_height
            current_x = img_width/2 + (target_x - img_width/2) * zoom_progress
            current_y = img_height/2 + (target_y - img_height/2) * zoom_progress
            
            # Calculate the scaled dimensions
            scaled_width = int(img_width * self.scale)
            scaled_height = int(img_height * self.scale)
            
            # Create scaled surface
            scaled_surface = pygame.transform.smoothscale(
                current['surface'], 
                (scaled_width, scaled_height)
            )
            
            # Calculate position to center the zoomed part
            x = self.width/2 - current_x * self.scale
            y = self.height/2 - current_y * self.scale
            
        else:
            # No zoom, just center the image
            x = self.width/2 - img_width/2
            y = self.height/2 - img_height/2
            scaled_surface = current['surface']
            scaled_width = img_width
            scaled_height = img_height
        
        # Draw the image
        self.screen.blit(scaled_surface, (x, y))
        
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
            pygame.draw.rect(self.screen, outline_color, 
                           (outline_x, outline_y, outline_w, outline_h), 2)
        
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

    def handle_animation(self):
        if not self.is_animating:
            return
        
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.animation_start_time
        progress = min(1.0, elapsed / self.animation_duration)
        
        # Apply easing function
        eased_progress = ease_in_out_cubic(progress)
        
        # Calculate current scale
        self.scale = self.start_scale + (self.target_scale - self.start_scale) * eased_progress
        
        if progress >= 1.0:
            # Animation complete
            self.is_animating = False
            
            # Check if we need to switch images
            if self.scale >= self.max_scale and self.current_index < len(self.images) - 1:
                next_config = self.images[self.current_index + 1]['config']
                if (next_config.get('nextRect') is not None or
                    next_config.get('nextPixelRect') is not None):
                    self.current_index += 1
                    self.start_zoom_animation(self.min_scale, self.max_scale)

    def start_zoom_animation(self, target, start=None):
        self.is_animating = True
        self.animation_start_time = pygame.time.get_ticks()
        self.target_scale = target
        self.start_scale = start if start is not None else self.scale

    def handle_continuous_zoom(self):
        keys = pygame.key.get_pressed()
        
        # Only handle continuous zoom if not already animating
        if not self.is_animating:
            if keys[pygame.K_UP]:  # Continuous zoom in
                if self.has_next_zoom():
                    new_scale = min(self.scale + (self.max_scale - self.min_scale) / 60,  # Slower continuous zoom
                                  self.max_scale)
                    if new_scale >= self.max_scale:
                        # If we hit max zoom, trigger animation to next image
                        if (self.current_index < len(self.images) - 1 and
                            (self.images[self.current_index + 1]['config'].get('nextRect') is not None or
                             self.images[self.current_index + 1]['config'].get('nextPixelRect') is not None)):
                            self.current_index += 1
                            self.scale = self.min_scale
                    else:
                        self.scale = new_scale

            elif keys[pygame.K_DOWN]:  # Continuous zoom out
                if self.scale > self.min_scale:
                    new_scale = max(self.scale - (self.max_scale - self.min_scale) / 60,  # Slower continuous zoom
                                  self.min_scale)
                    self.scale = new_scale
                elif self.current_index > 0:  # At minimum zoom, go to previous image
                    self.current_index -= 1
                    if self.has_next_zoom():
                        self.scale = self.max_scale

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
                            if not self.has_next_zoom() or self.is_animating:
                                continue
                            new_scale = min(self.scale + (self.max_scale - self.min_scale) / 20, 
                                          self.max_scale)
                            self.start_zoom_animation(new_scale)
                        
                        elif event.key == pygame.K_DOWN:  # Zoom out
                            if self.is_animating:
                                continue
                            if self.scale > self.min_scale:
                                new_scale = max(self.scale - (self.max_scale - self.min_scale) / 20,
                                              self.min_scale)
                                self.start_zoom_animation(new_scale)
                            elif self.current_index > 0:
                                self.current_index -= 1
                                if self.has_next_zoom():
                                    self.start_zoom_animation(self.max_scale)
                
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
            self.handle_animation()
            
            # Draw everything
            self.draw()
            
            # Control frame rate
            self.clock.tick(self.FPS)

        pygame.quit()

if __name__ == "__main__":
    viewer = ZoomViewer()
    viewer.run()