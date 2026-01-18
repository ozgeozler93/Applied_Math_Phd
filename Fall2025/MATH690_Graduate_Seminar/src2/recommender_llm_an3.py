# src2/recommender_llm_an3.py - FİNAL HİBRİT VERSİYON
"""
Andrew Ng Prensibi: "Combine the best of both approaches"

1. İBB Şehir Tiyatroları - Web Scraping (DÜZELTİLMİŞ sahne bilgisi)
2. Devlet Tiyatroları - Biletinial Selenium (DÜZELTİLMİŞ parse)
3. Özel Tiyatrolar - Google Search (çalışıyor)

KURULUM:
pip install selenium webdriver-manager beautifulsoup4 requests google-genai
"""

import os
import re
import requests
import time
from datetime import datetime
from bs4 import BeautifulSoup
import google.genai as genai
from google.genai import types

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  Selenium kurulu değil. Devlet Tiyatroları için Google Search kullanılacak.")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("❌ GOOGLE_API_KEY ayarlanmalı!")
    exit(1)

client = genai.Client(api_key=GOOGLE_API_KEY)

# Şehir -> Biletinial data-val eşleştirmesi
SEHIR_ID_MAP = {
    'İstanbul': '5', 'Ankara': '3', 'İzmir': '24', 'Mersin': '85',
    'Antalya': '23', 'Samsun': '43', 'Adana': '12', 'Bursa': '11',
    'Denizli': '14', 'Diyarbakır': '10',
}

# ═══════════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════════════════════════

