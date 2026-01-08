import torch
from torchvision import transforms
from PIL import Image
import os
import numpy as np
from model import AttentionUNet

# Ayarlar
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"
MODEL_PATH = "checkpoints/best_model.pth"
LABEL_DIR = "labels"
TEST_DIR = "to-test"

def calculate_iou(pred_mask, true_mask):
    intersection = np.logical_and(pred_mask, true_mask).sum()
    union = np.logical_or(pred_mask, true_mask).sum()
    if union == 0:
        return 1.0
    return intersection / union

def run_tuning():
    model = AttentionUNet(n_channels=3, n_classes=1).to(DEVICE)
    if not os.path.exists(MODEL_PATH):
        print("Hata: model bulunamadı.")
        return
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.eval()

    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    # Test edilecek eşik değerleri (0.1'den 0.9'a kadar)
    thresholds = np.arange(0.1, 1.0, 0.1)
    results = {round(t, 1): [] for t in thresholds}

    print(f"Cihaz: {DEVICE} üzerinde Threshold Tuning başlatılıyor...\n")

    for img_name in os.listdir(TEST_DIR):
        if img_name.endswith((".png", ".jpg", ".jpeg")):
            img_path = os.path.join(TEST_DIR, img_name)
            label_path = os.path.join(LABEL_DIR, img_name)
            
            if not os.path.exists(label_path):
                continue

            img = Image.open(img_path).convert("RGB")
            input_tensor = transform(img).unsqueeze(0).to(DEVICE)
            
            label_img = Image.open(label_path).convert("L").resize((256, 256))
            true_mask = (np.array(label_img) > 127).astype(np.uint8)

            with torch.no_grad():
                output = torch.sigmoid(model(input_tensor))
                output_np = output.squeeze().cpu().numpy()

            for t in thresholds:
                t_key = round(t, 1)
                pred_mask = (output_np > t).astype(np.uint8)
                iou = calculate_iou(pred_mask, true_mask)
                results[t_key].append(iou)

    # Sonuçları Analiz Et
    best_iou = 0
    best_t = 0
    
    print("--- EŞİK DEĞERİ ANALİZİ ---")
    for t in sorted(results.keys()):
        mean_iou = np.mean(results[t])
        print(f"Eşik {t:.1} -> Ortalama IoU: {mean_iou:.4f}")
        if mean_iou > best_iou:
            best_iou = mean_iou
            best_t = t

    print("\n" + "="*30)
    print(f"EN İYİ EŞİK DEĞERİ: {best_t}")
    print(f"MAKSİMUM MEAN IoU: {best_iou:.4f}")
    print("="*30)

if __name__ == "__main__":
    run_tuning()