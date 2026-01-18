# src2/recommender_llm_an1.py - ADIM 1: EN BASİT VERSİYON
"""
ANDREW NG PRENSİBİ 1: Start Simple
- Sadece 1 API (Gemini)
- Sadece 1 fonksiyon
- Sadece kullanıcıdan input al
"""

import os
import google.genai as genai

# 1. API anahtarı
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("❌ GOOGLE_API_KEY ayarlanmalı!")
    exit(1)

# 2. Basit kurulum
client = genai.Client(api_key=GOOGLE_API_KEY)

def tiyatro_ara_basit(sorgu):
    """En basit tiyatro arama"""
    prompt = f"""
    Kullanıcı tiyatro arıyor: "{sorgu}"
    
    Bu kişiye tiyatro önerileri yap.
    5-6 öneri yeterli.
    Her öneri için oyun adı ve mekan yaz.
    
    Örnek format:
    1. Oyun Adı - Mekan
    2. Oyun Adı - Mekan
    """
    
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=prompt
    )
    
    return response.text

# 3. Ana program
print("🎭 TİYATRO ARAMA v1 (Andrew Ng Style)")
print("=" * 40)

sorgu = input("Ne arıyorsunuz? (örn: İstanbul'da 23 ocak tiyatro): ")

print("\n⏳ Aranıyor...\n")

sonuc = tiyatro_ara_basit(sorgu)
print(sonuc)

print("\n" + "=" * 40)
print("✅ ADIM 1 TAMAMLANDI: En basit versiyon çalışıyor!")