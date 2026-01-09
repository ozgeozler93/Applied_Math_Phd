import torch
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import os
import numpy as np
import albumentations as A
from albumentations.pytorch import ToTensorV2

class SegmentationDataset(Dataset):
    def __init__(self, image_dir, mask_dir, height, width, is_train=True):
        self.image_dir = image_dir
        self.mask_dir = mask_dir
        # Gizli dosyaları (örn: .DS_Store) elemek için filtreleme
        self.image_filenames = sorted([f for f in os.listdir(image_dir) if f.endswith(('.png', '.jpg', '.jpeg'))])
        
        # Standart Normalizasyon
        norm_transform = [
            A.Resize(height, width),
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ToTensorV2(),
        ]
        
        if is_train:
            # Gelişmiş Augmentation Pipeline
        # Gelişmiş Augmentation Pipeline
            self.transform = A.Compose([
                A.Resize(height, width),
                A.HorizontalFlip(p=0.5),
                A.VerticalFlip(p=0.5),
                A.RandomRotate90(p=0.5),
                A.CLAHE(clip_limit=4.0, p=0.7), # Kontrast artırıldı
                A.ColorJitter(brightness=0.2, contrast=0.2, p=0.4),
                A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
                ToTensorV2(),
            ])
        else:
            self.transform = A.Compose(norm_transform)

    def __len__(self):
        return len(self.image_filenames)

    def __getitem__(self, idx):
        img_name = self.image_filenames[idx]
        img_path = os.path.join(self.image_dir, img_name)
        mask_path = os.path.join(self.mask_dir, img_name)
        
        image = np.array(Image.open(img_path).convert("RGB"))
        mask = np.array(Image.open(mask_path).convert("L"), dtype=np.float32)
        
        # Maskeyi 0-1 aralığına normalize et
        mask = mask / 255.0 if mask.max() > 1.0 else mask

        augmented = self.transform(image=image, mask=mask)
        return augmented["image"], augmented["mask"]

if __name__ == '__main__':
    # Bu blok, dataset sınıfını test etmek içindir.
    # Yalnızca bu betiği doğrudan çalıştırdığınızda çalışır.
    
    IMAGE_HEIGHT = 512
    IMAGE_WIDTH = 512
    
    print("Dataset sınıfı test ediliyor...")
    
    try:
        # Eğitim veri seti için (augmentation ile)
        train_dataset = SegmentationDataset(
            image_dir='images',
            mask_dir='labels',
            height=IMAGE_HEIGHT,
            width=IMAGE_WIDTH,
            is_train=True
        )
        
        # Test veri seti için (augmentation olmadan)
        test_dataset = SegmentationDataset(
            image_dir='images',
            mask_dir='labels',
            height=IMAGE_HEIGHT,
            width=IMAGE_WIDTH,
            is_train=False
        )

        print(f"Toplam {len(train_dataset)} adet eğitim verisi bulundu.")
        
        # DataLoader oluştur
        train_loader = DataLoader(train_dataset, batch_size=4, shuffle=True)
        
        # DataLoader'dan bir batch veri alıp kontrol et
        images, masks = next(iter(train_loader))
        
        print(f"Images batch shape: {images.shape}") # Beklenen: [batch_size, 3, height, width]
        print(f"Masks batch shape: {masks.shape}")   # Beklenen: [batch_size, height, width]
        
        # Maske değerlerinin 0 ile 1 arasında olduğunu kontrol et
        print(f"İlk maskenin içindeki benzersiz değerler: {torch.unique(masks[0])}")
        print("Dataset testi başarılı!")

    except FileNotFoundError:
        print("HATA: 'images' ve 'labels' klasörlerinin proje dizininde olduğundan emin olun.")
    except Exception as e:
        print(f"Bir hata oluştu: {e}")