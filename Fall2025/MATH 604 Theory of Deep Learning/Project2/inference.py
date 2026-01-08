import torch
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
import os
import numpy as np
from model import UNet
import cv2

DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"
MODEL_PATH = "checkpoints/best_model.pth"
LABEL_DIR = "labels"

def calculate_iou(pred_mask, true_mask):
    true_mask = (true_mask > 127).astype(np.uint8)
    intersection = np.logical_and(pred_mask, true_mask).sum()
    union = np.logical_or(pred_mask, true_mask).sum()
    return intersection / union if union > 0 else 1.0

def tta_predict(model, image_tensor):
    """Test Time Augmentation ile tahmin yapar."""
    model.eval()
    with torch.no_grad():
        # 1. Orijinal Görüntü
        original_output = torch.sigmoid(model(image_tensor.to(DEVICE)))

        # 2. Yatay Çevrilmiş Görüntü
        h_flipped_tensor = torch.flip(image_tensor, [3])
        h_flipped_output = torch.sigmoid(model(h_flipped_tensor.to(DEVICE)))
        h_flipped_output = torch.flip(h_flipped_output, [3]) # Geri çevir

        # 3. Dikey Çevrilmiş Görüntü
        v_flipped_tensor = torch.flip(image_tensor, [2])
        v_flipped_output = torch.sigmoid(model(v_flipped_tensor.to(DEVICE)))
        v_flipped_output = torch.flip(v_flipped_output, [2]) # Geri çevir
        
        # Tahminlerin ortalamasını al
        ensembled_output = (original_output + h_flipped_output + v_flipped_output) / 3.0
    return ensembled_output

def run_inference():
    model = UNet(n_channels=3, n_classes=1).to(DEVICE)
    if not os.path.exists(MODEL_PATH):
        print(f"Hata: {MODEL_PATH} bulunamadı.")
        return

    checkpoint = torch.load(MODEL_PATH, map_location=DEVICE)
    model.load_state_dict(checkpoint["model_state_dict"])
    
    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    os.makedirs("inference_results", exist_ok=True)
    iou_list = []
    test_images = [f for f in os.listdir("to-test") if f.endswith(('.png', '.jpg', '.jpeg'))]

    for img_name in test_images:
        img_path = os.path.join("to-test", img_name)
        img = Image.open(img_path).convert("RGB")
        input_tensor = transform(img).unsqueeze(0)
        
        # TTA ile tahmini al
        ensembled_output = tta_predict(model, input_tensor)
        
        mask_np = ensembled_output.squeeze().cpu().numpy()
        mask_binary = (mask_np > 0.5).astype(np.uint8)
        
        # Morphological operations
        kernel = np.ones((5,5),np.uint8)
        mask_closed = cv2.morphologyEx(mask_binary, cv2.MORPH_CLOSE, kernel)
        mask_opened = cv2.morphologyEx(mask_closed, cv2.MORPH_OPEN, kernel)

        # IoU Hesaplama
        label_path = os.path.join(LABEL_DIR, img_name)
        if os.path.exists(label_path):
            label_img = Image.open(label_path).convert("L").resize((256, 256))
            label_np = np.array(label_img)
            current_iou = calculate_iou(mask_opened, label_np)
            iou_list.append(current_iou)
            print(f"{img_name} için IoU (TTA + Morph): {current_iou:.4f}")

        # Sonucu kaydet
        file_base, file_ext = os.path.splitext(img_name)
        new_img_name = f"{file_base}_segmented{file_ext}"
        res_img = Image.fromarray(mask_opened * 255)
        res_img.save(os.path.join("inference_results", new_img_name))
        print(f"Tahmin kaydedildi: {new_img_name}")

    if iou_list:
        mean_iou = sum(iou_list) / len(iou_list)
        print("\n--- PROJE GENEL SONUCU (TTA + Morph ile) ---")
        print(f"Test edilen resim sayısı: {len(iou_list)}")
        print(f"Ortalama IoU (Mean IoU): {mean_iou:.4f}")

if __name__ == "__main__":
    run_inference()