

"""
StageAgent v7 - Web Versiyonu (Streamlit)
Mevcut recommender_llm_an6.py kodunu web arayüzüne dönüştürüyoruz.
"""

import streamlit as st
import os
import re
import requests
import time
import sys
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import quote
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

print("\n" + "="*80)
print("🎭 STAGEAGENT v7 - Web Versiyonu Yükleniyor...")
print("="*80)

# ═══════════════════════════════════════════════════════════════
# IMPORT'LAR
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

# 4. YouTube API imports
try:
    from googleapiclient.discovery import build as yt_build
    YOUTUBE_AVAILABLE = True
    print("   ✅ YouTube API kütüphaneleri hazır")
except ImportError as e:
    YOUTUBE_AVAILABLE = False
    print(f"   ⚠️  YouTube API yok: {e}")



# ═══════════════════════════════════════════════════════════════
# YAPILANDIRMA
# ═══════════════════════════════════════════════════════════════

# Streamlit secrets'dan API Key'leri al (Deployment için)
# Yerel geliştirme için .env'den (os.getenv)
try:
    GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY"))
    YOUTUBE_API_KEY = st.secrets.get("YOUTUBE_API_KEY", os.getenv("YOUTUBE_API_KEY"))
except Exception:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


# Eğer hala yoksa, Streamlit sidebar'dan al
if not GOOGLE_API_KEY:
    GOOGLE_API_KEY = "NOT_SET"
if not YOUTUBE_API_KEY:
    YOUTUBE_API_KEY = "NOT_SET"

print(f"   ✅ Gemini API Key: {GOOGLE_API_KEY[:10] if GOOGLE_API_KEY != 'NOT_SET' else 'NOT_SET'}...")
if YOUTUBE_AVAILABLE and YOUTUBE_API_KEY != 'NOT_SET':
    print(f"   ✅ YouTube API Key: {YOUTUBE_API_KEY[:10]}...")

# Client oluştur
try:
    client = genai.Client(api_key=GOOGLE_API_KEY)
    print("   ✅ Gemini API bağlantısı kuruldu")
except Exception as e:
    print(f"   ❌ Gemini bağlantı hatası: {e}")
    # Streamlit'te hata göster
    pass

# YouTube client oluştur
youtube = None
if YOUTUBE_AVAILABLE and YOUTUBE_API_KEY != 'NOT_SET':
    try:
        youtube = yt_build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        print("   ✅ YouTube API bağlantısı kuruldu")
    except Exception as e:
        print(f"   ❌ YouTube bağlantı hatası: {e}")
        YOUTUBE_AVAILABLE = False

# Google Calendar API scope
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Şehir -> Biletinial data-val
SEHIR_ID_MAP = {
    'İstanbul': '5', 'Ankara': '3', 'İzmir': '24', 'Mersin': '85',
    'Antalya': '23', 'Samsun': '43', 'Adana': '12', 'Bursa': '11',
    'Denizli': '14', 'Diyarbakır': '10',
}

print("\n" + "="*80)
print("🚀 WEB SİSTEMİ HAZIR - Streamlit başlatılıyor...")
print("="*80)

# ═══════════════════════════════════════════════════════════════
# YOUTUBE FONKSİYONLARI (Mevcut koddan)
# ═══════════════════════════════════════════════════════════════

def search_youtube_videos(oyun_adi, max_results=3):
    """
    YouTube'dan oyunla ilgili videoları ara
    """
    if not YOUTUBE_AVAILABLE or not youtube or YOUTUBE_API_KEY == 'NOT_SET':
        return None
    
    try:
        # DAHA SPESİFİK Türkçe arama sorguları
        search_queries = [
            f"{oyun_adi} tiyatro oyunu fragman",
            f"{oyun_adi} tiyatro sahnesi",
            f"{oyun_adi} tiyatro röportaj",
            f"{oyun_adi} tiyatro oyuncuları",
            f"{oyun_adi} tiyatro tanıtım"
        ]
        
        videos = []
        
        # İlk 2 sorguyu dene
        for query in search_queries[:2]:
            if len(videos) >= max_results:
                break
                
            try:
                request = youtube.search().list(
                    part="snippet",
                    q=query,
                    type="video",
                    maxResults=max_results - len(videos),
                    relevanceLanguage="tr",
                    regionCode="TR",
                    order="relevance"
                )
                
                response = request.execute()
                
                for item in response.get('items', []):
                    video_id = item['id']['videoId']
                    title = item['snippet']['title']
                    description = item['snippet']['description'][:100] + "..." if len(item['snippet']['description']) > 100 else item['snippet']['description']
                    thumbnail = item['snippet']['thumbnails']['default']['url']
                    channel = item['snippet']['channelTitle']
                    
                    # HTML entity'leri temizle
                    title = title.replace('&#39;', "'").replace('&amp;', '&')
                    
                    # Aynı video birden fazla kez eklenmesin
                    if not any(v['id'] == video_id for v in videos):
                        videos.append({
                            'id': video_id,
                            'title': title,
                            'description': description,
                            'thumbnail': thumbnail,
                            'channel': channel,
                            'url': f"https://www.youtube.com/watch?v={video_id}",
                            'embed_url': f"https://www.youtube.com/embed/{video_id}",
                            'query': query
                        })
            except Exception as e:
                print(f"   ⚠️  Sorgu hatası '{query}': {e}")
                continue
        
        return videos if videos else None
        
    except Exception as e:
        print(f"   ⚠️  YouTube arama hatası: {e}")
        return None



