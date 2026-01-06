# Image Segmentation with U-Net

This project implements a U-Net model for image segmentation using PyTorch. The model is trained to segment images and produce corresponding masks.

## Introduction

Image segmentation is the process of partitioning a digital image into multiple segments (sets of pixels, also known as super-pixels). The goal of segmentation is to simplify and/or change the representation of an image into something that is more meaningful and easier to analyze. In this project, we use the U-Net architecture, a popular convolutional neural network for biomedical image segmentation, to perform this task.

## Features

*   **U-Net Model:** A robust and widely-used architecture for image segmentation.
*   **PyTorch Implementation:** The model is built using the popular PyTorch deep learning framework.
*   **Custom Dataset Class:** A flexible dataset class for loading images and masks.
*   **Training and Inference Scripts:** Separate scripts for training the model and running inference on new images.
*   **Mixed Precision Training:** The training script supports mixed-precision training for faster training on compatible GPUs.

## Dependencies

The project requires the following dependencies:

*   `torch`
*   `torchvision`
*   `opencv-python-headless`
*   `scikit-learn`
*   `matplotlib`
*   `numpy`
*   `tqdm`

You can install the dependencies using pip:

```bash
pip install -r requirements.txt
```

## Dataset

The model is trained on a custom dataset of images and their corresponding segmentation masks. The dataset should be organized into two directories: `images` and `labels`, containing the input images and segmentation masks, respectively.

## Model Architecture

The U-Net architecture consists of a contracting path (encoder) to capture context and a symmetric expanding path (decoder) that enables precise localization. The encoder is a stack of convolutional and max-pooling layers, while the decoder is a stack of up-convolutional and convolutional layers. Skip connections are used to connect the encoder and decoder paths, which helps to preserve high-resolution information.

## Training

To train the model, run the `train.py` script:

```bash
python train.py
```

The training script will train the model for a specified number of epochs and save the model checkpoints in the `checkpoints` directory.

### Training Configuration

The training configuration can be modified in the `train.py` script:

*   `DEVICE`: The device to use for training (e.g., "cuda", "mps", "cpu").
*   `LEARNING_RATE`: The learning rate for the optimizer.
*   `BATCH_SIZE`: The batch size for training.
*   `NUM_EPOCHS`: The number of epochs to train the model.
*   `IMAGE_HEIGHT`: The height of the input images.
*   `IMAGE_WIDTH`: The width of the input images.
*   `VAL_PERCENT`: The percentage of the dataset to use for validation.
*   `CHECKPOINT_DIR`: The directory to save the model checkpoints.

## Inference

To run inference on new images, run the `inference.py` script:

```bash
python inference.py
```

The inference script will load a trained model from a checkpoint and generate segmentation masks for the images in the `to-test` directory. The generated masks will be saved in the `inference_results` directory.

### Inference Configuration

The inference configuration can be modified in the `inference.py` script:

*   `DEVICE`: The device to use for inference (e.g., "cuda", "mps", "cpu").
*   `CHECKPOINT_PATH`: The path to the trained model checkpoint.
*   `TEST_IMAGE_DIR`: The directory containing the images to run inference on.
*   `OUTPUT_DIR`: The directory to save the generated masks.
*   `IMAGE_HEIGHT`: The height of the input images.
*   `IMAGE_WIDTH`: The width of the input images.