import os
import json
import cv2
import torch


def load_image(path, resize=(256,256)):
    img = cv2.imread(path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, resize)
    img = torch.from_numpy(img).float() / 255.0
    # Convert from (H, W, C) to (C, H, W) format for PyTorch
    img = img.permute(2, 0, 1)
    return img

def load_annotation(path):
    with open(path, 'r') as f:
        annotation = json.load(f)

    #need parsing logicn still   
    return annotation