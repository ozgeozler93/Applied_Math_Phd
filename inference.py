import torch
from torchvision import transforms
from PIL import Image
import os
import numpy as np
from model import UNet

DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"
MODEL_PATH = "checkpoints/best_model.pth"

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

    for img_name in os.listdir("to-test"):
        if img_name.endswith((".png", ".jpg", ".jpeg")):
            img_path = os.path.join("to-test", img_name)
            img = Image.open(img_path).convert("RGB")
            input_tensor = transform(img).unsqueeze(0).to(DEVICE)
            
            with torch.no_grad():
                output = torch.sigmoid(model(input_tensor))
                # Hassasiyeti artırmak için eşiği 0.3'e çektik
                mask = (output > 0.8).float().squeeze().cpu().numpy()
            
            # Dosya adını ve uzantısını ayırıyoruz (Örn: '551' ve '.png')
            file_base, file_ext = os.path.splitext(img_name)
            # Yeni dosya adını oluşturuyoruz: '551_segmented.png'
            new_img_name = f"{file_base}_segmented{file_ext}"
            
            res_img = Image.fromarray((mask * 255).astype(np.uint8))
            output_path = os.path.join("inference_results", new_img_name)
            res_img.save(output_path)
            print(f"Tahmin kaydedildi: {new_img_name}")

if __name__ == "__main__":
    run_inference()