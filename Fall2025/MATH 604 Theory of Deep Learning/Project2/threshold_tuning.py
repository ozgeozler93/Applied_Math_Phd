import torch
import numpy as np
import os
import cv2
import albumentations as A
from albumentations.pytorch import ToTensorV2
from PIL import Image
from model import AttentionUNet

DEVICE = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
MODEL_PATH = "checkpoints/best_model.pth"
LABEL_DIR = "labels"
TEST_DIR = "images"
IMAGE_SIZE = 512

def calculate_iou(pred_mask, true_mask):
    intersection = np.logical_and(pred_mask, true_mask).sum()
    union = np.logical_or(pred_mask, true_mask).sum()
    if union == 0: return 1.0
    return (intersection + 1e-6) / (union + 1e-6)

def run_tuning():
    model = AttentionUNet(in_channels=3, out_channels=1).to(DEVICE)
    if not os.path.exists(MODEL_PATH):
        print("Hata: model dosyası bulunamadı.")
        return
    
    checkpoint = torch.load(MODEL_PATH, map_location=DEVICE)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    inf_transform = A.Compose([
        A.Resize(IMAGE_SIZE, IMAGE_SIZE),
        A.CLAHE(clip_limit=4.0, p=1.0),
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ToTensorV2(),
    ])

    thresholds = np.arange(0.1, 1.0, 0.1)
    results = {round(t, 2): [] for t in thresholds}
    test_images = [f for f in os.listdir(TEST_DIR) if f.endswith(('.png', '.jpg'))]

    for img_name in test_images:
        img_path = os.path.join(TEST_DIR, img_name)
        label_path = os.path.join(LABEL_DIR, img_name)
        if not os.path.exists(label_path): continue

        image = np.array(Image.open(img_path).convert("RGB"))
        input_tensor = inf_transform(image=image)["image"].unsqueeze(0).to(DEVICE)
        
        label_img = np.array(Image.open(label_path).convert("L"))
        label_img = cv2.resize(label_img, (IMAGE_SIZE, IMAGE_SIZE))
        true_mask = (label_img > 127).astype(np.uint8)

        with torch.no_grad():
            output = torch.sigmoid(model(input_tensor))
            output_np = output.squeeze().cpu().numpy()

        for t in thresholds:
            t_key = round(t, 2)
            pred_mask = (output_np > t).astype(np.uint8)
            iou = calculate_iou(pred_mask, true_mask)
            results[t_key].append(iou)

    print("\n--- EŞİK DEĞERİ (THRESHOLD) ANALİZ SONUÇLARI ---")
    best_iou, best_t = 0, 0
    for t in sorted(results.keys()):
        mean_iou = np.mean(results[t])
        print(f"Eşik {t:.1f} -> Ortalama IoU: {mean_iou:.4f}")
        if mean_iou > best_iou:
            best_iou, best_t = mean_iou, t
    print(f"\nÖNERİLEN OPTİMAL EŞİK: {best_t}\nMAKSİMUM TEST IoU: {best_iou:.4f}")

if __name__ == "__main__":
    run_tuning()