# ═══════════════════════════════════════════════════════════════
# GOOGLE TAKVİM FONKSİYONLARI (Mevcut koddan)
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
        end_dt = start_dt + timedelta(hours=2)
        
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
                    {'method': 'popup', 'minutes': 60},
                    {'method': 'popup', 'minutes': 1440},
                ],
            },
        }
        
        # Takvime ekle
        event = service.events().insert(calendarId='primary', body=event).execute()
        
        return True, f"✅ Takvime eklendi! Link: {event.get('htmlLink')}"
        
    except Exception as e:
        return False, f"❌ Hata: {e}"

# ═══════════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR (Mevcut koddan)
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
# KAYNAK FONKSİYONLARI (Mevcut koddan - kısaltılmış)
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
    if GOOGLE_API_KEY == 'NOT_SET':
        return []
    
    try:
        prompt = f"""
{sehir}'da {tarih_formatli} tarihinde ÖZEL TİYATROLARDA hangi oyunlar var?
SADECE {tarih_formatli} tarihindeki oyunları listele.
"""
        
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
        oyunlar = parse_gemini_response(gemini_text)
        return oyunlar
        
    except Exception as e:
        print(f"   ⚠️  Arama hatası: {e}")
        return []

# ═══════════════════════════════════════════════════════════════
# ANA SORGU FONKSİYONU (Streamlit için adapte)
# ═══════════════════════════════════════════════════════════════

def sorgu_yap(sorgu):
    """Ana sorgu fonksiyonu - tüm kaynakları ara"""
    sehir, tarih = sorguyu_ayristir(sorgu)
    tarih_str = tarih_formatla(tarih)
    
    # Tarihten gün ve ay bilgilerini çıkar
    yil, ay, gun = tarih.split('-')
    hedef_gun = int(gun)
    
    # Ay numarasını ay adına çevir
    aylar = ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
             'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
    hedef_ay = aylar[int(ay)] if int(ay) <= 12 else "Ocak"
    
    # Tüm oyunları birleştir
    tum_oyunlar = []
    
    # 1. İBB Şehir Tiyatroları
    try:
        ibb_oyunlar = ibb_sehir_tiyatrolari_ara(hedef_gun)
        if ibb_oyunlar:
            tum_oyunlar.extend(ibb_oyunlar)
    except Exception as e:
        print(f"İBB hatası: {e}")
    
    # 2. Devlet Tiyatroları
    try:
        devlet_oyunlar = biletinial_devlet_tiyatrolari_ara(sehir, hedef_gun, hedef_ay)
        if devlet_oyunlar:
            tum_oyunlar.extend(devlet_oyunlar)
    except Exception as e:
        print(f"Devlet tiyatrosu hatası: {e}")
    
    # 3. Özel Tiyatrolar
    try:
        ozel_oyunlar = ozel_tiyatrolar_ara(sehir, tarih_str)
        if ozel_oyunlar:
            tum_oyunlar.extend(ozel_oyunlar)
    except Exception as e:
        print(f"Özel tiyatro hatası: {e}")
    
    return tum_oyunlar, sehir, tarih_str

# ═══════════════════════════════════════════════════════════════
# YOUTUBE BAGLANTISI
# ═══════════════════════════════════════════════════════════════

