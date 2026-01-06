# 2D Konvülüsyon Implementasyonu: NumPy vs PyTorch

## 📌 Proje Özeti

Bu proje **2D konvülüsyon (2D Convolution)** işlemini NumPy ile adım adım implementasyon ederek PyTorch sonuçları ile karşılaştırır. Convolutional Neural Networks (CNN) öğreniminin temelini anlamak amacıyla hazırlanmıştır.

### Amaç
- Konvülüsyon operasyonunun matematiksel ve pratik olarak nasıl çalıştığını anlamak
- Padding, stride, kanal ve batch kavramlarını derinlemesine öğrenmek
- PyTorch gibi optimize edilmiş kütüphanelerin altında neler olduğunu görmek

---

## 🎯 Temel Kavramlar

### 1. **Konvülüsyon (Convolution)**
Bir **filtre (kernel)** adı verilen küçük matrisin bir görüntü üzerinde kayan pencere şeklinde uygulanması ve her pozisyonda çarp-toplama işlemi yapılmasıdır.

```
Görüntü (4×6) + Filtre (3×3) → Konvülüsyon → Çıkış Haritası (4×6)
```

**İşlem:**
1. Filtreyi sol üst köşeye yerleştir
2. Filtre altındaki 9 piksel × filtre ağırlıkları = 1 çıkış değeri
3. Filtreyi kaydır ve tekrarla

---

### 2. **Padding (Dolgu)**

Görüntünün etrafına sıfır eklemek.

```
Orijinal (4×6) + padding=1 → Padded (6×8)

[a b c d e f]        [0 0 0 0 0 0 0 0]
[g h i j k l]   →    [0 a b c d e f 0]
[m n o p q r]        [0 g h i j k l 0]
[s t u v w x]        [0 m n o p q r 0]
                     [0 s t u v w x 0]
                     [0 0 0 0 0 0 0 0]
```

**Neden?**
- Köşe ve kenar piksellerini daha iyi işlemek
- Çıkış boyutunu kontrol etmek
- Bilgi kaybını azaltmak

---

### 3. **Stride (Adım Sayısı)**

Filtrenin kaç piksel ilerleyeceğini belirler.

| Stride | Özellik | Çıkış Boyutu |
|--------|---------|-------------|
| stride=1 | Her piksele uygula | Orijinal boyut (padding ile) |
| stride=2 | Her 2. piksele uygula | ≈ Orijinalin yarısı |
| stride=3 | Her 3. piksele uygula | ≈ Orijinalin üçte biri |

**Örnek:**
```
Input (12×10), padding=1, kernel=3, stride=2
Output height = floor((12 + 2×1 - 3) / 2 + 1) = 6
Output width = floor((10 + 2×1 - 3) / 2 + 1) = 5
→ Output: (6×5)
```

---

### 4. **Channel (Kanal)**

Görüntünün kaç tane 2D katmanı olduğu.

```
RGB Resim:          Gri Resim:          İşlenmiş:
┌────────┐          ┌────────┐          ┌────────┐
│ RED    │ ←Kanal1  │ GRAY   │ ←Kanal1 │Feature1│ ←Kanal1
├────────┤          └────────┘          ├────────┤
│ GREEN  │ ←Kanal2                      │Feature2│ ←Kanal2
├────────┤                              └────────┘
│ BLUE   │ ←Kanal3                     2 output kanal
└────────┘                            (2 filtre kullanıldığı için)
3 input kanal
```

**Input Kanal:** Giriş görüntünün katman sayısı
- RGB görüntü: 3 kanal
- Gri görüntü: 1 kanal
- Önceki konvülüsyon çıkışı: İstediğiniz kadar kanal

**Output Kanal:** Kullanılan filtre sayısı
- 16 farklı filtre kullanırsan: 16 output kanal

---

### 5. **Batch Size (Toplu İşlem)**

Aynı anda kaç görüntü işleyelim.

```
Batch=1:   1 görüntü işle
           Hızlı ama tek resim

Batch=32:  32 görüntü aynı anda işle
           Paralellik (GPU'da çok hızlı!)
           Bilgisayar kaynakları daha iyi kullanılır
```

**Pratik:** GPU'da batch=1 ile batch=32 neredeyse aynı hız!

---

### 6. **Filtre/Kernel**

Görüntüdeki desenleri (kenarlar, dokular, renkler) algılayan ağırlık matrisi.

```
3×3 Filtre örneği:
[0.123  -0.456   0.789]
[0.234   0.567  -0.890]
[-0.123  0.456   0.789]

Kullanım: Her input kanalı için ayrı filtre
Input: 5 kanal, Output: 2 kanal
→ 2 filtre × 5 = 10 tane 3×3 matris
```

---

