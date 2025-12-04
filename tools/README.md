# Tools

Optional tools for performance analysis, optimization, and content creation.

## Performance Tools

### `benchmark.py`
Quick benchmark of specific operations:
```bash
cd tools
python benchmark.py
```
Tests image scaling methods, crop optimization, and transition loading.

### `performance_profile.py`
30-second profiling session with detailed analysis:
```bash
cd tools
python performance_profile.py
```
Generates comprehensive performance report with RPi optimization recommendations.

### `performance_config.json`
Pre-configured settings for Raspberry Pi optimization.

## Content Creation Tools

### `crop_alignment_tool.py`
Interactive tool to align crop regions with zoomed-in reference images:
```bash
cd tools
python crop_alignment_tool.py base_image.png zoomed_image.png
```

**Features:**
- Create crop selection with correct aspect ratio
- Overlay zoomed image with adjustable transparency to verify alignment
- Zoom and pan for precise positioning
- Resize crop while maintaining aspect ratio
- Saves crop coordinates and cropped image

**Controls:**
- **Mouse Wheel**: Zoom in/out
- **Right Click + Drag**: Pan view
- **Left Click + Drag**: Create crop selection
- **Drag handles**: Resize crop (maintains aspect ratio)
- **Drag center**: Move crop
- **SPACE**: Toggle overlay
- **↑/↓**: Adjust overlay opacity
- **C**: Clear selection
- **ENTER**: Save crop (outputs JSON with coordinates + cropped PNG)
- **ESC**: Exit

**Output:**
- `crop_alignment_output.json` - Crop coordinates (x, y, width, height)
- `cropped_output.png` - The cropped image

## Live Debug Mode

In the main viewer, press **D** to toggle live FPS and performance stats (no tools folder needed).
