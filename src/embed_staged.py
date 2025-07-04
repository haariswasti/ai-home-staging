import os, numpy as np
import torch
from src.data_loader import load_image
from src.feature_extractor import FeatureExtractor

model = FeatureExtractor().eval()
staged_dir = "../data/staged_bedroom"
embs, names = [], []

for fn in os.listdir(staged_dir):
    img = load_image(os.path.join(staged_dir, fn)).unsqueeze(0)  # add batch dim
    with torch.no_grad():
        feat = model(img).cpu().numpy().squeeze()
    embs.append(feat)
    names.append(fn)

os.makedirs("../models", exist_ok=True)
np.save("../models/staged_embs.npy", np.vstack(embs))
np.save("../models/staged_names.npy", np.array(names))