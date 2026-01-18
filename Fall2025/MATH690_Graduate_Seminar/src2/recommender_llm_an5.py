"""
StageAgent v5 - Google Calendar Entegrasyonu + Çoklu Sorgu
(ACİL DÜZELTME: Cache YOK, Disk dolu!)
"""

import os
import re
import requests
import time
import sys
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

print("\n" + "="*70)
print("🎭 STAGEAGENT v5 - Google Takvim + Çoklu Sorgu")
print("⚠️  ACİL MOD: Disk dolu - Cache kullanılmıyor!")
print("="*70)

# ═══════════════════════════════════════════════════════════════
# IMPORT'LAR - BASİT HATA KONTROLÜ
# ═══════════════════════════════════════════════════════════════

# 1. Google Calendar imports
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    import pickle
    GCAL_AVAILABLE = True
    print("   ✅ Google Calendar kütüphaneleri hazır")
except ImportError as e:
    GCAL_AVAILABLE = False
    print(f"   ⚠️  Google Calendar yok: {e}")

# 2. Gemini imports - ZORUNLU
try:
    import google.genai as genai
    from google.genai import types
    GEMINI_AVAILABLE = True
    print("   ✅ Gemini kütüphaneleri hazır")
except ImportError as e:
    GEMINI_AVAILABLE = False
    print(f"   ❌ Gemini yok: {e}")
    sys.exit(1)

# 3. Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
    print("   ✅ Selenium kütüphaneleri hazır")
except ImportError as e:
    SELENIUM_AVAILABLE = False
    print(f"   ⚠️  Selenium yok: {e}")

# ═══════════════════════════════════════════════════════════════
# YAPILANDIRMA - CACHE YOK!
# ═══════════════════════════════════════════════════════════════

# API Key kontrolü
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("\n🔑 GOOGLE_API_KEY bulunamadı!")
    GOOGLE_API_KEY = input("   Lütfen API Key girin: ").strip()
    if not GOOGLE_API_KEY:
        print("❌ API Key gerekiyor!")
        sys.exit(1)

print(f"   ✅ API Key kullanılıyor: {GOOGLE_API_KEY[:10]}...")

# Client oluştur
try:
    client = genai.Client(api_key=GOOGLE_API_KEY)
    print("   ✅ Gemini API bağlantısı kuruldu")
except Exception as e:
    print(f"   ❌ Gemini bağlantı hatası: {e}")
    sys.exit(1)

# Google Calendar API scope
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Şehir -> Biletinial data-val
SEHIR_ID_MAP = {
    'İstanbul': '5', 'Ankara': '3', 'İzmir': '24', 'Mersin': '85',
    'Antalya': '23', 'Samsun': '43', 'Adana': '12', 'Bursa': '11',
    'Denizli': '14', 'Diyarbakır': '10',
}

print("\n" + "="*70)
print("🚀 SİSTEM HAZIR - Cache OLMADAN çalışacak")
print("="*70)

# ═══════════════════════════════════════════════════════════════
# GOOGLE TAKVİM FONKSİYONLARI
# ═══════════════════════════════════════════════════════════════

def get_calendar_service():
    """Google Calendar API servisini başlat"""
    if not GCAL_AVAILABLE:
        return None
    
    creds = None
    
    # Token varsa yükle
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # Token yoksa veya geçersizse yenile
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # credentials.json dosyası gerekli
            if not os.path.exists('credentials.json'):
                print("\n⚠️  credentials.json dosyası bulunamadı!")
                print("   Google Cloud Console'dan OAuth credentials indirin.")
                print("   https://console.cloud.google.com/apis/credentials")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Token'ı kaydet
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('calendar', 'v3', credentials=creds)

def add_to_google_calendar(oyun, tarih_str, sehir):
    """
    Seçilen oyunu Google Takvim'e ekle
    
    Args:
        oyun: dict with keys: oyun, sahne, saat, tukendi, link/bilet
        tarih_str: "22 Ocak 2026" formatında tarih
        sehir: "İstanbul" gibi şehir adı
    
    Returns:
        (success: bool, message: str)
    """
    service = get_calendar_service()
    if not service:
        return False, "Google Calendar bağlantısı kurulamadı"
    
    try:
        # Tarihi parse et
        aylar = {'Ocak': 1, 'Şubat': 2, 'Mart': 3, 'Nisan': 4, 'Mayıs': 5, 'Haziran': 6,
                 'Temmuz': 7, 'Ağustos': 8, 'Eylül': 9, 'Ekim': 10, 'Kasım': 11, 'Aralık': 12}
        
        parts = tarih_str.split()
        gun = int(parts[0])
        ay = aylar.get(parts[1], 1)
        yil = int(parts[2])
        
        # Saat bilgisini parse et
        saat_str = oyun.get('saat', '20:00')
        saat_parts = saat_str.split(':')
        saat = int(saat_parts[0])
        dakika = int(saat_parts[1]) if len(saat_parts) > 1 else 0
        
        # Başlangıç ve bitiş zamanları
        start_dt = datetime(yil, ay, gun, saat, dakika)
        end_dt = start_dt + timedelta(hours=2)  # Ortalama 2 saat
        
        # Event oluştur
        event = {
            'summary': f"🎭 {oyun['oyun']}",
            'location': f"{oyun.get('sahne', 'Bilinmiyor')}, {sehir}",
            'description': f"""Tiyatro Oyunu: {oyun['oyun']}
Sahne: {oyun.get('sahne', 'Bilinmiyor')}
Şehir: {sehir}
Saat: {saat_str}
Bilet: {oyun.get('link', oyun.get('bilet', 'Bilinmiyor'))}

🎫 StageAgent tarafından eklendi""",
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'Europe/Istanbul',
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'Europe/Istanbul',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 60},  # 1 saat önce
                    {'method': 'popup', 'minutes': 1440},  # 1 gün önce
                ],
            },
        }
        
        # Takvime ekle
        event = service.events().insert(calendarId='primary', body=event).execute()
        
        return True, f"✅ Takvime eklendi! Link: {event.get('htmlLink')}"
        
    except Exception as e:
        return False, f"❌ Hata: {e}"

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
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

# ═══════════════════════════════════════════════════════════════
# KAYNAK FONKSİYONLARI
# ═══════════════════════════════════════════════════════════════

def ibb_sehir_tiyatrolari_ara(hedef_gun):
    """İBB Şehir Tiyatroları takviminden veri çek"""
    try:
        url = "https://sehirtiyatrolari.ibb.istanbul/takvim"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        oyunlar = []
        table = soup.find('table', class_='yn_calendar-table')
        if not table:
            table = soup.find('table')
        if not table:
            return []
        
        # Header'dan sahne isimlerini al
        sahneler = []
        thead = table.find('thead')
        if thead:
            header_row = thead.find('tr')
            if header_row:
                header_cells = header_row.find_all(['th', 'td'])
                for cell in header_cells[3:]:
                    text = cell.get_text(strip=True)
                    if text:
                        sahneler.append(text)
        
        # Tbody'den verileri al
        tbody = table.find('tbody', class_='yn_calendar_list')
        if not tbody:
            tbody = table.find('tbody') or table
        
        rows = tbody.find_all('tr')
        current_date = None
        current_saat = None
        
        for row in rows:
            cells = row.find_all('td')
            if not cells:
                continue
            
            day_cell = row.find('td', class_='yn_calendar_day')
            if day_cell:
                day_text = day_cell.get_text(strip=True)
                if day_text.isdigit():
                    current_date = int(day_text)
            
            time_cell = row.find('td', class_='yn_calendar_time')
            if time_cell:
                time_text = time_cell.get_text(strip=True)
                if re.match(r'^\d{2}:\d{2}$', time_text):
                    current_saat = time_text
            
            if current_date != hedef_gun:
                continue
            
            skip_count = 0
            for cell in cells:
                cell_class = cell.get('class', [])
                if any(c in cell_class for c in ['yn_calendar_day', 'yn_calendar_date', 'yn_calendar_time']):
                    skip_count += 1
                else:
                    break
            
            oyun_hucreleri = cells[skip_count:]
            
            for idx, cell in enumerate(oyun_hucreleri):
                sahne = sahneler[idx] if idx < len(sahneler) else f"Sahne {idx + 1}"
                links = cell.find_all('a')
                for link in links:
                    oyun_adi = link.get_text(strip=True)
                    if not oyun_adi or len(oyun_adi) < 3:
                        continue
                    href = link.get('href', '')
                    tukendi_span = cell.find('span', class_='yn_tukendi')
                    tukendi = tukendi_span is not None
                    
                    oyunlar.append({
                        'oyun': oyun_adi,
                        'sahne': sahne,
                        'saat': current_saat or '20:00',
                        'tukendi': tukendi,
                        'link': f"https://sehirtiyatrolari.ibb.istanbul{href}" if href.startswith('/') else href,
                        'kaynak': 'İBB Şehir Tiyatroları'
                    })
        
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
        return []

