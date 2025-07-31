#!/usr/bin/env python3
"""
Test script to verify all imports work correctly.
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.getcwd()))

print("🔍 Testing imports...")

try:
    import numpy as np
    print("✅ numpy imported successfully")
except ImportError as e:
    print(f"❌ numpy import failed: {e}")

try:
    import torch
    print("✅ torch imported successfully")
except ImportError as e:
    print(f"❌ torch import failed: {e}")

try:
    from src.data_loader import load_image
    print("✅ load_image imported successfully")
except ImportError as e:
    print(f"❌ load_image import failed: {e}")

try:
    from src.feature_extractor import FeatureExtractor
    print("✅ FeatureExtractor imported successfully")
    
    # Test creating an instance
    model = FeatureExtractor()
    model.eval()
    print("✅ FeatureExtractor instance created successfully")
    
    # Test with dummy input
    with torch.no_grad():
        dummy_input = torch.randn(1, 3, 256, 256)
        output = model(dummy_input)
        print(f"✅ Model forward pass successful, output shape: {output.shape}")
        
except ImportError as e:
    print(f"❌ FeatureExtractor import failed: {e}")
except Exception as e:
    print(f"❌ FeatureExtractor test failed: {e}")

try:
    from src.retrieval import retrieve
    print("✅ retrieve imported successfully")
except ImportError as e:
    print(f"❌ retrieve import failed: {e}")

print("\n🎯 All import tests completed!") 