def sorguyu_ayristir(sorgu):
    sehirler = {
        'istanbul': 'İstanbul', 'ankara': 'Ankara', 'izmir': 'İzmir',
        'bursa': 'Bursa', 'antalya': 'Antalya', 'mersin': 'Mersin',
        'samsun': 'Samsun', 'adana': 'Adana', 'denizli': 'Denizli'
    }
    sorgu_lower = sorgu.lower()
    sehir = "İstanbul"
    for anahtar, deger in sehirler.items():
        if anahtar in sorgu_lower:
            sehir = deger
            break
    
    ay_sozluk = {'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4, 'mayıs': 5, 'haziran': 6,
                 'temmuz': 7, 'ağustos': 8, 'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12}
    
    yil_eslesme = re.search(r'(\d{4})', sorgu)
    yil = yil_eslesme.group(1) if yil_eslesme else datetime.now().strftime("%Y")
    tarih = datetime.now().strftime("%Y-%m-%d")
    pattern = r'(\d{1,2})\s*(' + '|'.join(ay_sozluk.keys()) + r')'
    eslesme = re.search(pattern, sorgu_lower)
    if eslesme:
        gun, ay_adi = eslesme.groups()
        try:
            tarih = f"{int(yil)}-{ay_sozluk[ay_adi]:02d}-{int(gun):02d}"
        except:
            pass
    return sehir, tarih

def tarih_formatla(tarih):
    yil, ay, gun = tarih.split('-')
    aylar = ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
             'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
    return f"{int(gun)} {aylar[int(ay)]} {yil}"

def get_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

# ═══════════════════════════════════════════════════════════════
# KAYNAK 1: İBB ŞEHİR TİYATROLARI (DÜZELTİLMİŞ Web Scraping)
# ═══════════════════════════════════════════════════════════════

def ibb_sehir_tiyatrolari_ara(hedef_gun):
    """
    İBB Şehir Tiyatroları takviminden veri çek
    
    HTML YAPISI (gerçek):
    - Tablo: <table class="yn_calendar-table">
    - Header: <thead> içinde <td> (th değil!)
    - Sütunlar: Gün | Tarih | Saat | Sahne1 | Sahne2 | ... | Sahne10
    - Body: <tbody class="yn_calendar_list">
    - Gün hücresi: <td class="yn_calendar_day" rowspan="X">
    - Saat hücresi: <td class="yn_calendar_time">
    """
    try:
        url = "https://sehirtiyatrolari.ibb.istanbul/takvim"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        oyunlar = []
        
        # Tablo bul (class ile)
        table = soup.find('table', class_='yn_calendar-table')
        if not table:
            table = soup.find('table')
        if not table:
            print("   ⚠️  Tablo bulunamadı")
            return []
        
        # ═══════════════════════════════════════════════════════════
        # HEADER'DAN SAHNE İSİMLERİNİ AL
        # ÖNEMLİ: Header'da <th> değil <td> kullanılmış!
        # ═══════════════════════════════════════════════════════════
        sahneler = []
        thead = table.find('thead')
        if thead:
            header_row = thead.find('tr')
            if header_row:
                # Hem th hem td'yi dene
                header_cells = header_row.find_all(['th', 'td'])
                # İlk 3 sütun: Gün, Tarih, Saat - atla
                for cell in header_cells[3:]:
                    text = cell.get_text(strip=True)
                    if text:
                        sahneler.append(text)
        
        print(f"   📍 Sahneler ({len(sahneler)}): {[s[:25] for s in sahneler[:5]]}...")
        
        # ═══════════════════════════════════════════════════════════
        # TBODY'DEN VERİLERİ AL
        # ═══════════════════════════════════════════════════════════
        tbody = table.find('tbody', class_='yn_calendar_list')
        if not tbody:
            tbody = table.find('tbody')
        if not tbody:
            tbody = table
        
        rows = tbody.find_all('tr')
        
        current_date = None
        current_saat = None
        
        for row in rows:
            cells = row.find_all('td')
            if not cells:
                continue
            
            # ═══════════════════════════════════════════════════════════
            # GÜN VE SAAT BİLGİSİNİ BUL
            # Class'lara göre hücreleri ayır:
            # - yn_calendar_day: Gün numarası (02, 03, ...)
            # - yn_calendar_time: Saat (15:00, 20:00, ...)
            # ═══════════════════════════════════════════════════════════
            
            # Gün hücresini bul (class ile)
            day_cell = row.find('td', class_='yn_calendar_day')
            if day_cell:
                day_text = day_cell.get_text(strip=True)
                if day_text.isdigit():
                    current_date = int(day_text)
            
            # Saat hücresini bul (class ile)
            time_cell = row.find('td', class_='yn_calendar_time')
            if time_cell:
                time_text = time_cell.get_text(strip=True)
                if re.match(r'^\d{2}:\d{2}$', time_text):
                    current_saat = time_text
            
            # Hedef günü kontrol et
            if current_date != hedef_gun:
                continue
            
            # ═══════════════════════════════════════════════════════════
            # OYUN HÜCRELERİNİ PARSE ET
            # Gün, Tarih, Saat hücrelerini atla
            # Kalan hücreler sahne sütunları
            # ═══════════════════════════════════════════════════════════
            
            # Özel class'lı hücreleri say ve atla
            skip_count = 0
            for cell in cells:
                cell_class = cell.get('class', [])
                if any(c in cell_class for c in ['yn_calendar_day', 'yn_calendar_date', 'yn_calendar_time']):
                    skip_count += 1
                else:
                    break
            
            # Oyun hücreleri
            oyun_hucreleri = cells[skip_count:]
            
            for idx, cell in enumerate(oyun_hucreleri):
                # Sahne adını belirle
                sahne = sahneler[idx] if idx < len(sahneler) else f"Sahne {idx + 1}"
                
                # Hücredeki linkleri bul (oyun adları)
                links = cell.find_all('a')
                for link in links:
                    oyun_adi = link.get_text(strip=True)
                    if not oyun_adi or len(oyun_adi) < 3:
                        continue
                    
                    href = link.get('href', '')
                    
                    # Tükendi bilgisi - yn_tukendi class veya text
                    tukendi_span = cell.find('span', class_='yn_tukendi')
                    tukendi = tukendi_span is not None or 'TÜKENDİ' in cell.get_text().upper()
                    
                    oyunlar.append({
                        'oyun': oyun_adi,
                        'sahne': sahne,
                        'saat': current_saat or '20:00',
                        'tukendi': tukendi,
                        'link': f"https://sehirtiyatrolari.ibb.istanbul{href}" if href.startswith('/') else href
                    })
        
        # Benzersiz oyunları döndür
        seen = set()
        unique = []
        for o in oyunlar:
            key = (o['oyun'], o['saat'], o['sahne'])
            if key not in seen:
                seen.add(key)
                unique.append(o)
        
        return unique
        
    except Exception as e:
        print(f"   ⚠️  İBB Hata: {e}")
        import traceback
        traceback.print_exc()
        return []

# ═══════════════════════════════════════════════════════════════
# KAYNAK 2: DEVLET TİYATROLARI - BİLETİNİAL (DÜZELTİLMİŞ Selenium)
# ═══════════════════════════════════════════════════════════════

def biletinial_devlet_tiyatrolari_ara(sehir, hedef_gun, hedef_ay):
    """
    Biletinial'dan Selenium ile Devlet Tiyatroları verisi çek
    DÜZELTİLMİŞ: Parse mantığı iyileştirildi
    """
    if not SELENIUM_AVAILABLE:
        return None
    
    driver = None
    oyunlar = []
    
    try:
        print(f"      🌐 Biletinial açılıyor...")
        driver = get_chrome_driver()
        driver.get("https://biletinial.com/tr-tr/etkinlik-takvimi/708")
        
        wait = WebDriverWait(driver, 15)
        time.sleep(4)  # JavaScript'in yüklenmesi için
        
        # ═══════════════════════════════════════════════════════════
        # ADIM 1: ŞEHİR SEÇİMİ
        # ═══════════════════════════════════════════════════════════
        print(f"      📍 Şehir seçiliyor: {sehir}")
        sehir_id = SEHIR_ID_MAP.get(sehir, '5')
        
        try:
            # Dropdown'u aç
            city_selector = wait.until(EC.element_to_be_clickable((By.ID, "citySelector")))
            driver.execute_script("arguments[0].click();", city_selector)
            time.sleep(1)
            
            # Şehri seç
            city_option = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, f"#customCitySelect .scrollList ul li[data-val='{sehir_id}']")
            ))
            driver.execute_script("arguments[0].click();", city_option)
            print(f"      ✅ {sehir} seçildi")
            
            # Sayfanın güncellenmesini bekle
            time.sleep(4)
            
        except Exception as e:
            print(f"      ⚠️  Şehir seçimi: {e}")
        
        # ═══════════════════════════════════════════════════════════
        # ADIM 2: TABLOYU PARSE ET (DÜZELTİLMİŞ)
        # ═══════════════════════════════════════════════════════════
        print(f"      📅 Takvim parse ediliyor...")
        
        # Sayfayı yeniden al
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Tüm tabloları bul
        tables = soup.find_all('table', class_='bltn-table')
        if not tables:
            tables = soup.find_all('table')
        
        # İkinci tablo genelde ana veri tablosu (ilki floatThead)
        table = tables[-1] if tables else None
        
        if not table:
            print("      ⚠️  Tablo bulunamadı")
            return []
        
        # Header'dan sahne isimlerini al
        sahneler = []
        
        # Önce thead içindeki th'leri dene
        thead = table.find('thead')
        if thead:
            header_row = thead.find('tr')
            if header_row:
                ths = header_row.find_all('th')
                for th in ths:
                    # aria-label attribute'undan sahne adını al (daha temiz)
                    aria_label = th.get('aria-label', '')
                    if aria_label and aria_label.strip():
                        sahne_adi = aria_label.strip()
                    else:
                        # Text'ten al
                        sahne_adi = th.get_text(separator=' ', strip=True)
                    
                    sahne_adi = re.sub(r'\s+', ' ', sahne_adi).strip()
                    
                    # Boş olmayan ve tarih/filtre olmayan sahne isimlerini ekle
                    if sahne_adi and len(sahne_adi) > 2 and 'data-min' not in str(th):
                        sahneler.append(sahne_adi)
        
        # Sahneler boşsa, alternatif yöntem dene
        if not sahneler:
            # floatThead tablosundan al
            float_thead = soup.find('div', class_='floatThead-container')
            if float_thead:
                float_table = float_thead.find('table')
                if float_table:
                    ths = float_table.find_all('th')
                    for th in ths[1:]:  # İlk th tarih filtresi
                        text = th.get_text(separator=' ', strip=True)
                        text = re.sub(r'\s+', ' ', text).strip()
                        if text and len(text) > 2:
                            sahneler.append(text)
        
        print(f"      🎭 Sahneler ({len(sahneler)}): {sahneler[:5]}...")
        
        # Tbody'yi bul
        tbody = table.find('tbody')
        if not tbody:
            tbody = table
        
        rows = tbody.find_all('tr')
        print(f"      📊 Satır sayısı: {len(rows)}")
        
        for row in rows:
            cells = row.find_all('td')
            if not cells:
                continue
            
            # İlk hücrede tarih bilgisi
            first_cell = cells[0]
            first_text = first_cell.get_text(strip=True)
            
            # Tarih class'ını kontrol et
            if 'baslikAraYN' not in first_cell.get('class', []) and not re.search(r'\d{1,2}', first_text):
                continue
            
            # Gün numarasını çıkar
            gun_match = re.search(r'^(\d{1,2})', first_text)
            if not gun_match:
                continue
            
            current_gun = int(gun_match.group(1))
            
            # Ay kontrolü
            current_ay = None
            for ay in ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 
                       'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']:
                if ay in first_text:
                    current_ay = ay
                    break
            
            # Hedef günü kontrol et
            if current_gun != hedef_gun:
                continue
            
            if hedef_ay and current_ay and current_ay != hedef_ay:
                continue
            
            print(f"      📆 Hedef gün bulundu: {first_text}")
            
            # Her etkinlik hücresini kontrol et (ilk hücre tarih)
            for idx, cell in enumerate(cells[1:]):
                # act-line div'lerini bul (etkinlik kartları)
                act_lines = cell.find_all('div', class_=lambda x: x and 'act-line' in x)
                
                if not act_lines:
                    # Alternatif: doğrudan link ara
                    links = cell.find_all('a', class_='info-label')
                    for link in links:
                        oyun_adi = link.get_text(strip=True)
                        # Mobil sahne adını temizle
                        mobile = link.find('span', class_='mobile-saloon-name')
                        if mobile:
                            oyun_adi = oyun_adi.replace(mobile.get_text(), '').strip()
                        
                        if oyun_adi and len(oyun_adi) > 2:
                            sahne = sahneler[idx] if idx < len(sahneler) else "Devlet Tiyatrosu"
                            
                            # Seans bilgisini bul
                            parent = link.find_parent('div')
                            saat = "20:00"
                            tukendi = False
                            
                            if parent:
                                seances = parent.find('div', class_='seances-list')
                                if seances:
                                    btn = seances.find('button')
                                    if btn:
                                        btn_text = btn.get_text(strip=True)
                                        saat_match = re.search(r'(\d{2}:\d{2})', btn_text)
                                        if saat_match:
                                            saat = saat_match.group(1)
                                        tukendi = 'TÜKENDİ' in btn_text.upper()
                            
                            oyunlar.append({
                                'oyun': oyun_adi,
                                'sahne': sahne,
                                'saat': saat,
                                'tukendi': tukendi,
                                'bilet': 'biletinial.com'
                            })
                    continue
                
                for act in act_lines:
                    # Oyun adını al
                    info_label = act.find('a', class_='info-label')
                    if not info_label:
                        continue
                    
                    oyun_adi = info_label.get_text(strip=True)
                    
                    # Mobil sahne adını temizle
                    mobile_saloon = info_label.find('span', class_='mobile-saloon-name')
                    if mobile_saloon:
                        oyun_adi = oyun_adi.replace(mobile_saloon.get_text(), '').strip()
                    
                    if not oyun_adi or len(oyun_adi) < 2:
                        continue
                    
                    # Sahne adı
                    sahne = sahneler[idx] if idx < len(sahneler) else "Devlet Tiyatrosu"
                    
                    # Seans bilgilerini al
                    seances = act.find('div', class_='seances-list')
                    if seances:
                        buttons = seances.find_all('button')
                        for btn in buttons:
                            btn_text = btn.get_text(strip=True)
                            
                            # Saat
                            saat_match = re.search(r'(\d{2}:\d{2})', btn_text)
                            saat = saat_match.group(1) if saat_match else "20:00"
                            
                            # Tükendi
                            tukendi = 'TÜKENDİ' in btn_text.upper()
                            style = btn.get('style', '')
                            if '#ff4061' in style:
                                tukendi = True
                            if 'soldout' in ' '.join(act.get('class', [])):
                                tukendi = True
                            
                            oyunlar.append({
                                'oyun': oyun_adi,
                                'sahne': sahne,
                                'saat': saat,
                                'tukendi': tukendi,
                                'bilet': 'biletinial.com'
                            })
                    else:
                        # Seans bilgisi yoksa varsayılan ekle
                        oyunlar.append({
                            'oyun': oyun_adi,
                            'sahne': sahne,
                            'saat': '20:00',
                            'tukendi': False,
                            'bilet': 'biletinial.com'
                        })
        
        # Benzersiz oyunları döndür
        seen = set()
        unique = []
        for o in oyunlar:
            key = (o['oyun'], o['saat'], o['sahne'])
            if key not in seen:
                seen.add(key)
                unique.append(o)
        
        print(f"      📋 Toplam {len(unique)} benzersiz oyun bulundu")
        return unique
        
    except Exception as e:
        print(f"      ❌ Selenium hatası: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        if driver:
            driver.quit()

def devlet_tiyatrolari_google_ara(sehir, tarih_formatli):
    """Fallback: Google Search ile ara"""
    prompt = f"""{sehir}'da {tarih_formatli} tarihinde DEVLET TİYATROLARI'nda hangi oyunlar var?

Biletinial.com Devlet Tiyatroları etkinlik takviminden {sehir} için {tarih_formatli} tarihindeki oyunları listele.

SADECE bu tarih ve şehirdeki oyunları listele. Farklı tarihleri veya şehirleri EKLEME.

Format:
• [Oyun Adı] 📍 [Sahne] ⏰ [Saat] 🎫 biletinial.com"""
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.1,
            )
        )
        return response.text.strip()
    except Exception as e:
        return f"   ⚠️  Arama hatası: {e}"