def biletinial_devlet_tiyatrolari_ara(sehir, hedef_gun, hedef_ay):
    """Biletinial'dan Selenium ile Devlet Tiyatroları verisi çek"""
    if not SELENIUM_AVAILABLE:
        return None
    
    driver = None
    oyunlar = []
    
    try:
        driver = get_chrome_driver()
        driver.get("https://biletinial.com/tr-tr/etkinlik-takvimi/708")
        wait = WebDriverWait(driver, 15)
        time.sleep(4)
        
        # Şehir seçimi
        sehir_id = SEHIR_ID_MAP.get(sehir, '5')
        try:
            city_selector = wait.until(EC.element_to_be_clickable((By.ID, "citySelector")))
            driver.execute_script("arguments[0].click();", city_selector)
            time.sleep(1)
            city_option = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, f"#customCitySelect .scrollList ul li[data-val='{sehir_id}']")
            ))
            driver.execute_script("arguments[0].click();", city_option)
            time.sleep(4)
        except:
            pass
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        tables = soup.find_all('table', class_='bltn-table')
        table = tables[-1] if tables else None
        if not table:
            return []
        
        # Sahneleri al
        sahneler = []
        thead = table.find('thead')
        if thead:
            header_row = thead.find('tr')
            if header_row:
                ths = header_row.find_all('th')
                for th in ths:
                    aria_label = th.get('aria-label', '')
                    sahne_adi = aria_label.strip() if aria_label else th.get_text(separator=' ', strip=True)
                    sahne_adi = re.sub(r'\s+', ' ', sahne_adi).strip()
                    if sahne_adi and len(sahne_adi) > 2 and 'data-min' not in str(th):
                        sahneler.append(sahne_adi)
        
        tbody = table.find('tbody') or table
        rows = tbody.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            if not cells:
                continue
            
            first_cell = cells[0]
            first_text = first_cell.get_text(strip=True)
            
            gun_match = re.search(r'^(\d{1,2})', first_text)
            if not gun_match:
                continue
            
            current_gun = int(gun_match.group(1))
            current_ay = None
            for ay in ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 
                       'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']:
                if ay in first_text:
                    current_ay = ay
                    break
            
            if current_gun != hedef_gun:
                continue
            if hedef_ay and current_ay and current_ay != hedef_ay:
                continue
            
            for idx, cell in enumerate(cells[1:]):
                act_lines = cell.find_all('div', class_=lambda x: x and 'act-line' in x)
                
                for act in act_lines:
                    info_label = act.find('a', class_='info-label')
                    if not info_label:
                        continue
                    
                    oyun_adi = info_label.get_text(strip=True)
                    mobile_saloon = info_label.find('span', class_='mobile-saloon-name')
                    if mobile_saloon:
                        oyun_adi = oyun_adi.replace(mobile_saloon.get_text(), '').strip()
                    
                    if not oyun_adi or len(oyun_adi) < 2:
                        continue
                    
                    sahne = sahneler[idx] if idx < len(sahneler) else "Devlet Tiyatrosu"
                    
                    seances = act.find('div', class_='seances-list')
                    if seances:
                        buttons = seances.find_all('button')
                        for btn in buttons:
                            btn_text = btn.get_text(strip=True)
                            saat_match = re.search(r'(\d{2}:\d{2})', btn_text)
                            saat = saat_match.group(1) if saat_match else "20:00"
                            tukendi = 'TÜKENDİ' in btn_text.upper()
                            
                            oyunlar.append({
                                'oyun': oyun_adi,
                                'sahne': sahne,
                                'saat': saat,
                                'tukendi': tukendi,
                                'bilet': 'biletinial.com',
                                'kaynak': 'Devlet Tiyatroları'
                            })
        
        seen = set()
        unique = []
        for o in oyunlar:
            key = (o['oyun'], o['saat'], o['sahne'])
            if key not in seen:
                seen.add(key)
                unique.append(o)
        return unique
        
    except Exception as e:
        return None
    finally:
        if driver:
            driver.quit()

def devlet_tiyatrolari_google_ara(sehir, tarih_formatli):
    """Fallback: Google Search"""
    prompt = f"{sehir}'da {tarih_formatli} tarihinde DEVLET TİYATROLARI'nda hangi oyunlar var? SADECE bu tarih ve şehirdeki oyunları, mekan ve saat bilgileriyle listele."
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.1,
            )
        )
        
        gemini_text = response.text.strip()
        # Aynı parsing fonksiyonunu kullan
        oyunlar = parse_gemini_response(gemini_text)
        
        # Devlet tiyatrosu bilgilerini güncelle
        for oyun in oyunlar:
            oyun['kaynak'] = 'Devlet Tiyatroları (Gemini)'
            oyun['bilet'] = 'biletinial.com'
            
        return oyunlar
        
    except Exception as e:
        print(f"   ⚠️  Arama hatası: {e}")
        return []

def parse_gemini_response(gemini_text):
    """Gemini yanıtını parse edip oyun listesi oluştur"""
    if not gemini_text or "Arama hatası" in gemini_text:
        return []
    
    oyunlar = []
    lines = gemini_text.strip().split('\n')
    
    current_sahne = "Özel Tiyatro"
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Boş satırları atla
        if not line or len(line) < 2:
            continue
        
        # 1. MEKAN/Sahne adı bulma
        sahne_keywords = [
            'Kültür Merkezi', 'PSM', 'Sahnesi', 'DasDas', 'CKM', 'BKM', 'Hall',
            'Cambazhane', 'Merkezi', 'Salonu', 'Tiyatrosu', 'Stage', 'Theatre'
        ]
        
        is_sahne_line = (
            (line.endswith(':') and 5 < len(line) < 50) or
            ('**' in line and line.count('**') >= 2 and len(line) < 60) or
            any(keyword in line for keyword in sahne_keywords)
        )
        
        # Geçersiz sahne başlangıçları
        invalid_sahne_starts = ['http', 'www.', 'İBB', 'Devlet', 'Olası', 'Kesin', 'Liste']
        
        if is_sahne_line and not any(line.startswith(start) for start in invalid_sahne_starts):
            # Mekan adını temizle
            sahne = line.replace('**', '').replace('*', '').replace(':', '').strip()
            sahne = re.sub(r'\(.*?\)', '', sahne).strip()
            
            if 3 < len(sahne) < 50:
                current_sahne = sahne
                continue
        
        # 2. OYUN satırı ara
        invalid_patterns = [
            'http://', 'https://', 'www.', '.com', '.tr', '.gen.tr',
            'Not:', 'Dipnot:', 'Kaynak:', 'Dikkat:', 'Önemli:', 'Olası',
            'Kesin program', 'kontrol edin', 'tarihinde', 'İBB Şehir Tiyatroları',
            'Devlet Tiyatroları', 'SADECE', 'LÜTFEN', 'bilgisi belirtilmemiş',
            'olası oyunlar', 'için kontrol', 'program için'
        ]
        
        line_lower = line.lower()
        if any(pattern.lower() in line_lower for pattern in invalid_patterns):
            continue
        
        # Geçerli oyun adı mı kontrol et
        list_markers = ['•', '*', '-', '○', '▪', '‣']
        has_list_marker = any(line.startswith(marker) for marker in list_markers)
        
        has_number = re.match(r'^\d+[\.\)]\s+', line)
        
        looks_like_real_oyun = (
            5 < len(line) < 70 and
            re.match(r'^[A-ZÇĞİÖŞÜ]', line) and
            not line.endswith(':') and
            not any(word in line_lower for word in ['.com', 'www', 'http']) and
            len(re.findall(r'\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]+\b', line)) >= 1
        )
        
        if has_list_marker or has_number or looks_like_real_oyun:
            # Satırı temizle
            cleaned_line = line
            
            # Liste işaretlerini kaldır
            for marker in list_markers:
                if cleaned_line.startswith(marker):
                    cleaned_line = cleaned_line[len(marker):].strip()
                    break
            
            # Numaraları kaldır
            cleaned_line = re.sub(r'^\d+[\.\)]\s+', '', cleaned_line)
            
            # Markdown formatlarını temizle
            cleaned_line = cleaned_line.replace('**', '').replace('*', '').replace('__', '').replace('_', '')
            
            # Oyun adını ve saat bilgisini ayır
            oyun_adi = cleaned_line
            saat = "20:00"
            
            # "- Saat" formatını ara
            if ' - ' in oyun_adi:
                parts = oyun_adi.split(' - ')
                oyun_adi = parts[0].strip()
                if len(parts) > 1:
                    last_part = parts[-1].strip()
                    saat_match = re.search(r'(\d{1,2}[\.:]\d{2})', last_part)
                    if saat_match:
                        saat = saat_match.group(1).replace('.', ':')
            
            # Saat bilgisini ara (genel)
            saat_match = re.search(r'(\d{1,2}[\.:]\d{2})', oyun_adi)
            if saat_match:
                saat = saat_match.group(1).replace('.', ':')
                oyun_adi = re.sub(r'\s*\d{1,2}[\.:]\d{2}.*', '', oyun_adi).strip()
            
            # "Saat:" formatını temizle
            oyun_adi = re.sub(r'[Ss]aat\s*:?\s*\d{1,2}[\.:]\d{2}.*', '', oyun_adi)
            
            # Fazladan boşlukları temizle
            oyun_adi = re.sub(r'\s+', ' ', oyun_adi).strip()
            
            # Özel karakterleri temizle
            oyun_adi = re.sub(r'[\[\]()]', '', oyun_adi)
            
            # Geçersiz başlangıç/bitişleri kontrol et
            invalid_starts = ['İBB', 'Devlet', 'Olası', 'Kesin', 'Program', 'Kontrol']
            invalid_ends = ['.com', '.tr', 'edin', 'için']
            
            has_invalid_start = any(oyun_adi.startswith(start) for start in invalid_starts)
            has_invalid_end = any(oyun_adi.endswith(end) for end in invalid_ends)
            
            # Sahne adını temizle
            temiz_sahne = current_sahne
            if any(word in temiz_sahne.lower() for word in ['.com', '.tr', 'tiyatrolar', 'gen.tr']):
                temiz_sahne = "Özel Tiyatro"
            
            # Oyun adı geçerli mi kontrol et
            if (oyun_adi and 
                5 <= len(oyun_adi) <= 60 and
                not has_invalid_start and
                not has_invalid_end and
                not any(word in oyun_adi.lower() for word in ['.com', 'www', 'http', 'olası', 'kesin']) and
                re.search(r'[a-zA-ZÇĞİÖŞÜçğıöşü]{3,}', oyun_adi)):
                
                # Tükendi kontrolü
                tukendi = any(word in line.upper() for word in ['TÜKENDİ', 'BİTTİ', 'SOLD OUT', 'SATIŞTA DEĞİL'])
                
                oyunlar.append({
                    'oyun': oyun_adi,
                    'sahne': temiz_sahne,
                    'saat': saat,
                    'tukendi': tukendi,
                    'bilet': 'Biletix/Passo',
                    'kaynak': 'Özel Tiyatrolar'
                })
    
    # Benzersiz oyunları seç
    seen = set()
    unique_oyunlar = []
    
    for oyun in oyunlar:
        key = re.sub(r'\s+', '', oyun['oyun'].lower())[:25]
        if key not in seen:
            seen.add(key)
            unique_oyunlar.append(oyun)
    
    # İBB ve Devlet tiyatrolarındaki oyunları filtrele
    ibb_oyun_keywords = ['Haramiler', 'Yoldan Çıkan Oyun', 'Çingene Boksör', 
                         'Geçmişin Gölgesi', 'Öksüzler', 'Maviydi Bisikletim', 'Gölge']
    
    devlet_oyun_keywords = ['VANYA DAYI', 'Vanya Dayı', 'CALLBACK', 'KÜÇÜK BİR İŞ İÇİN YAŞLI BİR PALYAÇO ARANIYOR',
                           'Küçük Bir İş İçin Yaşlı Bir Palyaço Aranıyor']
    
    final_oyunlar = []
    for oyun in unique_oyunlar:
        oyun_adi = oyun['oyun']
        # İBB ve Devlet tiyatrosu oyunlarını atla
        if any(keyword.lower() in oyun_adi.lower() for keyword in ibb_oyun_keywords + devlet_oyun_keywords):
            continue
        
        # Geçersiz mekanları kontrol et
        if any(word in oyun['sahne'].lower() for word in ['.com', '.tr', 'tiyatrolar']):
            oyun['sahne'] = "Özel Tiyatro"
        
        final_oyunlar.append(oyun)
    
    return final_oyunlar[:10]

