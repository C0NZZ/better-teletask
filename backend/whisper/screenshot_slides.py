#!/usr/bin/env python3
"""
Script to extract screenshots from desktop.mp4 every 1 second
and identify groups of similar slides using OpenCV.
"""

import os
import cv2
from pathlib import Path
from PIL import Image
import imagehash

# Configuration
VIDEO_FILE = "input/desktop.mp4"
OUTPUT_DIR = "photos"
HASH_SIZE = 16  # Larger = more sensitive to differences
SIMILARITY_THRESHOLD = 10  # Lower = more strict matching (hamming distance)


def extract_screenshots(video_path: str, output_dir: str) -> list[str]:
    """Extract screenshots from video at 1 second intervals using OpenCV."""
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Clear existing screenshots
    for f in Path(output_dir).glob("frame_*.png"):
        f.unlink()
    
    print(f"Extracting screenshots from {video_path}...")
    
    # Open video with OpenCV
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: Could not open video file: {video_path}")
        return []
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    
    print(f"Video FPS: {fps:.2f}, Total frames: {total_frames}, Duration: {duration:.2f}s")
    
    screenshots = []
    frame_interval = int(fps)  # Capture every 1 second (every fps frames)
    frame_count = 0
    saved_count = 0
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            break
        
        # Save frame every 1 second
        if frame_count % frame_interval == 0:
            saved_count += 1
            output_path = os.path.join(output_dir, f"frame_{saved_count:04d}.png")
            cv2.imwrite(output_path, frame)
            screenshots.append(output_path)
            print(f"\rExtracted frame {saved_count} at {frame_count / fps:.1f}s", end="")
        
        frame_count += 1
    
    cap.release()
    print(f"\nExtracted {len(screenshots)} screenshots")
    
    return screenshots


def compute_image_hash(image_path: str) -> imagehash.ImageHash:
    """Compute perceptual hash of an image."""
    img = Image.open(image_path)
    return imagehash.phash(img, hash_size=HASH_SIZE)


def find_similar_groups(screenshots: list[str], threshold: int = SIMILARITY_THRESHOLD) -> list[list[str]]:
    """Group similar screenshots together based on perceptual hashing."""
    
    if not screenshots:
        return []
    
    print("Computing image hashes...")
    
    # Compute hash for each image
    hashes = {}
    for path in screenshots:
        try:
            hashes[path] = compute_image_hash(path)
        except Exception as e:
            print(f"Error processing {path}: {e}")
    
    # Group similar images
    groups = []
    processed = set()
    
    print("Identifying similar slide groups...")
    
    for path1, hash1 in hashes.items():
        if path1 in processed:
            continue
        
        # Start a new group
        group = [path1]
        processed.add(path1)
        
        # Find all similar images
        for path2, hash2 in hashes.items():
            if path2 in processed:
                continue
            
            # Calculate hamming distance between hashes
            distance = hash1 - hash2
            
            if distance <= threshold:
                group.append(path2)
                processed.add(path2)
        
        groups.append(sorted(group))
    
    return groups


def identify_slide_transitions(groups: list[list[str]]) -> None:
    """Analyze groups to identify slide transitions."""
    
    print("\n" + "=" * 60)
    print("SLIDE ANALYSIS RESULTS")
    print("=" * 60)
    
    print(f"\nFound {len(groups)} unique slides/scenes\n")
    
    for i, group in enumerate(groups, 1):
        # Extract frame numbers for time calculation
        frame_nums = []
        for path in group:
            try:
                num = int(Path(path).stem.split("_")[1])
                frame_nums.append(num)
            except:
                pass
        
        if frame_nums:
            start_time = min(frame_nums) - 1  # -1 because frames start at 1
            end_time = max(frame_nums)
            duration = end_time - start_time
            
            print(f"Slide {i}:")
            print(f"  - Screenshots: {len(group)} frames")
            print(f"  - Time range: {start_time}s - {end_time}s (duration: {duration}s)")
            print(f"  - Representative frame: {group[0]}")
            print()
    
    # Create a summary file
    summary_path = os.path.join(OUTPUT_DIR, "slide_summary.txt")
    with open(summary_path, "w") as f:
        f.write("Slide Analysis Summary\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Total unique slides: {len(groups)}\n\n")
        
        for i, group in enumerate(groups, 1):
            frame_nums = []
            for path in group:
                try:
                    num = int(Path(path).stem.split("_")[1])
                    frame_nums.append(num)
                except:
                    pass
            
            if frame_nums:
                start_time = min(frame_nums) - 1
                end_time = max(frame_nums)
                
                f.write(f"Slide {i}:\n")
                f.write(f"  Frames: {', '.join(Path(p).name for p in group)}\n")
                f.write(f"  Time: {start_time}s - {end_time}s\n")
                f.write(f"  Representative: {Path(group[0]).name}\n\n")
    
    print(f"Summary saved to: {summary_path}")


def main():
    """Main entry point."""
    
    # Check if video exists
    if not os.path.exists(VIDEO_FILE):
        print(f"Error: Video file not found: {VIDEO_FILE}")
        print("Please place desktop.mp4 in the input/ directory")
        return
    
    # Extract screenshots
    screenshots = extract_screenshots(VIDEO_FILE, OUTPUT_DIR)
    
    if not screenshots:
        print("No screenshots extracted. Check if video file is valid.")
        return
    
    # Find similar groups
    groups = find_similar_groups(screenshots)
    
    # Analyze and report
    identify_slide_transitions(groups)
    
    print("\nDone!")


if __name__ == "__main__":
    main()
