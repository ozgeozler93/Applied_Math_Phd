# Project Report: Image Segmentation with U-Net

**Course:** Math 604 - Theory of Deep Learning  
**Author:** Gemini CLI

---

## Abstract

This report details a project on image segmentation using the U-Net architecture, implemented in PyTorch. The primary objective is to develop and train a model capable of accurately segmenting images by generating corresponding masks. The report covers the project's introduction, setup, dataset, model architecture, training, and inference processes. It also discusses the results and potential future improvements.

---

## 1. Introduction

Image segmentation is a fundamental task in computer vision that involves partitioning an image into multiple segments or regions. The goal is to assign a label to every pixel in an image such that pixels with the same label share certain characteristics. This process is crucial for various applications, including medical imaging, autonomous driving, and satellite imagery analysis.

The U-Net architecture, first proposed for biomedical image segmentation, has become a standard for segmentation tasks. Its design features a contracting path (encoder) to capture context and a symmetric expanding path (decoder) for precise localization. Skip connections between the encoder and decoder paths are a key feature, allowing the network to combine deep, semantic information with shallow, high-resolution features.

This project implements a U-Net model from scratch using PyTorch and demonstrates its effectiveness on a custom dataset.

---

## 2. Project Setup & Dependencies

The project is developed in Python and relies on several open-source libraries.

### 2.1. Dependencies

The required dependencies are listed in the `requirements.txt` file and include:

- `torch`: The core deep learning framework.
- `torchvision`: Provides access to popular datasets, model architectures, and image transformations for computer vision.
- `opencv-python-headless`: Used for image processing tasks.
- `scikit-learn`: A machine learning library for various tasks.
- `matplotlib`: For data visualization.
- `numpy`: For numerical operations.
- `tqdm`: For creating progress bars.

### 2.2. Installation

To set up the project environment, clone the repository and install the dependencies using pip:

```bash
pip install -r requirements.txt
```

---

## 3. Dataset

The model is trained on a custom dataset consisting of images and their corresponding segmentation masks.

- **Images:** The input images are located in the `images/` directory.
- **Labels:** The ground truth segmentation masks are in the `labels/` directory.

The `dataset.py` script contains a custom `SegmentationDataset` class that handles loading and preprocessing of the data. This includes resizing images and masks to a uniform size and applying necessary transformations.

---

## 4. Model Architecture

The U-Net model is implemented in `model.py`. The architecture consists of:

- **Encoder (Contracting Path):** This path follows a typical convolutional network structure. It consists of the repeated application of two 3x3 convolutions, each followed by a Rectified Linear Unit (ReLU) and a 2x2 max pooling operation with stride 2 for downsampling. At each downsampling step, we double the number of feature channels.

- **Decoder (Expanding Path):** In the expanding path, each step consists of an upsampling of the feature map followed by a 2x2 convolution (“up-convolution”) that halves the number of feature channels, a concatenation with the correspondingly cropped feature map from the contracting path, and two 3x3 convolutions, each followed by a ReLU.

- **Skip Connections:** These connections concatenate feature maps from the encoder with the corresponding feature maps in the decoder. This is crucial for recovering fine-grained details lost during downsampling.

- **Output Layer:** A final 1x1 convolution maps the feature vector to the desired number of classes. In this project, for binary segmentation, the number of output classes is 1.

---

## 5. Training

The training process is managed by the `train.py` script.

### 5.1. Training Configuration

The following hyperparameters and settings can be configured in `train.py`:

- `DEVICE`: The device for training (`cuda`, `mps`, or `cpu`).
- `LEARNING_RATE`: The learning rate for the Adam optimizer (default: `1e-4`).
- `BATCH_SIZE`: The number of samples per batch (default: `4`).
- `NUM_EPOCHS`: The total number of training epochs (default: `25`).
- `IMAGE_HEIGHT`, `IMAGE_WIDTH`: The dimensions to which input images and masks are resized (default: `256x256`).
- `VAL_PERCENT`: The fraction of the dataset to be used for validation (default: `10%`).

### 5.2. Training Process

The training loop iterates over the dataset for the specified number of epochs. For each batch, the model performs a forward pass, calculates the loss, and updates the weights through backpropagation.

- **Loss Function:** `BCEWithLogitsLoss` is used, which combines a Sigmoid layer and the Binary Cross Entropy loss in one single class. This is suitable for binary segmentation tasks.
- **Optimizer:** The `Adam` optimizer is used for its efficiency and adaptive learning rate capabilities.
- **Mixed Precision Training:** The script supports mixed-precision training on CUDA-enabled GPUs, which can accelerate training and reduce memory consumption.

Model checkpoints are saved to the `checkpoints/` directory after each epoch.

---

## 6. Inference

The `inference.py` script is used to perform segmentation on new images using a trained model.

### 6.1. Inference Configuration

- `DEVICE`: The device for inference.
- `CHECKPOINT_PATH`: The path to the saved model checkpoint.
- `TEST_IMAGE_DIR`: The directory with images for segmentation (default: `to-test/`).
- `OUTPUT_DIR`: The directory where the generated masks will be saved.

### 6.2. Inference Process

The script loads the trained model from the specified checkpoint, preprocesses the input images from the `to-test/` directory, and generates segmentation masks. The output masks are saved in the `inference_results/` directory.

---

## 7. Results & Discussion

The model's performance can be evaluated by visually inspecting the generated masks and comparing them to the ground truth. For a quantitative analysis, metrics such as the Dice coefficient or Intersection over Union (IoU) could be implemented in the validation step.

The quality of the segmentation depends on several factors, including the model's capacity, the size and diversity of the training dataset, and the choice of hyperparameters.

Potential improvements for this project include:
- Implementing a validation loop to monitor performance on a hold-out set and prevent overfitting.
- Experimenting with different loss functions, such as the Dice loss, which is often used for segmentation tasks.
- Applying data augmentation techniques to increase the diversity of the training data and improve model generalization.

---

## 8. Conclusion

This project successfully implements a U-Net model for image segmentation. The provided scripts for training and inference demonstrate a complete pipeline from data loading to model deployment. The modular code structure allows for easy extension and experimentation with different datasets and model architectures. The project serves as a solid foundation for further exploration in the field of computer vision and image segmentation.

---

## 9. Code Structure

- `dataset.py`: Contains the `SegmentationDataset` class for loading and preprocessing data.
- `model.py`: Defines the U-Net architecture.
- `train.py`: The main script for training the model.
- `inference.py`: The script for running inference on new images.
- `requirements.txt`: Lists the project dependencies.
- `Readme.md`: The original project README file.
- `readmeReport.md`: This report.
- `images/`: Directory for input images.
- `labels/`: Directory for ground truth masks.
- `to-test/`: Directory for images to be segmented during inference.
- `checkpoints/`: Directory where model checkpoints are saved.