def ozel_tiyatrolar_ara(sehir, tarih_formatli):
    """Özel tiyatroları Google Search ile ara"""
    prompt = f"""
{sehir}'da {tarih_formatli} tarihinde ÖZEL TİYATROLARDA hangi oyunlar var?

ÖNEMLİ MEKANLAR:
• AKM (Atatürk Kültür Merkezi)
• Akatlar Kültür Merkezi
• Zorlu PSM - Turkcell Platinum Sahnesi  
• Zorlu PSM - % 100 Studio
• Zorlu PSM - Touché
• Kanyon Cambazhane
• DasDas
• Moda Sahnesi - Büyük Sahne
• BKM (Beşiktaş Kültür Merkezi)
• CKM (Caddebostan Kültür Merkezi)

ÇOK ÖNEMLİ KURALLAR:
1. SADECE OYUN ADLARINI ve SAAT BİLGİLERİNİ VER
2. URL, link, site adı, ".com", ".tr" KESİNLİKLE YAZMA
3. "İBB", "Devlet Tiyatroları", "olası oyunlar", "kontrol edin" gibi ifadeler KULLANMA
4. SADECE gerçek özel tiyatro oyunlarını listele

FORMAT ŞÖYLE OLSUN:
**Akatlar Kültür Merkezi:**
• 39 Buçuk Basamak - 20:30
• Korkusuz Salyangoz - 13:00

**Zorlu PSM:**
• Afife - 20:00

**Küçükçiftlik Park:**
• Aşk Biter Mi? - 20:30

**Kanyon Cambazhane:**
• Süper Patates ve Kaçak Bezelye - 13:00

SADECE {tarih_formatli} tarihindeki oyunları listele.
Her oyun için saat bilgisi mutlaka olsun.
"""
    
    try:
        print(f"   🔍 Gemini'ye soruluyor: {sehir} {tarih_formatli}")
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.1,
                max_output_tokens=800,
            )
        )
        
        gemini_text = response.text.strip()
        print(f"   📝 Gemini yanıtı aldı ({len(gemini_text)} karakter)")
        
        # Parse et
        oyunlar = parse_gemini_response(gemini_text)
        
        return oyunlar
        
    except Exception as e:
        print(f"   ⚠️  Arama hatası: {e}")
        return []

def tum_oyunlari_listele(ibb_oyunlar, devlet_oyunlar, ozel_oyunlar, tarih_str, sehir):
    """Tüm oyunları numaralı liste olarak göster"""
    tum_oyunlar = []
    
    print("\n" + "═" * 60)
    print(f"🎭 {sehir} TİYATRO PROGRAMI - {tarih_str}")
    print("═" * 60)
    
    numara = 1
    
    # İBB Şehir Tiyatroları
    if ibb_oyunlar:
        print("\n┌" + "─" * 58 + "┐")
        print("│ 📍 İBB ŞEHİR TİYATROLARI                                  │")
        print("└" + "─" * 58 + "┘")
        
        for o in ibb_oyunlar:
            durum = "❌ TÜKENDİ" if o['tukendi'] else "✅ Bilet Var"
            print(f"\n   [{numara}] {o['oyun']}")
            print(f"       📍 {o['sahne']}")
            print(f"       ⏰ {o['saat']}  {durum}")
            tum_oyunlar.append(o)
            numara += 1
    
    # Devlet Tiyatroları
    if devlet_oyunlar:
        print("\n┌" + "─" * 58 + "┐")
        print("│ 🏛️  DEVLET TİYATROLARI                                     │")
        print("└" + "─" * 58 + "┘")
        
        for o in devlet_oyunlar:
            durum = "❌ TÜKENDİ" if o['tukendi'] else "✅ Bilet Var"
            print(f"\n   [{numara}] {o['oyun']}")
            print(f"       📍 {o['sahne']}")
            print(f"       ⏰ {o['saat']}  {durum}")
            tum_oyunlar.append(o)
            numara += 1
    
    # Özel Tiyatrolar
    if ozel_oyunlar:
        print("\n┌" + "─" * 58 + "┐")
        print("│ 🎪 ÖZEL TİYATROLAR                                         │")
        print("│    Kaynak: DasDas, Zorlu PSM, Biletix, Passo vb.          │")
        print("└" + "─" * 58 + "┘")
        
        for o in ozel_oyunlar:
            durum = "❌ TÜKENDİ" if o['tukendi'] else "✅ Bilet Var"
            print(f"\n   [{numara}] {o['oyun']}")
            print(f"       📍 {o['sahne']}")
            print(f"       ⏰ {o['saat']}  {durum}")
            tum_oyunlar.append(o)
            numara += 1
    
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
    
    return tum_oyunlar

