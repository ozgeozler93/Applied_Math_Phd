# Attention U-Net for Building Segmentation in Satellite Imagery

This project was developed for **MATH 604: Theory of Deep Learning (Fall 2025)** as part of my Applied Mathematics PhD studies. The goal is the semantic segmentation of buildings from high-resolution satellite imagery using an **Attention U-Net** architecture.



##  Theoretical Background & Methodology

To address the challenges of small object detection and background noise in satellite data, the following strategies were implemented:

### 1. Model Architecture: Attention U-Net
Standard U-Nets use skip connections that can carry redundant low-level feature information. I integrated **Attention Gates (AGs)** into the skip connections. AGs automatically learn to focus on target structures (buildings) without additional supervision, effectively suppressing irrelevant regions.

### 2. Loss Function Optimization
A hybrid loss function was designed to balance pixel-wise accuracy with structural integrity:

* **Focal Loss:** Handles the extreme class imbalance by down-weighting easy-to-classify background pixels.
* **Dice Loss:** Directly optimizes the **Intersection over Union (IoU)**, ensuring that the predicted building shapes are geometrically precise.

This combination ensures the model learns both the distribution of pixels and the geometric structure of buildings:

$$
\mathcal{L}_{Hybrid} = \underbrace{0.3 \cdot \mathcal{L}_{Focal}}_{\text{Pixel-wise Imbalance}} + \underbrace{0.7 \cdot \mathcal{L}_{Dice}}_{\text{Structural Integrity}}
$$

**Why 0.7 Dice?** Satellite imagery contains sparse building masks. By weighting the **Dice Loss** at 70%, the optimization process prioritizes the **overlap area** over individual pixel accuracy, leading to the sharp, non-blurry boundaries observed in the results.

### 3. Training & Generalization
* **Honest Evaluation:** The dataset was strictly partitioned. The `to-test` directory contains images that the model **never saw** during training, ensuring a true measure of generalization.
* **Advanced Augmentation:** Used `Albumentations` for CLAHE (contrast enhancement), GridDistortion, and ShiftScaleRotate to simulate diverse lighting conditions.



### 4. Attention Gate Mechanism

If a standard U-Net is like looking at a satellite map in the dark, the **Attention Gate (AG)** is like having a smart flashlight that only shines on the buildings.

### a. What is an Attention Gate? 
In satellite images, there is a lot of "noise": trees, roads, shadows, and fields. A regular model tries to look at everything at once. The **Attention Gate** acts as a filter. It takes the high-level summary from the deeper layers and says: *"Hey, focus on this area; it looks like a building, and ignore that forest over there."*

### b. How it Works 
The gate takes two inputs:
1.  **Skip Connection ($x$):** Detailed information (edges, colors).
2.  **Gating Signal ($g$):** Contextual information (where the objects are).

The gate multiplies these. If the context ($g$) says an area is irrelevant, the gate "multiplies by zero," effectively silencing that part of the image. If it's a building, it "multiplies by one," letting the detail pass through.


### c. The Mathematics
The attention coefficient ($\alpha$) is calculated as follows:

$$\alpha = \sigma( \psi^T ( \text{ReLU}( W_x x + W_g g + b ) ) )$$

* **$W_x$ and $W_g$:** The model learns which features are important.
* **ReLU & $\sigma$ (Sigmoid):** These act as on/off switches. Sigmoid ensures the result is between 0 and 1 (0% attention to 100% attention).
* **Final Step ($x_{out} = x \cdot \alpha$):** We multiply the original detail by the attention score. Only the "useful" parts survive.


! Without Attention Gates, the model often confuses rooftops with bright roads or concrete pavements. By using AGs, we significantly reduced **False Positives**, leading to the cleaner masks seen in our Performance Analysis.


## Performance Metrics: IoU and Dice Coefficient

In semantic segmentation, evaluating pixel-wise accuracy is insufficient due to class imbalance. Therefore, we utilize the **Intersection over Union (IoU)**, also known as the **Jaccard Index**, as our primary evaluation metric.



