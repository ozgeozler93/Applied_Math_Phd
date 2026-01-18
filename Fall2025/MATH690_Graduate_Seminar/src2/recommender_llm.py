# src2/recommender_llm.py - ANDREW NG TARZI BASİT ÇÖZÜM
import os
import json
import re
from datetime import datetime
import google.genai as genai

# 1. SADECE GEREKLİ KÜTÜPHANELER
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyD...")  # Kendi API anahtarınızı ekleyin

if not GOOGLE_API_KEY or GOOGLE_API_KEY.startswith("AIzaSyD"):
    print("❌ GOOGLE_API_KEY gerekli!")
    print("Terminalde çalıştırın: export GOOGLE_API_KEY='sizin_anahtarınız'")
    exit(1)

# 2. BASİT KURULUM
client = genai.Client(api_key=GOOGLE_API_KEY)

print("=" * 60)
print("🎭 TİYATRO ARAMA ASİSTANI")
print("=" * 60)

def parse_query(query):
    """Basit sorgu ayrıştırma - regex ile"""
    # Şehir
    city = "İstanbul"  # Varsayılan
    if "ankara" in query.lower():
        city = "Ankara"
    elif "izmir" in query.lower():
        city = "İzmir"
    elif "bursa" in query.lower():
        city = "Bursa"
    
    # Tarih
    date = datetime.now().strftime("%Y-%m-%d")  # Bugün varsayılan
    
    month_map = {
        'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4,
        'mayıs': 5, 'haziran': 6, 'temmuz': 7, 'ağustos': 8,
        'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12
    }
    
    match = re.search(r'(\d{1,2})\s*(ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık)\s*(\d{4})', query.lower())
    
    if match:
        day, month_name, year = match.groups()
        try:
            date = f"{int(year):04d}-{month_map[month_name]}-{int(day):02d}"
        except:
            pass
    
    return city, date

def get_simple_recommendations(city, date):
    """Gemini'ye direkt sor - en basit yaklaşım"""
    
    # Tarihi güzel formatla
    year, month, day = date.split('-')
    months_tr = ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 
                'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
    date_formatted = f"{day} {months_tr[int(month)]} {year}"
    
    prompt = f"""
    Sen bir tiyatro uzmanı asistansın. Bana {city} şehrinde {date_formatted} tarihinde 
    izleyebileceğim tiyatro oyunları öner.
    
    LÜTFEN ŞU KAYNAKLARDAN ÖNERİLER YAP:
    1. İBB Şehir Tiyatroları (İstanbul ise)
    2. Devlet Tiyatrosu
    3. Biletix'te popüler tiyatrolar
    4. Passo'da bulunan tiyatrolar
    5. Diğer özel tiyatrolar
    
    HER KATEGORİDEN EN AZ 2-3 ÖNERİ YAP.
    
    Format:
    
    🏆 {city} - {date_formatted} TİYATRO ÖNERİLERİ
    
    🔵 İBB ŞEHİR TİYATROLARI (Sadece İstanbul için):
    1. 🎭 [Oyun Adı]
       📍 [Mekan/Sahne]
       🕒 [Saat]
       📝 [Kısa açıklama]
    
    🟢 DEVLET TİYATROSU:
    1. 🎭 [Oyun Adı]
       📍 [Mekan]
       🕒 [Saat]
       📝 [Kısa açıklama]
    
    🟡 BİLETIX'TE POPÜLER:
    1. 🎭 [Oyun Adı]
       📍 [Mekan]
       🕒 [Saat]
       📝 [Kısa açıklama]
    
    🟠 PASSO'DA BULUNAN:
    1. 🎭 [Oyun Adı]
       📍 [Mekan]
       🕒 [Saat]
       📝 [Kısa açıklama]
    
    🔴 DİĞER ÖZEL TİYATROLAR:
    1. 🎭 [Oyun Adı]
       📍 [Mekan]
       🕒 [Saat]
       📝 [Kısa açıklama]
    
    TOPLAM 10-12 ÖNERİ YAP.
    
    Eğer bir kategoride bilgin yoksa, o kategori için "Bu tarihte bilgi bulunamadı" yaz.
    
    Gerçekçi ve pratik öneriler yap. Oyun isimlerini, mekanları ve saatleri net ver.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=1500
            )
        )
        return response.text
    except Exception as e:
        return f"❌ Hata: {e}\n\n🔍 İnternette ara: {city} tiyatro {date_formatted}"

def get_fallback_recommendations(city, date):
    """İnternet bağlantısı olmazsa basit öneriler"""
    year, month, day = date.split('-')
    months_tr = ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 
                'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
    date_formatted = f"{day} {months_tr[int(month)]} {year}"
    
    recommendations = f"""
