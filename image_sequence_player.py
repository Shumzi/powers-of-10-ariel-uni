import pygame
import cv2
import numpy as np
import os
import glob

# Initialize Pygame
pygame.init()

# Screen setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Image Sequence Player")

# Load frames directory
frames_dir = "frames"
if not os.path.exists(frames_dir):
    print(f"Error: Frames directory '{frames_dir}' not found!")
    print("Run convert_to_frames.py first to create the image sequence.")
    pygame.quit()
    exit(1)

# Load metadata
metadata_path = os.path.join(frames_dir, "metadata.txt")
fps = 24.0  # default
total_frames = 0

if os.path.exists(metadata_path):
    with open(metadata_path, 'r') as f:
        for line in f:
            if line.startswith('fps='):
                fps = float(line.split('=')[1])
            elif line.startswith('total_frames='):
                total_frames = int(line.split('=')[1])

# Get list of frame files
frame_files = sorted(glob.glob(os.path.join(frames_dir, "frame_*.jpg")))
if not frame_files:
    print(f"Error: No frame images found in '{frames_dir}'")
    pygame.quit()
    exit(1)

total_frames = len(frame_files)
print(f"Loaded {total_frames} frames at {fps} FPS")

# Current playback state
current_frame = 0
last_displayed_frame = None
is_playing_forward = False
is_playing_backward = False

# Cache for loaded images (optional - preload for better performance)
USE_CACHE = True
frame_cache = {}

def load_frame(frame_index):
    """Load a frame from disk or cache"""
    if USE_CACHE and frame_index in frame_cache:
        return frame_cache[frame_index]
    
    if 0 <= frame_index < total_frames:
        frame = cv2.imread(frame_files[frame_index])
        if frame is not None:
            if USE_CACHE:
                frame_cache[frame_index] = frame
            return frame
    return None

# Preload all frames (optional - for instant playback)
PRELOAD_ALL = False
if PRELOAD_ALL:
    print("Preloading all frames...")
    for i in range(total_frames):
        load_frame(i)
        if i % 100 == 0:
            print(f"Loaded {i}/{total_frames} frames...")
    print("✓ All frames preloaded!")

# Load initial frame
last_displayed_frame = load_frame(0)

# Main loop
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                is_playing_forward = True
                is_playing_backward = False
            elif event.key == pygame.K_DOWN:
                is_playing_backward = True
                is_playing_forward = False
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_UP:
                is_playing_forward = False
            elif event.key == pygame.K_DOWN:
                is_playing_backward = False
    
    # Update frame based on playback state
    if is_playing_forward:
        current_frame = min(current_frame + 1, total_frames - 1)
        frame = load_frame(current_frame)
        if frame is not None:
            last_displayed_frame = frame
    elif is_playing_backward:
        current_frame = max(current_frame - 1, 0)
        frame = load_frame(current_frame)
        if frame is not None:
            last_displayed_frame = frame
    
    # Display the current frame
    if last_displayed_frame is not None:
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(last_displayed_frame, cv2.COLOR_BGR2RGB)
        # Convert to pygame surface
        frame_surface = pygame.surfarray.make_surface(np.transpose(frame_rgb, (1, 0, 2)))
        # Scale to fit screen
        frame_surface = pygame.transform.scale(frame_surface, (WIDTH, HEIGHT))
        screen.blit(frame_surface, (0, 0))
    else:
        screen.fill((0, 0, 0))
    
    # Display info overlay
    font = pygame.font.Font(None, 36)
    
    current_time = current_frame / fps if fps > 0 else 0
    total_time = total_frames / fps if fps > 0 else 0
    
    # Semi-transparent background for text
    info_bg = pygame.Surface((WIDTH, 100))
    info_bg.set_alpha(128)
    info_bg.fill((0, 0, 0))
    screen.blit(info_bg, (0, 0))
    
    status = "Playing Forward" if is_playing_forward else ("Playing Backward" if is_playing_backward else "Paused")
    status_text = font.render(f"{status} - {current_time:.1f}s / {total_time:.1f}s", True, (255, 255, 255))
    frame_text = font.render(f"Frame: {current_frame}/{total_frames}", True, (255, 255, 255))
    controls_text = font.render("UP: Play Forward | DOWN: Play Backward (hold)", True, (255, 255, 255))
    
    screen.blit(status_text, (10, 10))
    screen.blit(frame_text, (10, 40))
    screen.blit(controls_text, (10, 70))
    
    pygame.display.flip()
    clock.tick(int(fps))

# Cleanup
pygame.quit()
