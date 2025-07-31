#!/usr/bin/env python3
"""
Photo Addition Script for AI Home Staging
Helps you easily add more photos to improve your AI model
"""

import os
import shutil
from pathlib import Path
import argparse

def create_room_directories():
    """Create directories for all room types"""
    room_types = [
        'bedroom', 'living_room', 'dining_room', 'kitchen', 
        'bathroom', 'office', 'outdoor', 'entryway', 'basement',
        'laundry', 'garage', 'patio', 'deck', 'garden'
    ]
    
    staged_dir = Path("data/staged")
    empty_dir = Path("data/empty")
    
    for room_type in room_types:
        (staged_dir / room_type).mkdir(parents=True, exist_ok=True)
        (empty_dir / room_type).mkdir(parents=True, exist_ok=True)
    
    print(f"✅ Created directories for {len(room_types)} room types")

def count_photos():
    """Count photos in each room type"""
    staged_dir = Path("data/staged")
    empty_dir = Path("data/empty")
    
    print("\n📊 Current Photo Count:")
    print("-" * 40)
    
    for room_dir in sorted(staged_dir.iterdir()):
        if room_dir.is_dir():
            photo_count = len(list(room_dir.glob("*.jpg")) + 
                            list(room_dir.glob("*.jpeg")) + 
                            list(room_dir.glob("*.png")))
            print(f"{room_dir.name:15} | {photo_count:3d} photos")
    
    print("-" * 40)

def validate_image(image_path):
    """Validate if image is suitable for training"""
    from PIL import Image
    
    try:
        with Image.open(image_path) as img:
            # Check minimum size
            if img.size[0] < 400 or img.size[1] < 400:
                return False, f"Too small: {img.size[0]}x{img.size[1]}"
            
            # Check file size (max 10MB)
            if os.path.getsize(image_path) > 10 * 1024 * 1024:
                return False, "File too large (>10MB)"
            
            return True, f"Valid: {img.size[0]}x{img.size[1]}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def add_photos_from_folder(source_folder, room_type, is_staged=True):
    """Add photos from a source folder to the appropriate room type"""
    source_path = Path(source_folder)
    if not source_path.exists():
        print(f"❌ Source folder not found: {source_folder}")
        return
    
    target_dir = Path("data/staged" if is_staged else "data/empty") / room_type
    target_dir.mkdir(parents=True, exist_ok=True)
    
    image_extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(source_path.glob(f"*{ext}"))
    
    print(f"\n📸 Processing {len(image_files)} images for {room_type}...")
    
    added_count = 0
    skipped_count = 0
    
    for img_path in image_files:
        is_valid, message = validate_image(img_path)
        
        if is_valid:
            # Create unique filename
            counter = 1
            new_name = img_path.stem
            while (target_dir / f"{new_name}.{img_path.suffix}").exists():
                new_name = f"{img_path.stem}_{counter}"
                counter += 1
            
            target_path = target_dir / f"{new_name}.{img_path.suffix}"
            shutil.copy2(img_path, target_path)
            print(f"  ✅ Added: {img_path.name} -> {target_path.name}")
            added_count += 1
        else:
            print(f"  ❌ Skipped: {img_path.name} ({message})")
            skipped_count += 1
    
    print(f"\n📈 Summary for {room_type}:")
    print(f"  Added: {added_count} photos")
    print(f"  Skipped: {skipped_count} photos")

def generate_embeddings_after_adding():
    """Generate embeddings after adding new photos"""
    print("\n🔄 Generating embeddings for new photos...")
    
    try:
        import subprocess
        result = subprocess.run(['python', 'generate_embeddings.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Embeddings generated successfully!")
            print(result.stdout)
        else:
            print("❌ Error generating embeddings:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Error running embedding generation: {e}")

def main():
    parser = argparse.ArgumentParser(description="Add photos to AI Home Staging dataset")
    parser.add_argument("--create-dirs", action="store_true", 
                       help="Create directories for all room types")
    parser.add_argument("--count", action="store_true", 
                       help="Count current photos in each room type")
    parser.add_argument("--add", nargs=3, metavar=('SOURCE_FOLDER', 'ROOM_TYPE', 'TYPE'),
                       help="Add photos from source folder (TYPE: staged or empty)")
    parser.add_argument("--generate-embeddings", action="store_true",
                       help="Generate embeddings after adding photos")
    
    args = parser.parse_args()
    
    if args.create_dirs:
        create_room_directories()
    
    if args.count:
        count_photos()
    
    if args.add:
        source_folder, room_type, photo_type = args.add
        is_staged = photo_type.lower() == 'staged'
        add_photos_from_folder(source_folder, room_type, is_staged)
    
    if args.generate_embeddings:
        generate_embeddings_after_adding()
    
    if not any([args.create_dirs, args.count, args.add, args.generate_embeddings]):
        print("AI Home Staging - Photo Addition Tool")
        print("=" * 40)
        print("\nUsage examples:")
        print("  python add_photos.py --create-dirs")
        print("  python add_photos.py --count")
        print("  python add_photos.py --add /path/to/photos bedroom staged")
        print("  python add_photos.py --generate-embeddings")
        print("\nFor more help: python add_photos.py --help")

if __name__ == "__main__":
    main() 