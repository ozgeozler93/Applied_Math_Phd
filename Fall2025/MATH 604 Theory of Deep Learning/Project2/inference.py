import torch
import numpy as np
import os
import cv2
import albumentations as A
from albumentations.pytorch import ToTensorV2
from PIL import Image
from model import AttentionUNet

if torch.cuda.is_available(): DEVICE = "cuda"
elif torch.backends.mps.is_available(): DEVICE = "mps"
else: DEVICE = "cpu"

def run_inference():
    model = AttentionUNet(3, 1).to(DEVICE)
    checkpoint = torch.load("checkpoints/best_model.pth", map_location=DEVICE)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    # Inference Transform (CLAHE ekli)
    inf_transform = A.Compose([
        A.Resize(512, 512),
        A.CLAHE(clip_limit=4.0, p=1.0),
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ToTensorV2(),
    ])

    IMG_DIR, OUT_DIR = "to-test", "inference_results"
    os.makedirs(OUT_DIR, exist_ok=True)
    test_images = [f for f in os.listdir(IMG_DIR) if f.endswith(('.png', '.jpg'))]

    print(f"Tahmin başlıyor... Klasör: {IMG_DIR}")

    for img_name in test_images:
        image_pil = Image.open(os.path.join(IMG_DIR, img_name)).convert("RGB")
        image_np = np.array(image_pil)
        
        # TTA: Orijinal ve Yatay Çevrilmiş
        t1 = inf_transform(image=image_np)["image"].unsqueeze(0).to(DEVICE)
        t2 = inf_transform(image=np.fliplr(image_np))["image"].unsqueeze(0).to(DEVICE)
        
        with torch.no_grad():
            out1 = torch.sigmoid(model(t1))
            out2 = torch.sigmoid(model(t2))
            out2 = torch.flip(out2, [3]) # Geri çevir
            final_prob = (out1 + out2) / 2
        
        # Eşikleme ve Temizlik
        mask = (final_prob.squeeze().cpu().numpy() > 0.4).astype(np.uint8)
        kernel = np.ones((3,3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        cv2.imwrite(os.path.join(OUT_DIR, f"pred_{img_name}"), mask * 255)
        print(f"Segmented: {img_name}")

if __name__ == "__main__":
    run_inference()