### 1. Intersection over Union (IoU)
IoU measures the overlap between the predicted segmentation mask ($A$) and the ground truth mask ($B$):

$$IoU(A, B) = \frac{|A \cap B|}{|A \cup B|} = \frac{TP}{TP + FP + FN}$$

Where:
* **TP (True Positive):** Correctly identified building pixels.
* **FP (False Positive):** Background pixels incorrectly identified as buildings.
* **FN (False Negative):** Building pixels missed by the model.

### 2. Dice Coefficient (F1-Score)
While IoU is used for evaluation, the **Dice Coefficient** is utilized within our loss function because it is differentiable and provides smoother gradients during backpropagation:

$$Dice(A, B) = \frac{2|A \cap B|}{|A| + |B|} = \frac{2TP}{2TP + FP + FN}$$

In this project, optimizing for **0.7 Dice Loss** forced the model to maximize this overlap, directly leading to the sharper boundaries observed in the `to-test` results.




## 🔍 Model Performance Analysis

This section analyzes the qualitative and quantitative performance of the model on the independent `to-test` set.

### 1. Visual Comparative Analysis (Before vs. After Optimization)

By shifting to a **Dice-dominant Hybrid Loss** and implementing **Test Time Augmentation (TTA)**, we observed a significant reduction in segmentation noise and an increase in boundary sharpness.

| Sample ID | Original Image | Predicted Mask | Success Metrics | Analysis |
| :--- | :---: | :---: | :---: | :--- |
| **Img 535** | <img src="to-test/535.png" width="200"> | <img src="inference_results/pred_535.png" width="200"> | **IoU:** ~0.65<br>**Dice:** ~0.78 | **Success:** Robust performance in high-density urban layouts. Effectively distinguished separate building blocks despite their close proximity. |
| **Img 537** | <img src="to-test/537.png" width="200"> | <img src="inference_results/pred_537.png" width="200"> | **IoU:** ~0.72<br>**Dice:** ~0.84 | **Success:** Clear separation between adjacent buildings. Attention gates successfully ignored the surrounding vegetation. |
| **Img 539** | <img src="to-test/539.png" width="200"> | <img src="inference_results/pred_539.png" width="200"> | **IoU:** ~0.60<br>**Dice:** ~0.75 | **Success:** Solid object detection. Geometric consistency improved significantly with Dice-heavy training. |
| **Img 551** | <img src="to-test/551.png" width="200"> | <img src="inference_results/pred_551.png" width="200"> | **IoU:** ~0.70<br>**Dice:** ~0.82 | **Success:** Sharp rectangular boundaries. The model effectively identified building footprints despite shadows. |
| **Img 553** | <img src="to-test/553.png" width="200"> | <img src="inference_results/pred_553.png" width="200"> | **IoU:** ~0.55<br>**Dice:** ~0.71 | **Success:** Demonstrated strong generalization on low-contrast targets and dark-roofed structures obscured by shadows. |




### 2. Error Analysis & Edge Cases
While the model generalizes well, certain challenges remain:
* **Shadow Interference:** Tall building shadows are occasionally segmented as structures.
* **Spectral Similarity:** Concrete surfaces with similar spectral signatures to rooftops can trigger false positives, mitigated by the 0.7 Dice Loss weight.



## Project Structure
* `model.py`: Attention U-Net implementation with Gating mechanisms.
* `dataset.py`: Data pipeline featuring CLAHE and spatial augmentations.
* `train.py`: Training script with Linear Warmup and Cosine Annealing.
* `inference.py`: Evaluation script featuring **Test Time Augmentation (TTA)**.

---

## How to Run
1. Clone the repository: 
   ```bash
   git clone [https://github.com/ozgeozler93/Applied_Math_Phd.git](https://github.com/ozgeozler93/Applied_Math_Phd.git)
   ```

2. Install dependencies:
   ```bash
   !pip install torch albumentations opencv-python Pillow
   ```
   
3. Run inference on test data:
   ```bash
   python inference.py
   ```
