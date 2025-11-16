# Refactored Powers of Ten Viewer

This is a refactored version of the viewer with proper separation of concerns.

## Structure

### Components

1. **`image_manager.py`** (120 lines)
   - `ImageData`: Encapsulates image data
   - `ImageManager`: Loads and manages images
   - Responsibility: Image loading, scaling, and metadata

2. **`zoom_controller.py`** (100 lines)
   - `ZoomController`: Manages zoom state and animations
   - Responsibility: All zoom logic (step, continuous, boundaries)

3. **`transition_manager.py`** (80 lines)
   - `TransitionManager`: Handles transition animations
   - Responsibility: Loading and playing transition frames

4. **`renderer.py`** (150 lines)
   - `Renderer`: Handles all drawing
   - Responsibility: Rendering images, transitions, UI, crop optimization

5. **`input_handler.py`** (50 lines)
   - `InputHandler`: Processes keyboard input
   - Responsibility: Event processing, key timing

6. **`viewer.py`** (100 lines)
   - `ZoomViewer`: Main coordinator
   - Responsibility: Initializing components and running game loop

## Benefits

✅ **Single Responsibility**: Each class has one clear purpose
✅ **Open/Closed Principle**: Easy to extend without modifying existing code
✅ **Testable**: Each component can be tested independently
✅ **Maintainable**: Know exactly where to look for specific functionality
✅ **Reusable**: Components can be used in other projects

## Running

```bash
cd refactored
python viewer.py
```

## Original vs Refactored

- Original: 500 lines in one file
- Refactored: 600 lines across 6 files (~100 lines each)
- Slightly more total code, but much better organization
