import torch
import numpy as np
import os
import cv2
from PIL import Image
from torchvision import transforms
from model import AttentionUNet

DEVICE = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")

def run_inference():
    model = AttentionUNet(3, 1).to(DEVICE)
    checkpoint = torch.load("checkpoints/best_model.pth", map_location=DEVICE)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    transform = transforms.Compose([
        transforms.Resize((512, 512)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    IMG_DIR, LABEL_DIR, OUT_DIR = "to-test", "labels", "inference_results"
    os.makedirs(OUT_DIR, exist_ok=True)
    
    test_images = [f for f in os.listdir(IMG_DIR) if f.endswith('.png')]
    iou_list = []

    for img_name in test_images:
        img_path = os.path.join(IMG_DIR, img_name)
        image = Image.open(img_path).convert("RGB")
        
        # --- TEST TIME AUGMENTATION (TTA) ---
        # 1. Orijinal Görüntü
        img_orig = transform(image).unsqueeze(0).to(DEVICE)
        # 2. Yatay Çevrilmiş
        img_flip = transform(image.transpose(Image.FLIP_LEFT_RIGHT)).unsqueeze(0).to(DEVICE)
        
        with torch.no_grad():
            out_orig = torch.sigmoid(model(img_orig))
            out_flip = torch.sigmoid(model(img_flip))
            # Çevrilmiş olanı geri çevirip orijinalle topla ve ortala
            out_flip = torch.flip(out_flip, [3])
            final_out = (out_orig + out_flip) / 2
        
        # Eşik değerini (Threshold) 0.6 yaparak daha keskin sonuç alıyoruz
        mask = (final_out.squeeze().cpu().numpy() > 0.6).astype(np.uint8)
        
        # --- MORFOLOJİK TEMİZLİK (Gürültü Silme) ---
        kernel = np.ones((3,3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel) # Küçük lekeleri siler

        # IoU Hesapla
        label_path = os.path.join(LABEL_DIR, img_name)
        if os.path.exists(label_path):
            label = np.array(Image.open(label_path).convert("L").resize((512, 512)))
            label = (label > 128).astype(np.uint8)
            intersection = np.logical_and(mask, label).sum()
            union = np.logical_or(mask, label).sum()
            iou = intersection / union if union > 0 else 1.0
            iou_list.append(iou)
            print(f"{img_name} IoU: {iou:.4f}")

        cv2.imwrite(os.path.join(OUT_DIR, f"{img_name.split('.')[0]}_segmented.png"), mask * 255)
        print(f"{img_name} başarıyla segment edildi.")
        
    print(f"\n--- YENİ MEAN IoU (TTA + Morph): {np.mean(iou_list):.4f} ---")

if __name__ == "__main__":
    run_inference()