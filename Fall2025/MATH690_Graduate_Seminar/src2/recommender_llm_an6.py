"""
StageAgent v6 - Google Calendar + YouTube Videoları Entegrasyonu

Andrew Ng Agentic Pattern: TOOL USE + MULTI-QUERY + CONTEXT ENRICHMENT
- Kullanıcı birden fazla tarih için sorgu yapabilir
- Her sorguda Google Takvim'e ekleyebilir
- Seçilen oyun için YouTube'dan video önerileri alabilir
- Ana menü ile yönetim

KURULUM:
1. Google Cloud Console'da proje oluştur
2. Google Calendar API'yi etkinleştir
3. YouTube Data API v3'ü etkinleştir
4. OAuth 2.0 credentials oluştur (Desktop app)
5. API Key'leri .env dosyasına ekle

.env dosyası:
GOOGLE_API_KEY=your_gemini_api_key
YOUTUBE_API_KEY=your_youtube_api_key
"""

import os
import re
import requests
import time
import sys
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import quote

print("\n" + "="*80)
print("🎭 STAGEAGENT v6 - Google Takvim + YouTube Videoları + Çoklu Sorgu")
print("="*80)

# ═══════════════════════════════════════════════════════════════
# IMPORT'LAR - YENİ: YouTube API
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

# 4. YouTube API imports - YENİ
try:
    from googleapiclient.discovery import build as yt_build
    YOUTUBE_AVAILABLE = True
    print("   ✅ YouTube API kütüphaneleri hazır")
except ImportError as e:
    YOUTUBE_AVAILABLE = False
    print(f"   ⚠️  YouTube API yok: {e}")

# 5. QR Code imports (opsiyonel)
try:
    import qrcode
    from PIL import Image
    QR_AVAILABLE = True
    print("   ✅ QR Code kütüphaneleri hazır")
except ImportError:
    QR_AVAILABLE = False
    print("   ⚠️  QR Code yok: pip install qrcode[pil]")

# ═══════════════════════════════════════════════════════════════
# YAPILANDIRMA - YENİ API KEY'LER
# ═══════════════════════════════════════════════════════════════

# API Key kontrolü - GEMINI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("\n🔑 GOOGLE_API_KEY (Gemini) bulunamadı!")
    GOOGLE_API_KEY = input("   Lütfen Gemini API Key girin: ").strip()
    if not GOOGLE_API_KEY:
        print("❌ API Key gerekiyor!")
        sys.exit(1)

# API Key kontrolü - YOUTUBE (YENİ)
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
if not YOUTUBE_API_KEY and YOUTUBE_AVAILABLE:
    print("\n🎬 YOUTUBE_API_KEY bulunamadı!")
    YOUTUBE_API_KEY = input("   Lütfen YouTube API Key girin (boş bırakabilirsiniz): ").strip()
    if not YOUTUBE_API_KEY:
        print("   ⚠️  YouTube özellikleri devre dışı bırakıldı")
        YOUTUBE_AVAILABLE = False

print(f"   ✅ Gemini API Key: {GOOGLE_API_KEY[:10]}...")
if YOUTUBE_AVAILABLE and YOUTUBE_API_KEY:
    print(f"   ✅ YouTube API Key: {YOUTUBE_API_KEY[:10]}...")

# Client oluştur
try:
    client = genai.Client(api_key=GOOGLE_API_KEY)
    print("   ✅ Gemini API bağlantısı kuruldu")
except Exception as e:
    print(f"   ❌ Gemini bağlantı hatası: {e}")
    sys.exit(1)

# YouTube client oluştur (YENİ)
youtube = None
if YOUTUBE_AVAILABLE and YOUTUBE_API_KEY:
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
print("🚀 SİSTEM HAZIR - YouTube videolarıyla zenginleştirilmiş!")
print("="*80)

# ═══════════════════════════════════════════════════════════════
# YENİ: YOUTUBE FONKSİYONLARI
# ═══════════════════════════════════════════════════════════════