# ═══════════════════════════════════════════════════════════════
# KAYNAK 3: ÖZEL TİYATROLAR (Google Search - çalışıyor)
# ═══════════════════════════════════════════════════════════════

def ozel_tiyatrolar_ara(sehir, tarih_formatli):
    prompt = f"""{sehir}'da {tarih_formatli} tarihinde ÖZEL TİYATROLARDA hangi oyunlar var?

DasDas, Zorlu PSM, Moda Sahnesi, Craft Tiyatro, Biletix, Passo, Bubilet sitelerini ara.

SADECE {tarih_formatli} tarihindeki oyunları listele. Farklı tarihleri EKLEME.

Format:
• [Oyun Adı] 📍 [Tiyatro/Mekan] ⏰ [Saat] 🎫 [Bilet platformu]"""
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.1,
            )
        )
        return response.text.strip()
    except Exception as e:
        return f"   ⚠️  Arama hatası: {e}"

# ═══════════════════════════════════════════════════════════════
# FORMATLAMA
# ═══════════════════════════════════════════════════════════════

def ibb_sonuc_formatla(oyunlar):
    if not oyunlar:
        return "   Bu tarihte oyun bulunamadı.\n"
    
    # Saate göre grupla
    saat_gruplari = {}
    for o in oyunlar:
        saat = o['saat']
        if saat not in saat_gruplari:
            saat_gruplari[saat] = []
        saat_gruplari[saat].append(o)
    
    sonuc = ""
    for saat in sorted(saat_gruplari.keys()):
        sonuc += f"\n   ⏰ Saat {saat}:\n"
        for o in saat_gruplari[saat]:
            durum = "❌ TÜKENDİ" if o['tukendi'] else "✅ Bilet Var"
            sonuc += f"      • {o['oyun']}\n"
            sonuc += f"        📍 {o['sahne']}\n"
            sonuc += f"        {durum}\n"
    
    return sonuc

def devlet_sonuc_formatla(oyunlar, tarih_str):
    if not oyunlar:
        return f"   {tarih_str} tarihinde Devlet Tiyatroları'nda oyun bulunamadı.\n"
    
    sonuc = ""
    for o in oyunlar:
        durum = "❌ TÜKENDİ" if o['tukendi'] else "✅ Bilet Var"
        sonuc += f"\n   • {o['oyun']}\n"
        sonuc += f"     📍 {o['sahne']}\n"
        sonuc += f"     ⏰ {o['saat']}\n"
        sonuc += f"     {durum}\n"
        sonuc += f"     🎫 {o['bilet']}\n"
    
    return sonuc

# ═══════════════════════════════════════════════════════════════
# ANA PROGRAM
# ═══════════════════════════════════════════════════════════════

