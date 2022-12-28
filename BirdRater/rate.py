import torch
from torchvision.models import resnet50, ResNet50_Weights
import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.nn as nn
import torchvision.transforms as transforms

import matplotlib.pyplot as plt
from torchvision.datasets.folder import default_loader

MODEL_PATH = "./resnet50_cub_acc0.25.pth"
IMG_TO_RATE = "./BirdRater/tristan_set/456861741_2.00.jpg"

def rate_img(model, imdir):
    with torch.no_grad():
        img = test_trans(default_loader(imdir)).to(device).unsqueeze(0)
        return model(img) * 4 + 1

if __name__=="__main__":
        
    normalize = transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )

    test_trans = transforms.Compose([
        transforms.ToTensor(),
        transforms.Resize((224, 224)),
        normalize
    ])

    # Check for GPU
    if torch.cuda.is_available():  
        dev = "cuda:0"
        print(f"Found GPU. Using: {dev}")
    else:  
        dev = "cpu"
        print(f"Did not find GPU. Using: {dev}")
    device = torch.device(dev)

    model = resnet50(weights=ResNet50_Weights.DEFAULT)
    model = model.to(device)

    num_feats = model.fc.in_features
    model.fc = nn.Sequential(nn.Linear(num_feats, 256), nn.Linear(256, 1), nn.Sigmoid())
    model = model.to(device)

    model.load_state_dict(torch.load(MODEL_PATH))
    model.eval()
    
    print(rate_img(model, IMG_TO_RATE))