def search_youtube_videos(oyun_adi, max_results=3):
    """
    YouTube'dan oyunla ilgili videoları ara
    """
    if not YOUTUBE_AVAILABLE or not youtube:
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
                    order="relevance"  # En alakalı sonuçlar
                )
                
                response = request.execute()
                
                for item in response.get('items', []):
                    video_id = item['id']['videoId']
                    title = item['snippet']['title']
                    description = item['snippet']['description'][:100] + "..." if len(item['snippet']['description']) > 100 else item['snippet']['description']
                    thumbnail = item['snippet']['thumbnails']['default']['url']
                    channel = item['snippet']['channelTitle']
                    
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

def generate_qr_code(url, filename="youtube_qr.png"):
    """QR kodu oluştur (opsiyonel)"""
    if not QR_AVAILABLE:
        return None
    
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(filename)
        return filename
    except Exception as e:
        print(f"   ⚠️  QR kod hatası: {e}")
        return None

def show_video_recommendations(oyun_adi, oyun_bilgisi=None):
    """
    Oyun için video önerilerini göster
    
    Args:
        oyun_adi: Tiyatro oyunu adı
        oyun_bilgisi: Oyun hakkında ek bilgi (opsiyonel)
    """
    if not YOUTUBE_AVAILABLE:
        print("\n   ⚠️  YouTube API kullanılamıyor. Video önerileri devre dışı.")
        return []
    
    print(f"\n   🎬 '{oyun_adi}' için YouTube'da aranıyor...")
    videos = search_youtube_videos(oyun_adi, max_results=3)
    
    if not videos:
        print("   ⚠️  Bu oyun için video bulunamadı.")
        return []
    
    print(f"   ✅ {len(videos)} video bulundu:")
    
    video_listesi = []
    for i, video in enumerate(videos, 1):
        print(f"\n   📹 [{i}] {video['title']}")
        print(f"       👤 Kanal: {video['channel']}")
        print(f"       📝 {video['description']}")
        print(f"       🔗 {video['url']}")
        video_listesi.append(video)
    
    return video_listesi

def play_video_interactive(videos):
    """
    Kullanıcıyla etkileşimli video seçimi
    """
    if not videos:
        return
    
    while True:
        print("\n   💡 İzlemek istediğiniz video numarasını girin")
        print("      (Birden fazla için virgülle ayırın: 1,3)")
        print("      (Çıkmak için 'q' veya 'çık' yazın)")
        
        secim = input("\n   🎥 Seçiminiz: ").strip().lower()
        
        if secim in ['q', 'çık', 'cik', 'exit', '']:
            print("   👋 Video seçimi tamamlandı")
            break
        
        try:
            if secim == 'hepsi' or secim == 'all':
                # Tüm videoların linklerini göster
                print("\n   🔗 TÜM VİDEO LİNKLERİ:")
                for i, video in enumerate(videos, 1):
                    print(f"   {i:2d}. {video['title'][:50]}...")
                    print(f"       {video['url']}")
                break
            
            # Virgülle ayrılmış numaraları parse et
            numaralar = [int(n.strip()) for n in secim.split(',')]
            
            for numara in numaralar:
                if 1 <= numara <= len(videos):
                    video = videos[numara - 1]
                    print(f"\n   ▶️  [{numara}] {video['title']}")
                    print(f"   🔗 Link: {video['url']}")
                    
                    # QR kodu oluştur (opsiyonel)
                    if QR_AVAILABLE:
                        qr_file = generate_qr_code(video['url'], f"youtube_qr_{numara}.png")
                        if qr_file:
                            print(f"   📱 QR Kod: {qr_file} (telefonunuzla tarayın)")
                    
                    # Tarayıcıda açma seçeneği
                    acilsin_mi = input("   🌐 Tarayıcıda açılsın mı? (e/h): ").strip().lower()
                    if acilsin_mi in ['e', 'evet', 'y', 'yes']:
                        import webbrowser
                        webbrowser.open(video['url'])
                        print("   ✅ Tarayıcı açılıyor...")
                else:
                    print(f"   ❌ Geçersiz numara: {numara}")
            
        except ValueError:
            print("   ❌ Geçersiz giriş. Lütfen numara girin.")

