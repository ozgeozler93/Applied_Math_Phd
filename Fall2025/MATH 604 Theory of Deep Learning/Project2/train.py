import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from tqdm import tqdm
import os
import matplotlib.pyplot as plt
from dataset import SegmentationDataset
from model import AttentionUNet

# Cihaz Seçimi
if torch.cuda.is_available(): DEVICE = "cuda"
elif torch.backends.mps.is_available(): DEVICE = "mps"
else: DEVICE = "cpu"

LEARNING_RATE = 5e-5
BATCH_SIZE = 4
NUM_EPOCHS = 150
IMAGE_SIZE = 512
CHECKPOINT_PATH = "checkpoints/best_model.pth"

class DiceLoss(nn.Module):
    def __init__(self, smooth=1.0):
        super().__init__()
        self.smooth = smooth
    def forward(self, preds, targets):
        preds = torch.sigmoid(preds).view(-1)
        targets = targets.view(-1)
        intersection = (preds * targets).sum()
        return 1 - ((2. * intersection + self.smooth) / (preds.sum() + targets.sum() + self.smooth))

class FocalLoss(nn.Module):
    def __init__(self, alpha=0.8, gamma=2):
        super().__init__()
        self.alpha, self.gamma = alpha, gamma
    def forward(self, inputs, targets):
        BCE_loss = F.binary_cross_entropy_with_logits(inputs, targets, reduction='none')
        pt = torch.exp(-BCE_loss)
        return torch.mean(self.alpha * (1 - pt)**self.gamma * BCE_loss)

def evaluate_model(loader, model, focal_fn, dice_fn, device):
    model.eval()
    val_loss, total_iou, num_samples = 0, 0, 0
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device).unsqueeze(1)
            preds = model(x)
            # val_loss += (0.5 * focal_fn(preds, y) + 0.5 * dice_fn(preds, y)).item()
            val_loss += (0.3 * focal_fn(preds, y) + 0.7 * dice_fn(preds, y)).item()
            preds_binary = (torch.sigmoid(preds) > 0.5).float()
            intersection = (preds_binary * y).sum(dim=(1, 2, 3))
            union = preds_binary.sum(dim=(1, 2, 3)) + y.sum(dim=(1, 2, 3)) - intersection
            total_iou += ((intersection + 1e-6) / (union + 1e-6)).sum().item()
            num_samples += y.size(0)
    model.train()
    return val_loss / len(loader), total_iou / num_samples

def main():
    os.makedirs("checkpoints", exist_ok=True)
    full_dataset = SegmentationDataset("images", "labels", IMAGE_SIZE, IMAGE_SIZE, is_train=True)
    train_size = int(0.85 * len(full_dataset))
    train_set, val_set = random_split(full_dataset, [train_size, len(full_dataset)-train_size])
    train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=BATCH_SIZE, shuffle=False)

    model = AttentionUNet(3, 1).to(DEVICE)
    focal_fn, dice_fn = FocalLoss(), DiceLoss()
    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=NUM_EPOCHS)

    best_iou, counter, patience = 0.0, 0, 25
    train_losses, val_losses = [], []

    for epoch in range(1, NUM_EPOCHS + 1):
        model.train()
        epoch_loss = 0
        loop = tqdm(train_loader, desc=f"Epoch {epoch}/{NUM_EPOCHS}")
        for data, targets in loop:
            data, targets = data.to(DEVICE), targets.to(DEVICE).unsqueeze(1)
            # Warmup
            if epoch <= 5:
                for pg in optimizer.param_groups: pg['lr'] = LEARNING_RATE * (epoch / 5)
            
            preds = model(data)
            # loss = 0.5 * focal_fn(preds, targets) + 0.5 * dice_fn(preds, targets)
            loss = (0.3 * focal_fn(preds, targets)) + (0.7 * dice_fn(preds, targets))
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        
        avg_v_loss, mean_iou = evaluate_model(val_loader, model, focal_fn, dice_fn, DEVICE)
        print(f"Val IoU: {mean_iou:.4f}")
        scheduler.step()

        if mean_iou > best_iou:
            best_iou = mean_iou
            torch.save({"model_state_dict": model.state_dict()}, CHECKPOINT_PATH)
            counter = 0
        else:
            counter += 1
            if counter >= patience: break

if __name__ == "__main__":
    main()