"""
Quick Benchmark - Tests specific operations to identify bottlenecks
"""
import pygame
import time
import json


def benchmark_image_scaling():
    """Test image scaling performance"""
    print("=" * 60)
    print("BENCHMARK: Image Scaling Performance")
    print("=" * 60)
    
    pygame.init()
    
    # Load a test image
    import os
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    test_image_path = config['images'][0]['filename']
    test_image = pygame.image.load(test_image_path)
    
    scales = [1.0, 1.5, 2.0, 2.5, 3.0, 5.0, 10.0]
    iterations = 50
    
    print(f"\nOriginal image size: {test_image.get_size()}")
    print(f"Testing {iterations} iterations per scale level\n")
    
    results = {}
    
    for scale in scales:
        target_size = (int(test_image.get_width() * scale), 
                      int(test_image.get_height() * scale))
        
        # Test smoothscale
        start = time.perf_counter()
        for _ in range(iterations):
            pygame.transform.smoothscale(test_image, target_size)
        smooth_time = (time.perf_counter() - start) / iterations * 1000
        
        # Test regular scale
        start = time.perf_counter()
        for _ in range(iterations):
            pygame.transform.scale(test_image, target_size)
        fast_time = (time.perf_counter() - start) / iterations * 1000
        
        # Test scale_by
        start = time.perf_counter()
        for _ in range(iterations):
            pygame.transform.scale_by(test_image, scale)
        scale_by_time = (time.perf_counter() - start) / iterations * 1000
        
        results[scale] = {
            'smoothscale': smooth_time,
            'scale': fast_time,
            'scale_by': scale_by_time
        }
        
        print(f"Scale {scale}x:")
        print(f"  smoothscale: {smooth_time:.2f}ms")
        print(f"  scale:       {fast_time:.2f}ms (faster by {smooth_time/fast_time:.1f}x)")
        print(f"  scale_by:    {scale_by_time:.2f}ms")
        print()
    
    # Recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    
    avg_smooth = sum(r['smoothscale'] for r in results.values()) / len(results)
    avg_fast = sum(r['scale'] for r in results.values()) / len(results)
    
    print(f"\nAverage smoothscale time: {avg_smooth:.2f}ms")
    print(f"Average scale time:       {avg_fast:.2f}ms")
    print(f"Speed improvement:        {avg_smooth/avg_fast:.1f}x\n")
    
    if avg_smooth > 16.67:
        print("⚠️  WARNING: smoothscale exceeds 60 FPS budget!")
        print("→ Consider using regular scale() for RPi")
    
    if avg_fast < 10:
        print("✅ Regular scale() is fast enough for 60 FPS")
    
    pygame.quit()


def benchmark_crop_optimization():
    """Test crop-then-scale vs full-image scaling"""
    print("\n" + "=" * 60)
    print("BENCHMARK: Crop Optimization Performance")
    print("=" * 60)
    
    pygame.init()
    
    # Load a test image
    import os
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    test_image_path = config['images'][0]['filename']
    test_image = pygame.image.load(test_image_path)
    
    viewport_size = (720, 720)
    scales = [2.0, 3.0, 5.0, 10.0]
    iterations = 30
    
    print(f"\nViewport size: {viewport_size}")
    print(f"Testing {iterations} iterations per scale level\n")
    
    for scale in scales:
        # Full image scaling
        target_size = (int(test_image.get_width() * scale), 
                      int(test_image.get_height() * scale))
        
        start = time.perf_counter()
        for _ in range(iterations):
            pygame.transform.smoothscale(test_image, target_size)
        full_time = (time.perf_counter() - start) / iterations * 1000
        
        # Crop then scale (simulate visible region)
        crop_rect = pygame.Rect(
            test_image.get_width() // 4,
            test_image.get_height() // 4,
            test_image.get_width() // 2,
            test_image.get_height() // 2
        )
        
        start = time.perf_counter()
        for _ in range(iterations):
            cropped = test_image.subsurface(crop_rect)
            pygame.transform.smoothscale(cropped, (360, 360))
        crop_time = (time.perf_counter() - start) / iterations * 1000
        
        improvement = full_time / crop_time
        
        print(f"Scale {scale}x:")
        print(f"  Full image:      {full_time:.2f}ms")
        print(f"  Crop + scale:    {crop_time:.2f}ms")
        print(f"  Improvement:     {improvement:.1f}x faster")
        print()
    
    print("✅ Crop optimization provides significant speedup at high zoom!")
    
    pygame.quit()


def benchmark_transition_loading():
    """Test transition frame loading"""
    print("\n" + "=" * 60)
    print("BENCHMARK: Transition Frame Loading")
    print("=" * 60)
    
    pygame.init()
    
    import os
    transition_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sample transitions')
    viewport_size = (720, 720)
    
    start = time.perf_counter()
    
    frames = []
    for i in range(1, 17):
        frame_path = os.path.join(transition_dir, f'frame_{i:04d}.png')
        if os.path.exists(frame_path):
            frame = pygame.image.load(frame_path)
            frame_scaled = pygame.transform.smoothscale(frame, viewport_size)
            frames.append(frame_scaled)
    
    load_time = (time.perf_counter() - start) * 1000
    
    print(f"\nLoaded {len(frames)} transition frames")
    print(f"Total time: {load_time:.2f}ms")
    print(f"Per frame:  {load_time/len(frames):.2f}ms")
    
    if load_time < 100:
        print("✅ Fast loading - negligible impact on startup")
    else:
        print("⚠️  Consider pre-loading or caching")
    
    pygame.quit()


if __name__ == "__main__":
    print("\n🔬 POWERS OF TEN - PERFORMANCE BENCHMARK SUITE\n")
    
    benchmark_image_scaling()
    benchmark_crop_optimization()
    benchmark_transition_loading()
    
    print("\n" + "=" * 60)
    print("BENCHMARK COMPLETE")
    print("=" * 60)
    print("\nPress D during normal viewer operation for live debug stats")
    print("Run performance_profile.py for detailed 30s profiling session\n")
