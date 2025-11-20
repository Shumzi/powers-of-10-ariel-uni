
import pygame
import numpy as np
import cv2
import viewer
from tqdm import tqdm
import subprocess

class Recorder(viewer.ZoomViewer):
    def __init__(self):
        super().__init__()
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.filename = 'transition2.mp4'
        self.fps = 24
        self.video = cv2.VideoWriter(self.filename, fourcc, self.fps, self.screen.get_size())
        self.rate_of_slowness = 1.5  # Speed multiplier for zooming

    def run(self):

        prev_array = None
        frame_count = 0
        with tqdm(total=len(self.image_manager.images), desc="image # being processed") as pbar:
            while self.image_manager.current_index < len(self.image_manager.images) - 1:
                frame_start = pygame.time.get_ticks()
                dt = self.clock.get_time() / 1000.0
            
                # Process input
                if not self.transition_manager.is_active():
                    self.zoom_controller.zoom_continuous('in', 1/(self.fps*self.rate_of_slowness))

                # Update state
                transition_complete = self._update_state()
                
                if transition_complete:
                    pbar.update(1)
                # Render
                self._render_frame()
                
                self.video.write(
                    cv2.cvtColor(
                        np.array(pygame.surfarray.pixels3d(self.screen).swapaxes(0, 1)), 
                        cv2.COLOR_RGB2BGR
                    )
                )

        self.video.release()
        
        print(f"Prerendered video with {frame_count} unique frames")
    def reverse_video(self, filename=None):
        if filename is None:
            filename = self.filename
        output_file = "output_reversed.mp4"
        cmd = [
            "ffmpeg", "-i", filename,
            "-vf", "reverse",
            "-c:v", "mpeg4",
            "-profile:v", "0",
            "-b:v", "5584k", 
            "-pix_fmt", "yuv420p",
            "-r", "24",
            "-s", "1920x1080",
            output_file
        ]
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    recorder = Recorder()
    recorder.run()
    recorder.reverse_video()