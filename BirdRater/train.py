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

# FOR TRISTAN TO TUNE
BATCH_SIZE = 16
WORKERS = 4

NUM_EPOCHS = 100
LR = 1e-3
EVAL_EPOCH_EVERY = 10
DIR = "./BirdRater/tmp"
TEST_DIR = "./BirdRater/tristan_set"

def train_model(train_dl, model, val_dl):
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    train_losses = []
    val_losses = []
    model.train()
    for epoch in range(NUM_EPOCHS):
        train_losses_epoch = 0
        num_correct = 0
        num_total = 0
        with tqdm(train_dl, unit="batch") as tepoch:
            for inputs, targets in tepoch:
                tepoch.set_description(f"Epoch {epoch}")
                targets = targets.to(device).float()
                inputs = inputs.to(device)
                
                optimizer.zero_grad()
                
                yhat = model(inputs).flatten() * 4 + 1
                loss = criterion(yhat, targets)
                loss.backward()
                optimizer.step()
                train_losses_epoch += loss.item()

                num_total += targets.size(0)
                num_correct += (torch.abs(targets - yhat) < 0.5).sum().item()

                tepoch.set_postfix(loss=train_losses_epoch / num_total, accuracy=num_correct/num_total)

        # print(f"avg_loss: {train_losses_epoch/len(train_dl)}")
        train_losses.append(train_losses_epoch/len(train_dl))
        if epoch % EVAL_EPOCH_EVERY == 0 and epoch != 0:
            val_losses.append(evaluate_model(val_dl, model)[0])

    return train_losses

def evaluate_model(val_dl, model):
    model.eval()
    criterion = nn.MSELoss()

    test_loss, num_correct, num_total = 0, 0, 0
    with torch.no_grad():
        for inputs, targets in val_dl:
            targets = targets.to(device).float()
            inputs = inputs.to(device)
            yhat = model(inputs).flatten() * 4 + 1
            
            loss = criterion(yhat, targets)

            test_loss += loss.item()
            num_total += targets.size(0)
            num_correct += (torch.abs(targets - yhat) < 0.5).sum().item()

    print(f"val_loss: {test_loss}, num_correct: {num_correct}, num_total: {num_total}")
    accuracy = num_correct/num_total
    return test_loss / num_total, accuracy

if __name__=="__main__":
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
        trainset, batch_size=BATCH_SIZE, shuffle=True, num_workers=WORKERS
    )

    valset = RatedData(DIR, train=False, val=True, transform=test_trans)
    val_dl = torch.utils.data.DataLoader(
        valset, batch_size=BATCH_SIZE, shuffle=False, num_workers=WORKERS
    )

    testset = RatedData(TEST_DIR, split=False, transform=test_trans)
    test_dl = torch.utils.data.DataLoader(
        testset, batch_size=BATCH_SIZE, shuffle=False, num_workers=WORKERS
    )

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
    model.fc = nn.Sequential(nn.Linear(num_feats, 256), nn.Linear(256, 1), nn.Sigmoid())
    model = model.to(device)

    # model = ResNet50(img_channel=3, num_classes=10).to(device)
    # model = resnet50(num_classes=10)
    # model = model.to(device)
    
    train_losses = train_model(train_dl, model, val_dl)
    test_loss, accuracy = evaluate_model(test_dl, model)

    print(f"test_loss: {test_loss}, accuracy: {accuracy}")

    torch.save(model.state_dict(), f"resnet50_trist_acc{accuracy:.02f}.pth")