## 📊 Veri Şekilleri (Tensor Dimensions)

### Giriş Görüntüsü
```
Shape: (batch_size, channels_in, height, width)

Örneğin:
(1, 1, 4, 6)  → 1 görüntü, 1 kanal, 4 satır, 6 sütun
(2, 3, 224, 224) → 2 görüntü, 3 kanal (RGB), 224×224 piksel
(32, 64, 28, 28) → 32 görüntü, 64 kanal, 28×28 piksel
```

### Filtre Ağırlıkları
```
Shape: (channels_out, channels_in, kernel_height, kernel_width)

Örneğin:
(1, 1, 3, 3)  → 1 output, 1 input, 3×3 filtre
(32, 3, 5, 5) → 32 output, 3 input (RGB), 5×5 filtre
(64, 32, 3, 3) → 64 output, 32 input, 3×3 filtre
```

### Çıkış Haritası
```
Shape: (batch_size, channels_out, height_out, width_out)

Örneğin:
(1, 1, 4, 6)  → 1 görüntü, 1 kanal, 4×6
(2, 32, 28, 28) → 2 görüntü, 32 kanal, 28×28
```

---

## 🔍 10.3 Kodunun Yapısı

```
10 Hücre (Cell) ile ilerleyen yapı:

HÜCRE 1-2: HAZIRLIK
    └─ Kurulum ve PyTorch referansı

AŞAMA 1: TEMEL (stride=1, tek kanal)
    ├─ HÜCRE 3: conv_numpy_1() implementasyonu (4 döngü)
    └─ HÜCRE 4: Test ve karşılaştırma

AŞAMA 2: STRIDE ÖZELLİĞİ
    ├─ HÜCRE 5: conv_numpy_2() - stride desteği (4 döngü)
    └─ HÜCRE 6: Test ve karşılaştırma (stride=2)

AŞAMA 3: ÇOKLU KANAL
    ├─ HÜCRE 7: conv_numpy_3() - kanal döngüleri (6 döngü)
    └─ HÜCRE 8: Test ve karşılaştırma (5 kanal → 2 kanal)

AŞAMA 4: BATCH İŞLEME
    ├─ HÜCRE 9: conv_numpy_4() - batch desteği (7 döngü)
    └─ HÜCRE 10: Test ve karşılaştırma (2 görüntü)
```

---

## 📈 Gelişim Süreci

### Hücre 3 → Hücre 5: Stride Ekleme
```python
# Hücre 3 (stride=1):
this_pixel_value = image[0, 0, c_y + c_kernel_y, c_x + c_kernel_x]

# Hücre 5 (stride değişken):
this_pixel_value = image[0, 0, c_y * stride + c_kernel_y, c_x * stride + c_kernel_x]
                                 ↑ Değişiklik!
```

### Hücre 5 → Hücre 7: Kanal Ekleme
```python
# Hücre 5 (4 döngü):
for c_y:
  for c_x:
    for c_kernel_y:
      for c_kernel_x:
        # İşlem...

# Hücre 7 (6 döngü):
for c_y:
  for c_x:
    for c_channel_out:           # ← Yeni
      for c_channel_in:          # ← Yeni
        for c_kernel_y:
          for c_kernel_x:
            # İşlem...
```

### Hücre 7 → Hücre 9: Batch Ekleme
```python
# Hücre 7 (6 döngü):
for c_y:
  for c_x:
    for c_channel_out:
      for c_channel_in:
        for c_kernel_y:
          for c_kernel_x:
            # İşlem...

# Hücre 9 (7 döngü):
for c_batch:                     # ← Yeni
  for c_y:
    for c_x:
      for c_channel_out:
        for c_channel_in:
          for c_kernel_y:
            for c_kernel_x:
              # İşlem...
```

---

## 🧮 Konvülüsyon Matematik Formülü

```
output[b, c_out, y, x] = Σ Σ Σ Σ input[b, c_in, y*s+ky, x*s+kx] × weight[c_out, c_in, ky, kx]
                         c_in ky kx

Açıklama:
- b: Batch indeksi
- c_out: Output kanal indeksi
- y, x: Çıkış pozisyonu
- s: Stride
- ky, kx: Filtre koordinatları
- c_in: Input kanal indeksi

Özet: Tüm input kanallarının çarpımlarını topla!
```

---

## 📋 Test Senaryoları

| Hücre | İsim | Input Shape | Filtre | Stride | Output Shape |
|-------|------|------------|--------|--------|--------------|
| 4 | Basit | (1, 1, 4, 6) | (1, 1, 3, 3) | 1 | (1, 1, 4, 6) |
| 6 | Stride | (1, 1, 12, 10) | (1, 1, 3, 3) | 2 | (1, 1, 6, 5) |
| 8 | Kanal | (1, 5, 4, 6) | (2, 5, 3, 3) | 1 | (1, 2, 4, 6) |
| 10 | Batch | (2, 5, 4, 6) | (2, 5, 3, 3) | 1 | (2, 2, 4, 6) |

