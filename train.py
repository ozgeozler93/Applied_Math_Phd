import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from tqdm import tqdm
import os

# Kendi dosyalarımızdan import ediyoruz
from dataset import SegmentationDataset
from model import UNet 

# --- Ayarlar ---
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"
LEARNING_RATE = 1e-3
BATCH_SIZE = 8
NUM_EPOCHS = 50
IMAGE_SIZE = 256
CHECKPOINT_DIR = "checkpoints"

def check_accuracy(loader, model, loss_fn, device):
    model.eval()
    val_loss = 0
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device).unsqueeze(1)
            preds = model(x)
            loss = loss_fn(preds, y)
            val_loss += loss.item()
    model.train()
    return val_loss / len(loader)

def main():
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    print(f"Eğitim başlıyor... Cihaz: {DEVICE}")

    # Dataset ve Loader
    full_dataset = SegmentationDataset("images", "labels", IMAGE_SIZE, IMAGE_SIZE, is_train=True)
    train_size = int(0.9 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_set, val_set = random_split(full_dataset, [train_size, val_size])

    train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=BATCH_SIZE, shuffle=False)

    # Model Tanımlama (Parametreler model.py ile uyumlu)
    model = UNet(n_channels=3, n_classes=1).to(DEVICE)
    
    # Bina ağırlıklı kayıp fonksiyonu
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([5.0]).to(DEVICE))
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    # OneCycleLR: Hızlı yakınsama sağlar
    scheduler = optim.lr_scheduler.OneCycleLR(
        optimizer, max_lr=LEARNING_RATE, steps_per_epoch=len(train_loader), epochs=NUM_EPOCHS
    )

    best_loss = float("inf")

    for epoch in range(1, NUM_EPOCHS + 1):
        model.train()
        loop = tqdm(train_loader, desc=f"Epoch {epoch}/{NUM_EPOCHS}")
        
        for batch_idx, (data, targets) in enumerate(loop):
            data, targets = data.to(DEVICE), targets.to(DEVICE).unsqueeze(1)

            predictions = model(data)
            loss = loss_fn(predictions, targets)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            scheduler.step()

            loop.set_postfix(loss=loss.item())

        # Her epoch sonunda doğrulama
        val_loss = check_accuracy(val_loader, model, loss_fn, DEVICE)
        print(f"Validation Loss: {val_loss:.4f}")

        # En iyi modeli kaydet
        if val_loss < best_loss:
            best_loss = val_loss
            torch.save(model.state_dict(), os.path.join(CHECKPOINT_DIR, "best_model.pth"))
            print(">>> Yeni en iyi model kaydedildi!")

if __name__ == "__main__":
    main()