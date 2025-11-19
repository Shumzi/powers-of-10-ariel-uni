"""
Powers of Ten Viewer - Refactored version with proper separation of concerns
Main application that coordinates all components
"""
import pygame
import json
from image_manager import ImageManager
from tile_image_manager import TileImageManager
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
        # Use TileImageManager if tile caching is enabled, otherwise use standard ImageManager
        use_tiles = self.config.get('use_tile_cache', False)
        if use_tiles:
            print("Using tile-based image manager for optimized zoom performance")
            self.image_manager = TileImageManager(self.config, self.viewport_dims)
        else:
            print("Using standard image manager")
            self.image_manager = ImageManager(self.config, self.viewport_dims)
        
        self.image_manager.load_images()
        
        self.zoom_controller = ZoomController()
        # Set initial max scale
        self.zoom_controller.set_max_scale(
            self.image_manager.get_current_image().max_scale
        )
        
        self.transition_manager = TransitionManager(self.config, self.viewport_dims)
        self.transition_manager.load_all_transitions()
        
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
    
    def _handle_input(self, dt):
        """Process input events and handle actions"""
        input_start = pygame.time.get_ticks()
        actions = self.input_handler.process_events(self.transition_manager.is_active(), dt)
        
        for action in actions:
            if action[0] == 'quit':
                return False  # Signal to stop running
            elif action[0] == 'zoom_step':
                self.zoom_controller.zoom_step(action[1])
            elif action[0] == 'zoom_continuous':
                self.zoom_controller.zoom_continuous(action[1], action[2])  # direction, dt
            elif action[0] == 'toggle_debug':
                self.debug_mode = not self.debug_mode 
                print(f"Debug mode: {'ON' if self.debug_mode else 'OFF'}")
        
        self.perf_stats['input'] = pygame.time.get_ticks() - input_start
        return True  # Continue running
    
    def _handle_boundary_transition(self, boundary_direction):
        """Handle zoom boundary crossing and image transitions"""
        # Check if we can navigate in the boundary direction
        if boundary_direction == 'forward':
            can_transition = self.image_manager.can_go_next()
        else:  # 'backward'
            can_transition = self.image_manager.can_go_previous()
        
        if can_transition:
            # Start the transition animation
            self.transition_manager.start_transition(boundary_direction)
        else:
            # Can't transition - clamp scale to boundaries
            self.zoom_controller.clamp_scale()
    
    def _update_state(self):
        """Update zoom and transition state"""
        update_start = pygame.time.get_ticks()
        
        # Update zoom state and check boundaries
        boundary_direction = self.zoom_controller.update()
        if boundary_direction:
            self._handle_boundary_transition(boundary_direction)
        
        # Update transition animation
        transition_complete = self.transition_manager.update()
        if transition_complete:
            # Transition just finished - sync image manager to match transition manager position
            self.image_manager.set_image(self.transition_manager.transition_idx)
            
            # Update max scale for new image
            self.zoom_controller.set_max_scale(
                self.image_manager.get_current_image().max_scale
            )
            
            # Reset zoom to appropriate level based on direction
            if self.transition_manager.transition_direction == 'backward':
                self.zoom_controller.reset_to_max()
            else:
                self.zoom_controller.reset_to_min()
        
        self.perf_stats['update'] = pygame.time.get_ticks() - update_start
    
    def _render_frame(self):
        """Render current frame"""
        render_start = pygame.time.get_ticks()
        fps = self.clock.get_fps()
        avg_frame_time = sum(self.frame_times) / len(self.frame_times) if self.frame_times else 0
        self.renderer.draw_frame(
            self.image_manager, self.zoom_controller, self.transition_manager, 
            fps, self.debug_mode, self.perf_stats, avg_frame_time
        )
        self.perf_stats['render'] = pygame.time.get_ticks() - render_start
    
    def _track_performance(self, frame_start):
        """Track frame timing for performance monitoring"""
        frame_time = pygame.time.get_ticks() - frame_start
        self.perf_stats['total'] = frame_time
        self.frame_times.append(frame_time)
        if len(self.frame_times) > self.max_frame_samples:
            self.frame_times.pop(0)
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            frame_start = pygame.time.get_ticks()
            dt = self.clock.get_time() / 1000.0
            
            # Process input
            running = self._handle_input(dt)
            if not running:
                break
            
            # Update state
            self._update_state()
            
            # Render
            self._render_frame()
            
            # Track performance
            self._track_performance(frame_start)
            
            # Control frame rate
            self.clock.tick(self.FPS)
        
        pygame.quit()


if __name__ == "__main__":
    viewer = ZoomViewer()
    viewer.run()
