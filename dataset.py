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

class SegmentationDataset(Dataset):
    def __init__(self, image_dir, mask_dir, height, width, is_train=True):
        self.image_dir = image_dir
        self.mask_dir = mask_dir
        self.image_filenames = sorted(os.listdir(image_dir))
        
        # ImageNet standartlarında normalizasyon
        norm_transform = [
            A.Resize(height, width),
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ToTensorV2(),
        ]
        
        if is_train:
            self.transform = A.Compose([
                A.HorizontalFlip(p=0.5),
                A.VerticalFlip(p=0.5),
                A.RandomRotate90(p=0.5),
                *norm_transform
            ])
        else:
            self.transform = A.Compose(norm_transform)

    def __len__(self):
        return len(self.image_filenames)

    def __getitem__(self, idx):
        img_path = os.path.join(self.image_dir, self.image_filenames[idx])
        mask_path = os.path.join(self.mask_dir, self.image_filenames[idx])
        
        image = np.array(Image.open(img_path).convert("RGB"))
        mask = np.array(Image.open(mask_path).convert("L"), dtype=np.float32)
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