def main():
    print("🎭 TİYATRO ARAMA - FİNAL VERSİYON")
    print("=" * 60)
    print("   Kaynaklar:")
    print("   1️⃣  İBB Şehir Tiyatroları (Web Scraping)")
    print("   2️⃣  Devlet Tiyatroları (Biletinial Selenium)")
    print("   3️⃣  Özel Tiyatrolar (Google Search)")
    print("=" * 60)
    
    sorgu = input("\n🔍 Ne arıyorsunuz?: ")
    sehir, tarih = sorguyu_ayristir(sorgu)
    hedef_gun = int(tarih.split('-')[2])
    hedef_ay_num = int(tarih.split('-')[1])
    aylar = ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
             'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
    hedef_ay = aylar[hedef_ay_num]
    tarih_str = tarih_formatla(tarih)
    
    print(f"\n📍 Şehir: {sehir}")
    print(f"📅 Tarih: {tarih_str}")
    
    # ─────────────────────────────────────────────────────────────
    # KAYNAK 1: İBB Şehir Tiyatroları (sadece İstanbul için)
    # ─────────────────────────────────────────────────────────────
    ibb_oyunlar = []
    if sehir == "İstanbul":
        print("\n" + "─" * 60)
        print("1️⃣  İBB Şehir Tiyatroları aranıyor... (Web Scraping)")
        ibb_oyunlar = ibb_sehir_tiyatrolari_ara(hedef_gun)
        print(f"   ✅ {len(ibb_oyunlar)} oyun bulundu")
    
    # ─────────────────────────────────────────────────────────────
    # KAYNAK 2: Devlet Tiyatroları (Biletinial)
    # ─────────────────────────────────────────────────────────────
    print("\n" + "─" * 60)
    print("2️⃣  Devlet Tiyatroları aranıyor... (Biletinial)")
    
    devlet_oyunlar = biletinial_devlet_tiyatrolari_ara(sehir, hedef_gun, hedef_ay)
    
    if devlet_oyunlar is None or len(devlet_oyunlar) == 0:
        print("      ⚠️  Selenium veri bulamadı, Google Search kullanılıyor...")
        devlet_sonuc_text = devlet_tiyatrolari_google_ara(sehir, tarih_str)
        devlet_oyunlar = []
    else:
        devlet_sonuc_text = None
        print(f"   ✅ {len(devlet_oyunlar)} oyun bulundu")
    
    # ─────────────────────────────────────────────────────────────
    # KAYNAK 3: Özel Tiyatrolar
    # ─────────────────────────────────────────────────────────────
    print("\n" + "─" * 60)
    print("3️⃣  Özel Tiyatrolar aranıyor... (Google Search)")
    ozel_sonuc = ozel_tiyatrolar_ara(sehir, tarih_str)
    print("   ✅ Arama tamamlandı")
    
    # ═════════════════════════════════════════════════════════════
    # SONUÇLAR
    # ═════════════════════════════════════════════════════════════
    print("\n")
    print("═" * 60)
    print(f"🎭 {sehir} TİYATRO PROGRAMI - {tarih_str}")
    print("═" * 60)
    
    # İBB Şehir Tiyatroları
    if sehir == "İstanbul":
        print("\n┌" + "─" * 58 + "┐")
        print("│ 📍 İBB ŞEHİR TİYATROLARI                                  │")
        print("│    Kaynak: sehirtiyatrolari.ibb.istanbul                  │")
        print("└" + "─" * 58 + "┘")
        print(ibb_sonuc_formatla(ibb_oyunlar))
    
    # Devlet Tiyatroları
    print("\n┌" + "─" * 58 + "┐")
    print("│ 🏛️  DEVLET TİYATROLARI                                       │")
    if devlet_sonuc_text:
        print("│    Kaynak: Google Search                                  │")
    else:
        print("│    Kaynak: biletinial.com (Doğrudan Veri)                 │")
    print("└" + "─" * 58 + "┘")
    
    if devlet_sonuc_text:
        print(devlet_sonuc_text)
    else:
        print(devlet_sonuc_formatla(devlet_oyunlar, tarih_str))
    
    # Özel Tiyatrolar
    print("\n┌" + "─" * 58 + "┐")
    print("│ 🎪 ÖZEL TİYATROLAR                                         │")
    print("│    Kaynak: DasDas, Zorlu PSM, Biletix, Passo vb.          │")
    print("└" + "─" * 58 + "┘")
    print(ozel_sonuc)
    
    # Faydalı Linkler
    print("\n┌" + "─" * 58 + "┐")
    print("│ 🔗 FAYDALI LİNKLER                                         │")
    print("└" + "─" * 58 + "┘")
    if sehir == "İstanbul":
        print("   • İBB Şehir Tiyatroları: https://sehirtiyatrolari.ibb.istanbul/takvim")
    print("   • Devlet Tiyatroları: https://biletinial.com/tr-tr/etkinlik-takvimi/708")
    print("   • Biletinial: https://www.biletinial.com")
    print("   • Biletix: https://www.biletix.com")
    print("   • Passo: https://www.passo.com.tr")
    
    print("\n" + "═" * 60)
    print("✅ Arama tamamlandı!")

if __name__ == "__main__":
    main()


# ==================================================== *****************IBB OYUNLARININ SAHNE ISMI HEP AYNI, DEVLET TIYATROLARININ SONUCU IYI, OZEL TIYATOLARIN SONUCU IYI*********=================
# # src2/recommender_llm_an3.py - BİLETİNİAL DOĞRU SELECTOR'LAR
# """
# Devlet Tiyatroları için Biletinial'dan doğru veri çekme
# Şehir seçimi: #customCitySelect dropdown, İstanbul = data-val="5"

# KURULUM:
# pip install selenium webdriver-manager beautifulsoup4 requests google-genai
# """

# import os
# import re
# import requests
# import time
# from datetime import datetime
# from bs4 import BeautifulSoup
# import google.genai as genai
# from google.genai import types

# try:
#     from selenium import webdriver
#     from selenium.webdriver.common.by import By
#     from selenium.webdriver.support.ui import WebDriverWait
#     from selenium.webdriver.support import expected_conditions as EC
#     from selenium.webdriver.chrome.options import Options
#     from selenium.webdriver.chrome.service import Service
#     from webdriver_manager.chrome import ChromeDriverManager
#     SELENIUM_AVAILABLE = True
# except ImportError:
#     SELENIUM_AVAILABLE = False

# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# if not GOOGLE_API_KEY:
#     print("❌ GOOGLE_API_KEY ayarlanmalı!")
#     exit(1)

# client = genai.Client(api_key=GOOGLE_API_KEY)

# # Şehir -> Biletinial data-val eşleştirmesi
# SEHIR_ID_MAP = {
#     'İstanbul': '5',
#     'Ankara': '3',
#     'İzmir': '24',
#     'Mersin': '85',
#     'Antalya': '23',
#     'Samsun': '43',
#     'Adana': '12',
#     'Bursa': '11',
#     'Denizli': '14',
#     'Diyarbakır': '10',
# }

# def sorguyu_ayristir(sorgu):
#     sehirler = {
#         'istanbul': 'İstanbul', 'ankara': 'Ankara', 'izmir': 'İzmir',
#         'bursa': 'Bursa', 'antalya': 'Antalya', 'mersin': 'Mersin',
#         'samsun': 'Samsun', 'adana': 'Adana', 'denizli': 'Denizli'
#     }
#     sorgu_lower = sorgu.lower()
#     sehir = "İstanbul"
#     for anahtar, deger in sehirler.items():
#         if anahtar in sorgu_lower:
#             sehir = deger
#             break
    
#     ay_sozluk = {'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4, 'mayıs': 5, 'haziran': 6,
#                  'temmuz': 7, 'ağustos': 8, 'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12}
    
#     yil_eslesme = re.search(r'(\d{4})', sorgu)
#     yil = yil_eslesme.group(1) if yil_eslesme else datetime.now().strftime("%Y")
#     tarih = datetime.now().strftime("%Y-%m-%d")
#     pattern = r'(\d{1,2})\s*(' + '|'.join(ay_sozluk.keys()) + r')'
#     eslesme = re.search(pattern, sorgu_lower)
#     if eslesme:
#         gun, ay_adi = eslesme.groups()
#         try:
#             tarih = f"{int(yil)}-{ay_sozluk[ay_adi]:02d}-{int(gun):02d}"
#         except:
#             pass
#     return sehir, tarih

# def tarih_formatla(tarih):
#     yil, ay, gun = tarih.split('-')
#     aylar = ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
#              'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
#     return f"{int(gun)} {aylar[int(ay)]} {yil}"

# def get_chrome_driver():
#     chrome_options = Options()
#     chrome_options.add_argument("--headless=new")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     chrome_options.add_argument("--window-size=1920,1080")
#     service = Service(ChromeDriverManager().install())
#     return webdriver.Chrome(service=service, options=chrome_options)

# # ═══════════════════════════════════════════════════════════════
# # İBB ŞEHİR TİYATROLARI
# # ═══════════════════════════════════════════════════════════════

# def ibb_sehir_tiyatrolari_ara(hedef_gun):
#     try:
#         url = "https://sehirtiyatrolari.ibb.istanbul/takvim"
#         headers = {'User-Agent': 'Mozilla/5.0'}
#         response = requests.get(url, headers=headers, timeout=15)
#         soup = BeautifulSoup(response.content, 'html.parser')
        
#         oyunlar = []
#         table = soup.find('table')
#         if not table:
#             return []
        
