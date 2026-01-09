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

# --- Gelişmiş Hiperparametreler ---
DEVICE = "cuda" if torch.backends.mps.is_available() else "cpu"
LEARNING_RATE = 1e-4  # Biraz daha yüksek başladık, Warmup ile dengeleyeceğiz
BATCH_SIZE = 4
NUM_EPOCHS = 100
IMAGE_SIZE = 512
CHECKPOINT_DIR = "checkpoints"
CHECKPOINT_PATH = os.path.join(CHECKPOINT_DIR, "best_model.pth")

class DiceLoss(nn.Module):
    def __init__(self, smooth=1.0): # Smooth değerini artırdık
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
        return torch.mean(F_loss) if self.reduction == 'mean' else torch.sum(F_loss)

def evaluate_model(loader, model, focal_fn, dice_fn, device):
    model.eval()
    val_loss = 0
    total_iou = 0
    num_samples = 0
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device).unsqueeze(1)
            preds = model(x)
            # Eval sırasında da aynı ağırlıklı loss
            loss = (0.7 * focal_fn(preds, y)) + (0.3 * dice_fn(preds, y))
            val_loss += loss.item()
            
            preds_binary = (torch.sigmoid(preds) > 0.5).float()
            intersection = (preds_binary * y).sum(dim=(1, 2, 3))
            union = preds_binary.sum(dim=(1, 2, 3)) + y.sum(dim=(1, 2, 3)) - intersection
            total_iou += ((intersection + 1e-6) / (union + 1e-6)).sum().item()
            num_samples += y.size(0)
            
    model.train()
    return val_loss / len(loader), total_iou / num_samples

def main():
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    print(f"Gelişmiş Eğitim Başlıyor... Cihaz: {DEVICE}")

    full_dataset = SegmentationDataset("images", "labels", IMAGE_SIZE, IMAGE_SIZE, is_train=True)
    train_size = int(0.85 * len(full_dataset)) # Val setini biraz büyüttük daha güvenilir skor için
    val_size = len(full_dataset) - train_size
    train_set, val_set = random_split(full_dataset, [train_size, val_size])

    train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_set, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)

    model = AttentionUNet(in_channels=3, out_channels=1).to(DEVICE)
    
    # Agresif Loss Ağırlıkları
    focal_fn = FocalLoss(alpha=0.8, gamma=2.0) 
    dice_fn = DiceLoss()

    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-4) # AdamW daha iyi regülasyon sağlar
    
    # Cosine Annealing ile kademeli düşüş
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=NUM_EPOCHS)

    best_iou = 0.0
    train_losses, val_losses = [], []
    patience = 15 # Early stopping süresini biraz uzattık
    counter = 0

    for epoch in range(1, NUM_EPOCHS + 1):
        model.train()
        epoch_loss = 0
        loop = tqdm(train_loader, desc=f"Epoch {epoch}/{NUM_EPOCHS}")

        for data, targets in loop:
            data, targets = data.to(DEVICE), targets.to(DEVICE).unsqueeze(1)
            
            # Linear Warmup (İlk 5 epoch)
            if epoch <= 5:
                for param_group in optimizer.param_groups:
                    param_group['lr'] = LEARNING_RATE * (epoch / 5)

            preds = model(data)
            loss = (0.7 * focal_fn(preds, targets)) + (0.3 * dice_fn(preds, targets))

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            loop.set_postfix(loss=loss.item(), lr=optimizer.param_groups[0]['lr'])

        avg_train_loss = epoch_loss / len(train_loader)
        val_loss, mean_iou = evaluate_model(val_loader, model, focal_fn, dice_fn, DEVICE)
        
        train_losses.append(avg_train_loss)
        val_losses.append(val_loss)
        
        print(f"Epoch {epoch} -> Val Loss: {val_loss:.4f}, Mean IoU: {mean_iou:.4f}")

        scheduler.step()

        # En iyi IoU'ya göre kaydetmek segmentasyonda daha mantıklıdır
        if mean_iou > best_iou:
            best_iou = mean_iou
            torch.save({"model_state_dict": model.state_dict()}, CHECKPOINT_PATH)
            print(f">>> Yeni En İyi Model Kaydedildi! IoU: {best_iou:.4f}")
            counter = 0
        else:
            counter += 1
            if counter >= patience:
                print("Early Stopping Tetiklendi.")
                break
    
    # Grafik Çizimi
    plt.plot(train_losses, label="Train Loss")
    plt.plot(val_losses, label="Val Loss")
    plt.legend(); plt.savefig("loss_graph.png")

if __name__ == "__main__":
    main()