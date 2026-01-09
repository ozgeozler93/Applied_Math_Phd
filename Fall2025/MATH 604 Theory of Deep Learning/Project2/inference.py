import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
import numpy as np
import os
import cv2
from torchvision import transforms
from model import AttentionUNet

# Cihaz Ayarı
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

def calculate_iou(pred, target):
    intersection = np.logical_and(pred, target).sum()
    union = np.logical_or(pred, target).sum()
    return intersection / union if union > 0 else 1.0

def run_inference():
    # Modeli Başlat (n_channels=3, n_classes=1)
    model = AttentionUNet(3, 1).to(DEVICE)
    
    # En iyi modeli yükle
    checkpoint = torch.load("checkpoints/best_model.pth", map_location=DEVICE)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    
    # Görüntü dönüşümü (Eğitimle aynı olmalı)
    transform = transforms.Compose([
        transforms.Resize((512, 512)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    IMG_DIR = "images"
    LABEL_DIR = "labels"
    OUT_DIR = "inference_results"
    os.makedirs(OUT_DIR, exist_ok=True)
    
    iou_list = []
    # Test için ilk 10 resmi alalım
    test_images = [f for f in os.listdir(IMG_DIR) if f.endswith('.png')][:10]
    
    print(f"Inference başlıyor... Cihaz: {DEVICE}")
    
    for img_name in test_images:
        img_path = os.path.join(IMG_DIR, img_name)
        image = Image.open(img_path).convert("RGB")
        input_tensor = transform(image).unsqueeze(0).to(DEVICE)
        
        with torch.no_grad():
            output = torch.sigmoid(model(input_tensor))
            mask = (output.squeeze().cpu().numpy() > 0.5).astype(np.uint8)
        
        # IoU Hesaplama
        label_path = os.path.join(LABEL_DIR, img_name)
        if os.path.exists(label_path):
            label = np.array(Image.open(label_path).convert("L").resize((512, 512)))
            label = (label > 128).astype(np.uint8)
            iou = calculate_iou(mask, label)
            iou_list.append(iou)
            print(f"Resim: {img_name} | IoU: {iou:.4f}")
        
        # Sonucu kaydet
        cv2.imwrite(os.path.join(OUT_DIR, f"pred_{img_name}"), mask * 255)

    if iou_list:
        print(f"\n--- FİNAL MEAN IoU: {np.mean(iou_list):.4f} ---")

if __name__ == "__main__":
    run_inference()