---

## 🔄 PyTorch vs NumPy

### PyTorch (Hücre 2)
```python
def conv_pytorch(image, conv_weights, stride=1, pad=1):
    image_tensor = torch.from_numpy(image)
    conv_weights_tensor = torch.from_numpy(conv_weights)
    output_tensor = torch.nn.functional.conv2d(
        image_tensor, 
        conv_weights_tensor, 
        stride=stride, 
        padding=pad
    )
    return output_tensor.numpy()
```

| Özellik | PyTorch |
|---------|---------|
| **Hız** | Çok hızlı (C++ backend) |
| **Optimizasyon** | GPU desteği |
| **Okunaklılık** | Siyah kutu (detayları görmüyoruz) |
| **Amaç** | Referans ve doğrulama |

### NumPy (Hücre 3, 5, 7, 9)
```python
def conv_numpy_1(image, weights, pad=1):
    # Padding
    image = np.pad(image, ((0,0), (0,0), (pad,pad), (pad,pad)), 'constant')
    
    # Boyutlar
    batchSize, channelsIn, imageHeightIn, imageWidthIn = image.shape
    channelsOut, channelsIn, kernelHeight, kernelWidth = weights.shape
    
    # Çıkış boyutu
    imageHeightOut = np.floor(1 + imageHeightIn - kernelHeight).astype(int)
    imageWidthOut = np.floor(1 + imageWidthIn - kernelWidth).astype(int)
    
    # Çıkış
    out = np.zeros((batchSize, channelsOut, imageHeightOut, imageWidthOut))
    
    # Döngüler (yavaş ama açık!)
    for c_y in range(imageHeightOut):
        for c_x in range(imageWidthOut):
            for c_kernel_y in range(kernelHeight):
                for c_kernel_x in range(kernelWidth):
                    pixel = image[0, 0, c_y + c_kernel_y, c_x + c_kernel_x]
                    weight = weights[0, 0, c_kernel_y, c_kernel_x]
                    out[0, 0, c_y, c_x] += pixel * weight
    
    return out
```

| Özellik | NumPy |
|---------|-------|
| **Hız** | Yavaş (Pure Python döngüleri) |
| **Optimizasyon** | Yok (basit yapı) |
| **Okunaklılık** | Çok açık (her adım görülüyor) |
| **Amaç** | Öğrenme ve anlayış |

---

## ✅ Hedef Sonuç

Her test hücresinde (4, 6, 8, 10) PyTorch ve NumPy çıkışları **tam olarak aynı** olmalıdır:

```
HÜCRE 4:
PyTorch Results: [...] 
Your results:    [...]  ← Aynı olmalı!

HÜCRE 6:
PyTorch Results: [...] 
Your results:    [...]  ← Aynı olmalı!

... ve böyle devam
```

Eğer sonuçlar aynı değilse, NumPy implementasyonunda bir hata vardır.

---

## 📚 Öğrenme Çıktıları

Bu projeyi tamamladıktan sonra anlayacaksınız:

✅ Konvülüsyon operasyonu nasıl çalışır
✅ Padding neden kullanılır ve ne yapar
✅ Stride çıkış boyutunu nasıl etkiler
✅ Kanallar nasıl işlenir (input → output)
✅ Batch işleme neden verimli
✅ CNN'lerin temel yapı taşı
✅ PyTorch gibi kütüphanelerin altında neler olduğu

---

## 🚀 Kullanım

### Gerekli Kütüphaneler
```bash
pip install numpy torch
```

### Çalıştırma
```bash
python convolution_notebook.py
```

Veya Jupyter Notebook'ta:
```python
# Hücreleri sırayla çalıştır
# Her test hücresinde sonuçları kontrol et
```

---

## 💡 İpuçları

1. **Padding Analizi:** `c_y + c_kernel_y` indeksleri neden çalışır?
   - Çünkü görüntüyü padding=1 ile çevreledik!
   - İlk piksel (0,0) artık (1,1) konumunda!

2. **Stride Etkisi:** `c_y * stride` neden gerekli?
   - Filtreyi stride kadar ilerletiyoruz
   - stride=2 ise 2 piksel atlanır

3. **Kanal İşlemesi:** Neden tüm input kanallarını topluyoruz?
   - Çünkü output bir kanal, tüm input kanallarından bilgi alıyor!

4. **Batch İşleme:** Neden batch gerekli?
   - Paralellik: GPU 32 görüntüyü neredeyse 1 görüntü gibi hızında işler

---