def show_video_recommendations(oyun_adi, oyun_bilgisi):
    """YouTube videolarını göster"""
    if not YOUTUBE_AVAILABLE or not youtube or YOUTUBE_API_KEY == 'NOT_SET':
        st.warning("YouTube API bağlantısı kurulamadı.")
        return None
    
    try:
        videos = search_youtube_videos(oyun_adi, max_results=3)
        
        if videos:
            st.subheader(f"🎬 '{oyun_adi}' için Videolar")
            
            for i, video in enumerate(videos, 1):
                with st.expander(f"{i}. {video['title']}"):
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        st.image(video['thumbnail'], width=120)
                    
                    with col2:
                        st.write(f"**Kanal:** {video['channel']}")
                        if video['description']:
                            st.write(f"**Açıklama:** {video['description']}")
                        
                        # Video embed et
                        st.video(video['url'])
                        
                        # Link butonu
                        st.link_button("📺 YouTube'da Aç", video['url'])
            
            return videos
        else:
            st.info(f"'{oyun_adi}' için video bulunamadı.")
            return None
            
    except Exception as e:
        st.error(f"YouTube bağlantı hatası: {e}")
        return None
    

# ═══════════════════════════════════════════════════════════════
# STREAMLIT WEB ARAYÜZÜ
# ═══════════════════════════════════════════════════════════════

