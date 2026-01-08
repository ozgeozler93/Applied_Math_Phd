import torch
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
import os
import numpy as np
from model import AttentionUNet
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
    """Test Time Augmentation with flips and multi-scale."""
    model.eval()
    
    original_size = image_tensor.shape[-2:]
    predictions = []

    with torch.no_grad():
        # Define augmentations (original, horizontal flip, vertical flip)
        tensors = [
            image_tensor,
            torch.flip(image_tensor, [3]),
            torch.flip(image_tensor, [2])
        ]

        # Define how to reverse the augmentation for the output mask
        revert_ops = [
            lambda x: x,
            lambda x: torch.flip(x, [3]),
            lambda x: torch.flip(x, [2])
        ]

        scales = [0.8, 1.0, 1.2]

        for i, tensor in enumerate(tensors):
            for scale in scales:
                new_size = (int(original_size[0] * scale), int(original_size[1] * scale))
                
                # Scale, predict, and scale back
                scaled_tensor = F.interpolate(tensor, size=new_size, mode='bilinear', align_corners=False)
                output = torch.sigmoid(model(scaled_tensor.to(DEVICE)))
                output = F.interpolate(output, size=original_size, mode='bilinear', align_corners=False)
                
                # Revert augmentation and add to list
                predictions.append(revert_ops[i](output))

        # Average all predictions
        ensembled_output = torch.mean(torch.stack(predictions), dim=0)
        
    return ensembled_output

def run_inference():
    model = AttentionUNet(in_channels=3, n_classes=1).to(DEVICE)
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