🏆 {city} - {date_formatted} TİYATRO ÖNERİLERİ

🔵 POPÜLER TİYATROLAR:

1. 🎭 Kral Lear
   📍 {city} Devlet Tiyatrosu
   🕒 20:00
   📝 Shakespeare'in klasik tragedyası

2. 🎭 Venedik Taciri  
   📍 {city} Kültür Merkezi
   🕒 19:30
   📝 Komedi ve dramın iç içe geçtiği oyun

3. 🎭 Cyrano de Bergerac
   📍 Özel Tiyatro Sahnesi
   🕒 21:00
   📝 Aşk ve fedakarlık hikayesi

🟢 ÇOCUK TİYATROSU:

1. 🎭 Pinokyo
   📍 Çocuk Tiyatrosu
   🕒 14:00
   📝 Klasik masal tiyatro uyarlaması

2. 🎭 Pamuk Prenses
   📍 Aile Tiyatrosu
   🕒 15:30
   📝 Eğlenceli çocuk oyunu

🔍 DETAYLI BİLGİ İÇİN:
• Biletix: https://www.biletix.com/search?q={city}+tiyatro
• Passo: https://www.passo.com.tr/tiyatro
• Google: {city} tiyatro {date_formatted}
"""
    return recommendations

def main():
    print("\n📝 Örnek: 'İstanbul'da 23 ocak 2026 tiyatro' veya 'Ankara bugün tiyatro'")
    print("🔍 Ne arıyorsunuz?: ", end="")
    
    query = input().strip()
    if not query:
        print("Sorgu gerekli!")
        return
    
    print(f"\n⏳ Aranıyor...")
    
    # Basit parsing
    city, date = parse_query(query)
    
    # Tarihi formatla
    year, month, day = date.split('-')
    months_tr = ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 
                'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
    date_formatted = f"{day} {months_tr[int(month)]} {year}"
    
    print(f"📍 Şehir: {city}")
    print(f"📅 Tarih: {date_formatted}")
    print()
    
    # Gemini'den öneri al
    print("🤖 Gemini önerileri hazırlıyor...\n")
    
    try:
        recommendations = get_simple_recommendations(city, date)
        print(recommendations)
    except:
        print("⚠️  Gemini'ye bağlanılamadı, basit öneriler:\n")
        recommendations = get_fallback_recommendations(city, date)
        print(recommendations)
    
    # Pratik bilgiler
    print("\n" + "=" * 60)
    print("💡 PRATİK BİLGİLER:")
    print("=" * 60)
    
    info = f"""
    1. BİLET ALMAK İÇİN:
       • Biletix: https://www.biletix.com/search?q={city}+tiyatro
       • Passo: https://www.passo.com.tr/tiyatro
       • MyBilet: https://www.mybilet.com/tiyatro-biletleri/{city.lower()}
    
    2. RESMİ TİYATROLAR:
       • Devlet Tiyatroları: https://tiyatro.gov.tr
       • İBB Tiyatroları (İstanbul): https://sehirtiyatrolari.ibb.istanbul
    
    3. SON KONTROLLER:
       • Tarihi doğrulayın: {date_formatted}
       • Biletleri erken alın
       • Mekan adresini kontrol edin
    """
    print(info)
    
    print("\n" + "=" * 60)
    again = input("🔄 Yeni arama? (e/h): ").strip().lower()
    
    if again == 'e':
        print("\n" * 2)
        main()
    else:
        print("\n🎭 İyi seyirler!\n")

if __name__ == "__main__":
    # Sadece gerekli paket
    try:
        import google.genai
    except ImportError:
        print("📦 google-genai paketi kuruluyor...")
        os.system("pip install google-genai")
        import google.genai
    
    main()