#         rows = table.find_all('tr')
#         sahneler = []
#         header = rows[0] if rows else None
#         if header:
#             ths = header.find_all('th')
#             sahneler = [th.text.strip() for th in ths[3:]]
        
#         current_date = None
#         current_saat = None
        
#         for row in rows[1:]:
#             cells = row.find_all('td')
#             if not cells:
#                 continue
#             first_cell_text = cells[0].text.strip()
#             if first_cell_text.isdigit():
#                 current_date = int(first_cell_text)
#             for cell in cells:
#                 text = cell.text.strip()
#                 if re.match(r'^\d{2}:\d{2}$', text):
#                     current_saat = text
#                     break
#             if current_date != hedef_gun:
#                 continue
#             for idx, cell in enumerate(cells):
#                 links = cell.find_all('a')
#                 for link in links:
#                     oyun_adi = link.text.strip()
#                     if not oyun_adi or len(oyun_adi) < 3:
#                         continue
#                     href = link.get('href', '')
#                     tukendi = 'TÜKENDİ' in cell.text
#                     sahne_idx = idx - 3
#                     sahne = sahneler[sahne_idx] if 0 <= sahne_idx < len(sahneler) else "İBB Sahnesi"
#                     oyunlar.append({
#                         'oyun': oyun_adi, 'sahne': sahne[:50], 'saat': current_saat or '20:00',
#                         'tukendi': tukendi,
#                         'link': f"https://sehirtiyatrolari.ibb.istanbul{href}" if href.startswith('/') else href
#                     })
        
#         seen = set()
#         unique = []
#         for o in oyunlar:
#             key = (o['oyun'], o['saat'], o['sahne'])
#             if key not in seen:
#                 seen.add(key)
#                 unique.append(o)
#         return unique
#     except Exception as e:
#         print(f"   ⚠️  Hata: {e}")
#         return []

# # ═══════════════════════════════════════════════════════════════
# # DEVLET TİYATROLARI - BİLETİNİAL (Selenium)
# # ═══════════════════════════════════════════════════════════════

# def biletinial_devlet_tiyatrolari_ara(sehir, hedef_gun, hedef_ay):
#     """
#     Biletinial'dan Selenium ile Devlet Tiyatroları verisi çek
    
#     Sayfa yapısı:
#     - Şehir dropdown: #customCitySelect
#     - Şehir seçici: #citySelector (tıklanır)
#     - Şehir listesi: .scrollList ul li[data-val="X"]
#     - İstanbul: data-val="5"
#     """
#     if not SELENIUM_AVAILABLE:
#         return None
    
#     driver = None
#     oyunlar = []
    
#     try:
#         print(f"      🌐 Biletinial açılıyor...")
#         driver = get_chrome_driver()
#         driver.get("https://biletinial.com/tr-tr/etkinlik-takvimi/708")
        
#         wait = WebDriverWait(driver, 15)
#         time.sleep(3)
        
#         # ═══════════════════════════════════════════════════════════
#         # ADIM 1: ŞEHİR SEÇİMİ
#         # ═══════════════════════════════════════════════════════════
#         print(f"      📍 Şehir seçiliyor: {sehir}")
        
#         sehir_id = SEHIR_ID_MAP.get(sehir, '5')  # Varsayılan İstanbul
        
#         try:
#             # Dropdown'u aç - #citySelector'a tıkla
#             city_selector = wait.until(EC.element_to_be_clickable((By.ID, "citySelector")))
#             city_selector.click()
#             time.sleep(1)
            
#             # Şehri seç - li[data-val="X"]
#             city_option = wait.until(EC.element_to_be_clickable(
#                 (By.CSS_SELECTOR, f"#customCitySelect .scrollList ul li[data-val='{sehir_id}']")
#             ))
#             city_option.click()
#             print(f"      ✅ {sehir} seçildi (data-val={sehir_id})")
            
#             # Sayfanın yenilenmesini bekle
#             time.sleep(3)
            
#         except Exception as e:
#             print(f"      ⚠️  Şehir seçimi hatası: {e}")
#             # Alternatif: JavaScript ile seç
#             try:
#                 driver.execute_script(f"""
#                     document.querySelector('#citySelector').click();
#                     setTimeout(() => {{
#                         document.querySelector('#customCitySelect .scrollList ul li[data-val="{sehir_id}"]').click();
#                     }}, 500);
#                 """)
#                 time.sleep(3)
#                 print(f"      ✅ {sehir} JavaScript ile seçildi")
#             except Exception as e2:
#                 print(f"      ❌ JavaScript seçimi de başarısız: {e2}")
        
#         # ═══════════════════════════════════════════════════════════
#         # ADIM 2: TABLOYU PARSE ET
#         # ═══════════════════════════════════════════════════════════
#         print(f"      📅 Takvim parse ediliyor...")
        
#         soup = BeautifulSoup(driver.page_source, 'html.parser')
        
#         # Ana tabloyu bul (bltn-table class'ı)
#         table = soup.find('table', class_='bltn-table')
#         if not table:
#             tables = soup.find_all('table')
#             table = tables[1] if len(tables) > 1 else (tables[0] if tables else None)
        
#         if not table:
#             print("      ⚠️  Tablo bulunamadı")
#             return []
        
#         # Header'dan sahne isimlerini al
#         sahneler = []
#         thead = table.find('thead')
#         if thead:
#             ths = thead.find_all('th')
#             for th in ths[1:]:  # İlk th boş (tarih sütunu)
#                 # strong ve br taglarını temizle
#                 sahne_adi = th.get_text(separator=' ', strip=True)
#                 sahne_adi = re.sub(r'\s+', ' ', sahne_adi).strip()
#                 if sahne_adi:
#                     sahneler.append(sahne_adi)
        
#         print(f"      🎭 Sahneler: {sahneler[:5]}...")
        
#         # Tbody'deki satırları tara
#         tbody = table.find('tbody')
#         if not tbody:
#             tbody = table
        
#         rows = tbody.find_all('tr')
        
#         for row in rows:
#             cells = row.find_all('td')
#             if not cells:
#                 continue
            
#             # İlk hücre tarih bilgisi
#             first_cell = cells[0]
#             first_text = first_cell.get_text(strip=True)
            
#             # "16 Ocak Cuma" formatından gün numarasını çıkar
#             gun_match = re.search(r'^(\d{1,2})', first_text)
#             if not gun_match:
#                 continue
            
#             current_gun = int(gun_match.group(1))
            
#             # Ay kontrolü
#             current_ay = None
#             for ay in ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 
#                        'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']:
#                 if ay in first_text:
#                     current_ay = ay
#                     break
            
#             # Hedef günü kontrol et
#             if current_gun != hedef_gun:
#                 continue
            
#             if hedef_ay and current_ay and current_ay != hedef_ay:
#                 continue
            
#             # Her etkinlik hücresini kontrol et
#             for idx, cell in enumerate(cells[1:], start=0):
#                 # act-line div'lerini bul (etkinlik kartları)
#                 act_lines = cell.find_all('div', class_='act-line')
                
#                 for act in act_lines:
#                     # Oyun adını al
#                     info_label = act.find('a', class_='info-label')
#                     if not info_label:
#                         continue
                    
#                     oyun_adi = info_label.get_text(strip=True)
#                     # Sahne adını temizle
#                     mobile_saloon = info_label.find('span', class_='mobile-saloon-name')
#                     if mobile_saloon:
#                         oyun_adi = oyun_adi.replace(mobile_saloon.get_text(), '').strip()
                    
#                     if not oyun_adi or len(oyun_adi) < 2:
#                         continue
                    
#                     # Seans bilgilerini al
#                     seances = act.find('div', class_='seances-list')
#                     if seances:
#                         buttons = seances.find_all('button')
#                         for btn in buttons:
#                             btn_text = btn.get_text(strip=True)
                            
