# Aerial Semantic Segmentation: Custom U-Net & Hyperparameter Optimization

**Course:** MATH605 - Deep Learning Theory

**Instructor:** Gönenç ONAY

**Student:** Duygu ÇAKIR

## 📌 Project Overview

This project addresses the challenge of semantic segmentation in aerial imagery using a fully custom Convolutional Neural Network (CNN) based on the U-Net architecture. Unlike standard implementations that utilize pre-trained models, this project involves building the entire encoder-decoder pipeline from scratch to explore architectural influence on feature extraction and reconstruction.

---

## 🚀 Key Features

* **Custom CNN / U-Net Architecture:** Full control over filter depth, kernel sizes, and dropout placement.
* **Anti-Artifact Upsampling:** Replaced standard Transposed Convolutions with **Bilinear Upsampling + Conv2D** to eliminate checkerboard artifacts in final masks.
* **High-Performance Pipeline:** Uses `tf.data` with `prefetch(AUTOTUNE)` and GPU-integrated augmentation layers for 2x faster training.
* **Systematic Grid Search:** Exhaustive search across 6 dimensions (Learning Rate, Dropout, Gamma, Filters, Kernels, and Pooling).
* **Persistent Logging:** Automatic CSV logging with "Skip Logic" to allow search resumption after interruptions.

---

## 🛠 Technical Methodology

### 1. Data Augmentation (GPU-Native)

To prevent CPU-to-GPU bottlenecks, spatial augmentations are integrated as layers at the beginning of the model.

* **Transformations:** Random Flip, Rotation (), and Zoom.
* **Benefit:** Allows the entire batch to be augmented in parallel on the GPU.

### 2. Loss Function & Metrics

Due to the class imbalance typically found in aerial datasets, the model utilizes **Focal Loss**.

* **Focal Loss ():** Dynamically scales the cross-entropy loss, forcing the model to focus on "hard" pixels (edges/boundaries).
* **Metrics:** Dice Coefficient, Intersection over Union (IoU), Precision, and Recall.

---

## 🔮 Future Improvements

* **k-Fold Cross-Validation:** Essential for this project due to the small dataset size (). Implementing cross-validation will provide a statistically robust estimate of the model's generalization capability.
* **Attention Mechanisms:** Integrating Attention Gates to further refine boundary detection.
* **Bayesian Optimization:** Moving from discrete Grid Search to continuous search spaces using Optuna.

---

## 📂 Project Structure

```bash
├── Semantic_Segmentation_Aerial.ipynb  # Main Research Notebook
├── images/                             # Aerial images
├── labels/                             # Aerial labels
├── to_test/                            # Unseen images for inference
├── hyperparameter_search_results.csv   # Log of all grid search iterations

```

---

## ⚙️ How to Run

1. Ensure requirements.txt is installed.
2. Run the data preparation cells to load the aerial tiles.
3. The Grid Search cell will automatically skip previously tested combinations found in the CSV.
4. Run the **Testing & Visualization** cell to view the Original | Heatmap | Found table.