def sorgu_yap(sorgu):
    """Tek bir sorgu yap ve sonuçları göster"""
    sehir, tarih = sorguyu_ayristir(sorgu)
    hedef_gun = int(tarih.split('-')[2])
    hedef_ay_num = int(tarih.split('-')[1])
    aylar = ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
             'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
    hedef_ay = aylar[hedef_ay_num]
    tarih_str = tarih_formatla(tarih)
    
    print(f"\n📍 Şehir: {sehir}")
    print(f"📅 Tarih: {tarih_str}")
    
    # Kaynakları ara
    print("\n" + "─" * 60)
    print("1️⃣  İBB Şehir Tiyatroları aranıyor...")
    ibb_oyunlar = ibb_sehir_tiyatrolari_ara(hedef_gun) if sehir == "İstanbul" else []
    print(f"   ✅ {len(ibb_oyunlar)} oyun bulundu")
    
    print("\n" + "─" * 60)
    print("2️⃣  Devlet Tiyatroları aranıyor...")
    devlet_oyunlar = biletinial_devlet_tiyatrolari_ara(sehir, hedef_gun, hedef_ay)
    
    # Selenium başarısız olursa Gemini'yi kullan
    if not devlet_oyunlar or len(devlet_oyunlar) == 0:
        print("   ⚠️  Selenium başarısız, Gemini ile aranıyor...")
        devlet_oyunlar = devlet_tiyatrolari_google_ara(sehir, tarih_str)
    
    print(f"   ✅ {len(devlet_oyunlar)} oyun bulundu")
    
    print("\n" + "─" * 60)
    print("3️⃣  Özel Tiyatrolar aranıyor... (Google Search)")
    ozel_oyunlar = ozel_tiyatrolar_ara(sehir, tarih_str)
    print(f"   ✅ {len(ozel_oyunlar)} oyun bulundu")
    
    # Tüm oyunları listele
    tum_oyunlar = tum_oyunlari_listele(ibb_oyunlar, devlet_oyunlar, ozel_oyunlar, tarih_str, sehir)
    
    print("\n" + "═" * 60)
    print("✅ Arama tamamlandı!")
    
    return tum_oyunlar, sehir, tarih_str

