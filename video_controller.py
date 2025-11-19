import pygame
import cv2
import numpy as np
import os
import subprocess

# Initialize Pygame
pygame.init()

# Screen setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Video Scrubber")

# Video paths
video_path = "sample transitions/non-optimized.mp4"
reversed_video_path = "sample transitions/non-optimized_reversed.mp4"

# Create reversed video if it doesn't exist
if not os.path.exists(reversed_video_path):
    print("Creating reversed video...")
    subprocess.run([
        'ffmpeg', '-i', video_path,
        '-vf', 'reverse',
        '-af', 'areverse',
        reversed_video_path
    ])
    print("Reversed video created!")

# OpenCV video setup
cap_forward = cv2.VideoCapture(video_path)
cap_backward = cv2.VideoCapture(reversed_video_path)

# Get video properties
fps = cap_forward.get(cv2.CAP_PROP_FPS)
total_frames = int(cap_forward.get(cv2.CAP_PROP_FRAME_COUNT))

# Current playback position (in forward video frame numbers)
current_frame = 0
last_frame = None

# Playback state
is_playing_forward = False
is_playing_backward = False

# Main loop
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                # Switch to forward playback
                if not is_playing_forward:
                    is_playing_forward = True
                    is_playing_backward = False
                    # Sync forward video to current position
                    cap_forward.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            elif event.key == pygame.K_DOWN:
                # Switch to backward playback
                if not is_playing_backward:
                    is_playing_backward = True
                    is_playing_forward = False
                    # Sync backward video to mirrored position
                    backward_frame = total_frames - current_frame - 1
                    cap_backward.set(cv2.CAP_PROP_POS_FRAMES, backward_frame)
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_UP:
                is_playing_forward = False
            elif event.key == pygame.K_DOWN:
                is_playing_backward = False
    
    # Read frame if playing (sequential read, no seeking)
    if is_playing_forward:
        ret, frame = cap_forward.read()
        if ret:
            last_frame = frame
            current_frame = min(current_frame + 1, total_frames - 1)
        else:
            # Reached end
            is_playing_forward = False
            current_frame = total_frames - 1
    elif is_playing_backward:
        ret, frame = cap_backward.read()
        if ret:
            last_frame = frame
            current_frame = max(current_frame - 1, 0)
        else:
            # Reached beginning
            is_playing_backward = False
            current_frame = 0
    
    # Display the last frame
    if last_frame is not None:
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(last_frame, cv2.COLOR_BGR2RGB)
        # Convert to pygame surface (transpose for correct orientation)
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
    
    info_text = font.render(f"Time: {current_time:.1f}s / {total_time:.1f}s", True, (255, 255, 255))
    frame_text = font.render(f"Frame: {current_frame}/{total_frames}", True, (255, 255, 255))
    controls_text = font.render("UP: Play Forward | DOWN: Play Backward (hold)", True, (255, 255, 255))
    
    screen.blit(info_text, (10, 10))
    screen.blit(frame_text, (10, 40))
    screen.blit(controls_text, (10, 70))
    
    pygame.display.flip()
    clock.tick(int(fps))  # Match video FPS

# Cleanup
cap_forward.release()
cap_backward.release()
pygame.quit()