#!/usr/bin/env python3
"""
Test GStreamer video playback with OpenCV
Run this on the Raspberry Pi to verify GStreamer is working
"""

import cv2
import sys

# Video file to test
video_path = "/tmp/non-optimized_mjpeg.avi"

print("="*60)
print("GStreamer Test Script")
print("="*60)

# Test 1: Default backend
print("\n1. Testing DEFAULT backend...")
cap_default = cv2.VideoCapture(video_path)

if cap_default.isOpened():
    fps = cap_default.get(cv2.CAP_PROP_FPS)
    frames = int(cap_default.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap_default.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap_default.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"✓ Default backend WORKS")
    print(f"  FPS: {fps}")
    print(f"  Frames: {frames}")
    print(f"  Size: {width}x{height}")
    
    # Try reading a frame
    ret, frame = cap_default.read()
    if ret:
        print(f"  ✓ Successfully read frame: {frame.shape}")
    else:
        print(f"  ✗ Failed to read frame")
    
    cap_default.release()
else:
    print(f"✗ Default backend FAILED to open: {video_path}")
    sys.exit(1)

# Test 2: GStreamer backend
print("\n2. Testing GSTREAMER backend...")

# Try multiple pipeline variations
pipelines = [
    ("MJPEG with avidemux", 
     f'filesrc location="{video_path}" ! avidemux ! jpegdec ! videoconvert ! appsink'),
    
    ("MJPEG with decodebin (auto)", 
     f'filesrc location="{video_path}" ! decodebin ! videoconvert ! appsink'),
    
    ("Direct playback", 
     f'playbin uri=file://{video_path}'),
    
    ("MJPEG with avdemux_avi", 
     f'filesrc location="{video_path}" ! avdemux_avi ! jpegdec ! videoconvert ! appsink'),
]

working_pipeline = None

for name, gst_pipeline in pipelines:
    print(f"\nTrying: {name}")
    print(f"  Pipeline: {gst_pipeline}")
    
    cap_gst = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
    
    if cap_gst.isOpened():
        print("  ✓ Pipeline opened")
        
        # Try reading a frame to verify it actually works
        ret, frame = cap_gst.read()
        if ret:
            fps = cap_gst.get(cv2.CAP_PROP_FPS)
            frames = cap_gst.get(cv2.CAP_PROP_FRAME_COUNT)
            
            print(f"  ✓ Successfully read frame: {frame.shape}")
            print(f"    FPS: {fps}")
            print(f"    Frames: {frames}")
            
            working_pipeline = (name, gst_pipeline, cap_gst)
            break
        else:
            print(f"  ✗ Opened but failed to read frame")
            cap_gst.release()
    else:
        print(f"  ✗ Failed to open")

if working_pipeline:
    name, pipeline, cap_gst = working_pipeline
    print(f"\n✓ WORKING PIPELINE FOUND: {name}")
    print(f"  Use this: {pipeline}")
    
    # Test seeking
    print("\n  Testing seeking...")
    seek_result = cap_gst.set(cv2.CAP_PROP_POS_FRAMES, 10)
    print(f"  Seek to frame 10: {seek_result}")
    
    ret, frame = cap_gst.read()
    if ret:
        actual_pos = cap_gst.get(cv2.CAP_PROP_POS_FRAMES)
        print(f"  ✓ Read after seek, position: {actual_pos}")
    else:
        print(f"  ✗ Failed to read after seek")
    
    cap_gst.release()
else:
    print("\n✗ NO WORKING GSTREAMER PIPELINE FOUND")

# Test 3: Check OpenCV build info
print("\n3. Checking OpenCV GStreamer support...")
build_info = cv2.getBuildInformation()

if "GStreamer" in build_info:
    # Extract GStreamer line
    for line in build_info.split('\n'):
        if 'GStreamer' in line:
            print(f"  {line.strip()}")
else:
    print("  ✗ GStreamer support not found in OpenCV build")
    print("  OpenCV needs to be rebuilt with GStreamer support")

print("\n" + "="*60)
print("Test complete!")
print("="*60)