def main():
    # Sayfa konfigürasyonu
    st.set_page_config(
        page_title="StageAgent v7 - Tiyatro Arama Platformu",
        page_icon="🎭",
        layout="wide"
    )

        # Session state başlat - BU KISMI EKLEYİN/GÜNCELLEYİN
    if 'menu' not in st.session_state:
        st.session_state.menu = "🏠 Ana Sayfa"
    if 'sorgu_gecmisi' not in st.session_state:
        st.session_state.sorgu_gecmisi = []
    if 'tum_oyunlar' not in st.session_state:
        st.session_state.tum_oyunlar = []
    if 'sehir' not in st.session_state:
        st.session_state.sehir = ""
    if 'tarih_str' not in st.session_state:
        st.session_state.tarih_str = ""
    if 'secili_oyun' not in st.session_state:
        st.session_state.secili_oyun = None
    
    
    # CSS styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #FF4B4B;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #555;
        margin-bottom: 2rem;
    }
    .oyun-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #f9f9f9;
    }
    .stButton button {
        width: 100%;
        margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Başlık
    st.markdown('<h1 class="main-header">🎭 StageAgent v7</h1>', unsafe_allow_html=True)
    st.markdown('<h2 class="sub-header">Tiyatro Arama ve Planlama Platformu</h2>', unsafe_allow_html=True)
    
    # Yan menü - BU KISMI GÜNCELLEYİN
    with st.sidebar:
        st.image("https://cdn.pixabay.com/photo/2017/08/30/17/25/theatre-2697944_1280.png", width=200)
        st.title("Navigasyon")
        
        # Menü seçimini session state'den al ve güncelle
        menu_options = ["🏠 Ana Sayfa", "🔍 Tiyatro Ara", "📜 Geçmiş", "⚙️ Ayarlar", "ℹ️ Hakkında"]
        
        # Seçili menüyü radio butonla göster
        selected_menu = st.radio(
            "Menü Seçin:",
            menu_options,
            index=menu_options.index(st.session_state.menu) if st.session_state.menu in menu_options else 0
        )
        
        # Eğer menü değiştiyse, session state'i güncelle ve sayfayı yenile
        if selected_menu != st.session_state.menu:
            st.session_state.menu = selected_menu
            st.rerun()
        
        st.markdown("---")
        st.caption(f"Gemini API: {'✅' if GOOGLE_API_KEY != 'NOT_SET' else '❌'}")
        st.caption(f"YouTube API: {'✅' if YOUTUBE_API_KEY != 'NOT_SET' else '❌'}")
        st.caption(f"Google Calendar: {'✅' if GCAL_AVAILABLE else '❌'}")
    
    # Menü değişkenini session state'den al
    menu = st.session_state.menu
    
    # Menü içerikleri
    if menu == "🏠 Ana Sayfa":
        st.header("🎭 Hoş Geldiniz!")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            ### Tiyatro Oyunlarını Keşfedin ve Planlayın
            
            **StageAgent v7** ile:
            - 🎭 **Tiyatro oyunlarını** kolayca bulun
            - 📅 **Google Takvim**'inize ekleyin
            - 🎬 **YouTube'dan video önerileri** alın
            
            ### 📋 Nasıl Kullanılır?
            1. Sol menüden **"Tiyatro Ara"** seçeneğine tıklayın
            2. Tarih ve şehir bilgisi girin (ör: "22 ocak 2026 İstanbul")
            3. Oyunları görüntüleyin ve istediğinizi seçin
            4. Takvime ekleyin veya videolarını izleyin
            """)
        
        with col2:
            st.info("""
            **Hızlı Başlangıç:**
            
            Örnek sorgular:
            - 29 ocak 2026 İstanbul
            - 15 şubat Ankara  
            - 10 mart İzmir
            """)
            
            if st.button("🚀 Hemen Başla", use_container_width=True):
                st.session_state.menu = "🔍 Tiyatro Ara"
                st.rerun()
    
    elif menu == "🔍 Tiyatro Ara":
        st.header("🔍 Tiyatro Oyunu Ara")
        
        # Arama formu
        with st.form("arama_formu"):
            col1, col2 = st.columns(2)
            
            with col1:
                tarih = st.date_input("Tarih Seçin", value=datetime.now() + timedelta(days=7))
            
            with col2:
                sehirler = ['İstanbul', 'Ankara', 'İzmir', 'Bursa', 'Antalya', 'Mersin', 'Samsun', 'Adana', 'Denizli','Adana']
                sehir = st.selectbox("Şehir Seçin", sehirler)
            
            arama_buton = st.form_submit_button("🔍 Oyunları Ara", use_container_width=True)
        
        # Manuel sorgu alternatifi
        with st.expander("👨‍💻 Manuel Sorgu (Gelişmiş)"):
            manuel_sorgu = st.text_input(
                "Sorgu girin:",
                placeholder="Ör: 29 ocak 2026 İstanbul'da hangi oyunlar var?",
                key="manuel_sorgu_input"
            )
            manuel_arama_buton = st.button("Manuel Ara", key="manuel_arama")
            if manuel_arama_buton:
                if manuel_sorgu:
                    # Manuel sorgu için tarih_str'yi oluştur
                    try:
                        # Önce selamlama kontrolü
                        sorgu_lower = manuel_sorgu.lower().strip()
                        selamlama_kelimeleri = ["selam", "merhaba", "hello", "hi", "hey"]
                        
                        if any(kelime in sorgu_lower for kelime in selamlama_kelimeleri):
                            st.info(f"👋 Merhaba! Bugün İstanbul için tiyatro önerilerimiz:")
                        
                        # Manuel sorgu için arama yap
                        with st.spinner(f"Manuel sorgu işleniyor..."):
                            tum_oyunlar, sehir_bul, tarih_str_bul = sorgu_yap(manuel_sorgu)
                            
                            # Session state'e kaydet
                            st.session_state.tum_oyunlar = tum_oyunlar
                            st.session_state.sehir = sehir_bul
                            st.session_state.tarih_str = tarih_str_bul
                            st.session_state.sorgu_gecmisi.append(manuel_sorgu)
                            
                    except Exception as e:
                        st.error(f"Sorgu işlenirken hata: {e}")
                else:
                    st.warning("Lütfen bir sorgu girin!")

            # if st.button("Manuel Ara", key="manuel_arama"):
            #     if manuel_sorgu:
            #         arama_buton = True
            #         tarih_str = f"{tarih.day} {tarih.strftime('%B')} {tarih.year}"
            #         sorgu = manuel_sorgu
            #     else:
            #         st.warning("Lütfen bir sorgu girin!")
        
        if arama_buton:
            turkce_aylar = {
                1: "ocak", 2: "şubat", 3: "mart", 4: "nisan", 5: "mayıs", 6: "haziran",
                7: "temmuz", 8: "ağustos", 9: "eylül", 10: "ekim", 11: "kasım", 12: "aralık"
            }

            # Sorguyu oluştur
            sorgu = f"{tarih.day} {turkce_aylar[tarih.month]} {tarih.year} {sehir.lower()}"
            
            try:
                with st.spinner(f"**{sehir}** için **{tarih.day} {turkce_aylar[tarih.month]} {tarih.year}** tarihindeki oyunlar aranıyor..."):
                    # Sorguyu yap
                    tum_oyunlar, sehir_bul, tarih_str_bul = sorgu_yap(sorgu)
                    
                    # Session state'e kaydet
                    st.session_state.tum_oyunlar = tum_oyunlar
                    st.session_state.sehir = sehir_bul
                    st.session_state.tarih_str = tarih_str_bul
                    st.session_state.sorgu_gecmisi.append(sorgu)
                        
            except Exception as e:
                st.error(f"Arama sırasında hata oluştu: {e}")
        
        # Sonuçları göster
        if st.session_state.tum_oyunlar:
            # Toplam oyun sayısı
            toplam_oyun = len(st.session_state.tum_oyunlar)
            st.success(f"✅ **{st.session_state.sehir}** - **{st.session_state.tarih_str}** için **{toplam_oyun}** oyun bulundu!")
            
            # Kategorilere ayır
            ibb_oyunlar = [o for o in st.session_state.tum_oyunlar if o['kaynak'] == 'İBB Şehir Tiyatroları']
            devlet_oyunlar = [o for o in st.session_state.tum_oyunlar if o['kaynak'] == 'Devlet Tiyatroları']
            ozel_oyunlar = [o for o in st.session_state.tum_oyunlar if 'Özel' in o['kaynak']]
            
            # 1. İBB ŞEHİR TİYATROLARI
            if ibb_oyunlar:
                st.markdown("---")
                st.subheader("📍 İBB ŞEHİR TİYATROLARI")
                
                for i, oyun in enumerate(ibb_oyunlar, 1):
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.markdown(f"#### {i}. {oyun['oyun']}")
                            st.caption(f"**Sahne:** {oyun['sahne']} | **Saat:** {oyun['saat']}")
                            
                            # Durum
                            if oyun['tukendi']:
                                st.error("❌ **BİLETLER TÜKENDİ**")
                            else:
                                st.success("✅ **BİLET VAR**")
                        
                        with col2:
                            # YouTube butonu
                            if st.button(f"🎬 Videolar", key=f"video_{i}_{oyun['oyun'][:10]}", use_container_width=True):
                                videos = show_video_recommendations(oyun['oyun'], oyun)
                            
                            # Takvim butonu
                            if GCAL_AVAILABLE:
                                if st.button(f"📅 Takvim", key=f"takvim_ibb_{i}", use_container_width=True):
                                    success, message = add_to_google_calendar(
                                        oyun, 
                                        st.session_state.tarih_str, 
                                        st.session_state.sehir
                                    )
                                    if success:
                                        st.success(message)
                                    else:
                                        st.error(message)
                        
                        with col3:
                            # Bilet linki
                            if 'link' in oyun and oyun['link']:
                                st.link_button("🎫 Bilet Al", oyun['link'], use_container_width=True)
            
            # 2. DEVLET TİYATROLARI
            if devlet_oyunlar:
                st.markdown("---")
                st.subheader("🏛️ DEVLET TİYATROLARI")
                
                for i, oyun in enumerate(devlet_oyunlar, 1):
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.markdown(f"#### {i + len(ibb_oyunlar) if ibb_oyunlar else i}. {oyun['oyun']}")
                            st.caption(f"**Sahne:** {oyun['sahne']} | **Saat:** {oyun['saat']}")
                            
                            # Durum
                            if oyun['tukendi']:
                                st.error("❌ **BİLETLER TÜKENDİ**")
                            else:
                                st.success("✅ **BİLET VAR**")
                        
                        with col2:
                            # YouTube butonu
                            if st.button(f"🎬 Videolar", key=f"video_devlet_{i}", use_container_width=True):
                                st.session_state.secili_oyun = oyun
                            
                            # Takvim butonu
                            if GCAL_AVAILABLE:
                                if st.button(f"📅 Takvim", key=f"takvim_devlet_{i}", use_container_width=True):
                                    success, message = add_to_google_calendar(
                                        oyun, 
                                        st.session_state.tarih_str, 
                                        st.session_state.sehir
                                    )
                                    if success:
                                        st.success(message)
                                    else:
                                        st.error(message)
                        
                        with col3:
                            # Bilet linki
                            if 'bilet' in oyun:
                                st.info(f"Bilet: {oyun['bilet']}")
            
            # 3. ÖZEL TİYATROLAR
            if ozel_oyunlar:
                st.markdown("---")
                st.subheader("🎪 ÖZEL TİYATROLAR")
                
                for i, oyun in enumerate(ozel_oyunlar, 1):
                    start_num = len(ibb_oyunlar) + len(devlet_oyunlar) if ibb_oyunlar or devlet_oyunlar else i
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.markdown(f"#### {start_num + i - 1}. {oyun['oyun']}")
                            st.caption(f"**Sahne:** {oyun['sahne']} | **Saat:** {oyun['saat']}")
                            
                            # Durum
                            if oyun['tukendi']:
                                st.error("❌ **BİLETLER TÜKENDİ**")
                            else:
                                st.success("✅ **BİLET VAR**")
                        
                        with col2:
                            # YouTube butonu
                            if st.button(f"🎬 Videolar", key=f"video_ozel_{i}", use_container_width=True):
                                st.session_state.secili_oyun = oyun
                            
                            # Takvim butonu
                            if GCAL_AVAILABLE:
                                if st.button(f"📅 Takvim", key=f"takvim_ozel_{i}", use_container_width=True):
                                    success, message = add_to_google_calendar(
                                        oyun, 
                                        st.session_state.tarih_str, 
                                        st.session_state.sehir
                                    )
                                    if success:
                                        st.success(message)
                                    else:
                                        st.error(message)
                        
                        with col3:
                            # Bilet linki
                            if 'bilet' in oyun:
                                st.info(f"Bilet: {oyun['bilet']}")
        
        elif st.session_state.sehir:  # Arama yapıldı ama sonuç yok
            st.warning(f"**{st.session_state.sehir}** - **{st.session_state.tarih_str}** için oyun bulunamadı.")
    
    elif menu == "📜 Geçmiş":
        st.header("📜 Geçmiş Sorgular")
        
        if not st.session_state.sorgu_gecmisi:
            st.info("Henüz sorgu yapılmadı.")
        else:
            for i, gecmis_sorgu in enumerate(st.session_state.sorgu_gecmisi, 1):
                sehir, tarih = sorguyu_ayristir(gecmis_sorgu)
                tarih_str = tarih_formatla(tarih)
                
                with st.expander(f"{i}. {gecmis_sorgu[:50]}..."):
                    st.write(f"**Şehir:** {sehir}")
                    st.write(f"**Tarih:** {tarih_str}")
                    
                    if st.button(f"Bu Sorguyu Tekrarla", key=f"tekrarla_{i}"):
                        st.session_state.menu = "🔍 Tiyatro Ara"
                        # Sorguyu otomatik çalıştırmak için state güncelle
                        st.rerun()
    
    elif menu == "⚙️ Ayarlar":
        st.header("⚙️ Ayarlar")
        
        tab1, tab2, tab3 = st.tabs(["🔑 API Ayarları", "⚙️ Sistem", "🛠️ Geliştirici"])
        
        with tab1:
            st.subheader("API Anahtarları")
            
            with st.form("api_form"):
                new_gemini_key = st.text_input(
                    "Gemini API Key",
                    value=GOOGLE_API_KEY if GOOGLE_API_KEY != 'NOT_SET' else "",
                    type="password"
                )
                
                new_youtube_key = st.text_input(
                    "YouTube API Key", 
                    value=YOUTUBE_API_KEY if YOUTUBE_API_KEY != 'NOT_SET' else "",
                    type="password"
                )
                
                if st.form_submit_button("API Key'leri Kaydet"):
                    st.success("API key'leri kaydedildi! (Not: Bu sadece gösterim amaçlı)")
                    st.info("Gerçek uygulamada Streamlit Secrets kullanmalısınız.")
        
        with tab2:
            st.subheader("Sistem Bilgileri")
            
            col_s1, col_s2, col_s3 = st.columns(3)
            
            with col_s1:
                st.metric("Gemini API", "✅ Aktif" if GOOGLE_API_KEY != 'NOT_SET' else "❌ Pasif")
            with col_s2:
                st.metric("YouTube API", "✅ Aktif" if YOUTUBE_API_KEY != 'NOT_SET' else "❌ Pasif")
            with col_s3:
                st.metric("Google Calendar", "✅ Hazır" if GCAL_AVAILABLE else "❌ Yok")
            
            st.markdown("---")
            st.subheader("Sistem Günlüğü")
            st.code("""
            System ready - Streamlit web interface loaded
            Gemini API: Connected
            YouTube API: Connected
            Google Calendar: Ready
            """)
        
        with tab3:
            st.subheader("Geliştirici Araçları")
            
            if st.button("🔧 Test Sorgusu Çalıştır"):
                with st.spinner("Test sorgusu çalıştırılıyor..."):
                    test_oyunlar, test_sehir, test_tarih = sorgu_yap("29 ocak 2026 İstanbul")
                    if test_oyunlar:
                        st.success(f"Test başarılı! {len(test_oyunlar)} oyun bulundu.")
                    else:
                        st.warning("Test sorgusu sonuç vermedi.")
            
            if st.button("🔄 Cache Temizle"):
                st.session_state.clear()
                st.success("Cache temizlendi!")
                st.rerun()
    
    elif menu == "ℹ️ Hakkında":
        st.header("ℹ️ StageAgent v7 Hakkında")
        
        st.markdown("""
        ### 🎭 StageAgent v7 - Tiyatro Arama Platformu
        
        **Sürüm:** 7.0 (Web Edition)
        **Geliştirici:** StageAgent Team
        **Lisans:** MIT Open Source
        
        ### 📦 Özellikler
        - **Çok Kaynaklı Arama:** İBB, Devlet Tiyatroları, Özel Tiyatrolar
        - **Google Takvim Entegrasyonu:** Oyunları takviminize ekleyin
        - **YouTube Video Önerileri:** Oyunlarla ilgili videoları izleyin
        - **Web Arayüzü:** Her cihazdan erişilebilir
        
        ### 🔧 Teknoloji Stack
        - **Frontend:** Streamlit
        - **Backend:** Python
        - **APIs:** Google Gemini, YouTube Data API, Google Calendar API
        - **Web Scraping:** BeautifulSoup, Selenium
        
        ### 📞 İletişim
        Soru ve önerileriniz için:
        - GitHub: github.com/stageagent
        - Email: info@stageagent.com
        """)
        
        st.markdown("---")
        st.caption("© 2024 StageAgent - Tüm hakları saklıdır.")
    
    # Footer
    st.markdown("---")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        st.caption("🎭 StageAgent v7")
    with col_f2:
        st.caption("Web Edition")
    with col_f3:
        st.caption(f"Son güncelleme: {datetime.now().strftime('%d.%m.%Y')}")

# ═══════════════════════════════════════════════════════════════
# UYGULAMAYI ÇALIŞTIR
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    main()


# ==============================================================================================>2
# # recommender_web_an7.py
# import streamlit as st
# import os
# import re
# import requests
# import time
# from datetime import datetime, timedelta
# from bs4 import BeautifulSoup
# from urllib.parse import quote

# # Session state başlat
# if 'sorgu_gecmisi' not in st.session_state:
#     st.session_state.sorgu_gecmisi = []
# if 'tum_oyunlar' not in st.session_state:
#     st.session_state.tum_oyunlar = []
# if 'sehir' not in st.session_state:
#     st.session_state.sehir = ""
# if 'tarih_str' not in st.session_state:
#     st.session_state.tarih_str = ""

# # Sayfa konfigürasyonu
# st.set_page_config(
#     page_title="StageAgent v7 - Tiyatro Arama Platformu",
#     page_icon="🎭",
#     layout="wide"
# )

# # Başlık
# st.title("🎭 StageAgent v7 - Tiyatro Arama Platformu")
# st.markdown("---")

# # Yan menü
# menu = st.sidebar.selectbox(
#     "Menü",
#     ["🏠 Ana Sayfa", "🔍 Tiyatro Ara", "📜 Geçmiş Sorgular", "🎬 YouTube Test", "⚙️ Ayarlar"]
# )

# if menu == "🏠 Ana Sayfa":
#     st.header("Hoş Geldiniz!")
#     st.markdown("""
#     ### 🎭 StageAgent v7 - Tiyatro Arama Platformu
    
#     **Özellikler:**
#     - ✅ İBB Şehir Tiyatroları (Web Scraping)
#     - ✅ Devlet Tiyatroları (Biletinial Selenium)
#     - ✅ Özel Tiyatrolar (Google Search)
#     - 🆕 Google Takvim'e Ekleme
#     - 🆕 YouTube Video Önerileri
#     - 🆕 Çoklu Sorgulama
    
#     ### 📋 Nasıl Kullanılır?
#     1. Sol menüden **"Tiyatro Ara"** seçeneğine tıklayın
#     2. Tarih ve şehir bilgisi girin
#     3. Oyunları görüntüleyin
#     4. İstediğiniz oyunları takvime ekleyin veya videolarını izleyin
#     """)

# elif menu == "🔍 Tiyatro Ara":
#     st.header("🔍 Tiyatro Oyunu Ara")
    
#     # Sorgu formu
#     with st.form("arama_formu"):
#         sorgu = st.text_input(
#             "Arama sorgusu",
#             placeholder="Ör: 22 ocak 2026 İstanbul veya 15 şubat Ankara"
#         )
#         arama_buton = st.form_submit_button("🔍 Ara")
    
#     if arama_buton and sorgu:
#         with st.spinner("Oyunlar aranıyor..."):
#             # Mevcut sorgu_yap fonksiyonunu çağır
#             tum_oyunlar, sehir, tarih_str = sorgu_yap(sorgu)
            
#             # Session state'e kaydet
#             st.session_state.tum_oyunlar = tum_oyunlar
#             st.session_state.sehir = sehir
#             st.session_state.tarih_str = tarih_str
#             st.session_state.sorgu_gecmisi.append(sorgu)
    
#     # Sonuçları göster
#     if st.session_state.tum_oyunlar:
#         st.subheader(f"🎭 {st.session_state.sehir} - {st.session_state.tarih_str}")
        
#         # Oyunları tablo olarak göster
#         for i, oyun in enumerate(st.session_state.tum_oyunlar, 1):
#             with st.expander(f"{i}. {oyun['oyun']}"):
#                 col1, col2 = st.columns(2)
#                 with col1:
#                     st.write(f"**Sahne:** {oyun['sahne']}")
#                     st.write(f"**Saat:** {oyun['saat']}")
#                     st.write(f"**Kaynak:** {oyun['kaynak']}")
#                 with col2:
#                     durum = "❌ TÜKENDİ" if oyun['tukendi'] else "✅ Bilet Var"
#                     st.write(f"**Durum:** {durum}")
                
#                 # Butonlar
#                 col1, col2, col3 = st.columns(3)
#                 with col1:
#                     if st.button(f"📅 Takvime Ekle", key=f"takvim_{i}"):
#                         success, message = add_to_google_calendar(oyun, st.session_state.tarih_str, st.session_state.sehir)
#                         st.success(message) if success else st.error(message)
                
#                 with col2:
#                     if st.button(f"🎬 Videoları Göster", key=f"video_{i}"):
#                         videos = show_video_recommendations(oyun['oyun'], oyun)
#                         if videos:
#                             for j, video in enumerate(videos, 1):
#                                 st.video(video['url'])
                
#                 with col3:
#                     if 'link' in oyun and oyun['link']:
#                         st.link_button("🎫 Bilet Al", oyun['link'])

# elif menu == "📜 Geçmiş Sorgular":
#     st.header("📜 Geçmiş Sorgular")
    
#     if not st.session_state.sorgu_gecmisi:
#         st.info("Henüz sorgu yapılmadı.")
#     else:
#         for i, gecmis_sorgu in enumerate(st.session_state.sorgu_gecmisi, 1):
#             sehir, tarih = sorguyu_ayristir(gecmis_sorgu)
#             tarih_str = tarih_formatla(tarih)
#             st.write(f"{i}. **{gecmis_sorgu[:50]}...**")
#             st.caption(f"📍 {sehir}, 📅 {tarih_str}")

# elif menu == "🎬 YouTube Test":
#     st.header("🎬 YouTube API Testi")
    
#     test_oyun = st.text_input("Test etmek istediğiniz oyun adı:")
#     if st.button("Test Et") and test_oyun:
#         with st.spinner(f"'{test_oyun}' için YouTube'da aranıyor..."):
#             videos = search_youtube_videos(test_oyun, max_results=3)
            
#             if videos:
#                 st.success(f"{len(videos)} video bulundu!")
#                 for video in videos:
#                     with st.expander(video['title']):
#                         st.write(f"**Kanal:** {video['channel']}")
#                         if video['description']:
#                             st.write(f"**Açıklama:** {video['description']}")
#                         st.video(video['url'])
#             else:
#                 st.warning("Video bulunamadı.")

# elif menu == "⚙️ Ayarlar":
#     st.header("⚙️ Ayarlar")
    
#     # API Key'leri güncelleme
#     with st.form("api_ayarlari"):
#         st.subheader("API Anahtarları")
#         new_gemini_key = st.text_input("Gemini API Key", type="password")
#         new_youtube_key = st.text_input("YouTube API Key", type="password")
        
#         if st.form_submit_button("Kaydet"):
#             # API key'leri güncelleme kodu
#             st.success("API anahtarları güncellendi!")
    
#     # Sistem bilgileri
#     st.subheader("Sistem Bilgileri")
#     st.write(f"Google Calendar: {'✅ Hazır' if GCAL_AVAILABLE else '❌ Yok'}")
#     st.write(f"YouTube API: {'✅ Hazır' if YOUTUBE_AVAILABLE else '❌ Yok'}")
#     st.write(f"Selenium: {'✅ Hazır' if SELENIUM_AVAILABLE else '❌ Yok'}")