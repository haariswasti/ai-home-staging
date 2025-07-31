   # AI Home Staging Project

An intelligent system that automatically suggests bedroom designs based on your existing furniture and preferences using computer vision and similarity search.

## 🏠 Project Overview

This AI system helps you stage your bedroom by:
1. **Analyzing your empty bedroom** - Takes photos of your current bedroom
2. **Finding similar designs** - Uses computer vision to find staged bedrooms with similar layouts
3. **Providing inspiration** - Suggests furniture arrangements and styling ideas

## 📁 Project Structure

```
ai-home-staging/
├── data/
│   ├── empty bedroom/          # Your empty bedroom photos
│   └── staged bedroom/         # Reference staged bedroom designs
├── models/                     # Generated embeddings and model files
├── src/                        # Core Python modules
│   ├── data_loader.py         # Image loading utilities
│   ├── feature_extractor.py   # ResNet-50 feature extraction
│   ├── retrieval.py           # Similarity search functions
│   └── embed_staged.py        # Embedding generation
├── Notebooks/                  # Jupyter notebooks for exploration
├── generate_embeddings.py      # Script to generate embeddings
└── requirements.txt           # Python dependencies
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate Embeddings

First, generate embeddings for the staged bedroom reference images:

```bash
python generate_embeddings.py
```

This will create:
- `models/staged_embs.npy` - Feature embeddings for staged bedrooms
- `models/staged_names.npy` - Corresponding image filenames

### 3. Run the Demo

Open the Jupyter notebook to test the system:

```bash
jupyter lab
```

Then open `Notebooks/02_retrieval_demo_fixed.ipynb`

## 🔧 How It Works

### 1. Feature Extraction
- Uses **ResNet-50** (pretrained on ImageNet) to extract 2048-dimensional feature vectors
- Images are resized to 256x256 and normalized
- Features capture high-level visual patterns (furniture, layout, style)

### 2. Similarity Search
- Computes **cosine similarity** between your bedroom and staged designs
- Returns top-k most similar staged bedrooms
- Higher similarity scores indicate better matches

### 3. Retrieval Pipeline
```
Empty Bedroom → Feature Extraction → Similarity Search → Top Matches
```

## 📊 Usage Examples

### Basic Retrieval
```python
from src.data_loader import load_image
from src.feature_extractor import FeatureExtractor
from src.retrieval import retrieve

# Load your empty bedroom
img = load_image("data/empty bedroom/IMG_0938.jpeg").unsqueeze(0)

# Extract features
model = FeatureExtractor().eval()
with torch.no_grad():
    query_emb = model(img).cpu().numpy()

# Find similar staged designs
idxs, sims = retrieve(query_emb, staged_embs, top_k=3)
```

### Batch Processing
```python
# Process multiple bedrooms
bedroom_images = ["bedroom1.jpg", "bedroom2.jpg", "bedroom3.jpg"]
for img_path in bedroom_images:
    img = load_image(img_path).unsqueeze(0)
    # ... process and find matches
```

## 🛠️ Customization

### Adding New Staged Designs
1. Add new images to `data/staged bedroom/`
2. Re-run `python generate_embeddings.py`
3. The system will automatically include new designs in searches

### Using Different Models
Modify `src/feature_extractor.py` to use different architectures:
- ResNet-18/34/101/152
- EfficientNet
- Vision Transformer

### Adjusting Similarity Metrics
Modify `src/retrieval.py` to use different similarity measures:
- Euclidean distance
- Manhattan distance
- Custom similarity functions

## 📈 Performance Tips

1. **Image Quality**: Use high-resolution photos (minimum 256x256)
2. **Lighting**: Ensure good, consistent lighting for better feature extraction
3. **Angles**: Take photos from similar angles for better comparisons
4. **Batch Size**: Process multiple images together for efficiency

## 🔍 Troubleshooting

### Common Issues

**ModuleNotFoundError: No module named 'src'**
- Solution: The notebook includes path fixing code, or run from project root

**CUDA out of memory**
- Solution: Use CPU mode or reduce batch size

**Low similarity scores**
- Solution: Check image quality, lighting, and angles

### Debug Mode
Enable verbose logging in notebooks to see detailed processing steps.

## 🎯 Future Enhancements

- [ ] **Furniture Detection**: Identify specific furniture pieces
- [ ] **Style Classification**: Categorize design styles (modern, rustic, etc.)
- [ ] **Room Layout Analysis**: Understand room dimensions and layout
- [ ] **Personalization**: Learn user preferences over time
- [ ] **3D Visualization**: Generate 3D room mockups
- [ ] **Shopping Integration**: Link to furniture retailers

## 📚 Technical Details

### Model Architecture
- **Backbone**: ResNet-50 (pretrained on ImageNet)
- **Feature Dimension**: 2048
- **Input Size**: 256x256x3
- **Normalization**: ImageNet mean/std

### Similarity Metrics
- **Primary**: Cosine Similarity
- **Alternative**: Euclidean Distance
- **Range**: 0-1 (higher = more similar)

### Performance
- **Inference Time**: ~50ms per image (CPU)
- **Memory Usage**: ~100MB for model + embeddings
- **Accuracy**: Depends on image quality and similarity

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- ResNet architecture by Microsoft Research
- PyTorch and torchvision for deep learning
- OpenCV for image processing
- scikit-learn for similarity metrics

---

**Happy Home Staging! 🏠✨** 