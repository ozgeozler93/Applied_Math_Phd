import torch
from torch.utils.data import Dataset
from PIL import Image
import os
import numpy as np
import albumentations as A
from albumentations.pytorch import ToTensorV2

def get_validation_transform(height, width):
    """Returns the validation/inference transformation pipeline."""
    return A.Compose([
        A.Resize(height, width),
        A.CLAHE(clip_limit=4.0, p=1.0), 
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ToTensorV2(),
    ])

class SegmentationDataset(Dataset):
    def __init__(self, image_dir, mask_dir, height, width, is_train=True):
        self.image_dir = image_dir
        self.mask_dir = mask_dir
        self.image_filenames = sorted([f for f in os.listdir(image_dir) if f.endswith(('.png', '.jpg', '.jpeg'))])
        
        if is_train:
            self.transform = A.Compose([
                A.Resize(height, width),
                A.HorizontalFlip(p=0.5),
                A.VerticalFlip(p=0.5),
                A.RandomRotate90(p=0.5),
                A.ShiftScaleRotate(shift_limit=0.0625, scale_limit=0.1, rotate_limit=45, p=0.5),
                A.OneOf([
                    A.GridDistortion(p=0.5),
                    A.OpticalDistortion(distort_limit=0.05, shift_limit=0.05, p=0.5),
                ], p=0.3),
                A.CLAHE(clip_limit=4.0, p=1.0), 
                A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
                A.HueSaturationValue(p=0.3),
                A.CoarseDropout(max_holes=8, max_height=0.1, max_width=0.1, fill_value=0, p=0.5),
                A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
                ToTensorV2(),
            ])
        else:
            self.transform = get_validation_transform(height, width)

    def __len__(self):
        return len(self.image_filenames)

    def __getitem__(self, idx):
        img_name = self.image_filenames[idx]
        image = np.array(Image.open(os.path.join(self.image_dir, img_name)).convert("RGB"))
        mask = np.array(Image.open(os.path.join(self.mask_dir, img_name)).convert("L"), dtype=np.float32)
        mask = mask / 255.0 if mask.max() > 1.0 else mask
        augmented = self.transform(image=image, mask=mask)
        return augmented["image"], augmented["mask"]