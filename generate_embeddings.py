#!/usr/bin/env python3
"""
Generate embeddings for staged bedroom images.
This script processes all images in the staged bedroom directory and saves their embeddings.
"""

import os
import sys
import numpy as np
import torch
from pathlib import Path

# Add src to path
sys.path.append('src')

from src.data_loader import load_image
from src.feature_extractor import FeatureExtractor

def generate_embeddings_for_all_room_types():
    """Generate embeddings for all room types in data/staged/"""
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    staged_root = Path("data/staged")
    if not staged_root.exists():
        print(f"❌ Staged directory not found: {staged_root}")
        return
    room_types = [d.name for d in staged_root.iterdir() if d.is_dir()]
    if not room_types:
        print(f"❌ No room type folders found in {staged_root}")
        return
    print(f"🏷️  Found room types: {room_types}")
    model = FeatureExtractor()
    model.eval()
    for room_type in room_types:
        staged_dir = staged_root / room_type
        image_files = list(staged_dir.glob("*.jpeg")) + list(staged_dir.glob("*.jpg")) + list(staged_dir.glob("*.png"))
        if not image_files:
            print(f"⚠️  No images found for room type '{room_type}' in {staged_dir}")
            continue
        print(f"\n📸 Processing {len(image_files)} images for room type '{room_type}'")
        embeddings = []
        image_names = []
        for i, img_path in enumerate(image_files):
            print(f"   🔍 {i+1}/{len(image_files)}: {img_path.name}")
            try:
                img = load_image(str(img_path)).unsqueeze(0)
                with torch.no_grad():
                    emb = model(img).cpu().numpy()
                embeddings.append(emb)
                image_names.append(img_path.name)
                print(f"      ✅ {img_path.name}")
            except Exception as e:
                print(f"      ❌ Error: {e}")
                continue
        if embeddings:
            embeddings = np.vstack(embeddings)
            image_names = np.array(image_names)
            emb_path = models_dir / f"staged_{room_type}_embs.npy"
            names_path = models_dir / f"staged_{room_type}_names.npy"
            np.save(emb_path, embeddings)
            np.save(names_path, image_names)
            print(f"   ✅ Saved embeddings for '{room_type}' to {emb_path} and {names_path}")
            print(f"   📊 Shape: {embeddings.shape}")
        else:
            print(f"   ❌ No embeddings generated for '{room_type}'")

if __name__ == "__main__":
    generate_embeddings_for_all_room_types() 