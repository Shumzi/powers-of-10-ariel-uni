"""
Input Handler - Processes user input
"""
import pygame


class InputHandler:
    """Handles keyboard input and timing"""
    
    def __init__(self):
        self.last_key_time = {}
        self.key_delay = 200  # Milliseconds before continuous zoom starts
    
    def process_events(self, transition_active):
        """Process pygame events and return actions"""
        actions = []
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                actions.append(('quit', None))
            
            # Ignore input during transition
            elif not transition_active:
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_UP, pygame.K_DOWN]:
                        self.last_key_time[event.key] = current_time
                        
                        if event.key == pygame.K_UP:
                            actions.append(('zoom_step', 'in'))
                        elif event.key == pygame.K_DOWN:
                            actions.append(('zoom_step', 'out'))
                    
                    elif event.key == pygame.K_d:
                        actions.append(('toggle_debug', None))
                
                elif event.type == pygame.KEYUP:
                    if event.key in self.last_key_time:
                        del self.last_key_time[event.key]
        
        return actions
    
    def check_continuous_zoom(self, transition_active, dt):
        """Check for continuous zoom input and return action"""
        if transition_active:
            return None
        
        current_time = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()
        
        for key in [pygame.K_UP, pygame.K_DOWN]:
            if (key in self.last_key_time and 
                current_time - self.last_key_time[key] > self.key_delay and 
                keys[key]):
                
                direction = 'in' if key == pygame.K_UP else 'out'
                return ('zoom_continuous', direction, dt)
        
        return None