# ═══════════════════════════════════════════════════════════════
# GOOGLE TAKVİM FONKSİYONLARI (v5'ten aynı)
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
# YARDIMCI FONKSİYONLAR (v5'ten aynı)
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
# KAYNAK FONKSİYONLARI (v5'ten aynı - bu kısmı kopyalamanız gerekecek)
# ═══════════════════════════════════════════════════════════════

# BU FONKSİYONLARI recommender_llm_an5.py'den KOPYALAYIN:
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
    """Ana sorgu fonksiyonu - tüm kaynakları ara"""
    sehir, tarih = sorguyu_ayristir(sorgu)
    tarih_str = tarih_formatla(tarih)
    
    print(f"\n🔍 Arama yapılıyor...")
    print(f"   📍 Şehir: {sehir}")
    print(f"   📅 Tarih: {tarih_str}")
    
    # Tarihten gün ve ay bilgilerini çıkar
    yil, ay, gun = tarih.split('-')
    hedef_gun = int(gun)
    
    # Ay numarasını ay adına çevir
    aylar = ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
             'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
    hedef_ay = aylar[int(ay)] if int(ay) <= 12 else "Ocak"
    
    # İBB Şehir Tiyatroları
    print(f"\n🎭 İBB Şehir Tiyatroları aranıyor...")
    ibb_oyunlar = ibb_sehir_tiyatrolari_ara(hedef_gun)
    
    # Devlet Tiyatroları
    print(f"🎭 Devlet Tiyatroları aranıyor...")
    devlet_oyunlar = biletinial_devlet_tiyatrolari_ara(sehir, hedef_gun, hedef_ay)
    
    # Özel Tiyatrolar
    print(f"🎭 Özel Tiyatrolar aranıyor...")
    ozel_oyunlar = ozel_tiyatrolar_ara(sehir, tarih_str)
    
    # Tüm oyunları birleştir
    tum_oyunlar = []
    if ibb_oyunlar:
        tum_oyunlar.extend(ibb_oyunlar)
    if devlet_oyunlar:
        tum_oyunlar.extend(devlet_oyunlar)
    if ozel_oyunlar:
        tum_oyunlar.extend(ozel_oyunlar)
    
    # ÖNCE OYUNLARI GÖSTER
    if tum_oyunlar:
        tum_oyunlar = tum_oyunlari_listele(ibb_oyunlar, devlet_oyunlar, ozel_oyunlar, tarih_str, sehir)
        return tum_oyunlar, sehir, tarih_str
    else:
        print("❌ Hiç oyun bulunamadı!")
        return [], sehir, tarih_str
    
# takvim_islemleri
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
# YENİ: GELİŞTİRİLMİŞ TAKVİM İŞLEMLERİ (YouTube entegrasyonlu)
# ═══════════════════════════════════════════════════════════════

