#!/usr/bin/env python3
# debug_biletinial.py - Biletinial sayfa yapısını analiz et
"""
Andrew Ng Prensibi: "Understand your data before building models"
Bu script Biletinial'ın HTML yapısını analiz eder ve doğru selector'ları bulur.
"""

import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def get_driver():
    """Chrome driver oluştur (headless KAPALI - görmek için)"""
    options = Options()
    # options.add_argument("--headless=new")  # Görmek için kapalı
    options.add_argument("--window-size=1920,1080")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def analyze_page():
    driver = None
    try:
        print("=" * 70)
        print("🔍 BİLETİNİAL SAYFA ANALİZİ")
        print("=" * 70)
        
        driver = get_driver()
        driver.get("https://biletinial.com/tr-tr/etkinlik-takvimi/708")
        
        print("\n⏳ Sayfa yükleniyor (5 saniye)...")
        time.sleep(5)
        
        # Ekran görüntüsü al
        driver.save_screenshot("biletinial_screenshot.png")
        print("📸 Ekran görüntüsü kaydedildi: biletinial_screenshot.png")
        
        # HTML'i parse et
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # ════════════════════════════════════════════════════════════════
        # 1. DROPDOWN ANALİZİ
        # ════════════════════════════════════════════════════════════════
        print("\n" + "=" * 70)
        print("📍 ADIM 1: ŞEHİR DROPDOWN ANALİZİ")
        print("=" * 70)
        
        # "İstanbul" kelimesini içeren tüm elementleri bul
        istanbul_elements = soup.find_all(string=re.compile(r'İstanbul', re.IGNORECASE))
        print(f"\n'İstanbul' içeren element sayısı: {len(istanbul_elements)}")
        
        for i, elem in enumerate(istanbul_elements[:10]):
            parent = elem.parent
            if parent:
                print(f"\n  [{i+1}] Parent: <{parent.name}> class='{parent.get('class')}'")
                grandparent = parent.parent
                if grandparent:
                    print(f"      Grandparent: <{grandparent.name}> class='{grandparent.get('class')}'")
        
        # Dropdown/Select elementlerini ara
        print("\n--- Select/Dropdown Elementleri ---")
        
        selectors_to_check = [
            ('select', soup.find_all('select')),
            ('[class*=select]', soup.find_all(class_=re.compile(r'select', re.I))),
            ('[class*=dropdown]', soup.find_all(class_=re.compile(r'dropdown', re.I))),
            ('[class*=filter]', soup.find_all(class_=re.compile(r'filter', re.I))),
            ('[class*=city]', soup.find_all(class_=re.compile(r'city', re.I))),
        ]
        
        for name, elements in selectors_to_check:
            if elements:
                print(f"\n  {name}: {len(elements)} element")
                for elem in elements[:3]:
                    text = elem.get_text(strip=True)[:50]
                    print(f"    - <{elem.name}> class='{elem.get('class')}' text='{text}'")
        
        # ════════════════════════════════════════════════════════════════
        # 2. TABLO ANALİZİ
        # ════════════════════════════════════════════════════════════════
        print("\n" + "=" * 70)
        print("📊 ADIM 2: TABLO ANALİZİ")
        print("=" * 70)
        
        tables = soup.find_all('table')
        print(f"\nToplam tablo sayısı: {len(tables)}")
        
        for t_idx, table in enumerate(tables):
            print(f"\n--- Tablo {t_idx + 1} ---")
            print(f"Class: {table.get('class')}")
            
            rows = table.find_all('tr')
            print(f"Satır sayısı: {len(rows)}")
            
            # Header satırı
            if rows:
                header = rows[0]
                header_cells = header.find_all(['th', 'td'])
                header_texts = [c.get_text(strip=True)[:25] for c in header_cells]
                print(f"Header: {header_texts}")
            
            # İlk 5 veri satırı
            print("\nİlk 5 veri satırı:")
            for r_idx, row in enumerate(rows[1:6]):
                cells = row.find_all('td')
                row_data = []
                for c in cells:
                    text = c.get_text(strip=True)[:20]
                    cls = c.get('class', [])
                    style = c.get('style', '')[:30] if c.get('style') else ''
                    row_data.append(f"'{text}' (cls:{cls})")
                print(f"  Row {r_idx + 1}: {row_data}")
        
        # ════════════════════════════════════════════════════════════════
        # 3. ETKİNLİK HÜCRELERİ ANALİZİ
        # ════════════════════════════════════════════════════════════════
        print("\n" + "=" * 70)
        print("🎭 ADIM 3: ETKİNLİK HÜCRELERİ ANALİZİ")
        print("=" * 70)
        
        # Renkli hücreleri bul (yeşil, sarı, kırmızı)
        colored_cells = soup.find_all('td', class_=True)
        
        # Class isimlerini topla
        all_td_classes = set()
        for td in colored_cells:
            classes = td.get('class', [])
            all_td_classes.update(classes)
        
        print(f"\nTüm TD class'ları: {all_td_classes}")
        
        # Etkinlik içeren hücreleri bul
        event_cells = []
        for td in soup.find_all('td'):
            text = td.get_text(strip=True)
            # Saat formatı içeren hücreler (örn: 20:00)
            if re.search(r'\d{2}:\d{2}', text) and len(text) > 5:
                event_cells.append(td)
        
        print(f"\nSaat içeren hücre sayısı: {len(event_cells)}")
        print("\nÖrnek etkinlik hücreleri:")
        for i, cell in enumerate(event_cells[:10]):
            text = cell.get_text(strip=True)
            cls = cell.get('class', [])
            print(f"  [{i+1}] Class: {cls}")
            print(f"      Text: {text[:60]}")
        
        # ════════════════════════════════════════════════════════════════
        # 4. SELENIUM İLE DROPDOWN TEST
        # ════════════════════════════════════════════════════════════════
        print("\n" + "=" * 70)
        print("🖱️ ADIM 4: SELENIUM DROPDOWN TEST")
        print("=" * 70)
        
        # Tıklanabilir elementleri bul
        print("\nDropdown elementlerini arıyorum...")
        
        # Farklı XPath'leri dene
        xpaths_to_try = [
            ("//div[contains(text(), 'İstanbul')]", "İstanbul text içeren div"),
            ("//span[contains(text(), 'İstanbul')]", "İstanbul text içeren span"),
            ("//button[contains(@class, 'select')]", "select class'lı button"),
            ("//div[contains(@class, 'select')]//span", "select class'lı div içindeki span"),
            ("//div[contains(@class, 'dropdown')]", "dropdown class'lı div"),
            ("//div[contains(@class, 'filter')]", "filter class'lı div"),
            ("//select", "select elementi"),
        ]
        
        for xpath, desc in xpaths_to_try:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                if elements:
                    print(f"\n  ✅ {desc}: {len(elements)} element bulundu")
                    for elem in elements[:2]:
                        try:
                            text = elem.text[:50] if elem.text else "(boş)"
                            tag = elem.tag_name
                            print(f"      <{tag}> '{text}'")
                        except:
                            pass
            except Exception as e:
                print(f"\n  ❌ {desc}: {e}")
        
        # ════════════════════════════════════════════════════════════════
        # 5. ŞEHİR DROPDOWN'U TIKLAMA DENEMESİ
        # ════════════════════════════════════════════════════════════════
        print("\n" + "=" * 70)
        print("🎯 ADIM 5: DROPDOWN TIKLAMA DENEMESİ")
        print("=" * 70)
        
        wait = WebDriverWait(driver, 10)
        
        # Muhtemel dropdown trigger'ları
        dropdown_xpaths = [
            "//div[contains(@class, 'select')]//span[contains(text(), 'İstanbul') or contains(text(), 'Ankara') or contains(text(), 'Seç')]",
            "//div[contains(@class, 'select-box')]",
            "//div[contains(@class, 'city-select')]",
            "//div[contains(@class, 'form-select')]",
            "//button[contains(@class, 'dropdown')]",
            "//div[@role='button']",
            "//div[@role='listbox']",
        ]
        
        for xpath in dropdown_xpaths:
            try:
                element = driver.find_element(By.XPATH, xpath)
                print(f"\n  Bulundu: {xpath[:50]}...")
                print(f"  Tag: {element.tag_name}, Text: '{element.text[:30]}'")
                
                # Tıklamayı dene
                print("  Tıklanıyor...")
                element.click()
                time.sleep(1)
                
                # Açılan menüyü kontrol et
                options = driver.find_elements(By.XPATH, "//li | //div[contains(@class, 'option')]")
                print(f"  Açılan seçenek sayısı: {len(options)}")
                
                # İstanbul'u ara
                istanbul_option = driver.find_elements(By.XPATH, "//li[contains(text(), 'İstanbul')] | //div[contains(text(), 'İstanbul')]")
                if istanbul_option:
                    print(f"  ✅ İstanbul seçeneği bulundu!")
                    # Tıkla
                    istanbul_option[0].click()
                    time.sleep(2)
                    print("  İstanbul seçildi!")
                    
                    # Yeni ekran görüntüsü al
                    driver.save_screenshot("biletinial_istanbul.png")
                    print("  📸 İstanbul seçili ekran görüntüsü kaydedildi")
                    break
                    
            except Exception as e:
                pass
        
        # ════════════════════════════════════════════════════════════════
        # 6. HTML'İ KAYDET
        # ════════════════════════════════════════════════════════════════
        print("\n" + "=" * 70)
        print("💾 HTML KAYDET")
        print("=" * 70)
        
        with open("biletinial_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("\n✅ HTML kaydedildi: biletinial_page.html")
        
        print("\n" + "=" * 70)
        print("🏁 ANALİZ TAMAMLANDI")
        print("=" * 70)
        print("\nŞimdi şunları yap:")
        print("1. biletinial_screenshot.png dosyasına bak")
        print("2. biletinial_page.html dosyasını tarayıcıda aç")
        print("3. Chrome DevTools (F12) ile elementleri incele")
        
        input("\nDevam etmek için Enter'a bas...")
        
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    analyze_page()