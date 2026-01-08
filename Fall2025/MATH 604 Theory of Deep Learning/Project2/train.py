import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from tqdm import tqdm
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from dataset import SegmentationDataset
from model import AttentionUNet

# --- Ayarlar ---
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"
LEARNING_RATE = 5e-5 # Attention U-Net için biraz daha düşük bir LR daha stabil olabilir
BATCH_SIZE = 4
NUM_EPOCHS = 100
IMAGE_SIZE = 256
CHECKPOINT_DIR = "checkpoints"
CHECKPOINT_PATH = os.path.join(CHECKPOINT_DIR, "best_model.pth")

class DiceLoss(nn.Module):
    def __init__(self, smooth=1e-6):
        super(DiceLoss, self).__init__()
        self.smooth = smooth

    def forward(self, preds, targets):
        preds = torch.sigmoid(preds)
        preds = preds.view(-1)
        targets = targets.view(-1)
        intersection = (preds * targets).sum()
        dice = (2. * intersection + self.smooth) / (preds.sum() + targets.sum() + self.smooth)
        return 1 - dice

class FocalLoss(nn.Module):
    def __init__(self, alpha=0.8, gamma=2, reduction='mean'):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, inputs, targets):
        BCE_loss = F.binary_cross_entropy_with_logits(inputs, targets, reduction='none')
        pt = torch.exp(-BCE_loss)
        F_loss = self.alpha * (1 - pt)**self.gamma * BCE_loss
        
        if self.reduction == 'mean':
            return torch.mean(F_loss)
        elif self.reduction == 'sum':
            return torch.sum(F_loss)
        else:
            return F_loss

def evaluate_model(loader, model, focal_fn, dice_fn, device):
    model.eval()
    val_loss = 0
    total_iou = 0
    num_samples = 0
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device).unsqueeze(1)
            preds = model(x)

            loss_focal = focal_fn(preds, y)
            loss_dice = dice_fn(preds, y)
            loss = (0.5 * loss_focal) + (0.5 * loss_dice)
            val_loss += loss.item()
            
            preds_prob = torch.sigmoid(preds)
            preds_binary = (preds_prob > 0.5).float()
            
            intersection = (preds_binary * y).sum(dim=(1, 2, 3))
            union = preds_binary.sum(dim=(1, 2, 3)) + y.sum(dim=(1, 2, 3)) - intersection
            iou = (intersection + 1e-6) / (union + 1e-6)
            
            total_iou += iou.sum().item()
            num_samples += y.size(0)
            
    model.train()
    avg_loss = val_loss / len(loader)
    mean_iou = total_iou / num_samples
    return avg_loss, mean_iou

def main():
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    print(f"Eğitim başlıyor... Cihaz: {DEVICE}")

    full_dataset = SegmentationDataset("images", "labels", IMAGE_SIZE, IMAGE_SIZE, is_train=True)
    train_size = int(0.9 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_set, val_set = random_split(full_dataset, [train_size, val_size])

    train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_set, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)

    model = AttentionUNet(in_channels=3, out_channels=1).to(DEVICE)
    
    # Yeni Hibrit Kayıp Fonksiyonları: Focal + Dice
    focal_fn = FocalLoss(alpha=0.25, gamma=2.5)
    dice_fn = DiceLoss()

    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, T_0=10, T_mult=2, eta_min=1e-6)

    start_epoch = 1
    best_loss = float("inf")
    train_losses, val_losses = [], []
    early_stopping_patience = 10
    early_stopping_counter = 0



    for epoch in range(start_epoch, NUM_EPOCHS + 1):
        model.train()
        loop = tqdm(train_loader, desc=f"Epoch {epoch}/{NUM_EPOCHS}")
        epoch_loss = 0

        for batch_idx, (data, targets) in enumerate(loop):
            data, targets = data.to(DEVICE), targets.to(DEVICE).unsqueeze(1)
            predictions = model(data)

            loss_focal = focal_fn(predictions, targets)
            loss_dice = dice_fn(predictions, targets)
            loss = (0.5 * loss_focal) + (0.5 * loss_dice)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            loop.set_postfix(loss=loss.item())

        avg_epoch_loss = epoch_loss / len(train_loader)
        train_losses.append(avg_epoch_loss)

        val_loss, mean_iou = evaluate_model(val_loader, model, focal_fn, dice_fn, DEVICE)
        val_losses.append(val_loss)
        print(f"Validation Loss: {val_loss:.4f}, Mean IoU: {mean_iou:.4f}")

        scheduler.step()

        if val_loss < best_loss:
            best_loss = val_loss
            checkpoint = {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "loss": best_loss,
                "train_losses": train_losses,
                "val_losses": val_losses
            }
            torch.save(checkpoint, CHECKPOINT_PATH)
            print(">>> Yeni en iyi model kaydedildi! (Focal + Dice Hybrid)")
            early_stopping_counter = 0
        else:
            early_stopping_counter += 1
            print(f">>> Early stopping counter: {early_stopping_counter}/{early_stopping_patience}")
            if early_stopping_counter >= early_stopping_patience:
                print(">>> Early stopping! Eğitim durduruluyor.")
                break
    
    plt.figure(figsize=(10, 5))
    plt.plot(train_losses, label="Training Loss")
    plt.plot(val_losses, label="Validation Loss")
    plt.title("Training & Validation Loss (Focal + Dice)")
    plt.xlabel("Epochs")
    plt.ylabel("Loss")
    plt.legend()
    plt.savefig("loss_graph.png")
    print(">>> Eğitim tamamlandı ve kayıp grafiği 'loss_graph.png' olarak kaydedildi.")

if __name__ == "__main__":
    main()
