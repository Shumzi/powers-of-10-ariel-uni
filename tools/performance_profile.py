"""
Performance Profiling Tool for Powers of Ten Viewer
Run this to generate a detailed performance report for RPi optimization
"""
import pygame
import json
import time
from collections import defaultdict
import statistics


class PerformanceProfiler:
    """Profiles the viewer performance and generates optimization recommendations"""
    
    def __init__(self, viewer):
        self.viewer = viewer
        self.metrics = {
            'fps_samples': [],
            'frame_times': [],
            'render_times': [],
            'input_times': [],
            'update_times': [],
            'image_scale_times': [],
            'transition_times': [],
            'zoom_levels': []
        }
        self.event_counts = defaultdict(int)
        self.total_frames = 0
        self.profile_duration = 30  # seconds
        
    def profile(self):
        """Run profiling session"""
        print(f"Starting {self.profile_duration}s performance profile...")
        print("Interact with the viewer normally (zoom in/out, transitions)")
        print("-" * 60)
        
        start_time = time.time()
        
        while time.time() - start_time < self.profile_duration:
            # Capture current stats
            if self.viewer.clock.get_fps() > 0:
                self.metrics['fps_samples'].append(self.viewer.clock.get_fps())
            
            if self.viewer.perf_stats['total'] > 0:
                self.metrics['frame_times'].append(self.viewer.perf_stats['total'])
                self.metrics['render_times'].append(self.viewer.perf_stats['render'])
                self.metrics['input_times'].append(self.viewer.perf_stats['input'])
                self.metrics['update_times'].append(self.viewer.perf_stats['update'])
            
            # Track zoom level
            self.metrics['zoom_levels'].append(self.viewer.zoom_controller.scale)
            
            # Track events
            if self.viewer.transition_manager.is_active():
                self.event_counts['transitions'] += 1
                
            self.total_frames += 1
            time.sleep(0.016)  # ~60 Hz sampling
        
        self.generate_report()
    
    def generate_report(self):
        """Generate performance report"""
        print("\n" + "=" * 60)
        print("PERFORMANCE PROFILE REPORT")
        print("=" * 60)
        
        # FPS Analysis
        if self.metrics['fps_samples']:
            avg_fps = statistics.mean(self.metrics['fps_samples'])
            min_fps = min(self.metrics['fps_samples'])
            max_fps = max(self.metrics['fps_samples'])
            fps_stddev = statistics.stdev(self.metrics['fps_samples']) if len(self.metrics['fps_samples']) > 1 else 0
            
            print(f"\n📊 FRAME RATE")
            print(f"   Average: {avg_fps:.1f} FPS")
            print(f"   Min:     {min_fps:.1f} FPS")
            print(f"   Max:     {max_fps:.1f} FPS")
            print(f"   StdDev:  {fps_stddev:.2f}")
            
            if avg_fps < 30:
                print(f"   ⚠️  CRITICAL: Average FPS below 30!")
            elif avg_fps < 55:
                print(f"   ⚠️  WARNING: FPS below target (60)")
            else:
                print(f"   ✅ Good performance")
        
        # Frame Time Analysis
        if self.metrics['frame_times']:
            avg_frame = statistics.mean(self.metrics['frame_times'])
            max_frame = max(self.metrics['frame_times'])
            p95_frame = sorted(self.metrics['frame_times'])[int(len(self.metrics['frame_times']) * 0.95)]
            
            print(f"\n⏱️  FRAME TIMING")
            print(f"   Average:  {avg_frame:.2f}ms (target: 16.67ms for 60 FPS)")
            print(f"   95th %:   {p95_frame:.2f}ms")
            print(f"   Max:      {max_frame:.2f}ms")
            
            if avg_frame > 16.67:
                slowdown = (avg_frame / 16.67 - 1) * 100
                print(f"   ⚠️  {slowdown:.1f}% slower than 60 FPS target")
        
        # Component Breakdown
        if self.metrics['render_times']:
            print(f"\n🔧 COMPONENT TIMINGS (Average)")
            avg_render = statistics.mean(self.metrics['render_times'])
            avg_input = statistics.mean(self.metrics['input_times'])
            avg_update = statistics.mean(self.metrics['update_times'])
            
            total_component = avg_render + avg_input + avg_update
            
            print(f"   Render:  {avg_render:.2f}ms ({avg_render/total_component*100:.1f}%)")
            print(f"   Update:  {avg_update:.2f}ms ({avg_update/total_component*100:.1f}%)")
            print(f"   Input:   {avg_input:.2f}ms ({avg_input/total_component*100:.1f}%)")
            
            # Identify bottleneck
            if avg_render > avg_update and avg_render > avg_input:
                print(f"   🎯 PRIMARY BOTTLENECK: Rendering")
                print(f"      → Image scaling/blitting is the slowest component")
            elif avg_update > avg_render:
                print(f"   🎯 PRIMARY BOTTLENECK: Update logic")
            else:
                print(f"   ✅ Well balanced")
        
        # Zoom Analysis
        if self.metrics['zoom_levels']:
            avg_zoom = statistics.mean(self.metrics['zoom_levels'])
            max_zoom = max(self.metrics['zoom_levels'])
            
            print(f"\n🔍 ZOOM STATISTICS")
            print(f"   Average zoom: {avg_zoom:.2f}x")
            print(f"   Max zoom:     {max_zoom:.2f}x")
            
            high_zoom_frames = sum(1 for z in self.metrics['zoom_levels'] if z > 2.5)
            high_zoom_pct = (high_zoom_frames / len(self.metrics['zoom_levels'])) * 100
            print(f"   High zoom (>2.5x): {high_zoom_pct:.1f}% of frames")
        
        # RPi Optimization Recommendations
        print(f"\n🥧 RASPBERRY PI 4 OPTIMIZATION RECOMMENDATIONS")
        print("=" * 60)
        
        if avg_fps < 60:
            print("\n1. RESOLUTION REDUCTION")
            print("   Current viewport: 720x720")
            if avg_fps < 30:
                print("   → RECOMMENDED: Reduce to 540x540 or 480x480")
            elif avg_fps < 45:
                print("   → RECOMMENDED: Reduce to 600x600")
            else:
                print("   → Consider: Reduce to 640x640 for smoother performance")
        
        if avg_render > 12:
            print("\n2. RENDERING OPTIMIZATIONS")
            print("   → Enable hardware acceleration: SDL_VIDEODRIVER=x11")
            print("   → Use pygame.SCALED flag for faster scaling")
            print("   → Pre-scale transition frames to exact viewport size")
            print("   → Consider using pygame.transform.scale (faster than smoothscale)")
        
        if max_zoom > 3.0:
            print("\n3. ZOOM OPTIMIZATIONS")
            print("   → High zoom levels detected")
            print("   → Crop threshold is working (currently 1.5x)")
            print("   → Consider caching cropped regions")
        
        print("\n4. GENERAL RPi 4 TIPS")
        print("   → Overclock to 2.0 GHz if not already")
        print("   → Ensure GPU memory split is at least 256MB")
        print("   → Run in fullscreen mode for better performance")
        print("   → Disable desktop compositor if running X11")
        print("   → Use lite OS without desktop for maximum performance")
        
        # Save report to file
        report_file = "performance_report.txt"
        with open(report_file, 'w') as f:
            f.write("Performance Profile Report\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Average FPS: {avg_fps:.2f}\n")
            f.write(f"Average Frame Time: {avg_frame:.2f}ms\n")
            f.write(f"Render Time: {avg_render:.2f}ms\n")
            f.write(f"Update Time: {avg_update:.2f}ms\n")
            f.write(f"Input Time: {avg_input:.2f}ms\n")
        
        print(f"\n📄 Report saved to: {report_file}")


if __name__ == "__main__":
    # Import after defining profiler
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from viewer import ZoomViewer
    
    print("Initializing viewer...")
    viewer = ZoomViewer()
    
    profiler = PerformanceProfiler(viewer)
    
    # Run in separate thread
    import threading
    profile_thread = threading.Thread(target=profiler.profile)
    profile_thread.start()
    
    # Run viewer
    viewer.run()
    
    # Wait for profiling to complete
    profile_thread.join()
