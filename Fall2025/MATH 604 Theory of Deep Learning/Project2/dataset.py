import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms


from PIL import Image
import os
import numpy as np
import albumentations as A
from albumentations.pytorch import ToTensorV2


import os
import numpy as np
from PIL import Image
from torch.utils.data import Dataset
import albumentations as A
from albumentations.pytorch import ToTensorV2

import torch
from torch.utils.data import Dataset, DataLoader
import os
import numpy as np
from PIL import Image
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
            self.transform = A.Compose([
                # Geometrik Dönüşümler (Uydu verisi her yöne bakabilir)
                A.HorizontalFlip(p=0.5),
                A.VerticalFlip(p=0.5),
                A.RandomRotate90(p=0.5),
                A.ShiftScaleRotate(shift_limit=0.0625, scale_limit=0.1, rotate_limit=45, p=0.5),
                
                # Renk ve Işık Değişimleri (Farklı gün saatlerini simüle eder)
                A.RandomBrightnessContrast(p=0.3),
                A.HueSaturationValue(hue_shift_limit=20, sat_shift_limit=30, val_shift_limit=20, p=0.3),
                A.RGBShift(r_shift_limit=15, g_shift_limit=15, b_shift_limit=15, p=0.3),
                
                # Gürültü ve Netlik (Sensör hatalarını simüle eder)
                A.GaussNoise(p=0.2),
                A.OneOf([
                    A.MotionBlur(p=0.2),
                    A.MedianBlur(blur_limit=3, p=0.1),
                    A.Blur(blur_limit=3, p=0.1),
                ], p=0.2),
                
                *norm_transform
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
    # This block is for testing the dataset class.
    # It will only run when you execute this script directly.

    # Define transformations for images and masks separately
    image_transforms = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    mask_transforms = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor()
    ])

    # Create an instance of the dataset
    try:
        segmentation_dataset = SegmentationDataset(
            image_dir='images',
            mask_dir='labels',
            transform=image_transforms,
            target_transform=mask_transforms
        )

        # Create a DataLoader
        dataloader = DataLoader(segmentation_dataset, batch_size=4, shuffle=True, num_workers=0)

        # Iterate through the DataLoader to see a batch of data
        for images, masks in dataloader:
            print(f"Images batch shape: {images.shape}")
            print(f"Masks batch shape: {masks.shape}")
            # The mask should now have 1 channel and values between 0 and 1.
            print(f"Unique mask values in the first mask of the batch: {torch.unique(masks[0])}")
            break # We only inspect the first batch

    except FileNotFoundError:
        print("Please make sure the 'images' and 'labels' directories exist in your project folder.")
    except ValueError as e:
        print(e)
