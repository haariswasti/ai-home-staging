import os
import json
import cv2
import torch


def load_image(path, resize=(256,256)):
    img = cv2.imread(path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, resize)
    img = torch.from_numpy(img).float() / 255.0
    return img

def load_annotation(path):
    with open(path, 'r') as f:
        annotation = json.load(f)

    #need parsing logicn still   
    return annotation