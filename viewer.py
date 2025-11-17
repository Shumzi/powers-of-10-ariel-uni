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
        
        # Performance monitoring
        self.debug_mode = False
        self.frame_times = []
        self.max_frame_samples = 60
        self.perf_stats = {
            'input': 0,
            'update': 0,
            'render': 0,
            'total': 0
        }
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            frame_start = pygame.time.get_ticks()
            current_time = frame_start
            
            # Process input
            input_start = pygame.time.get_ticks()
            actions = self.input_handler.process_events(self.transition_manager.is_active())
            
            for action in actions:
                if action[0] == 'quit':
                    running = False
                elif action[0] == 'zoom_step':
                    self.zoom_controller.zoom_step(action[1])
                elif action[0] == 'toggle_debug':
                    self.debug_mode = not self.debug_mode
                    print(f"Debug mode: {'ON' if self.debug_mode else 'OFF'}")
            
            self.perf_stats['input'] = pygame.time.get_ticks() - input_start
            
            # Check continuous zoom
            update_start = pygame.time.get_ticks()
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
            
            self.perf_stats['update'] = pygame.time.get_ticks() - update_start
            
            # Render
            render_start = pygame.time.get_ticks()
            fps = self.clock.get_fps()
            avg_frame_time = sum(self.frame_times) / len(self.frame_times) if self.frame_times else 0
            self.renderer.draw_frame(self.image_manager, self.zoom_controller, self.transition_manager, 
                                    fps, self.debug_mode, self.perf_stats, avg_frame_time)
            self.perf_stats['render'] = pygame.time.get_ticks() - render_start
            
            # Track frame time
            frame_time = pygame.time.get_ticks() - frame_start
            self.perf_stats['total'] = frame_time
            self.frame_times.append(frame_time)
            if len(self.frame_times) > self.max_frame_samples:
                self.frame_times.pop(0)
            
            # Control frame rate
            self.clock.tick(self.FPS)
        
        pygame.quit()


if __name__ == "__main__":
    viewer = ZoomViewer()
    viewer.run()