def takvim_islemleri_gelismis(tum_oyunlar, sehir, tarih_str):
    """
    Google Takvim işlemlerini yönet - YouTube entegrasyonlu
    """
    if not tum_oyunlar:
        print("\n⚠️  Bu tarihte oyun bulunamadı.")
        return False
    
    # ═══════════════════════════════════════════════════════════════
    # GOOGLE TAKVİM ENTEGRASYONU + YOUTUBE
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "═" * 80)
    print("📅 GOOGLE TAKVİM'E EKLEME + YOUTUBE VİDEOLARI")
    print("═" * 80)
    
    if not GCAL_AVAILABLE:
        print("\n⚠️  Google Calendar kütüphaneleri kurulu değil.")
        print("   pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        return False
    
    while True:
        print("\n💡 Takvime eklemek istediğiniz oyunun numarasını girin")
        print("   (Birden fazla için virgülle ayırın: 1,3,5)")
        print("   (YouTube videolarını görüntülemek için 'video X' yazın)")
        print("   (Takvim eklemeden çıkmak için '/q','/', 'q' veya 'çık' yazın)")
        print("   (Ana menüye dönmek için 'ana' yazın)")
        
        secim = input("\n🎫 Seçiminiz: ").strip().lower()
        
        if secim in ['q', 'çık', 'cik', 'exit', '']:
            print("\n👋 Takvim ekleme tamamlandı!")
            return False
        elif secim == 'ana':
            print("\n🏠 Ana menüye dönülüyor...")
            return True
        elif secim.startswith('video '):
            # Video görüntüleme komutu: "video 13"
            try:
                oyun_numarasi = int(secim.split()[1])
                if 1 <= oyun_numarasi <= len(tum_oyunlar):
                    oyun = tum_oyunlar[oyun_numarasi - 1]
                    print(f"\n🎬 '{oyun['oyun']}' için video araştırması...")
                    videos = show_video_recommendations(oyun['oyun'], oyun)
                    if videos:
                        play_video_interactive(videos)
                else:
                    print(f"\n❌ Geçersiz oyun numarası: {oyun_numarasi}")
            except (ValueError, IndexError):
                print("\n❌ Geçersiz format. Örnek: 'video 13'")
            continue
        
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
                    
                    # YouTube video önerilerini göster
                    print(f"\n⏳ [{numara}] {oyun['oyun']} hakkında araştırma yapılıyor...")
                    videos = show_video_recommendations(oyun['oyun'], oyun)
                    
                    # Videoları izlemek isteyip istemediğini sor
                    if videos:
                        izle = input("   🎬 Videoları izlemek ister misiniz? (e/h): ").strip().lower()
                        if izle in ['e', 'evet', 'y', 'yes']:
                            play_video_interactive(videos)
                    
                    # Takvime ekleme
                    takvim_ekle = input(f"   📅 '{oyun['oyun']}' takvime eklensin mi? (e/h): ").strip().lower()
                    if takvim_ekle in ['e', 'evet', 'y', 'yes']:
                        print(f"   ⏳ Takvime ekleniyor...")
                        success, message = add_to_google_calendar(oyun, tarih_str, sehir)
                        print(f"   {message}")
                    else:
                        print(f"   ⏭️  Takvime ekleme atlandı")
                else:
                    print(f"\n❌ Geçersiz numara: {numara}")
                    
        except ValueError:
            print("\n❌ Geçersiz giriş. Lütfen numara girin.")

# ═══════════════════════════════════════════════════════════════
# ANA PROGRAM - GELİŞTİRİLMİŞ (YouTube entegrasyonlu)
# ═══════════════════════════════════════════════════════════════

def main():
    print("🎭 STAGEAGENT v6 - Google Takvim + YouTube Videoları + Çoklu Sorgu")
    print("═" * 80)
    print("   Özellikler:")
    print("   ✅ İBB Şehir Tiyatroları (Web Scraping)")
    print("   ✅ Devlet Tiyatroları (Biletinial Selenium)")
    print("   ✅ Özel Tiyatrolar (Google Search)")
    print("   🆕 Google Takvim'e Ekleme")
    print("   🆕 YouTube Video Önerileri")
    print("   🆕 QR Kod Oluşturma (telefonla hızlı erişim)")
    print("   🆕 Çoklu Sorgulama (Birden fazla tarih için arama)")
    print("═" * 80)
    
    # Oturum geçmişi
    sorgu_gecmisi = []
    
    while True:
        print("\n" + "═" * 80)
        print("🏠 ANA MENÜ")
        print("═" * 80)
        print("1️⃣  Yeni tiyatro araması yap")
        print("2️⃣  Geçmiş sorguları görüntüle")
        print("3️⃣  YouTube API testi")
        print("4️⃣  Çıkış")
        
        menu_secim = input("\n📋 Seçiminiz (1-4): ").strip()
        
        if menu_secim == '1':
            # Yeni sorgu
            sorgu = input("\n🔍 Ne arıyorsunuz? (ör: 22 ocak 2026 İstanbul): ")
            
            if not sorgu:
                print("\n⚠️  Lütfen geçerli bir sorgu girin.")
                continue
            
            sorgu_gecmisi.append(sorgu)
            
            # Sorguyu yap (v5'ten aynı fonksiyon)
            tum_oyunlar, sehir, tarih_str = sorgu_yap(sorgu)
            
            # Gelişmiş takvim işlemleri (YouTube entegrasyonlu)
            ana_menu_don = takvim_islemleri_gelismis(tum_oyunlar, sehir, tarih_str)
            
            if not ana_menu_don:
                # Takvim işlemlerinden çıkınca ana menüye dön
                continue
            
        elif menu_secim == '2':
            # Geçmiş sorguları göster
            print("\n" + "═" * 80)
            print("📜 SORGULAR GEÇMİŞİ")
            print("═" * 80)
            
            if not sorgu_gecmisi:
                print("\n   Henüz sorgu yapılmadı.")
            else:
                for i, gecmis_sorgu in enumerate(sorgu_gecmisi, 1):
                    sehir, tarih = sorguyu_ayristir(gecmis_sorgu)
                    tarih_str = tarih_formatla(tarih)
                    print(f"\n   {i:2d}. {gecmis_sorgu[:50]}...")
                    print(f"       📍 {sehir}, 📅 {tarih_str}")
            
            input("\n   🔄 Devam etmek için Enter'a basın...")
            
        elif menu_secim == '3':
            # YouTube API testi
            print("\n" + "═" * 80)
            print("🎬 YOUTUBE API TESTİ")
            print("═" * 80)
            
            if not YOUTUBE_AVAILABLE:
                print("\n   ❌ YouTube API kullanılamıyor.")
                print("   💡 Lütfen YOUTUBE_API_KEY ayarlayın.")
                continue
            
            test_oyun = input("\n   🎭 Test etmek istediğiniz oyun adı: ").strip()
            if not test_oyun:
                print("   ⚠️  Oyun adı gerekli.")
                continue
            
            print(f"\n   🔍 '{test_oyun}' için YouTube'da aranıyor...")
            videos = search_youtube_videos(test_oyun, max_results=5)
            
            if videos:
                print(f"\n   ✅ {len(videos)} video bulundu:")
                for i, video in enumerate(videos, 1):
                    print(f"\n   [{i}] {video['title']}")
                    print(f"       👤 {video['channel']}")
                    print(f"       🔗 {video['url']}")
                
                # Video seçimi
                sec = input("\n   🎥 Hangi videoyu test etmek istersiniz? (numara): ").strip()
                if sec.isdigit() and 1 <= int(sec) <= len(videos):
                    video = videos[int(sec) - 1]
                    print(f"\n   ▶️  Test ediliyor: {video['title']}")
                    print(f"   🔗 {video['url']}")
                    
                    # QR kodu oluştur
                    if QR_AVAILABLE:
                        qr_file = generate_qr_code(video['url'], "test_qr.png")
                        if qr_file:
                            print(f"   📱 QR Kod oluşturuldu: {qr_file}")
                    
                    # Tarayıcıda aç
                    acilsin_mi = input("   🌐 Tarayıcıda açılsın mı? (e/h): ").strip().lower()
                    if acilsin_mi in ['e', 'evet', 'y', 'yes']:
                        import webbrowser
                        webbrowser.open(video['url'])
                        print("   ✅ Tarayıcı açılıyor...")
            else:
                print("   ⚠️  Video bulunamadı.")
            
            input("\n   🔄 Devam etmek için Enter'a basın...")
            
        elif menu_secim == '4' or menu_secim.lower() in ['/','/cik','q', 'çık', 'exit']:
            print("\n" + "═" * 80)
            print("👋 Görüşmek üzere! StageAgent v6 oturumu sonlandırıldı.")
            print("═" * 80)
            break
        
        else:
            print("\n❌ Geçersiz seçim. Lütfen 1-4 arası bir seçenek girin.")

if __name__ == "__main__":
    main()