#                             # Saat bilgisini çıkar
#                             saat_match = re.search(r'(\d{2}:\d{2})', btn_text)
#                             saat = saat_match.group(1) if saat_match else "20:00"
                            
#                             # Tükendi mi?
#                             tukendi = 'TÜKENDİ' in btn_text.upper()
#                             # veya style'dan kontrol et
#                             style = btn.get('style', '')
#                             if '#ff4061' in style or 'soldout' in ' '.join(act.get('class', [])):
#                                 tukendi = True
                            
#                             # Sahne adı
#                             sahne = sahneler[idx] if idx < len(sahneler) else "Devlet Tiyatrosu"
                            
#                             oyunlar.append({
#                                 'oyun': oyun_adi,
#                                 'sahne': sahne,
#                                 'saat': saat,
#                                 'tukendi': tukendi,
#                                 'bilet': 'biletinial.com'
#                             })
        
#         # Benzersiz oyunları döndür
#         seen = set()
#         unique = []
#         for o in oyunlar:
#             key = (o['oyun'], o['saat'], o['sahne'])
#             if key not in seen:
#                 seen.add(key)
#                 unique.append(o)
        
#         return unique
        
#     except Exception as e:
#         print(f"      ❌ Selenium hatası: {e}")
#         import traceback
#         traceback.print_exc()
#         return None
    
#     finally:
#         if driver:
#             driver.quit()

# def devlet_tiyatrolari_google_ara(sehir, tarih_formatli):
#     """Fallback: Google Search ile ara"""
#     prompt = f"""{sehir}'da {tarih_formatli} tarihinde DEVLET TİYATROLARI'nda hangi oyunlar var?
# SADECE {sehir}'daki sahneleri ve TAM OLARAK {tarih_formatli} tarihindeki oyunları listele.
# Format: • [Oyun] 📍 [Sahne] ⏰ [Saat] 🎫 biletinial.com"""
    
#     try:
#         response = client.models.generate_content(
#             model="gemini-2.0-flash-exp",
#             contents=prompt,
#             config=types.GenerateContentConfig(
#                 tools=[types.Tool(google_search=types.GoogleSearch())],
#                 temperature=0.1,
#             )
#         )
#         return response.text.strip()
#     except Exception as e:
#         return f"   ⚠️  Arama hatası: {e}"

# # ═══════════════════════════════════════════════════════════════
# # ÖZEL TİYATROLAR (Google Search)
# # ═══════════════════════════════════════════════════════════════

# def ozel_tiyatrolar_ara(sehir, tarih_formatli):
#     prompt = f"""{sehir}'da {tarih_formatli} tarihinde ÖZEL TİYATROLARDA hangi oyunlar var?
# DasDas, Zorlu PSM, Moda Sahnesi, Biletix, Passo ara. SADECE {tarih_formatli} tarihindeki oyunları listele."""
    
#     try:
#         response = client.models.generate_content(
#             model="gemini-2.0-flash-exp",
#             contents=prompt,
#             config=types.GenerateContentConfig(
#                 tools=[types.Tool(google_search=types.GoogleSearch())],
#                 temperature=0.1,
#             )
#         )
#         return response.text.strip()
#     except Exception as e:
#         return f"   ⚠️  Arama hatası: {e}"

# # ═══════════════════════════════════════════════════════════════
# # FORMATLAMA
# # ═══════════════════════════════════════════════════════════════

# def ibb_sonuc_formatla(oyunlar):
#     if not oyunlar:
#         return "   Bu tarihte oyun bulunamadı.\n"
#     sonuc = ""
#     for saat in ['15:00', '20:00']:
#         grup = [o for o in oyunlar if o['saat'] == saat]
#         if grup:
#             sonuc += f"\n   ⏰ Saat {saat}:\n"
#             for o in grup:
#                 durum = "❌ TÜKENDİ" if o['tukendi'] else "✅ Bilet Var"
#                 sonuc += f"      • {o['oyun']}\n        📍 {o['sahne']}\n        {durum}\n"
#     return sonuc

# def devlet_sonuc_formatla(oyunlar, tarih_str):
#     if not oyunlar:
#         return f"   {tarih_str} tarihinde oyun bulunamadı.\n"
#     sonuc = ""
#     for o in oyunlar:
#         durum = "❌ TÜKENDİ" if o['tukendi'] else "✅ Bilet Var"
#         sonuc += f"\n   • {o['oyun']}\n     📍 {o['sahne']}\n     ⏰ {o['saat']}\n     {durum}\n     🎫 {o['bilet']}\n"
#     return sonuc

# # ═══════════════════════════════════════════════════════════════
# # ANA PROGRAM
# # ═══════════════════════════════════════════════════════════════

# def main():
#     print("🎭 TİYATRO ARAMA v6 (Biletinial Doğru Selector)")
#     print("=" * 60)
    
#     sorgu = input("\n🔍 Ne arıyorsunuz?: ")
#     sehir, tarih = sorguyu_ayristir(sorgu)
#     hedef_gun = int(tarih.split('-')[2])
#     hedef_ay_num = int(tarih.split('-')[1])
#     aylar = ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
#              'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
#     hedef_ay = aylar[hedef_ay_num]
#     tarih_str = tarih_formatla(tarih)
    
#     print(f"\n📍 Şehir: {sehir}")
#     print(f"📅 Tarih: {tarih_str}")
    
#     # İBB (sadece İstanbul)
#     ibb_oyunlar = []
#     if sehir == "İstanbul":
#         print("\n" + "─" * 60)
#         print("1️⃣  İBB Şehir Tiyatroları aranıyor...")
#         ibb_oyunlar = ibb_sehir_tiyatrolari_ara(hedef_gun)
#         print(f"   ✅ {len(ibb_oyunlar)} oyun bulundu")
    
#     # Devlet Tiyatroları
#     print("\n" + "─" * 60)
#     print("2️⃣  Devlet Tiyatroları aranıyor... (Biletinial)")
#     devlet_oyunlar = biletinial_devlet_tiyatrolari_ara(sehir, hedef_gun, hedef_ay)
#     if devlet_oyunlar is None or len(devlet_oyunlar) == 0:
#         print("      ⚠️  Selenium başarısız veya veri yok, Google Search kullanılıyor...")
#         devlet_sonuc_text = devlet_tiyatrolari_google_ara(sehir, tarih_str)
#         devlet_oyunlar = []
#     else:
#         devlet_sonuc_text = None
#         print(f"   ✅ {len(devlet_oyunlar)} oyun bulundu")
    
#     # Özel Tiyatrolar
#     print("\n" + "─" * 60)
#     print("3️⃣  Özel Tiyatrolar aranıyor... (Google Search)")
#     ozel_sonuc = ozel_tiyatrolar_ara(sehir, tarih_str)
#     print("   ✅ Arama tamamlandı")
    
#     # Sonuçlar
#     print("\n" + "═" * 60)
#     print(f"🎭 {sehir} TİYATRO PROGRAMI - {tarih_str}")
#     print("═" * 60)
    
#     if sehir == "İstanbul":
#         print("\n┌" + "─" * 58 + "┐")
#         print("│ 📍 İBB ŞEHİR TİYATROLARI                                  │")
#         print("│    Kaynak: sehirtiyatrolari.ibb.istanbul                  │")
#         print("└" + "─" * 58 + "┘")
#         print(ibb_sonuc_formatla(ibb_oyunlar))
    
