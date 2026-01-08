import torch
from torchvision import transforms
from PIL import Image
import os
import numpy as np
from model import UNet

DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"
MODEL_PATH = "checkpoints/best_model.pth"
LABEL_DIR = "labels"  # Etiketlerin olduğu klasör

def calculate_iou(pred_mask, true_mask):
    """Intersection over Union (IoU) hesaplayan fonksiyon"""
    # Pred_mask zaten 0-1 arasında threshold uygulanmış geliyor
    # pred_mask = (pred_mask > 0.8).astype(np.uint8)
    # True_mask'ı (label) binary hale getiriyoruz
    true_mask = (true_mask > 127).astype(np.uint8) # Etiketler genellikle 0-255 arasındadır
        
    intersection = np.logical_and(pred_mask, true_mask).sum()
    union = np.logical_or(pred_mask, true_mask).sum()
        
    if union == 0:
        return 1.0
    return intersection / union


def run_inference():
    # Model sınıfını parametrelerle başlatıyoruz
    model = UNet(n_channels=3, n_classes=1).to(DEVICE)
    
    if not os.path.exists(MODEL_PATH):
        print("Hata: best_model.pth bulunamadı. Lütfen önce eğitimi tamamlayın.")
        return

    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.eval()

    # Eğitimdeki normalizasyonun aynısı
    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    os.makedirs("inference_results", exist_ok=True)
    iou_list = [] # Tüm skorları toplamak için

    for img_name in os.listdir("to-test"):
        if img_name.endswith((".png", ".jpg", ".jpeg")):
            img_path = os.path.join("to-test", img_name)
            img = Image.open(img_path).convert("RGB")
            input_tensor = transform(img).unsqueeze(0).to(DEVICE)
            
            with torch.no_grad():
                output = torch.sigmoid(model(input_tensor))
                # Hassasiyeti artırmak için eşiği 0.3'e çektik
                mask_np = output.squeeze().cpu().numpy()
                mask_binary = (mask_np > 0.5).astype(np.uint8)
            
            # --- IoU HESAPLAMA BÖLÜMÜ ---
            label_path = os.path.join(LABEL_DIR, img_name)
            if os.path.exists(label_path):
                label_img = Image.open(label_path).convert("L").resize((256, 256))
                label_np = np.array(label_img)
                
                current_iou = calculate_iou(mask_binary, label_np)
                iou_list.append(current_iou)
                print(f"{img_name} için IoU: {current_iou:.4f}")
            # ----------------------------


            # Dosya adını ve uzantısını ayırıyoruz (Örn: '551' ve '.png')
            file_base, file_ext = os.path.splitext(img_name)
            # Yeni dosya adını oluşturuyoruz: '551_segmented.png'
            new_img_name = f"{file_base}_segmented{file_ext}"
            
            res_img = Image.fromarray((mask_binary * 255).astype(np.uint8))
            output_path = os.path.join("inference_results", new_img_name)
            res_img.save(output_path)
            print(f"Tahmin kaydedildi: {new_img_name}")
        

    if iou_list:
        mean_iou = sum(iou_list) / len(iou_list)
        print(f"\nPROJE GENEL SONUCU")
        print(f"Test edilen resim sayısı: {len(iou_list)}")
        print(f"Ortalama IoU (Mean IoU): {mean_iou:.4f}")
    else:
        print("\nUyarı: Karşılaştırma yapılacak etiket (label) bulunamadı.")

if __name__ == "__main__":
    run_inference()

