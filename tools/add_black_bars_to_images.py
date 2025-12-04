import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
from PIL import Image
import sys
"""
adds black bars to images in a folder to match the aspect ratio defined in config.json

usage: python add_black_bars_to_images.py <folder_with_images> [<config.json>] [<R,G,B>]
"""



def add_bars_to_match_aspect_image(img: Image.Image, target_ratio: float, bg=(0, 0, 0)) -> Image.Image:
    w, h = img.size
    src_ratio = w / h

    if abs(src_ratio - target_ratio) < 1e-6:
        return img.copy()

    if src_ratio > target_ratio:
        # wider than target → bars top/bottom
        canvas_w = w
        canvas_h = round(w / target_ratio)
    else:
        # taller/narrower → bars left/right
        canvas_h = h
        canvas_w = round(h * target_ratio)

    canvas = Image.new("RGB", (canvas_w, canvas_h), bg)
    offset_x = (canvas_w - w) // 2
    offset_y = (canvas_h - h) // 2
    canvas.paste(img, (offset_x, offset_y))
    return canvas

def process_folder(folder, config_path="config.json", bg=(0, 0, 0)):
    folder = Path(folder)
    out_dir = folder / "resized"
    out_dir.mkdir(exist_ok=True)

    cfg = json.loads(Path(config_path).read_text())
    vw, vh = cfg["setup"]["viewportDims"]  # e.g. [1920, 1080]
    target_ratio = vw / vh

    exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}  # extend if needed

    for path in folder.iterdir():
        if not path.is_file() or path.suffix.lower() not in exts:
            continue

        img = Image.open(path).convert("RGB")
        out_img = add_bars_to_match_aspect_image(img, target_ratio, bg=bg)
        out_path = out_dir / path.name
        out_img.save(out_path)
        print(f"Saved {out_path}")

# Example usage:
# process_folder("path/to/folder", "config.json")

def choose_folder_gui() -> Path | None:
    root = tk.Tk()
    root.withdraw()                  # hide root window
    root.attributes("-topmost", True)
    folder = filedialog.askdirectory(title="Select folder with images")
    root.destroy()
    return Path(folder) if folder else None

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python add_black_bars_to_images.py <config.json> [<folder_with_images>] [<R,G,B>]")
        sys.exit(1)

    config_path = sys.argv[1]
    if len(sys.argv) >= 3:
        folder = sys.argv[2]
    else:
        folder_path = choose_folder_gui()
        if folder_path is None:
            print("No folder selected, exiting.")
            sys.exit(0)
        folder = folder_path
    if len(sys.argv) >= 4:
        bg = tuple(map(int, sys.argv[3].split(",")))
    else:
        bg = (0, 0, 0)

    process_folder(folder, config_path, bg)