#     print("\n┌" + "─" * 58 + "┐")
#     print("│ 🏛️  DEVLET TİYATROLARI                                       │")
#     if devlet_sonuc_text:
#         print("│    Kaynak: Google Search                                  │")
#     else:
#         print("│    Kaynak: biletinial.com (Kesin Veri)                    │")
#     print("└" + "─" * 58 + "┘")
#     if devlet_sonuc_text:
#         print(devlet_sonuc_text)
#     else:
#         print(devlet_sonuc_formatla(devlet_oyunlar, tarih_str))
    
#     print("\n┌" + "─" * 58 + "┐")
#     print("│ 🎪 ÖZEL TİYATROLAR                                         │")
#     print("│    Kaynak: DasDas, Zorlu PSM, Biletix, Passo vb.          │")
#     print("└" + "─" * 58 + "┘")
#     print(ozel_sonuc)
    
#     print("\n┌" + "─" * 58 + "┐")
#     print("│ 🔗 FAYDALI LİNKLER                                         │")
#     print("└" + "─" * 58 + "┘")
#     print("   • Devlet Tiyatroları: https://biletinial.com/tr-tr/etkinlik-takvimi/708")
#     if sehir == "İstanbul":
#         print("   • İBB Şehir Tiyatroları: https://sehirtiyatrolari.ibb.istanbul/takvim")
#     print("   • Biletinial: https://www.biletinial.com")
    
#     print("\n" + "═" * 60)
#     print("✅ Arama tamamlandı!")

# if __name__ == "__main__":
#     main()
# ==================================================== *****************IBB OYUNLARININ SAHNE ISMI HEP AYNI, DEVLET TIYATROLARININ SONUCU IYI, OZEL TIYATOLARIN SONUCU IYI*********=================



# ===================================================================================================>> bir oncekii


# # src2/recommender_llm_an3.py - FİNAL DÜZELTİLMİŞ KOD (İBB için Gelişmiş Web Kazıma)
# """
# İBB Şehir Tiyatroları için gelişmiş web kazıma, diğerleri için Google Search API.

# KURULUM:
# pip install requests beautifulsoup4 google-genai
# """

# import os
# import re
# import requests
# from datetime import datetime
# from bs4 import BeautifulSoup
# import google.genai as genai
# from google.genai import types

# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# if not GOOGLE_API_KEY:
#     print("❌ GOOGLE_API_KEY ayarlanmalı!")
#     exit(1)

# client = genai.Client(api_key=GOOGLE_API_KEY)

# SEHIR_ID_MAP = {
#     'İstanbul': '5', 'Ankara': '3', 'İzmir': '24', 'Mersin': '85',
#     'Antalya': '23', 'Samsun': '43', 'Adana': '12', 'Bursa': '11',
#     'Denizli': '14', 'Diyarbakır': '10',
# }

# def sorguyu_ayristir(sorgu):
#     sehirler = {
#         'istanbul': 'İstanbul', 'ankara': 'Ankara', 'izmir': 'İzmir',
#         'bursa': 'Bursa', 'antalya': 'Antalya', 'mersin': 'Mersin',
#         'samsun': 'Samsun', 'adana': 'Adana', 'denizli': 'Denizli'
#     }
#     sorgu_lower = sorgu.lower()
#     sehir = "İstanbul"
#     for anahtar, deger in sehirler.items():
#         if anahtar in sorgu_lower:
#             sehir = deger
#             break
    
#     ay_sozluk = {'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4, 'mayıs': 5, 'haziran': 6,
#                  'temmuz': 7, 'ağustos': 8, 'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12}
    
#     yil_eslesme = re.search(r'(\d{4})', sorgu)
#     yil = yil_eslesme.group(1) if yil_eslesme else datetime.now().strftime("%Y")
#     tarih = datetime.now().strftime("%Y-%m-%d")
#     pattern = r'(\d{1,2})\s*(' + '|'.join(ay_sozluk.keys()) + r')'
#     eslesme = re.search(pattern, sorgu_lower)
#     if eslesme:
#         gun, ay_adi = eslesme.groups()
#         try:
#             tarih = f"{int(yil)}-{ay_sozluk[ay_adi]:02d}-{int(gun):02d}"
#         except:
#             pass
#     return sehir, tarih

# def tarih_formatla(tarih):
#     yil, ay, gun = tarih.split('-')
#     aylar = ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
#              'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
#     return f"{int(gun)} {aylar[int(ay)]} {yil}"

# # ═══════════════════════════════════════════════════════════════
# # İBB ŞEHİR TİYATROLARI (Gelişmiş Web Kazıma)
# # ═══════════════════════════════════════════════════════════════
# def ibb_sehir_tiyatrolari_ara(hedef_gun):
#     try:
#         url = "https://sehirtiyatrolari.ibb.istanbul/takvim"
#         headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
#         response = requests.get(url, headers=headers, timeout=15)
#         response.raise_for_status() # HTTP hatalarını kontrol et
#         soup = BeautifulSoup(response.content, 'html.parser')
        
#         oyunlar = []
#         table = soup.find('table')
#         if not table: return []
        
#         rows = table.find_all('tr')
#         sahneler = [th.text.strip() for th in rows[0].find_all('th')[3:]] if rows else []
        
#         current_date_val = None
#         current_saat = "Bilinmiyor" # Varsayılan saat

#         for row_index, row in enumerate(rows[1:]):
#             cells = row.find_all('td')
#             if not cells: continue

#             # Gün bilgisini içeren hücreyi işle
#             # Eğer ilk hücrede rowspan varsa veya 'day' sınıfı varsa bu yeni bir gün başlangıcıdır.
#             if cells[0].has_attr('rowspan') or 'day' in cells[0].get('class', []):
#                 day_text = cells[0].text.strip()
#                 if day_text.isdigit():
#                     current_date_val = int(day_text)
#                 # Saat hücresi, gün hücresi ile aynı satırda başlayabilir (genellikle 3. hücre)
#                 if len(cells) > 2 and re.match(r'^\d{2}:\d{2}$', cells[2].text.strip()):
#                     current_saat = cells[2].text.strip()
#                     oyun_hucre_baslangic_indexi = 3 # Oyun hücreleri 4.den başlar
#                 else:
#                     oyun_hucre_baslangic_indexi = 1 # Eğer saat yoksa, ilk hücreden sonra başlar
#             else:
#                 # Gün hücresi yoksa (rowspan devamı), saat hücresi genellikle 2. hücrededir (index 1)
#                 if len(cells) > 1 and re.match(r'^\d{2}:\d{2}$', cells[0].text.strip()):
#                  current_saat = cells[0].text.strip()
#                  oyun_hucre_baslangic_indexi = 1 # Oyun hücreleri 2.den başlar
#                 elif len(cells) > 1 and re.match(r'^\d{2}:\d{2}$', cells[1].text.strip()):
#                     current_saat = cells[1].text.strip()
#                     oyun_hucre_baslangic_indexi = 2
#                 else:
#                     oyun_hucre_baslangic_indexi = 0 # Saat bilgisi yoksa veya tanımsızsa ilk hücreden başla

#             if current_date_val != hedef_gun: continue

#             # Oyun hücrelerini gez
#             for idx, cell in enumerate(cells[oyun_hucre_baslangic_indexi:]):
#                 sahne_idx = idx
#                 if sahne_idx >= len(sahneler): continue
#                 sahne = sahneler[sahne_idx]

#                 links = cell.find_all('a')
#                 for link in links:
#                     oyun_adi = link.text.strip()
#                     if not oyun_adi or len(oyun_adi) < 3: continue
                    
#                     href = link.get('href', '')
#                     tukendi = 'TÜKENDİ' in cell.text
                    
