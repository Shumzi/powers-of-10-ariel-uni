"""
Transition Manager - Handles transition animations between images
"""
import pygame
import os


class TransitionManager:
    """Manages transition animations between images"""
    
    def __init__(self, viewport_dims, transition_dir='sample transitions'):
        self.viewport_dims = viewport_dims
        self.transition_dir = transition_dir
        
        self.is_transitioning = False
        self.transition_frames = []
        self.transition_frame_index = 0
        self.transition_start_time = None
        self.transition_fps = 30
        self.transition_direction = None
        self.pending_image_index = None
    
    def load_transition_frames(self):
        """Load transition frames from directory"""
        if os.path.exists(self.transition_dir):
            frame_files = sorted([f for f in os.listdir(self.transition_dir) if f.endswith('.png')])
            print(f"Loading {len(frame_files)} transition frames from {self.transition_dir}")
            
            for frame_file in frame_files:
                frame_path = os.path.join(self.transition_dir, frame_file)
                frame = pygame.image.load(frame_path).convert_alpha()
                
                # Scale frame to fit viewport
                scale = min(self.viewport_dims[0] / frame.get_width(), 
                           self.viewport_dims[1] / frame.get_height())
                new_size = (int(frame.get_width() * scale),
                           int(frame.get_height() * scale))
                scaled_frame = pygame.transform.smoothscale(frame, new_size)
                
                self.transition_frames.append(scaled_frame)
            
            print(f"Loaded {len(self.transition_frames)} frames")
        else:
            print(f"Transition directory not found: {self.transition_dir}")
    
    def start_transition(self, direction, target_index):
        """Start transition animation"""
        self.is_transitioning = True
        self.transition_frame_index = 0
        self.transition_start_time = pygame.time.get_ticks()
        self.transition_direction = direction  # 'forward' or 'backward'
        self.pending_image_index = target_index
    
    def update(self):
        """Update transition animation and return completion status"""
        if not self.is_transitioning or len(self.transition_frames) == 0:
            return False
        
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.transition_start_time
        
        # Calculate which frame to show
        frame_duration = 1000 / self.transition_fps
        target_frame = int(elapsed / frame_duration)
        
        if target_frame >= len(self.transition_frames):
            # Transition complete
            self.is_transitioning = False
            return True
        else:
            # Update frame index - reverse if going backward
            if self.transition_direction == 'backward':
                self.transition_frame_index = len(self.transition_frames) - 1 - target_frame
            else:
                self.transition_frame_index = target_frame
            return False
    
    def get_current_frame(self):
        """Get the current transition frame"""
        if self.transition_frame_index < len(self.transition_frames):
            return self.transition_frames[self.transition_frame_index]
        return None
    
    def is_active(self):
        """Check if transition is currently playing"""
        return self.is_transitioning
