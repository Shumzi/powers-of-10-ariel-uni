"""
Powers of Ten Viewer - Refactored version with proper separation of concerns
Main application that coordinates all components
"""
import pygame
import json
from image_manager import ImageManager
from zoom_controller import ZoomController
from transition_manager import TransitionManager
from renderer import Renderer
from input_handler import InputHandler


class ZoomViewer:
    """Main application coordinator"""
    
    def __init__(self):
        pygame.init()
        
        # Display setup
        self.width = 1600
        self.height = 919
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Powers of Ten Viewer")
        
        self.viewport_dims = (720, 720)
        self.viewport_rect = pygame.Rect(812, 76, *self.viewport_dims)
        
        # Font setup
        self.font = pygame.font.SysFont('Arial', 16)
        
        # Load configuration
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Initialize components
        self.image_manager = ImageManager(self.config, self.viewport_dims)
        self.image_manager.load_images()
        
        self.zoom_controller = ZoomController(self.image_manager)
        
        self.transition_manager = TransitionManager(self.viewport_dims, 'sample transitions')
        self.transition_manager.load_transition_frames()
        
        self.renderer = Renderer(self.screen, self.viewport_dims, self.viewport_rect, self.font)
        
        self.input_handler = InputHandler()
        
        # Clock for frame rate control
        self.clock = pygame.time.Clock()
        self.FPS = 60
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            current_time = pygame.time.get_ticks()
            
            # Process input
            actions = self.input_handler.process_events(self.transition_manager.is_active())
            
            for action in actions:
                if action[0] == 'quit':
                    running = False
                elif action[0] == 'zoom_step':
                    self.zoom_controller.zoom_step(action[1])
            
            # Check continuous zoom
            dt = self.clock.get_time() / 1000.0
            continuous_action = self.input_handler.check_continuous_zoom(
                self.transition_manager.is_active(), dt
            )
            
            if continuous_action:
                _, direction, dt = continuous_action
                self.zoom_controller.zoom_continuous(direction, dt)
                
                # Check if continuous zoom triggered boundary
                transition_info = self.zoom_controller.check_boundaries_continuous()
                if transition_info:
                    direction, target_index = transition_info
                    self.transition_manager.start_transition(direction, target_index)
            
            # Update animations
            boundary_info = self.zoom_controller.update_step_animation()
            if boundary_info:
                direction, target_index = boundary_info
                self.transition_manager.start_transition(direction, target_index)
            
            # Update transition
            transition_complete = self.transition_manager.update()
            if transition_complete:
                # Switch to pending image
                self.image_manager.current_index = self.transition_manager.pending_image_index
                
                # Set appropriate zoom level
                if self.transition_manager.transition_direction == 'backward':
                    self.zoom_controller.reset_to_max()
                else:
                    self.zoom_controller.reset_to_min()
            
            # Render
            self.renderer.draw_frame(self.image_manager, self.zoom_controller, self.transition_manager)
            
            # Control frame rate
            self.clock.tick(self.FPS)
        
        pygame.quit()


if __name__ == "__main__":
    viewer = ZoomViewer()
    viewer.run()
