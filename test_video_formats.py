#!/usr/bin/env python3
"""
Test different video formats for seeking performance on Raspberry Pi
This will help determine the best format for your use case
"""

import cv2
import time
import os

# Input video
input_video = "sample transitions/non-optimized.mp4"

print("="*60)
print("Video Format Performance Test")
print("="*60)

# Test configurations: (name, codec, extension, extra_params)
formats = [
    ("H.264 standard (default)", "libx264", "mp4", []),
    ("H.264 all I-frames", "libx264", "mp4", ["-g", "1", "-crf", "18"]),
    ("MJPEG high quality", "mjpeg", "avi", ["-q:v", "3"]),
    ("MJPEG medium quality", "mjpeg", "avi", ["-q:v", "5"]),
]

results = []

for name, codec, ext, extra_params in formats:
    output_file = f"/tmp/test_{codec}_{len(extra_params)}.{ext}"
    
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    
    # Convert video
    print(f"Converting to {output_file}...")
    cmd = ["ffmpeg", "-y", "-i", input_video, "-c:v", codec] + extra_params + [output_file]
    
    import subprocess
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"✗ Conversion failed!")
        continue
    
    # Get file size
    file_size_mb = os.path.getsize(output_file) / (1024*1024)
    print(f"File size: {file_size_mb:.2f} MB")
    
    # Test with OpenCV default backend
    print("\nTesting DEFAULT backend...")
    cap = cv2.VideoCapture(output_file)
    
    if not cap.isOpened():
        print("✗ Failed to open")
        continue
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"  Frames: {total_frames} @ {fps} FPS")
    
    # Test seek performance
    seek_times = []
    frame_positions = [0, 100, 500, 1000, 1500, 100, 500]  # Include backward seeks
    
    print("  Testing seeks...")
    for target_frame in frame_positions:
        if target_frame >= total_frames:
            continue
            
        t0 = time.perf_counter()
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        ret, frame = cap.read()
        t1 = time.perf_counter()
        
        if ret:
            seek_time = (t1 - t0) * 1000
            seek_times.append(seek_time)
    
    cap.release()
    
    if seek_times:
        avg_seek = sum(seek_times) / len(seek_times)
        min_seek = min(seek_times)
        max_seek = max(seek_times)
        
        print(f"  Seek times: min={min_seek:.1f}ms, avg={avg_seek:.1f}ms, max={max_seek:.1f}ms")
        
        results.append({
            'name': name,
            'size_mb': file_size_mb,
            'avg_seek': avg_seek,
            'min_seek': min_seek,
            'max_seek': max_seek
        })
    else:
        print("  ✗ All seeks failed")

# Summary
print("\n" + "="*60)
print("SUMMARY - Ranked by average seek time")
print("="*60)

results.sort(key=lambda x: x['avg_seek'])

print(f"\n{'Format':<30} {'Size (MB)':<12} {'Avg Seek':<12} {'Min/Max'}")
print("-"*70)

for r in results:
    print(f"{r['name']:<30} {r['size_mb']:<12.1f} {r['avg_seek']:<12.1f} {r['min_seek']:.1f}/{r['max_seek']:.1f}ms")

print("\n" + "="*60)
print("RECOMMENDATION:")
if results:
    best = results[0]
    print(f"Use: {best['name']}")
    print(f"  - Fastest seeks: {best['avg_seek']:.1f}ms average")
    print(f"  - File size: {best['size_mb']:.1f}MB")
    
    if best['avg_seek'] > 100:
        print(f"\n⚠ WARNING: Even best format has slow seeks (>{best['avg_seek']:.0f}ms)")
        print(f"  Consider RAM preloading instead!")
print("="*60)