#                     oyunlar.append({
#                         'oyun': oyun_adi, 'sahne': sahne, 'saat': current_saat,
#                         'tukendi': tukendi,
#                         'link': f"https://sehirtiyatrolari.ibb.istanbul{href}" if href.startswith('/') else href
#                     })
        
#         seen = set()
#         unique = []
#         for o in oyunlar:
#             key = (o['oyun'], o['saat'], o['sahne'])
#             if key not in seen:
#                 seen.add(key)
#                 unique.append(o)
#         return unique
#     except Exception as e:
#         print(f"   ⚠️  İBB Tiyatroları aranırken hata: {e}")
#         return []

# # ═══════════════════════════════════════════════════════════════
# # DEVLET TİYATROLARI - BİLETİNİAL (API) - Google Search ile değiştirildi
# # ═══════════════════════════════════════════════════════════════
# def biletinial_api_devlet_tiyatrolari_ara(sehir, tarih_formatli):
#     print("      🌐 Devlet Tiyatroları Google Search ile aranıyor...")
#     prompt = f"{sehir}'da {tarih_formatli} tarihinde DEVLET TİYATROLARI'nda hangi oyunlar var? SADECE {sehir}'daki sahneleri ve TAM OLARAK {tarih_formatli} tarihindeki oyunları listele. Format: • [Oyun] 📍 [Sahne] ⏰ [Saat] 🎫 biletinial.com"
#     try:
#         response = client.models.generate_content(
#             model="gemini-2.0-flash-exp",
#             contents=prompt,
#             config=types.GenerateContentConfig(
#                 tools=[types.Tool(google_search=types.GoogleSearch())],
#                 temperature=0.1,
#             )
#         )
#         return response.text.strip()
#     except Exception as e:
#         return f"   ⚠️  Arama hatası: {e}"


# # ═══════════════════════════════════════════════════════════════
# # ÖZEL TİYATROLAR (Google Search)
# # ═══════════════════════════════════════════════════════════════

# def ozel_tiyatrolar_ara(sehir, tarih_formatli):
#     print("      🌐 Özel Tiyatrolar Google Search ile aranıyor...")
#     prompt = f"{sehir}'da {tarih_formatli} tarihinde ÖZEL TİYATROLARDA hangi oyunlar var? DasDas, Zorlu PSM, Moda Sahnesi, Biletix, Passo ara. SADECE {tarih_formatli} tarihindeki oyunları listele. Format: • [Oyun] 📍 [Tiyatro adı] ⏰ [Saat] 🎫 [Bilet linki varsa]"
#     try:
#         response = client.models.generate_content(
#             model="gemini-2.0-flash-exp",
#             contents=prompt,
#             config=types.GenerateContentConfig(
#                 tools=[types.Tool(google_search=types.GoogleSearch())],
#                 temperature=0.1,
#             )
#         )
#         return response.text.strip()
#     except Exception as e:
#         return f"   ⚠️  Arama hatası: {e}"

# # ═══════════════════════════════════════════════════════════════
# # FORMATLAMA
# # ═══════════════════════════════════════════════════════════════
# def ibb_sonuc_formatla(oyunlar):
#     if not oyunlar: return "   Bu tarihte oyun bulunamadı.\n"
#     sonuc, saat_gruplari = "", {}
#     oyunlar.sort(key=lambda x: x['saat'])
#     for o in oyunlar: saat_gruplari.setdefault(o['saat'], []).append(o)
#     for saat, grup in saat_gruplari.items():
#         sonuc += f"\n   ⏰ Saat {saat}:\n"
#         for o in grup:
#             durum = "❌ TÜKENDİ" if o['tukendi'] else "✅ Bilet Var"
#             sonuc += f"      • {o['oyun']}\n        📍 {o['sahne']}\n        {durum}\n"
#     return sonuc

# def devlet_sonuc_formatla(oyunlar, tarih_str):
#     if not oyunlar: return f"   {tarih_str} tarihinde Devlet Tiyatroları programında oyun bulunamadı.\n"
#     sonuc = ""
#     oyunlar.sort(key=lambda x: x['saat'])
#     for o in oyunlar:
#         durum = "❌ TÜKENDİ" if o['tukendi'] else "✅ Bilet Var"
#         sonuc += f"\n   • {o['oyun']}\n     📍 {o['sahne']}\n     ⏰ {o['saat']}\n     {durum}\n     🎫 {o['bilet']}\n"
#     return sonuc

# # ═══════════════════════════════════════════════════════════════
# # ANA PROGRAM
# # ═══════════════════════════════════════════════════════════════

# def main():
#     print("🎭 TİYATRO ARAMA v12 (İBB için Gelişmiş Web Kazıma)")
#     print("=" * 60)
#     sorgu = input("\n🔍 Ne arıyorsunuz?: ")
#     sehir, tarih = sorguyu_ayristir(sorgu)
#     hedef_gun = int(tarih.split('-')[2])
#     tarih_str = tarih_formatla(tarih)
#     print(f"\n📍 Şehir: {sehir}\n📅 Tarih: {tarih_str}")
    
#     # İBB Şehir Tiyatroları (Gelişmiş Kazıma)
#     print("\n" + "─" * 60 + "\n1️⃣  İBB Şehir Tiyatroları aranıyor...")
#     ibb_oyunlar = ibb_sehir_tiyatrolari_ara(hedef_gun)
#     print(f"   ✅ {len(ibb_oyunlar)} oyun bulundu")
    
#     # Devlet Tiyatroları (Google Search)
#     print("\n" + "─" * 60 + "\n2️⃣  Devlet Tiyatroları aranıyor... (Google Search)")
#     devlet_sonuc = biletinial_api_devlet_tiyatrolari_ara(sehir, tarih_str)
#     print("   ✅ Arama tamamlandı")
    
#     # Özel Tiyatrolar (Google Search)
#     print("\n" + "─" * 60 + "\n3️⃣  Özel Tiyatrolar aranıyor... (Google Search)")
#     ozel_sonuc = ozel_tiyatrolar_ara(sehir, tarih_str)
#     print("   ✅ Arama tamamlandı")
    
#     print("\n" + "═" * 60 + f"\n🎭 {sehir} TİYATRO PROGRAMI - {tarih_str}\n" + "═" * 60)
    
#     # İBB Sonuçları
#     print("\n┌" + "─" * 58 + "┐\n│ 📍 İBB ŞEHİR TİYATROLARI                                  │\n│    Kaynak: sehirtiyatrolari.ibb.istanbul (Kazıma)         │\n└" + "─" * 58 + "┘")
#     print(ibb_sonuc_formatla(ibb_oyunlar))
    
#     # Devlet Tiyatroları Sonuçları
#     print("\n┌" + "─" * 58 + "┐\n│ 🏛️  DEVLET TİYATROLARI                                       │\n│    Kaynak: Google Search                                  │\n└" + "─" * 58 + "┘")
#     print(devlet_sonuc)
    
#     # Özel Tiyatrolar Sonuçları
#     print("\n┌" + "─" * 58 + "┐\n│ 🎪 ÖZEL TİYATROLAR                                         │\n│    Kaynak: Google Search                                  │\n└" + "─" * 58 + "┘")
#     print(ozel_sonuc)
    
#     print("\n┌" + "─" * 58 + "┐\n│ 🔗 FAYDALI LİNKLER                                         │\n└" + "─" * 58 + "┘")
#     print("   • İBB Şehir Tiyatroları: https://sehirtiyatrolari.ibb.istanbul/takvim")
#     print("   • Devlet Tiyatroları: https://biletinial.com/tr-tr/etkinlik-takvimi/708")
#     print("   • Biletinial: https://www.biletinial.com")
    
#     print("\n" + "═" * 60 + "\n✅ Arama tamamlandı!")

# if __name__ == "__main__":
#     main()