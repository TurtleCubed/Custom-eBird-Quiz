import torch
from torchvision.models import resnet50, ResNet50_Weights
import numpy as np


import torch
import torch.nn as nn
import torch.nn.functional as F

import torch.nn as nn
import torchvision
import torchvision.transforms as transforms

from tqdm import tqdm
import pickle
import os
import matplotlib.pyplot as plt

from rated_data import RatedData

NUM_EPOCHS = 10
EVAL_EPOCH_EVERY = 10
DIR = "./BirdRater/rating_dataset"

normalize = transforms.Normalize(
   mean=[0.485, 0.456, 0.406],
   std=[0.229, 0.224, 0.225]
)
trans = transforms.Compose([
    transforms.ToTensor(),
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    normalize
])

test_trans = transforms.Compose([
    transforms.ToTensor(),
    transforms.Resize((224, 224)),
    normalize
])

trainset = RatedData(DIR, train=True, transform=trans)
train_dl = torch.utils.data.DataLoader(
    trainset, batch_size=16, shuffle=True, num_workers=2
    )

testset = RatedData(DIR, train=False, transform=test_trans)
test_dl = torch.utils.data.DataLoader(
    testset, batch_size=16, shuffle=False, num_workers=2
    )

def train_model(train_dl, model):
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    train_losses = []
    val_losses = []
    model.train()
    for epoch in tqdm(range(NUM_EPOCHS)):
        print(f"Epoch {epoch+1:02d}/{NUM_EPOCHS}")
        num_total, num_correct = 0, 0
        train_losses_epoch = 0
        for i, (inputs, targets) in enumerate(train_dl):
            torch.cuda.empty_cache()
            targets = targets.to(device)
            inputs = inputs.to(device)
            
            optimizer.zero_grad()
            
            yhat = model(inputs)
            loss = criterion(yhat, targets)
            loss.backward()
            optimizer.step()
            train_losses_epoch += loss.item()
            _, predicted = yhat.max(1)
            num_total += targets.size(0)
            num_correct += (predicted == targets).sum().item()

        print(f"avg_loss: {train_losses_epoch/len(train_dl)}, num_correct: {num_correct}, num_total: {num_total}")
        train_losses.append(train_losses_epoch/len(train_dl))

    return train_losses

def evaluate_model(val_dl, model):
    model.eval()
    criterion = nn.CrossEntropyLoss()

    test_loss, num_correct, num_total = 0, 0, 0
    with torch.no_grad():
        for i, (inputs, targets) in enumerate(val_dl):
            targets = targets.to(device)
            inputs = inputs.to(device)
            yhat = model(inputs)
            
            loss = criterion(yhat, targets)

            test_loss += loss.item()
            _, predicted = yhat.max(1)
            num_total += targets.size(0)
            num_correct += (predicted == targets).sum().item()

            print(f"test_loss: {test_loss}, num_correct: {num_correct}, num_total: {num_total}")

    accuracy = num_correct/num_total
    return test_loss, accuracy

if __name__=="__main__":
    # Check for GPU
    if torch.cuda.is_available():  
        dev = "cuda:0"
        print(f"Found GPU. Using: {dev}")
    else:  
        dev = "cpu"
    # dev = "cpu"
    device = torch.device(dev)

    model = resnet50(weights=ResNet50_Weights.DEFAULT)
    model = model.to(device)

    # Freeze the layers
    for param in model.parameters():
        param.requires_grad = True

    # Change the last layer to cifar10 number of output classes, and then just finetune these layers
    num_feats = model.fc.in_features
    model.fc = nn.Sequential(nn.Linear(num_feats, 5))
    model = model.to(device)

    # model = ResNet50(img_channel=3, num_classes=10).to(device)
    # model = resnet50(num_classes=10)
    # model = model.to(device)
    
    train_losses = train_model(train_dl, model)
    test_loss, accuracy = evaluate_model(test_dl, model)

    logger.info(f"test_loss: {test_loss}, accuracy: {accuracy}")

    torch.save(model.state_dict(), f"resnet50_cub_acc{accuracy:.02f}.pth")