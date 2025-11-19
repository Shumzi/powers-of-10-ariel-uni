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

# GStreamer pipeline for MJPEG AVI
gst_pipeline = (
    f'filesrc location="{video_path}" ! '
    'avidemux ! jpegdec ! videoconvert ! appsink'
)

print(f"Pipeline: {gst_pipeline}")

cap_gst = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

if cap_gst.isOpened():
    print("✓ GStreamer pipeline opened")
    
    fps = cap_gst.get(cv2.CAP_PROP_FPS)
    frames = cap_gst.get(cv2.CAP_PROP_FRAME_COUNT)
    width = cap_gst.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap_gst.get(cv2.CAP_PROP_FRAME_HEIGHT)
    
    print(f"  FPS: {fps}")
    print(f"  Frames: {frames}")
    print(f"  Size: {width}x{height}")
    
    if frames <= 0:
        print(f"  ⚠ WARNING: Frame count is {frames} (GStreamer can't determine length)")
        print(f"  This is NORMAL for some containers. Seeking may still work.")
    
    # Try reading a frame
    ret, frame = cap_gst.read()
    if ret:
        print(f"  ✓ Successfully read frame: {frame.shape}")
    else:
        print(f"  ✗ Failed to read frame")
    
    # Try seeking
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
    print("✗ GStreamer pipeline FAILED to open")
    print("\nPossible issues:")
    print("  1. GStreamer plugins missing: sudo apt-get install gstreamer1.0-plugins-good")
    print("  2. OpenCV not built with GStreamer: rebuild opencv with -D WITH_GSTREAMER=ON")
    print("  3. File path is wrong")

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
