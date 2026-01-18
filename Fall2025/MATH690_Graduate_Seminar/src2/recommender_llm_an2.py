# src2/recommender_llm_an2.py - ADIM 2: SORGULARI AYRIŞTIR
"""
ANDREW NG PRENSİBİ 2: Parse Before Process
- Sorgudan şehir ve tarih çıkar
- Basit regex kullan
"""

import os
import re
from datetime import datetime
import google.genai as genai

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("❌ GOOGLE_API_KEY ayarlanmalı!")
    exit(1)

client = genai.Client(api_key=GOOGLE_API_KEY)

def sorguyu_ayristir(sorgu):
    """Sorgudan şehir ve tarih çıkar"""
    # Şehir bul
    sehirler = {
        'istanbul': 'İstanbul',
        'ankara': 'Ankara',
        'izmir': 'İzmir',
        'bursa': 'Bursa'
    }
    
    sorgu_lower = sorgu.lower()
    sehir = "İstanbul"  # Varsayılan
    
    for anahtar, deger in sehirler.items():
        if anahtar in sorgu_lower:
            sehir = deger
            break
    
    # Tarih bul
    ay_sozluk = {
        'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4,
        'mayıs': 5, 'haziran': 6, 'temmuz': 7, 'ağustos': 8,
        'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12
    }
    
    tarih = datetime.now().strftime("%Y-%m-%d")
    
    eslesme = re.search(r'(\d{1,2})\s*(' + '|'.join(ay_sozluk.keys()) + r')\s*(\d{4})', sorgu_lower)
    
    if eslesme:
        gun, ay_adi, yil = eslesme.groups()
        try:
            tarih = f"{int(yil)}-{ay_sozluk[ay_adi]:02d}-{int(gun):02d}"
        except:
            pass
    
    return sehir, tarih

def tiyatro_ara_akilli(sehir, tarih, sorgu):
    """Daha akıllı tiyatro arama"""
    # Tarihi formatla
    yil, ay, gun = tarih.split('-')
    aylar = ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
             'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
    
    tarih_formatli = f"{gun} {aylar[int(ay)]} {yil}"
    
    prompt = f"""
    Kullanıcı: "{sorgu}"
    Şehir: {sehir}
    Tarih: {tarih_formatli}
    
    Bu şehir ve tarih için tiyatro önerileri yap.
    
    Lütfen:
    1. Gerçekçi öneriler yap (uydurma)
    2. Her öneri için:
       - Oyun adı
       - Mekan
       - Saat (varsa)
       - Kısa açıklama
    
    6-8 öneri yeterli.
    """
    
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=prompt
    )
    
    return response.text

# Ana program
print("🎭 TİYATRO ARAMA v2 (Query Parsing)")
print("=" * 50)

sorgu = input("Ne arıyorsunuz?: ")

print(f"\n🔍 Sorgu analiz ediliyor...")
sehir, tarih = sorguyu_ayristir(sorgu)

print(f"📍 Şehir: {sehir}")
print(f"📅 Tarih: {tarih}")

print("\n🤖 Öneriler hazırlanıyor...\n")

sonuc = tiyatro_ara_akilli(sehir, tarih, sorgu)
print(sonuc)

print("\n" + "=" * 50)
print("✅ ADIM 2 TAMAMLANDI: Sorgu parsing eklendi!")