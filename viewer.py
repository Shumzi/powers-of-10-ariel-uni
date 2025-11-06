import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import json
import os
import math

def ease_out_cubic(x):
    return 1 - pow(1 - x, 3)

def ease_in_out_cubic(x):
    if x < 0.5:
        return 4 * x * x * x
    return 1 - pow(-2 * x + 2, 3) / 2

class ZoomViewer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Powers of Ten Viewer")
        self.configure(bg='#111111')
        
        # Animation properties
        self.animation_duration = 300  # milliseconds
        self.animation_frame_rate = 60  # fps
        self.frame_duration = int(1000 / self.animation_frame_rate)  # milliseconds per frame
        self.target_scale = 1.0
        self.start_scale = 1.0
        self.animation_start_time = None
        self.is_animating = False
        self.next_frame_id = None  # For canceling animation frames

        # Load configuration
        with open('config.json', 'r', encoding='utf-8') as f:
            try:
                self.config = json.load(f)
            except json.JSONDecodeError as e:
                print("Error parsing JSON. Processed text:")
                print(f)
                print("\nError details:", str(e))
                raise

        # Initialize variables
        self.current_index = 0
        self.scale = 1.0
        self.zoom_step = 0.05
        self.min_scale = 1.0
        self.max_scale = 2.0

        # Setup the main container
        self.container = ttk.Frame(self)
        self.container.pack(padx=20, pady=20)
        self.window_side_length = 840
        # Create and configure the image display
        self.canvas = tk.Canvas(
            self.container,
            width=self.window_side_length,
            height=self.window_side_length,
            bg='#111111',
            highlightbackground='#333333',
            highlightthickness=1
        )
        self.canvas.pack()

        # Caption label
        self.caption = ttk.Label(
            self.container,
            text="",
            foreground='#eeeeee',
            background='#111111',
            wraplength=600,
            justify='center'
        )
        self.caption.pack(pady=10)

        # Instructions label
        ttk.Label(
            self.container,
            text="⬆ Zoom In    ⬇ Zoom Out",
            foreground='#999999',
            background='#111111'
        ).pack()

        # Bind keyboard events
        self.bind('<Up>', self.zoom_in)
        self.bind('<Down>', self.zoom_out)

        # Load images
        self.images = []
        self.photo_images = []  # Keep reference to prevent garbage collection
        self.load_images()

        # Initial display
        self.update_display()

    def load_images(self):
        for img_config in self.config['images']:
            # Load image from file
            image_path = img_config['src']
            if image_path.startswith('http'):
                # For the example, you'll need to have local copies of the images
                # You might want to implement downloading or use local paths instead
                image_path = f"sample photos/{os.path.basename(image_path)}"
            
            image = Image.open(image_path)
            # Resize to fit canvas while maintaining aspect ratio
            image.thumbnail((self.window_side_length, self.window_side_length), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            
            self.images.append({
                'config': img_config,
                'image': image,
                'photo': photo
            })

    def get_rect(self, img_config):
        if 'nextPixelRect' in img_config:
            px, py, pw, ph = img_config['nextPixelRect']
            img = self.images[self.current_index]['image']
            return [px/img.width, py/img.height, pw/img.width, ph/img.height]
        return img_config.get('nextRect')

    def update_display(self):
        self.canvas.delete('all')
        
        current = self.images[self.current_index]
        img_config = current['config']
        rect = self.get_rect(img_config)
        
        # Get the original image dimensions
        img_width = current['photo'].width()
        img_height = current['photo'].height()
        
        # Calculate zoom transform
        if rect and self.scale > 1.0:
            # Calculate center of the target rectangle
            cx = rect[0] + rect[2]/2
            cy = rect[1] + rect[3]/2
            
            # Calculate how much we've zoomed between min_scale and max_scale
            zoom_progress = (self.scale - self.min_scale) / (self.max_scale - self.min_scale)
            
            # Interpolate between original position and zoomed position
            target_x = cx * img_width
            target_y = cy * img_height
            current_x = img_width/2 + (target_x - img_width/2) * zoom_progress
            current_y = img_height/2 + (target_y - img_height/2) * zoom_progress
            
            # Calculate the scaled dimensions
            scaled_width = img_width * self.scale
            scaled_height = img_height * self.scale
            
            # Calculate position to center the zoomed part
            x = 300 - current_x * self.scale
            y = 300 - current_y * self.scale
        else:
            # No zoom, just center the image
            x = 300 - img_width/2
            y = 300 - img_height/2
            scaled_width = img_width
            scaled_height = img_height

        # Create a new resized image for the current zoom level
        scaled_image = current['image'].resize(
            (int(scaled_width), int(scaled_height)),
            Image.Resampling.LANCZOS
        )
        current['scaled_photo'] = ImageTk.PhotoImage(scaled_image)
        
        # Display the scaled image
        self.canvas.create_image(
            x + scaled_width/2,
            y + scaled_height/2,
            image=current['scaled_photo']
        )
        
        # Draw outline if rect exists
        if rect:
            # Use image-specific outline color or fall back to default from config
            default_color = self.config.get('defaultOutlineColor')  # Fallback to original green if not specified
            outline_color = img_config.get('outlineColor', default_color)
            
            # Convert 8-digit hex (#RRGGBBAA) to tkinter-compatible color
            if len(outline_color) > 7:  # If color includes alpha channel
                outline_color = outline_color[:7]  # Take only RGB part
            
            rx, ry, rw, rh = rect
            
            # Scale and position the outline
            outline_x = x + rx * scaled_width
            outline_y = y + ry * scaled_height
            outline_w = rw * scaled_width
            outline_h = rh * scaled_height
            
            self.canvas.create_rectangle(
                outline_x, outline_y,
                outline_x + outline_w,
                outline_y + outline_h,
                outline=outline_color,
                width=2
            )
        
        # Update caption
        self.caption.config(text=img_config['caption'])

    def zoom_in(self, event=None):
        self.scale += self.zoom_step
        if self.scale >= self.max_scale:
            self.scale = self.max_scale
            if self.current_index < len(self.images) - 1:
                self.current_index += 1
                self.scale = self.min_scale
        self.update_display()

    def zoom_out(self, event=None):
        self.scale -= self.zoom_step
        if self.scale <= self.min_scale:
            self.scale = self.min_scale
            if self.current_index > 0:
                self.current_index -= 1
                self.scale = self.max_scale
        self.update_display()

if __name__ == "__main__":
    app = ZoomViewer()
    # Set window to dark theme
    app.tk_setPalette(background='#111111', foreground='#eeeeee')
    app.mainloop()