def takvim_islemleri(tum_oyunlar, sehir, tarih_str):
    """Google Takvim işlemlerini yönet"""
    if not tum_oyunlar:
        print("\n⚠️  Bu tarihte oyun bulunamadı.")
        return False
    
    # ═══════════════════════════════════════════════════════════════
    # GOOGLE TAKVİM ENTEGRASYONU
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "═" * 60)
    print("📅 GOOGLE TAKVİM'E EKLEME")
    print("═" * 60)
    
    if not GCAL_AVAILABLE:
        print("\n⚠️  Google Calendar kütüphaneleri kurulu değil.")
        print("   pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        return False
    
    while True:
        print("\n💡 Takvime eklemek istediğiniz oyunun numarasını girin")
        print("   (Birden fazla için virgülle ayırın: 1,3,5)")
        print("   (Takvim eklemeden çıkmak için 'q' veya 'çık' yazın)")
        print("   (Ana menüye dönmek için 'ana' yazın)")
        
        secim = input("\n🎫 Seçiminiz: ").strip().lower()
        
        if secim in ['q', 'çık', 'cik', 'exit', '']:
            print("\n👋 Takvim ekleme tamamlandı!")
            return False
        elif secim == 'ana':
            print("\n🏠 Ana menüye dönülüyor...")
            return True
        
        try:
            # Virgülle ayrılmış numaraları parse et
            numaralar = [int(n.strip()) for n in secim.split(',')]
            
            for numara in numaralar:
                if 1 <= numara <= len(tum_oyunlar):
                    oyun = tum_oyunlar[numara - 1]
                    
                    if oyun['tukendi']:
                        print(f"\n⚠️  [{numara}] {oyun['oyun']} - Biletler tükenmiş!")
                        devam = input("   Yine de takvime eklemek ister misiniz? (e/h): ")
                        if devam.lower() not in ['e', 'evet', 'y', 'yes']:
                            continue
                    
                    print(f"\n⏳ [{numara}] {oyun['oyun']} takvime ekleniyor...")
                    success, message = add_to_google_calendar(oyun, tarih_str, sehir)
                    print(f"   {message}")
                else:
                    print(f"\n❌ Geçersiz numara: {numara}")
                    
        except ValueError:
            print("\n❌ Geçersiz giriş. Lütfen numara girin.")

# ═══════════════════════════════════════════════════════════════
# ANA PROGRAM - ÇOKLU SORGULU
# ═══════════════════════════════════════════════════════════════

def main():
    print("🎭 STAGEAGENT v5 - Google Takvim Entegrasyonu + Çoklu Sorgu")
    print("═" * 60)
    print("   Özellikler:")
    print("   ✅ İBB Şehir Tiyatroları (Web Scraping)")
    print("   ✅ Devlet Tiyatroları (Biletinial Selenium)")
    print("   ✅ Özel Tiyatrolar (Google Search)")
    print("   🆕 Google Takvim'e Ekleme")
    print("   🆕 Çoklu Sorgulama (Birden fazla tarih için arama)")
    print("═" * 60)
    
    # Oturum geçmişi
    sorgu_gecmisi = []
    
    while True:
        print("\n" + "═" * 60)
        print("🏠 ANA MENÜ")
        print("═" * 60)
        print("1️  Yeni tiyatro araması yap")
        print("2️  Geçmiş sorguları görüntüle")
        print("3️  Çıkış")
        
        menu_secim = input("\n📋 Seçiminiz (1-3): ").strip()
        
        if menu_secim == '1':
            # Yeni sorgu
            sorgu = input("\n🔍 Ne arıyorsunuz? (ör: 22 ocak 2026 İstanbul): ")
            
            if not sorgu:
                print("\n⚠️  Lütfen geçerli bir sorgu girin.")
                continue
            
            sorgu_gecmisi.append(sorgu)
            
            # Sorguyu yap
            tum_oyunlar, sehir, tarih_str = sorgu_yap(sorgu)
            
            # Takvim işlemleri
            ana_menu_don = takvim_islemleri(tum_oyunlar, sehir, tarih_str)
            
            if not ana_menu_don:
                # Takvim işlemlerinden çıkınca ana menüye dön
                continue
            
        elif menu_secim == '2':
            # Geçmiş sorguları göster
            print("\n" + "═" * 60)
            print("📜 SORGULAR GEÇMİŞİ")
            print("═" * 60)
            
            if not sorgu_gecmisi:
                print("\n   Henüz sorgu yapılmadı.")
            else:
                for i, gecmis_sorgu in enumerate(sorgu_gecmisi, 1):
                    sehir, tarih = sorguyu_ayristir(gecmis_sorgu)
                    tarih_str = tarih_formatla(tarih)
                    print(f"\n   {i:2d}. {gecmis_sorgu[:50]}...")
                    print(f"       📍 {sehir}, 📅 {tarih_str}")
            
            input("\n   🔄 Devam etmek için Enter'a basın...")
            
        elif menu_secim == '3' or menu_secim.lower() in ['/','/q', 'çık', 'exit','cik']:
            print("\n" + "═" * 60)
            print("👋 Görüşmek üzere! StageAgent oturumu sonlandırıldı.")
            print("═" * 60)
            break
        
        else:
            print("\n❌ Geçersiz seçim. Lütfen 1-3 arası bir seçenek girin.")

if __name__ == "__main__":
    main()


# =========================================================================>1
# """
# StageAgent v5 - Google Calendar Entegrasyonu + Çoklu Sorgu

# Andrew Ng Agentic Pattern: TOOL USE + MULTI-QUERY
# - Kullanıcı birden fazla tarih için sorgu yapabilir
# - Her sorguda Google Takvim'e ekleyebilir
# - Ana menü ile yönetim

# KURULUM:
# 1. Google Cloud Console'da proje oluştur
# 2. Google Calendar API'yi etkinleştir
# 3. OAuth 2.0 credentials oluştur (Desktop app)
# 4. credentials.json dosyasını indir ve src2/ klasörüne koy

# pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
# pip install selenium webdriver-manager beautifulsoup4 requests google-genai
# """

# import os
# import re
# import requests
# import time
# from datetime import datetime, timedelta
# from bs4 import BeautifulSoup

# # Google Calendar imports
# try:
#     from google.oauth2.credentials import Credentials
#     from google_auth_oauthlib.flow import InstalledAppFlow
#     from google.auth.transport.requests import Request
#     from googleapiclient.discovery import build
#     import pickle
#     GCAL_AVAILABLE = True
# except ImportError:
#     GCAL_AVAILABLE = False
#     print("⚠️  Google Calendar kütüphaneleri kurulu değil.")
#     print("   pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")

# # Gemini imports
# import google.genai as genai
# from google.genai import types

# # Selenium imports
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

# # ═══════════════════════════════════════════════════════════════
# # YAPILANDIRMA
# # ═══════════════════════════════════════════════════════════════

# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# if not GOOGLE_API_KEY:
#     print("❌ GOOGLE_API_KEY ayarlanmalı!")
#     exit(1)

# client = genai.Client(api_key=GOOGLE_API_KEY)

# # Google Calendar API scope
# SCOPES = ['https://www.googleapis.com/auth/calendar']

# # Şehir -> Biletinial data-val
# SEHIR_ID_MAP = {
#     'İstanbul': '5', 'Ankara': '3', 'İzmir': '24', 'Mersin': '85',
#     'Antalya': '23', 'Samsun': '43', 'Adana': '12', 'Bursa': '11',
#     'Denizli': '14', 'Diyarbakır': '10',
# }

# # ═══════════════════════════════════════════════════════════════
# # GOOGLE TAKVİM FONKSİYONLARI
# # ═══════════════════════════════════════════════════════════════

# def get_calendar_service():
#     """Google Calendar API servisini başlat"""
#     if not GCAL_AVAILABLE:
#         return None
    
#     creds = None
    
#     # Token varsa yükle
#     if os.path.exists('token.pickle'):
#         with open('token.pickle', 'rb') as token:
#             creds = pickle.load(token)
    
#     # Token yoksa veya geçersizse yenile
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             # credentials.json dosyası gerekli
#             if not os.path.exists('credentials.json'):
#                 print("\n⚠️  credentials.json dosyası bulunamadı!")
#                 print("   Google Cloud Console'dan OAuth credentials indirin.")
#                 print("   https://console.cloud.google.com/apis/credentials")
#                 return None
            
#             flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
#             creds = flow.run_local_server(port=0)
        
#         # Token'ı kaydet
#         with open('token.pickle', 'wb') as token:
#             pickle.dump(creds, token)
    
#     return build('calendar', 'v3', credentials=creds)

# def add_to_google_calendar(oyun, tarih_str, sehir):
#     """
#     Seçilen oyunu Google Takvim'e ekle
    
#     Args:
#         oyun: dict with keys: oyun, sahne, saat, tukendi, link/bilet
#         tarih_str: "22 Ocak 2026" formatında tarih
#         sehir: "İstanbul" gibi şehir adı
    
#     Returns:
#         (success: bool, message: str)
#     """
#     service = get_calendar_service()
#     if not service:
#         return False, "Google Calendar bağlantısı kurulamadı"
    
#     try:
#         # Tarihi parse et
#         aylar = {'Ocak': 1, 'Şubat': 2, 'Mart': 3, 'Nisan': 4, 'Mayıs': 5, 'Haziran': 6,
#                  'Temmuz': 7, 'Ağustos': 8, 'Eylül': 9, 'Ekim': 10, 'Kasım': 11, 'Aralık': 12}
        
#         parts = tarih_str.split()
#         gun = int(parts[0])
#         ay = aylar.get(parts[1], 1)
#         yil = int(parts[2])
        
#         # Saat bilgisini parse et
#         saat_str = oyun.get('saat', '20:00')
#         saat_parts = saat_str.split(':')
#         saat = int(saat_parts[0])
#         dakika = int(saat_parts[1]) if len(saat_parts) > 1 else 0
        
#         # Başlangıç ve bitiş zamanları
#         start_dt = datetime(yil, ay, gun, saat, dakika)
#         end_dt = start_dt + timedelta(hours=2)  # Ortalama 2 saat
        
#         # Event oluştur
#         event = {
#             'summary': f"🎭 {oyun['oyun']}",
#             'location': f"{oyun.get('sahne', 'Bilinmiyor')}, {sehir}",
#             'description': f"""Tiyatro Oyunu: {oyun['oyun']}
# Sahne: {oyun.get('sahne', 'Bilinmiyor')}
# Şehir: {sehir}
# Saat: {saat_str}
# Bilet: {oyun.get('link', oyun.get('bilet', 'Bilinmiyor'))}

# 🎫 StageAgent tarafından eklendi""",
#             'start': {
#                 'dateTime': start_dt.isoformat(),
#                 'timeZone': 'Europe/Istanbul',
#             },
#             'end': {
#                 'dateTime': end_dt.isoformat(),
#                 'timeZone': 'Europe/Istanbul',
#             },
#             'reminders': {
#                 'useDefault': False,
#                 'overrides': [
#                     {'method': 'popup', 'minutes': 60},  # 1 saat önce
#                     {'method': 'popup', 'minutes': 1440},  # 1 gün önce
#                 ],
#             },
#         }
        
#         # Takvime ekle
#         event = service.events().insert(calendarId='primary', body=event).execute()
        
#         return True, f"✅ Takvime eklendi! Link: {event.get('htmlLink')}"
        
#     except Exception as e:
#         return False, f"❌ Hata: {e}"

# # ═══════════════════════════════════════════════════════════════
# # YARDIMCI FONKSİYONLAR
# # ═══════════════════════════════════════════════════════════════

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
# # KAYNAK 1: İBB ŞEHİR TİYATROLARI
# # ═══════════════════════════════════════════════════════════════

# def ibb_sehir_tiyatrolari_ara(hedef_gun):
#     """İBB Şehir Tiyatroları takviminden veri çek"""
#     try:
#         url = "https://sehirtiyatrolari.ibb.istanbul/takvim"
#         headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
#         response = requests.get(url, headers=headers, timeout=15)
#         soup = BeautifulSoup(response.content, 'html.parser')
        
#         oyunlar = []
#         table = soup.find('table', class_='yn_calendar-table')
#         if not table:
#             table = soup.find('table')
#         if not table:
#             return []
        
#         # Header'dan sahne isimlerini al
#         sahneler = []
#         thead = table.find('thead')
#         if thead:
#             header_row = thead.find('tr')
#             if header_row:
#                 header_cells = header_row.find_all(['th', 'td'])
#                 for cell in header_cells[3:]:
#                     text = cell.get_text(strip=True)
#                     if text:
#                         sahneler.append(text)
        
#         # Tbody'den verileri al
#         tbody = table.find('tbody', class_='yn_calendar_list')
#         if not tbody:
#             tbody = table.find('tbody') or table
        
#         rows = tbody.find_all('tr')
#         current_date = None
#         current_saat = None
        
#         for row in rows:
#             cells = row.find_all('td')
#             if not cells:
#                 continue
            
#             day_cell = row.find('td', class_='yn_calendar_day')
#             if day_cell:
#                 day_text = day_cell.get_text(strip=True)
#                 if day_text.isdigit():
#                     current_date = int(day_text)
            
#             time_cell = row.find('td', class_='yn_calendar_time')
#             if time_cell:
#                 time_text = time_cell.get_text(strip=True)
#                 if re.match(r'^\d{2}:\d{2}$', time_text):
#                     current_saat = time_text
            
#             if current_date != hedef_gun:
#                 continue
            
#             skip_count = 0
#             for cell in cells:
#                 cell_class = cell.get('class', [])
#                 if any(c in cell_class for c in ['yn_calendar_day', 'yn_calendar_date', 'yn_calendar_time']):
#                     skip_count += 1
#                 else:
#                     break
            
#             oyun_hucreleri = cells[skip_count:]
            
#             for idx, cell in enumerate(oyun_hucreleri):
#                 sahne = sahneler[idx] if idx < len(sahneler) else f"Sahne {idx + 1}"
#                 links = cell.find_all('a')
#                 for link in links:
#                     oyun_adi = link.get_text(strip=True)
#                     if not oyun_adi or len(oyun_adi) < 3:
#                         continue
#                     href = link.get('href', '')
#                     tukendi_span = cell.find('span', class_='yn_tukendi')
#                     tukendi = tukendi_span is not None
                    
#                     oyunlar.append({
#                         'oyun': oyun_adi,
#                         'sahne': sahne,
#                         'saat': current_saat or '20:00',
#                         'tukendi': tukendi,
#                         'link': f"https://sehirtiyatrolari.ibb.istanbul{href}" if href.startswith('/') else href,
#                         'kaynak': 'İBB Şehir Tiyatroları'
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
#         print(f"   ⚠️  İBB Hata: {e}")
#         return []

# # ═══════════════════════════════════════════════════════════════
# # KAYNAK 2: DEVLET TİYATROLARI (Biletinial Selenium)
# # ═══════════════════════════════════════════════════════════════

# def biletinial_devlet_tiyatrolari_ara(sehir, hedef_gun, hedef_ay):
#     """Biletinial'dan Selenium ile Devlet Tiyatroları verisi çek"""
#     if not SELENIUM_AVAILABLE:
#         return None
    
#     driver = None
#     oyunlar = []
    
#     try:
#         driver = get_chrome_driver()
#         driver.get("https://biletinial.com/tr-tr/etkinlik-takvimi/708")
#         wait = WebDriverWait(driver, 15)
#         time.sleep(4)
        
#         # Şehir seçimi
#         sehir_id = SEHIR_ID_MAP.get(sehir, '5')
#         try:
#             city_selector = wait.until(EC.element_to_be_clickable((By.ID, "citySelector")))
#             driver.execute_script("arguments[0].click();", city_selector)
#             time.sleep(1)
#             city_option = wait.until(EC.element_to_be_clickable(
#                 (By.CSS_SELECTOR, f"#customCitySelect .scrollList ul li[data-val='{sehir_id}']")
#             ))
#             driver.execute_script("arguments[0].click();", city_option)
#             time.sleep(4)
#         except:
#             pass
        
#         soup = BeautifulSoup(driver.page_source, 'html.parser')
#         tables = soup.find_all('table', class_='bltn-table')
#         table = tables[-1] if tables else None
#         if not table:
#             return []
        
#         # Sahneleri al
#         sahneler = []
#         thead = table.find('thead')
#         if thead:
#             header_row = thead.find('tr')
#             if header_row:
#                 ths = header_row.find_all('th')
#                 for th in ths:
#                     aria_label = th.get('aria-label', '')
#                     sahne_adi = aria_label.strip() if aria_label else th.get_text(separator=' ', strip=True)
#                     sahne_adi = re.sub(r'\s+', ' ', sahne_adi).strip()
#                     if sahne_adi and len(sahne_adi) > 2 and 'data-min' not in str(th):
#                         sahneler.append(sahne_adi)
        
#         tbody = table.find('tbody') or table
#         rows = tbody.find_all('tr')
        
#         for row in rows:
#             cells = row.find_all('td')
#             if not cells:
#                 continue
            
#             first_cell = cells[0]
#             first_text = first_cell.get_text(strip=True)
            
#             gun_match = re.search(r'^(\d{1,2})', first_text)
#             if not gun_match:
#                 continue
            
#             current_gun = int(gun_match.group(1))
#             current_ay = None
#             for ay in ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 
#                        'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']:
#                 if ay in first_text:
#                     current_ay = ay
#                     break
            
#             if current_gun != hedef_gun:
#                 continue
#             if hedef_ay and current_ay and current_ay != hedef_ay:
#                 continue
            
#             for idx, cell in enumerate(cells[1:]):
#                 act_lines = cell.find_all('div', class_=lambda x: x and 'act-line' in x)
                
#                 for act in act_lines:
#                     info_label = act.find('a', class_='info-label')
#                     if not info_label:
#                         continue
                    
#                     oyun_adi = info_label.get_text(strip=True)
#                     mobile_saloon = info_label.find('span', class_='mobile-saloon-name')
#                     if mobile_saloon:
#                         oyun_adi = oyun_adi.replace(mobile_saloon.get_text(), '').strip()
                    
#                     if not oyun_adi or len(oyun_adi) < 2:
#                         continue
                    
#                     sahne = sahneler[idx] if idx < len(sahneler) else "Devlet Tiyatrosu"
                    
#                     seances = act.find('div', class_='seances-list')
#                     if seances:
#                         buttons = seances.find_all('button')
#                         for btn in buttons:
#                             btn_text = btn.get_text(strip=True)
#                             saat_match = re.search(r'(\d{2}:\d{2})', btn_text)
#                             saat = saat_match.group(1) if saat_match else "20:00"
#                             tukendi = 'TÜKENDİ' in btn_text.upper()
                            
#                             oyunlar.append({
#                                 'oyun': oyun_adi,
#                                 'sahne': sahne,
#                                 'saat': saat,
#                                 'tukendi': tukendi,
#                                 'bilet': 'biletinial.com',
#                                 'kaynak': 'Devlet Tiyatroları'
#                             })
        
#         seen = set()
#         unique = []
#         for o in oyunlar:
#             key = (o['oyun'], o['saat'], o['sahne'])
#             if key not in seen:
#                 seen.add(key)
#                 unique.append(o)
#         return unique
        
#     except Exception as e:
#         return None
#     finally:
#         if driver:
#             driver.quit()

# def devlet_tiyatrolari_google_ara(sehir, tarih_formatli):
#     """Fallback: Google Search"""
#     prompt = f"{sehir}'da {tarih_formatli} tarihinde DEVLET TİYATROLARI'nda hangi oyunlar var? SADECE bu tarih ve şehirdeki oyunları, mekan ve saat bilgileriyle listele."
    
#     try:
#         response = client.models.generate_content(
#             model="gemini-2.0-flash-exp",
#             contents=prompt,
#             config=types.GenerateContentConfig(
#                 tools=[types.Tool(google_search=types.GoogleSearch())],
#                 temperature=0.1,
#             )
#         )
        
#         gemini_text = response.text.strip()
#         # Aynı parsing fonksiyonunu kullan
#         oyunlar = parse_gemini_response(gemini_text)
        
#         # Devlet tiyatrosu bilgilerini güncelle
#         for oyun in oyunlar:
#             oyun['kaynak'] = 'Devlet Tiyatroları (Gemini)'
#             oyun['bilet'] = 'biletinial.com'
            
#         return oyunlar
        
#     except Exception as e:
#         print(f"   ⚠️  Arama hatası: {e}")
#         return []

# # ═══════════════════════════════════════════════════════════════
# # KAYNAK 3: ÖZEL TİYATROLAR (Google Search)
# # ═══════════════════════════════════════════════════════════════

# def parse_gemini_response(gemini_text):
#     """Gemini yanıtını parse edip oyun listesi oluştur - SON İYİLEŞTİRME"""
#     if not gemini_text or "Arama hatası" in gemini_text:
#         return []
    
#     oyunlar = []
#     lines = gemini_text.strip().split('\n')
    
#     current_sahne = "Özel Tiyatro"
    
#     for i, line in enumerate(lines):
#         line = line.strip()
        
#         # Boş satırları atla
#         if not line or len(line) < 2:
#             continue
        
#         # 1. MEKAN/Sahne adı bulma
#         sahne_keywords = [
#             'Kültür Merkezi', 'PSM', 'Sahnesi', 'DasDas', 'CKM', 'BKM', 'Hall',
#             'Cambazhane', 'Merkezi', 'Salonu', 'Tiyatrosu', 'Stage', 'Theatre'
#         ]
        
#         is_sahne_line = (
#             (line.endswith(':') and 5 < len(line) < 50) or
#             ('**' in line and line.count('**') >= 2 and len(line) < 60) or
#             any(keyword in line for keyword in sahne_keywords)
#         )
        
#         # Geçersiz sahne başlangıçları
#         invalid_sahne_starts = ['http', 'www.', 'İBB', 'Devlet', 'Olası', 'Kesin', 'Liste']
        
#         if is_sahne_line and not any(line.startswith(start) for start in invalid_sahne_starts):
#             # Mekan adını temizle
#             sahne = line.replace('**', '').replace('*', '').replace(':', '').strip()
#             sahne = re.sub(r'\(.*?\)', '', sahne).strip()
            
#             if 3 < len(sahne) < 50:
#                 current_sahne = sahne
#                 continue
        
#         # 2. OYUN satırı ara
#         invalid_patterns = [
#             'http://', 'https://', 'www.', '.com', '.tr', '.gen.tr',
#             'Not:', 'Dipnot:', 'Kaynak:', 'Dikkat:', 'Önemli:', 'Olası',
#             'Kesin program', 'kontrol edin', 'tarihinde', 'İBB Şehir Tiyatroları',
#             'Devlet Tiyatroları', 'SADECE', 'LÜTFEN', 'bilgisi belirtilmemiş',
#             'olası oyunlar', 'için kontrol', 'program için'
#         ]
        
#         line_lower = line.lower()
#         if any(pattern.lower() in line_lower for pattern in invalid_patterns):
#             continue
        
#         # Geçerli oyun adı mı kontrol et
#         is_valid_oyun = False
        
#         # Liste işaretleri
#         list_markers = ['•', '*', '-', '○', '▪', '‣']
#         has_list_marker = any(line.startswith(marker) for marker in list_markers)
        
#         # Numara ile başlayan
#         has_number = re.match(r'^\d+[\.\)]\s+', line)
        
#         # Oyun adı formatı
#         looks_like_real_oyun = (
#             5 < len(line) < 70 and
#             re.match(r'^[A-ZÇĞİÖŞÜ]', line) and
#             not line.endswith(':') and
#             not any(word in line_lower for word in ['.com', 'www', 'http']) and
#             len(re.findall(r'\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]+\b', line)) >= 1
#         )
        
#         if has_list_marker or has_number or looks_like_real_oyun:
#             # Satırı temizle
#             cleaned_line = line
            
#             # Liste işaretlerini kaldır
#             for marker in list_markers:
#                 if cleaned_line.startswith(marker):
#                     cleaned_line = cleaned_line[len(marker):].strip()
#                     break
            
#             # Numaraları kaldır
#             cleaned_line = re.sub(r'^\d+[\.\)]\s+', '', cleaned_line)
            
#             # Markdown formatlarını temizle
#             cleaned_line = cleaned_line.replace('**', '').replace('*', '').replace('__', '').replace('_', '')
            
#             # Oyun adını ve saat bilgisini ayır
#             oyun_adi = cleaned_line
#             saat = "20:00"
            
#             # "- Saat" formatını ara
#             if ' - ' in oyun_adi:
#                 parts = oyun_adi.split(' - ')
#                 oyun_adi = parts[0].strip()
#                 if len(parts) > 1:
#                     last_part = parts[-1].strip()
#                     saat_match = re.search(r'(\d{1,2}[\.:]\d{2})', last_part)
#                     if saat_match:
#                         saat = saat_match.group(1).replace('.', ':')
            
#             # Saat bilgisini ara (genel)
#             saat_match = re.search(r'(\d{1,2}[\.:]\d{2})', oyun_adi)
#             if saat_match:
#                 saat = saat_match.group(1).replace('.', ':')
#                 oyun_adi = re.sub(r'\s*\d{1,2}[\.:]\d{2}.*', '', oyun_adi).strip()
            
#             # "Saat:" formatını temizle
#             oyun_adi = re.sub(r'[Ss]aat\s*:?\s*\d{1,2}[\.:]\d{2}.*', '', oyun_adi)
            
#             # Fazladan boşlukları temizle
#             oyun_adi = re.sub(r'\s+', ' ', oyun_adi).strip()
            
#             # Özel karakterleri temizle
#             oyun_adi = re.sub(r'[\[\]()]', '', oyun_adi)
            
#             # Geçersiz başlangıç/bitişleri kontrol et
#             invalid_starts = ['İBB', 'Devlet', 'Olası', 'Kesin', 'Program', 'Kontrol']
#             invalid_ends = ['.com', '.tr', 'edin', 'için']
            
#             has_invalid_start = any(oyun_adi.startswith(start) for start in invalid_starts)
#             has_invalid_end = any(oyun_adi.endswith(end) for end in invalid_ends)
            
#             # Sahne adını temizle
#             temiz_sahne = current_sahne
#             if any(word in temiz_sahne.lower() for word in ['.com', '.tr', 'tiyatrolar', 'gen.tr']):
#                 temiz_sahne = "Özel Tiyatro"
            
#             # Oyun adı geçerli mi kontrol et
#             if (oyun_adi and 
#                 5 <= len(oyun_adi) <= 60 and
#                 not has_invalid_start and
#                 not has_invalid_end and
#                 not any(word in oyun_adi.lower() for word in ['.com', 'www', 'http', 'olası', 'kesin']) and
#                 re.search(r'[a-zA-ZÇĞİÖŞÜçğıöşü]{3,}', oyun_adi)):
                
#                 # Tükendi kontrolü
#                 tukendi = any(word in line.upper() for word in ['TÜKENDİ', 'BİTTİ', 'SOLD OUT', 'SATIŞTA DEĞİL'])
                
#                 oyunlar.append({
#                     'oyun': oyun_adi,
#                     'sahne': temiz_sahne,
#                     'saat': saat,
#                     'tukendi': tukendi,
#                     'bilet': 'Biletix/Passo',
#                     'kaynak': 'Özel Tiyatrolar'
#                 })
    
#     # Benzersiz oyunları seç ve tekrarları temizle
#     seen = set()
#     unique_oyunlar = []
    
#     for oyun in oyunlar:
#         key = re.sub(r'\s+', '', oyun['oyun'].lower())[:25]
#         if key not in seen:
#             seen.add(key)
#             unique_oyunlar.append(oyun)
    
#     # İBB ve Devlet tiyatrolarındaki oyunları filtrele
#     ibb_oyun_keywords = ['Haramiler', 'Yoldan Çıkan Oyun', 'Çingene Boksör', 
#                          'Geçmişin Gölgesi', 'Öksüzler', 'Maviydi Bisikletim', 'Gölge']
    
#     devlet_oyun_keywords = ['VANYA DAYI', 'Vanya Dayı', 'CALLBACK', 'KÜÇÜK BİR İŞ İÇİN YAŞLI BİR PALYAÇO ARANIYOR',
#                            'Küçük Bir İş İçin Yaşlı Bir Palyaço Aranıyor']
    
#     final_oyunlar = []
#     for oyun in unique_oyunlar:
#         oyun_adi = oyun['oyun']
#         # İBB ve Devlet tiyatrosu oyunlarını atla
#         if any(keyword.lower() in oyun_adi.lower() for keyword in ibb_oyun_keywords + devlet_oyun_keywords):
#             continue
        
#         # Geçersiz mekanları kontrol et
#         if any(word in oyun['sahne'].lower() for word in ['.com', '.tr', 'tiyatrolar']):
#             oyun['sahne'] = "Özel Tiyatro"
        
#         final_oyunlar.append(oyun)
    
#     return final_oyunlar[:10]

# def ozel_tiyatrolar_ara(sehir, tarih_formatli):
#     """Özel tiyatroları Google Search ile ara"""
#     prompt = f"""
# {sehir}'da {tarih_formatli} tarihinde ÖZEL TİYATROLARDA hangi oyunlar var?

# ÖNEMLİ MEKANLAR:
# • AKM (Atatürk Kültür Merkezi)
# • Akatlar Kültür Merkezi
# • Zorlu PSM - Turkcell Platinum Sahnesi  
# • Zorlu PSM - % 100 Studio
# • Zorlu PSM - Touché
# • Kanyon Cambazhane
# • DasDas
# • Moda Sahnesi - Büyük Sahne
# • BKM (Beşiktaş Kültür Merkezi)
# • CKM (Caddebostan Kültür Merkezi)

# ÇOK ÖNEMLİ KURALLAR:
# 1. SADECE OYUN ADLARINI ve SAAT BİLGİLERİNİ VER
# 2. URL, link, site adı, ".com", ".tr" KESİNLİKLE YAZMA
# 3. "İBB", "Devlet Tiyatroları", "olası oyunlar", "kontrol edin" gibi ifadeler KULLANMA
# 4. SADECE gerçek özel tiyatro oyunlarını listele

# FORMAT ŞÖYLE OLSUN:
# **Akatlar Kültür Merkezi:**
# • 39 Buçuk Basamak - 20:30
# • Korkusuz Salyangoz - 13:00

# **Zorlu PSM:**
# • Afife - 20:00

# **Küçükçiftlik Park:**
# • Aşk Biter Mi? - 20:30

# **Kanyon Cambazhane:**
# • Süper Patates ve Kaçak Bezelye - 13:00

# SADECE {tarih_formatli} tarihindeki oyunları listele.
# Her oyun için saat bilgisi mutlaka olsun.
# """
    
#     try:
#         print(f"   🔍 Gemini'ye soruluyor: {sehir} {tarih_formatli}")
#         response = client.models.generate_content(
#             model="gemini-2.0-flash-exp",
#             contents=prompt,
#             config=types.GenerateContentConfig(
#                 tools=[types.Tool(google_search=types.GoogleSearch())],
#                 temperature=0.1,
#                 max_output_tokens=800,
#             )
#         )
        
#         gemini_text = response.text.strip()
#         print(f"   📝 Gemini yanıtı aldı ({len(gemini_text)} karakter)")
        
#         # Parse et
#         oyunlar = parse_gemini_response(gemini_text)
        
#         return oyunlar
        
#     except Exception as e:
#         print(f"   ⚠️  Arama hatası: {e}")
#         return []

# # ═══════════════════════════════════════════════════════════════
# # SONUÇ FORMATLAMA
# # ═══════════════════════════════════════════════════════════════

# def tum_oyunlari_listele(ibb_oyunlar, devlet_oyunlar, ozel_oyunlar, tarih_str, sehir):
#     """Tüm oyunları numaralı liste olarak göster"""
#     tum_oyunlar = []
    
#     print("\n" + "═" * 60)
#     print(f"🎭 {sehir} TİYATRO PROGRAMI - {tarih_str}")
#     print("═" * 60)
    
#     numara = 1
    
#     # İBB Şehir Tiyatroları
#     if ibb_oyunlar:
#         print("\n┌" + "─" * 58 + "┐")
#         print("│ 📍 İBB ŞEHİR TİYATROLARI                                  │")
#         print("└" + "─" * 58 + "┘")
        
#         for o in ibb_oyunlar:
#             durum = "❌ TÜKENDİ" if o['tukendi'] else "✅ Bilet Var"
#             print(f"\n   [{numara}] {o['oyun']}")
#             print(f"       📍 {o['sahne']}")
#             print(f"       ⏰ {o['saat']}  {durum}")
#             tum_oyunlar.append(o)
#             numara += 1
    
#     # Devlet Tiyatroları
#     if devlet_oyunlar:
#         print("\n┌" + "─" * 58 + "┐")
#         print("│ 🏛️  DEVLET TİYATROLARI                                     │")
#         print("└" + "─" * 58 + "┘")
        
#         for o in devlet_oyunlar:
#             durum = "❌ TÜKENDİ" if o['tukendi'] else "✅ Bilet Var"
#             print(f"\n   [{numara}] {o['oyun']}")
#             print(f"       📍 {o['sahne']}")
#             print(f"       ⏰ {o['saat']}  {durum}")
#             tum_oyunlar.append(o)
#             numara += 1
    
#     # Özel Tiyatrolar
#     if ozel_oyunlar:
#         print("\n┌" + "─" * 58 + "┐")
#         print("│ 🎪 ÖZEL TİYATROLAR                                         │")
#         print("│    Kaynak: DasDas, Zorlu PSM, Biletix, Passo vb.          │")
#         print("└" + "─" * 58 + "┘")
        
#         for o in ozel_oyunlar:
#             durum = "❌ TÜKENDİ" if o['tukendi'] else "✅ Bilet Var"
#             print(f"\n   [{numara}] {o['oyun']}")
#             print(f"       📍 {o['sahne']}")
#             print(f"       ⏰ {o['saat']}  {durum}")
#             tum_oyunlar.append(o)
#             numara += 1
    
#     # Faydalı Linkler
#     print("\n┌" + "─" * 58 + "┐")
#     print("│ 🔗 FAYDALI LİNKLER                                         │")
#     print("└" + "─" * 58 + "┘")
#     if sehir == "İstanbul":
#         print("   • İBB Şehir Tiyatroları: https://sehirtiyatrolari.ibb.istanbul/takvim")
#     print("   • Devlet Tiyatroları: https://biletinial.com/tr-tr/etkinlik-takvimi/708")
#     print("   • Biletinial: https://www.biletinial.com")
#     print("   • Biletix: https://www.biletix.com")
#     print("   • Passo: https://www.passo.com.tr")
    
#     return tum_oyunlar

# # ═══════════════════════════════════════════════════════════════
# # ANA SORGU FONKSİYONU
# # ═══════════════════════════════════════════════════════════════

# def sorgu_yap(sorgu):
#     """Tek bir sorgu yap ve sonuçları göster"""
#     sehir, tarih = sorguyu_ayristir(sorgu)
#     hedef_gun = int(tarih.split('-')[2])
#     hedef_ay_num = int(tarih.split('-')[1])
#     aylar = ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
#              'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
#     hedef_ay = aylar[hedef_ay_num]
#     tarih_str = tarih_formatla(tarih)
    
#     print(f"\n📍 Şehir: {sehir}")
#     print(f"📅 Tarih: {tarih_str}")
    
#     # Kaynakları ara
#     print("\n" + "─" * 60)
#     print("1️⃣  İBB Şehir Tiyatroları aranıyor...")
#     ibb_oyunlar = ibb_sehir_tiyatrolari_ara(hedef_gun) if sehir == "İstanbul" else []
#     print(f"   ✅ {len(ibb_oyunlar)} oyun bulundu")
    
#     print("\n" + "─" * 60)
#     print("2️⃣  Devlet Tiyatroları aranıyor...")
#     devlet_oyunlar = biletinial_devlet_tiyatrolari_ara(sehir, hedef_gun, hedef_ay)
    
#     # Selenium başarısız olursa Gemini'yi kullan
#     if not devlet_oyunlar or len(devlet_oyunlar) == 0:
#         print("   ⚠️  Selenium başarısız, Gemini ile aranıyor...")
#         devlet_oyunlar = devlet_tiyatrolari_google_ara(sehir, tarih_str)
    
#     print(f"   ✅ {len(devlet_oyunlar)} oyun bulundu")
    
#     print("\n" + "─" * 60)
#     print("3️⃣  Özel Tiyatrolar aranıyor... (Google Search)")
#     ozel_oyunlar = ozel_tiyatrolar_ara(sehir, tarih_str)
#     print(f"   ✅ {len(ozel_oyunlar)} oyun bulundu")
    
#     # Tüm oyunları listele
#     tum_oyunlar = tum_oyunlari_listele(ibb_oyunlar, devlet_oyunlar, ozel_oyunlar, tarih_str, sehir)
    
#     print("\n" + "═" * 60)
#     print("✅ Arama tamamlandı!")
    
#     return tum_oyunlar, sehir, tarih_str

# def takvim_islemleri(tum_oyunlar, sehir, tarih_str):
#     """Google Takvim işlemlerini yönet"""
#     if not tum_oyunlar:
#         print("\n⚠️  Bu tarihte oyun bulunamadı.")
#         return False
    
#     # ═══════════════════════════════════════════════════════════════
#     # GOOGLE TAKVİM ENTEGRASYONU
#     # ═══════════════════════════════════════════════════════════════
#     print("\n" + "═" * 60)
#     print("📅 GOOGLE TAKVİM'E EKLEME")
#     print("═" * 60)
    
#     if not GCAL_AVAILABLE:
#         print("\n⚠️  Google Calendar kütüphaneleri kurulu değil.")
#         print("   pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
#         return False
    
#     while True:
#         print("\n💡 Takvime eklemek istediğiniz oyunun numarasını girin")
#         print("   (Birden fazla için virgülle ayırın: 1,3,5)")
#         print("   (Takvim eklemeden çıkmak için 'q' veya 'çık' yazın)")
#         print("   (Ana menüye dönmek için 'ana' yazın)")
        
#         secim = input("\n🎫 Seçiminiz: ").strip().lower()
        
#         if secim in ['q', 'çık', 'cik', 'exit', '']:
#             print("\n👋 Takvim ekleme tamamlandı!")
#             return False
#         elif secim == 'ana':
#             print("\n🏠 Ana menüye dönülüyor...")
#             return True
        
#         try:
#             # Virgülle ayrılmış numaraları parse et
#             numaralar = [int(n.strip()) for n in secim.split(',')]
            
#             for numara in numaralar:
#                 if 1 <= numara <= len(tum_oyunlar):
#                     oyun = tum_oyunlar[numara - 1]
                    
#                     if oyun['tukendi']:
#                         print(f"\n⚠️  [{numara}] {oyun['oyun']} - Biletler tükenmiş!")
#                         devam = input("   Yine de takvime eklemek ister misiniz? (e/h): ")
#                         if devam.lower() not in ['e', 'evet', 'y', 'yes']:
#                             continue
                    
#                     print(f"\n⏳ [{numara}] {oyun['oyun']} takvime ekleniyor...")
#                     success, message = add_to_google_calendar(oyun, tarih_str, sehir)
#                     print(f"   {message}")
#                 else:
#                     print(f"\n❌ Geçersiz numara: {numara}")
                    
#         except ValueError:
#             print("\n❌ Geçersiz giriş. Lütfen numara girin.")

# # ═══════════════════════════════════════════════════════════════
# # ANA PROGRAM - ÇOKLU SORGULU
# # ═══════════════════════════════════════════════════════════════

# def main():
#     print("🎭 STAGEAGENT v5 - Google Takvim Entegrasyonu + Çoklu Sorgu")
#     print("═" * 60)
#     print("   Özellikler:")
#     print("   ✅ İBB Şehir Tiyatroları (Web Scraping)")
#     print("   ✅ Devlet Tiyatroları (Biletinial Selenium)")
#     print("   ✅ Özel Tiyatrolar (Google Search)")
#     print("   🆕 Google Takvim'e Ekleme")
#     print("   🆕 Çoklu Sorgulama (Birden fazla tarih için arama)")
#     print("═" * 60)
    
#     # Oturum geçmişi
#     sorgu_gecmisi = []
    
#     while True:
#         print("\n" + "═" * 60)
#         print("🏠 ANA MENÜ")
#         print("═" * 60)
#         print("1️⃣  Yeni tiyatro araması yap")
#         print("2️⃣  Geçmiş sorguları görüntüle")
#         print("3️⃣  Çıkış")
        
#         menu_secim = input("\n📋 Seçiminiz (1-3): ").strip()
        
#         if menu_secim == '1':
#             # Yeni sorgu
#             sorgu = input("\n🔍 Ne arıyorsunuz? (ör: 22 ocak 2026 İstanbul): ")
            
#             if not sorgu:
#                 print("\n⚠️  Lütfen geçerli bir sorgu girin.")
#                 continue
            
#             sorgu_gecmisi.append(sorgu)
            
#             # Sorguyu yap
#             tum_oyunlar, sehir, tarih_str = sorgu_yap(sorgu)
            
#             # Takvim işlemleri
#             ana_menu_don = takvim_islemleri(tum_oyunlar, sehir, tarih_str)
            
#             if not ana_menu_don:
#                 # Takvim işlemlerinden çıkınca ana menüye dön
#                 continue
            
#         elif menu_secim == '2':
#             # Geçmiş sorguları göster
#             print("\n" + "═" * 60)
#             print("📜 SORGULAR GEÇMİŞİ")
#             print("═" * 60)
            
#             if not sorgu_gecmisi:
#                 print("\n   Henüz sorgu yapılmadı.")
#             else:
#                 for i, gecmis_sorgu in enumerate(sorgu_gecmisi, 1):
#                     sehir, tarih = sorguyu_ayristir(gecmis_sorgu)
#                     tarih_str = tarih_formatla(tarih)
#                     print(f"\n   {i:2d}. {gecmis_sorgu[:50]}...")
#                     print(f"       📍 {sehir}, 📅 {tarih_str}")
            
#             input("\n   🔄 Devam etmek için Enter'a basın...")
            
#         elif menu_secim == '3' or menu_secim.lower() in ['q', 'çık', 'exit']:
#             print("\n" + "═" * 60)
#             print("👋 Görüşmek üzere! StageAgent oturumu sonlandırıldı.")
#             print("═" * 60)
#             break
        
#         else:
#             print("\n❌ Geçersiz seçim. Lütfen 1-3 arası bir seçenek girin.")

# if __name__ == "__main__":
#     main()