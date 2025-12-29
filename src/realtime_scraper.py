# # src/realtime_scraper.py
# """
# Real-Time Theater Scraper - Biletinial'dan Anlık Veri Çekme

# Bu modül, kullanıcı sorgusu geldiğinde biletinial.com'dan
# güncel oyun bilgilerini çeker. Tavily'den çok daha güvenilir!

# Desteklenen şehirler:
# - Istanbul (Avrupa + Anadolu)
# - Ankara
# - Izmir
# - Adana
# - Bursa
# - Antalya
# """

# import requests
# from bs4 import BeautifulSoup
# from datetime import datetime, timedelta
# import re
# from typing import List, Dict, Optional
# import time


# class RealtimeScraper:
#     """
#     Biletinial.com'dan anlık tiyatro bilgisi çeken scraper
#     """
    
#     # Şehir URL'leri
#     CITY_URLS = {
#         'istanbul': [
#             'https://biletinial.com/tr-tr/tiyatro/istanbul-avrupa',
#             'https://biletinial.com/tr-tr/tiyatro/istanbul-anadolu'
#         ],
#         'ankara': ['https://biletinial.com/tr-tr/tiyatro/ankara'],
#         'izmir': ['https://biletinial.com/tr-tr/tiyatro/izmir'],
#         'adana': ['https://biletinial.com/tr-tr/tiyatro/adana'],
#         'bursa': ['https://biletinial.com/tr-tr/tiyatro/bursa'],
#         'antalya': ['https://biletinial.com/tr-tr/tiyatro/antalya'],
#     }
    
#     # Turkish month mapping
#     TURKISH_MONTHS = {
#         'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4,
#         'mayıs': 5, 'haziran': 6, 'temmuz': 7, 'ağustos': 8,
#         'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12,
#         # ASCII versions
#         'subat': 2, 'mayis': 5, 'agustos': 8, 'eylul': 9, 'aralik': 12, 'kasim': 11
#     }
    
#     def __init__(self):
#         self.session = requests.Session()
#         self.session.headers.update({
#             'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
#             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
#             'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
#         })
#         # Cache for avoiding repeated requests
#         self._cache = {}
#         self._cache_time = {}
#         self._cache_duration = 300  # 5 minutes
    
#     def get_plays_for_city(self, city: str, max_plays: int = 20) -> List[Dict]:
#         """
#         Bir şehirdeki tüm oyunları çek
        
#         Args:
#             city: Şehir adı (istanbul, ankara, etc.)
#             max_plays: Maximum oyun sayısı
            
#         Returns:
#             List of play dictionaries
#         """
#         city_lower = city.lower().replace('İ', 'i').replace('ı', 'i')
        
#         if city_lower not in self.CITY_URLS:
#             print(f"⚠️  {city} şehri desteklenmiyor")
#             return []
        
#         # Check cache
#         cache_key = f"city_{city_lower}"
#         if self._is_cache_valid(cache_key):
#             print(f"📦 Using cached data for {city}")
#             return self._cache[cache_key]
        
#         all_plays = []
#         urls = self.CITY_URLS[city_lower]
        
#         for url in urls:
#             print(f"🌐 Fetching: {url}")
#             plays = self._scrape_listing_page(url, city)
#             all_plays.extend(plays)
#             time.sleep(0.5)  # Be nice to the server
        
#         # Remove duplicates
#         unique_plays = self._deduplicate_plays(all_plays)
        
#         # Cache results
#         self._cache[cache_key] = unique_plays[:max_plays]
#         self._cache_time[cache_key] = datetime.now()
        
#         print(f"✅ Found {len(unique_plays)} unique plays in {city}")
        
#         return unique_plays[:max_plays]
    
#     def get_plays_for_date(self, city: str, target_date: datetime, max_plays: int = 10) -> List[Dict]:
#         """
#         Belirli bir tarihteki oyunları getir
        
#         Args:
#             city: Şehir adı
#             target_date: Hedef tarih
#             max_plays: Maximum oyun sayısı
            
#         Returns:
#             Filtered list of plays
#         """
#         # First get all plays
#         all_plays = self.get_plays_for_city(city, max_plays=50)
        
#         # Filter by date
#         matching_plays = []
#         target_str = target_date.strftime("%Y-%m-%d")
        
#         print(f"📅 Filtering for date: {target_str}")
        
#         for play in all_plays:
#             if play.get('dates'):
#                 for date_info in play['dates']:
#                     play_date = date_info.get('date_obj')
#                     if play_date and play_date.strftime("%Y-%m-%d") == target_str:
#                         # Add the matching showtime info
#                         play_copy = play.copy()
#                         play_copy['matching_showtime'] = date_info
#                         matching_plays.append(play_copy)
#                         print(f"   ✓ Match: {play['title']} - {date_info.get('display')}")
#                         break
        
#         print(f"✅ Found {len(matching_plays)} plays for {target_str}")
        
#         return matching_plays[:max_plays]
    
#     def get_plays_for_date_range(self, city: str, start_date: datetime, end_date: datetime, max_plays: int = 15) -> List[Dict]:
#         """
#         Tarih aralığındaki oyunları getir (hafta sonu, bu hafta, vs.)
#         """
#         all_plays = self.get_plays_for_city(city, max_plays=50)
        
#         matching_plays = []
        
#         print(f"📅 Filtering for range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
#         for play in all_plays:
#             if play.get('dates'):
#                 for date_info in play['dates']:
#                     play_date = date_info.get('date_obj')
#                     if play_date and start_date <= play_date <= end_date:
#                         play_copy = play.copy()
#                         play_copy['matching_showtime'] = date_info
#                         matching_plays.append(play_copy)
#                         print(f"   ✓ Match: {play['title']} - {date_info.get('display')}")
#                         break
        
#         return matching_plays[:max_plays]
    
#     def _scrape_listing_page(self, url: str, city: str) -> List[Dict]:
#         """
#         Biletinial listing sayfasından oyunları çek
#         """
#         try:
#             response = self.session.get(url, timeout=15)
#             response.raise_for_status()
            
#             soup = BeautifulSoup(response.text, 'html.parser')
#             plays = []
            
#             # Find play cards - biletinial uses various card structures
#             # Method 1: Look for event cards
#             cards = soup.select('.event-card, .card, .activity-card, [class*="event"], [class*="activity"]')
            
#             if not cards:
#                 # Method 2: Look for links to individual plays
#                 cards = soup.select('a[href*="/tiyatro/"][href*="-"]')
            
#             print(f"   Found {len(cards)} potential cards")
            
#             for card in cards:
#                 play = self._parse_play_card(card, city, url)
#                 if play:
#                     plays.append(play)
            
#             # If no cards found, try alternative parsing
#             if not plays:
#                 plays = self._parse_alternative_structure(soup, city, url)
            
#             return plays
            
#         except Exception as e:
#             print(f"   ❌ Error scraping {url}: {e}")
#             return []
    
#     def _parse_play_card(self, card, city: str, base_url: str) -> Optional[Dict]:
#         """
#         Bir oyun kartından bilgi çıkar
#         """
#         try:
#             # Get title
#             title_elem = card.select_one('h3, h4, .title, .event-title, [class*="title"]')
#             if not title_elem:
#                 # If card is a link, get text
#                 if card.name == 'a':
#                     title = card.get_text(strip=True)
#                 else:
#                     title = card.get_text(strip=True)[:50]
#             else:
#                 title = title_elem.get_text(strip=True)
            
#             # Clean title
#             title = self._clean_title(title)
            
#             if not title or len(title) < 3 or not self._is_valid_play_title(title):
#                 return None
            
#             # Get URL
#             if card.name == 'a':
#                 play_url = card.get('href', '')
#             else:
#                 link = card.select_one('a[href]')
#                 play_url = link.get('href', '') if link else ''
            
#             if play_url and not play_url.startswith('http'):
#                 play_url = 'https://biletinial.com' + play_url
            
#             # Skip category pages
#             if play_url and ('/istanbul-avrupa' in play_url or '/istanbul-anadolu' in play_url or play_url.endswith('/tiyatro')):
#                 return None
            
#             # Get venue
#             venue_elem = card.select_one('.venue, .location, [class*="venue"], [class*="location"]')
#             venue = venue_elem.get_text(strip=True) if venue_elem else None
            
#             # Get dates
#             date_elem = card.select_one('.date, .time, [class*="date"], [class*="time"]')
#             date_text = date_elem.get_text(strip=True) if date_elem else ''
#             dates = self._parse_dates(date_text)
            
#             return {
#                 'title': title,
#                 'venue': venue or f"{city} Tiyatrosu",
#                 'city': city,
#                 'ticket_url': play_url,
#                 'dates': dates,
#                 'raw_date_text': date_text,
#                 'source': 'biletinial_scrape'
#             }
            
#         except Exception as e:
#             return None
    
#     def _parse_alternative_structure(self, soup: BeautifulSoup, city: str, base_url: str) -> List[Dict]:
#         """
#         Alternatif HTML yapısı için parsing
#         """
#         plays = []
        
#         # Look for all links that might be plays
#         all_links = soup.select('a[href*="/tiyatro/"]')
        
#         seen_titles = set()
        
#         for link in all_links:
#             href = link.get('href', '')
            
#             # Skip category pages
#             skip_patterns = ['/istanbul-avrupa', '/istanbul-anadolu', '/ankara', '/izmir', 
#                           '/adana', '/bursa', '/antalya', '/tiyatro/profesyonel',
#                           '/cocuk-tiyatro', 'sehrineozel']
            
#             if any(p in href for p in skip_patterns):
#                 continue
            
#             # Must have a specific play path (contains hyphen after /tiyatro/)
#             if not re.search(r'/tiyatro/[a-z0-9-]+-', href):
#                 continue
            
#             title = link.get_text(strip=True)
#             title = self._clean_title(title)
            
#             if title and len(title) > 3 and title.lower() not in seen_titles:
#                 if self._is_valid_play_title(title):
#                     seen_titles.add(title.lower())
                    
#                     full_url = href if href.startswith('http') else 'https://biletinial.com' + href
                    
#                     plays.append({
#                         'title': title,
#                         'venue': f"{city} Tiyatrosu",
#                         'city': city,
#                         'ticket_url': full_url,
#                         'dates': [],
#                         'source': 'biletinial_scrape'
#                     })
        
#         return plays
    
#     def get_play_details(self, play_url: str) -> Optional[Dict]:
#         """
#         Tek bir oyunun detay sayfasından bilgi çek
#         """
#         try:
#             print(f"   📄 Fetching details: {play_url[:50]}...")
#             response = self.session.get(play_url, timeout=10)
#             response.raise_for_status()
            
#             soup = BeautifulSoup(response.text, 'html.parser')
            
#             # Title
#             title_elem = soup.select_one('h1, .event-title, [class*="title"]')
#             title = title_elem.get_text(strip=True) if title_elem else None
            
#             # Venue
#             venue_elem = soup.select_one('.venue, [class*="venue"], [class*="location"]')
#             venue = venue_elem.get_text(strip=True) if venue_elem else None
            
#             # All dates/showtimes
#             date_elems = soup.select('.date, .showtime, [class*="date"], [class*="time"], [class*="seans"]')
#             all_dates = []
#             for elem in date_elems:
#                 text = elem.get_text(strip=True)
#                 parsed = self._parse_dates(text)
#                 all_dates.extend(parsed)
            
#             # Description
#             desc_elem = soup.select_one('.description, .about, [class*="description"]')
#             description = desc_elem.get_text(strip=True)[:300] if desc_elem else None
            
#             return {
#                 'title': title,
#                 'venue': venue,
#                 'dates': all_dates,
#                 'description': description,
#                 'ticket_url': play_url
#             }
            
#         except Exception as e:
#             print(f"   ❌ Error fetching details: {e}")
#             return None
    
#     def _parse_dates(self, text: str) -> List[Dict]:
#         """
#         Tarih metninden yapılandırılmış tarih bilgisi çıkar
#         """
#         dates = []
#         if not text:
#             return dates
        
#         text_lower = text.lower()
        
#         # Pattern: "15 Ocak 2026" or "15 Ocak Çarşamba 2026" or "15 Ocak 20:30"
#         for month_name, month_num in self.TURKISH_MONTHS.items():
#             # Pattern with year
#             pattern1 = rf'(\d{{1,2}})\s+{month_name}\s+(\d{{4}})'
#             matches1 = re.findall(pattern1, text_lower)
            
#             for match in matches1:
#                 day = int(match[0])
#                 year = int(match[1])
#                 try:
#                     date_obj = datetime(year, month_num, day)
#                     dates.append({
#                         'date_obj': date_obj,
#                         'display': f"{day} {month_name.capitalize()} {year}",
#                         'raw': f"{day} {month_name} {year}"
#                     })
#                 except ValueError:
#                     pass
            
#             # Pattern without year (assume current/next year)
#             pattern2 = rf'(\d{{1,2}})\s+{month_name}(?:\s+\w+)?\s+(\d{{2}}:\d{{2}})'
#             matches2 = re.findall(pattern2, text_lower)
            
#             for match in matches2:
#                 day = int(match[0])
#                 time_str = match[1]
#                 year = datetime.now().year
                
#                 # If month already passed, use next year
#                 if month_num < datetime.now().month:
#                     year += 1
                
#                 try:
#                     date_obj = datetime(year, month_num, day)
#                     dates.append({
#                         'date_obj': date_obj,
#                         'display': f"{day} {month_name.capitalize()} {year} {time_str}",
#                         'time': time_str,
#                         'raw': f"{day} {month_name} {time_str}"
#                     })
#                 except ValueError:
#                     pass
        
#         # Remove duplicates
#         seen = set()
#         unique_dates = []
#         for d in dates:
#             key = d['date_obj'].strftime("%Y-%m-%d") if d.get('date_obj') else d.get('raw')
#             if key and key not in seen:
#                 seen.add(key)
#                 unique_dates.append(d)
        
#         return unique_dates
    
#     def _clean_title(self, title: str) -> str:
#         """Oyun başlığını temizle"""
#         if not title:
#             return ""
        
#         # Remove common suffixes
#         suffixes = [
#             ' | Biletinial', ' - Biletinial', ' Tiyatro Biletleri',
#             ' Biletleri', ' Bileti', '...', ' Tiyatro Oyunu'
#         ]
        
#         for suffix in suffixes:
#             if title.endswith(suffix):
#                 title = title[:-len(suffix)]
        
#         return title.strip()
    
#     def _is_valid_play_title(self, title: str) -> bool:
#         """Geçerli oyun başlığı mı kontrol et"""
#         if not title or len(title) < 3:
#             return False
        
#         title_lower = title.lower()
        
#         # Invalid keywords
#         invalid = [
#             'tiyatro oyunları', 'biletleri', 'etkinlik', 'takvim',
#             'istanbul', 'ankara', 'izmir', 'adana', 'türkiye',
#             'tüm oyunlar', 'kategori', 'filtrele', 'avrupa', 'anadolu',
#             'şehir tiyatro', 'devlet tiyatro', 'çocuk tiyatro'
#         ]
        
#         for inv in invalid:
#             if title_lower == inv or title_lower.startswith(inv):
#                 return False
        
#         return True
    
#     def _deduplicate_plays(self, plays: List[Dict]) -> List[Dict]:
#         """Duplicate oyunları kaldır"""
#         seen = set()
#         unique = []
        
#         for play in plays:
#             title_lower = play['title'].lower()
#             if title_lower not in seen:
#                 seen.add(title_lower)
#                 unique.append(play)
        
#         return unique
    
#     def _is_cache_valid(self, key: str) -> bool:
#         """Cache hala geçerli mi?"""
#         if key not in self._cache or key not in self._cache_time:
#             return False
        
#         elapsed = (datetime.now() - self._cache_time[key]).total_seconds()
#         return elapsed < self._cache_duration


# # ==================== TEST ====================

# def test_scraper():
#     """Test the realtime scraper"""
#     print("\n" + "="*60)
#     print("  🔍 REALTIME SCRAPER TEST")
#     print("="*60 + "\n")
    
#     scraper = RealtimeScraper()
    
#     # Test 1: Get all plays in Istanbul
#     print("\n📍 Test 1: Istanbul'daki tüm oyunlar")
#     plays = scraper.get_plays_for_city("Istanbul", max_plays=10)
    
#     for i, play in enumerate(plays[:5], 1):
#         print(f"\n{i}. {play['title']}")
#         print(f"   📍 {play['venue']}")
#         print(f"   🎫 {play['ticket_url'][:50]}..." if play.get('ticket_url') else "")
    
#     # Test 2: Get plays for specific date
#     print("\n\n📍 Test 2: 15 Ocak 2026 için oyunlar")
#     target = datetime(2026, 1, 15)
#     date_plays = scraper.get_plays_for_date("Istanbul", target, max_plays=5)
    
#     for i, play in enumerate(date_plays[:5], 1):
#         print(f"\n{i}. {play['title']}")
#         if play.get('matching_showtime'):
#             print(f"   📅 {play['matching_showtime'].get('display')}")
    
#     print("\n" + "="*60)


# if __name__ == "__main__":
#     test_scraper()


# -----------------------2------------------------- #
# src/realtime_scraper.py
"""
Real-Time Theater Scraper - Biletinial'dan Anlık Veri Çekme

Bu modül, kullanıcı sorgusu geldiğinde biletinial.com'dan
güncel oyun bilgilerini çeker. Tavily'den çok daha güvenilir!

Desteklenen şehirler:
- Istanbul (Avrupa + Anadolu)
- Ankara
- Izmir
- Adana
- Bursa
- Antalya
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
from typing import List, Dict, Optional
import time


class RealtimeScraper:
    """
    Biletinial.com'dan anlık tiyatro bilgisi çeken scraper
    """
    
    # Şehir URL'leri
    CITY_URLS = {
        'istanbul': [
            'https://biletinial.com/tr-tr/tiyatro/istanbul-avrupa',
            'https://biletinial.com/tr-tr/tiyatro/istanbul-anadolu'
        ],
        'ankara': ['https://biletinial.com/tr-tr/tiyatro/ankara'],
        'izmir': ['https://biletinial.com/tr-tr/tiyatro/izmir'],
        'adana': ['https://biletinial.com/tr-tr/tiyatro/adana'],
        'bursa': ['https://biletinial.com/tr-tr/tiyatro/bursa'],
        'antalya': ['https://biletinial.com/tr-tr/tiyatro/antalya'],
    }
    
    # Tarih filtreli URL template
    DATE_FILTER_URL = "https://biletinial.com/tr-tr/tiyatro?city={city}&date={date}"
    
    # Turkish month mapping
    TURKISH_MONTHS = {
        'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4,
        'mayıs': 5, 'haziran': 6, 'temmuz': 7, 'ağustos': 8,
        'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12,
        # ASCII versions
        'subat': 2, 'mayis': 5, 'agustos': 8, 'eylul': 9, 'aralik': 12, 'kasim': 11
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        })
        # Cache for avoiding repeated requests
        self._cache = {}
        self._cache_time = {}
        self._cache_duration = 300  # 5 minutes
    
    def get_plays_for_city(self, city: str, max_plays: int = 20) -> List[Dict]:
        """
        Bir şehirdeki tüm oyunları çek
        
        Args:
            city: Şehir adı (istanbul, ankara, etc.)
            max_plays: Maximum oyun sayısı
            
        Returns:
            List of play dictionaries
        """
        city_lower = city.lower().replace('İ', 'i').replace('ı', 'i')
        
        if city_lower not in self.CITY_URLS:
            print(f"⚠️  {city} şehri desteklenmiyor")
            return []
        
        # Check cache
        cache_key = f"city_{city_lower}"
        if self._is_cache_valid(cache_key):
            print(f"📦 Using cached data for {city}")
            return self._cache[cache_key]
        
        all_plays = []
        urls = self.CITY_URLS[city_lower]
        
        for url in urls:
            print(f"🌐 Fetching: {url}")
            plays = self._scrape_listing_page(url, city)
            all_plays.extend(plays)
            time.sleep(0.5)  # Be nice to the server
        
        # Remove duplicates
        unique_plays = self._deduplicate_plays(all_plays)
        
        # Cache results
        self._cache[cache_key] = unique_plays[:max_plays]
        self._cache_time[cache_key] = datetime.now()
        
        print(f"✅ Found {len(unique_plays)} unique plays in {city}")
        
        return unique_plays[:max_plays]
    
    def get_plays_for_date(self, city: str, target_date: datetime, max_plays: int = 10) -> List[Dict]:
        """
        Belirli bir tarihteki oyunları getir - YENİ: Takvim sayfasından çek
        
        Args:
            city: Şehir adı
            target_date: Hedef tarih
            max_plays: Maximum oyun sayısı
            
        Returns:
            Filtered list of plays
        """
        city_lower = city.lower().replace('İ', 'i').replace('ı', 'i')
        date_str = target_date.strftime("%Y-%m-%d")
        
        print(f"📅 Fetching plays for {city} on {date_str}")
        
        # Method 1: Try the event calendar API/page
        plays = self._scrape_calendar_page(city_lower, target_date)
        
        if plays:
            print(f"   ✅ Found {len(plays)} plays from calendar")
            return plays[:max_plays]
        
        # Method 2: Scrape listing and get details for top plays
        print(f"   📋 Calendar empty, checking top plays' schedules...")
        all_plays = self.get_plays_for_city(city, max_plays=20)
        
        matching_plays = []
        checked = 0
        
        for play in all_plays[:15]:  # Check first 15 plays
            if not play.get('ticket_url'):
                continue
            
            # Get play details including dates
            details = self.get_play_details(play['ticket_url'])
            checked += 1
            
            if details and details.get('dates'):
                for date_info in details['dates']:
                    play_date = date_info.get('date_obj')
                    if play_date and play_date.strftime("%Y-%m-%d") == date_str:
                        play_copy = play.copy()
                        play_copy['matching_showtime'] = date_info
                        play_copy['venue'] = details.get('venue') or play.get('venue')
                        play_copy['dates'] = details.get('dates', [])
                        matching_plays.append(play_copy)
                        print(f"   ✓ Match: {play['title']} - {date_info.get('display')}")
                        break
            
            # Stop if we found enough or checked too many
            if len(matching_plays) >= max_plays or checked >= 15:
                break
        
        print(f"   ✅ Found {len(matching_plays)} plays for {date_str}")
        return matching_plays[:max_plays]
    
    def _scrape_calendar_page(self, city: str, target_date: datetime) -> List[Dict]:
        """
        Biletinial takvim sayfasından belirli tarihteki oyunları çek
        """
        # Try different URL formats
        date_str = target_date.strftime("%Y-%m-%d")
        day = target_date.day
        month = target_date.month
        year = target_date.year
        
        # URL format 1: Event calendar with date filter
        urls_to_try = [
            f"https://biletinial.com/tr-tr/tiyatro?city={city}&startDate={date_str}",
            f"https://biletinial.com/tr-tr/etkinlik-takvimi?category=tiyatro&city={city}&date={date_str}",
        ]
        
        # Add city-specific URLs with date
        if city == 'istanbul':
            urls_to_try.extend([
                f"https://biletinial.com/tr-tr/tiyatro/istanbul-avrupa?startDate={date_str}",
                f"https://biletinial.com/tr-tr/tiyatro/istanbul-anadolu?startDate={date_str}",
            ])
        
        plays = []
        
        for url in urls_to_try:
            try:
                print(f"   🌐 Trying: {url[:60]}...")
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    page_plays = self._parse_calendar_results(soup, city, target_date)
                    
                    if page_plays:
                        plays.extend(page_plays)
                        print(f"      ✓ Found {len(page_plays)} plays")
                
            except Exception as e:
                print(f"      ✗ Error: {e}")
                continue
        
        return self._deduplicate_plays(plays)
    
    def get_plays_for_date_range(self, city: str, start_date: datetime, end_date: datetime, max_plays: int = 15) -> List[Dict]:
        """
        Tarih aralığındaki oyunları getir (hafta sonu, bu hafta, vs.)
        """
        all_plays = self.get_plays_for_city(city, max_plays=50)
        
        matching_plays = []
        
        print(f"📅 Filtering for range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        for play in all_plays:
            if play.get('dates'):
                for date_info in play['dates']:
                    play_date = date_info.get('date_obj')
                    if play_date and start_date <= play_date <= end_date:
                        play_copy = play.copy()
                        play_copy['matching_showtime'] = date_info
                        matching_plays.append(play_copy)
                        print(f"   ✓ Match: {play['title']} - {date_info.get('display')}")
                        break
        
        return matching_plays[:max_plays]
    
    def _scrape_listing_page(self, url: str, city: str) -> List[Dict]:
        """
        Biletinial listing sayfasından oyunları çek
        """
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            plays = []
            
            # Find play cards - biletinial uses various card structures
            # Method 1: Look for event cards
            cards = soup.select('.event-card, .card, .activity-card, [class*="event"], [class*="activity"]')
            
            if not cards:
                # Method 2: Look for links to individual plays
                cards = soup.select('a[href*="/tiyatro/"][href*="-"]')
            
            print(f"   Found {len(cards)} potential cards")
            
            for card in cards:
                play = self._parse_play_card(card, city, url)
                if play:
                    plays.append(play)
            
            # If no cards found, try alternative parsing
            if not plays:
                plays = self._parse_alternative_structure(soup, city, url)
            
            return plays
            
        except Exception as e:
            print(f"   ❌ Error scraping {url}: {e}")
            return []
    
    def _parse_play_card(self, card, city: str, base_url: str) -> Optional[Dict]:
        """
        Bir oyun kartından bilgi çıkar
        """
        try:
            # Get title
            title_elem = card.select_one('h3, h4, .title, .event-title, [class*="title"]')
            if not title_elem:
                # If card is a link, get text
                if card.name == 'a':
                    title = card.get_text(strip=True)
                else:
                    title = card.get_text(strip=True)[:50]
            else:
                title = title_elem.get_text(strip=True)
            
            # Clean title
            title = self._clean_title(title)
            
            if not title or len(title) < 3 or not self._is_valid_play_title(title):
                return None
            
            # Get URL
            if card.name == 'a':
                play_url = card.get('href', '')
            else:
                link = card.select_one('a[href]')
                play_url = link.get('href', '') if link else ''
            
            if play_url and not play_url.startswith('http'):
                play_url = 'https://biletinial.com' + play_url
            
            # Skip category pages
            if play_url and ('/istanbul-avrupa' in play_url or '/istanbul-anadolu' in play_url or play_url.endswith('/tiyatro')):
                return None
            
            # Get venue
            venue_elem = card.select_one('.venue, .location, [class*="venue"], [class*="location"]')
            venue = venue_elem.get_text(strip=True) if venue_elem else None
            
            # Get dates
            date_elem = card.select_one('.date, .time, [class*="date"], [class*="time"]')
            date_text = date_elem.get_text(strip=True) if date_elem else ''
            dates = self._parse_dates(date_text)
            
            return {
                'title': title,
                'venue': venue or f"{city} Tiyatrosu",
                'city': city,
                'ticket_url': play_url,
                'dates': dates,
                'raw_date_text': date_text,
                'source': 'biletinial_scrape'
            }
            
        except Exception as e:
            return None
    
    def _parse_alternative_structure(self, soup: BeautifulSoup, city: str, base_url: str) -> List[Dict]:
        """
        Alternatif HTML yapısı için parsing
        """
        plays = []
        
        # Look for all links that might be plays
        all_links = soup.select('a[href*="/tiyatro/"]')
        
        seen_titles = set()
        
        for link in all_links:
            href = link.get('href', '')
            
            # Skip category pages
            skip_patterns = ['/istanbul-avrupa', '/istanbul-anadolu', '/ankara', '/izmir', 
                          '/adana', '/bursa', '/antalya', '/tiyatro/profesyonel',
                          '/cocuk-tiyatro', 'sehrineozel']
            
            if any(p in href for p in skip_patterns):
                continue
            
            # Must have a specific play path (contains hyphen after /tiyatro/)
            if not re.search(r'/tiyatro/[a-z0-9-]+-', href):
                continue
            
            title = link.get_text(strip=True)
            title = self._clean_title(title)
            
            if title and len(title) > 3 and title.lower() not in seen_titles:
                if self._is_valid_play_title(title):
                    seen_titles.add(title.lower())
                    
                    full_url = href if href.startswith('http') else 'https://biletinial.com' + href
                    
                    # Try to get venue from parent/sibling elements
                    venue = None
                    parent = link.find_parent(['div', 'article', 'li'])
                    if parent:
                        venue_elem = parent.select_one('.venue, .location, [class*="venue"], [class*="location"], [class*="mekan"]')
                        if venue_elem:
                            venue = venue_elem.get_text(strip=True)
                    
                    plays.append({
                        'title': title,
                        'venue': venue or f"{city} Tiyatrosu",
                        'city': city,
                        'ticket_url': full_url,
                        'dates': [],
                        'source': 'biletinial_scrape'
                    })
        
        return plays
    
    def _parse_calendar_results(self, soup: BeautifulSoup, city: str, target_date: datetime) -> List[Dict]:
        """
        Parse results from calendar/filtered page
        """
        plays = []
        
        # Look for event cards with date info
        cards = soup.select('.event-card, .activity-card, [class*="event"], [class*="etkinlik"]')
        
        for card in cards:
            try:
                # Title
                title_elem = card.select_one('h3, h4, .title, [class*="title"], [class*="name"]')
                if not title_elem:
                    continue
                
                title = self._clean_title(title_elem.get_text(strip=True))
                if not title or not self._is_valid_play_title(title):
                    continue
                
                # URL
                link = card.select_one('a[href*="/tiyatro/"]')
                play_url = link.get('href', '') if link else ''
                if play_url and not play_url.startswith('http'):
                    play_url = 'https://biletinial.com' + play_url
                
                # Venue
                venue_elem = card.select_one('.venue, .location, [class*="venue"], [class*="mekan"]')
                venue = venue_elem.get_text(strip=True) if venue_elem else None
                
                # Date/Time
                date_elem = card.select_one('.date, .time, [class*="date"], [class*="time"], [class*="tarih"]')
                date_text = date_elem.get_text(strip=True) if date_elem else ''
                
                # Parse showtime
                showtime = None
                time_match = re.search(r'(\d{1,2}:\d{2})', date_text)
                if time_match:
                    showtime = time_match.group(1)
                
                plays.append({
                    'title': title,
                    'venue': venue or f"{city} Tiyatrosu",
                    'city': city,
                    'ticket_url': play_url,
                    'matching_showtime': {
                        'date_obj': target_date,
                        'display': f"{target_date.day} {self._get_turkish_month(target_date.month)} {target_date.year}" + (f" {showtime}" if showtime else ""),
                        'time': showtime
                    },
                    'source': 'biletinial_calendar'
                })
                
            except Exception as e:
                continue
        
        return plays
    
    def _get_turkish_month(self, month: int) -> str:
        """Get Turkish month name"""
        months = ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
                 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
        return months[month] if 1 <= month <= 12 else ''
    
    def get_play_details(self, play_url: str) -> Optional[Dict]:
        """
        Tek bir oyunun detay sayfasından bilgi çek - GELİŞTİRİLMİŞ
        """
        try:
            response = self.session.get(play_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Title
            title_elem = soup.select_one('h1, .event-title, [class*="title"]')
            title = title_elem.get_text(strip=True) if title_elem else None
            
            # Venue - try multiple selectors
            venue = None
            venue_selectors = [
                '.venue', '.location', '[class*="venue"]', '[class*="location"]',
                '[class*="mekan"]', '.event-location', '.place'
            ]
            for selector in venue_selectors:
                venue_elem = soup.select_one(selector)
                if venue_elem:
                    venue = venue_elem.get_text(strip=True)
                    if venue and len(venue) > 3:
                        break
            
            # All dates/showtimes - try multiple approaches
            all_dates = []
            
            # Method 1: Look for date/showtime sections
            date_sections = soup.select('.date, .showtime, [class*="date"], [class*="time"], [class*="seans"], [class*="tarih"]')
            for elem in date_sections:
                text = elem.get_text(strip=True)
                parsed = self._parse_dates(text)
                all_dates.extend(parsed)
            
            # Method 2: Look for calendar/schedule elements
            schedule_elem = soup.select_one('.schedule, .calendar, [class*="schedule"], [class*="takvim"]')
            if schedule_elem:
                schedule_text = schedule_elem.get_text(strip=True)
                parsed = self._parse_dates(schedule_text)
                all_dates.extend(parsed)
            
            # Method 3: Look in the entire page for date patterns
            if not all_dates:
                page_text = soup.get_text()
                # Look for specific date patterns
                for month_name, month_num in self.TURKISH_MONTHS.items():
                    pattern = rf'(\d{{1,2}})\s+{month_name}\s+(\d{{4}})\s*[,]?\s*(\d{{2}}:\d{{2}})?'
                    matches = re.findall(pattern, page_text.lower())
                    for match in matches[:5]:  # Limit to 5 dates
                        day = int(match[0])
                        year = int(match[1])
                        time_str = match[2] if len(match) > 2 else None
                        try:
                            date_obj = datetime(year, month_num, day)
                            display = f"{day} {month_name.capitalize()} {year}"
                            if time_str:
                                display += f" {time_str}"
                            all_dates.append({
                                'date_obj': date_obj,
                                'display': display,
                                'time': time_str
                            })
                        except ValueError:
                            pass
            
            # Deduplicate dates
            seen_dates = set()
            unique_dates = []
            for d in all_dates:
                key = d['date_obj'].strftime("%Y-%m-%d") if d.get('date_obj') else d.get('display')
                if key and key not in seen_dates:
                    seen_dates.add(key)
                    unique_dates.append(d)
            
            # Description
            desc_elem = soup.select_one('.description, .about, [class*="description"], [class*="aciklama"]')
            description = desc_elem.get_text(strip=True)[:300] if desc_elem else None
            
            return {
                'title': title,
                'venue': venue,
                'dates': unique_dates[:10],  # Max 10 dates
                'description': description,
                'ticket_url': play_url
            }
            
        except Exception as e:
            return None
    
    def _parse_dates(self, text: str) -> List[Dict]:
        """
        Tarih metninden yapılandırılmış tarih bilgisi çıkar
        """
        dates = []
        if not text:
            return dates
        
        text_lower = text.lower()
        
        # Pattern: "15 Ocak 2026" or "15 Ocak Çarşamba 2026" or "15 Ocak 20:30"
        for month_name, month_num in self.TURKISH_MONTHS.items():
            # Pattern with year
            pattern1 = rf'(\d{{1,2}})\s+{month_name}\s+(\d{{4}})'
            matches1 = re.findall(pattern1, text_lower)
            
            for match in matches1:
                day = int(match[0])
                year = int(match[1])
                try:
                    date_obj = datetime(year, month_num, day)
                    dates.append({
                        'date_obj': date_obj,
                        'display': f"{day} {month_name.capitalize()} {year}",
                        'raw': f"{day} {month_name} {year}"
                    })
                except ValueError:
                    pass
            
            # Pattern without year (assume current/next year)
            pattern2 = rf'(\d{{1,2}})\s+{month_name}(?:\s+\w+)?\s+(\d{{2}}:\d{{2}})'
            matches2 = re.findall(pattern2, text_lower)
            
            for match in matches2:
                day = int(match[0])
                time_str = match[1]
                year = datetime.now().year
                
                # If month already passed, use next year
                if month_num < datetime.now().month:
                    year += 1
                
                try:
                    date_obj = datetime(year, month_num, day)
                    dates.append({
                        'date_obj': date_obj,
                        'display': f"{day} {month_name.capitalize()} {year} {time_str}",
                        'time': time_str,
                        'raw': f"{day} {month_name} {time_str}"
                    })
                except ValueError:
                    pass
        
        # Remove duplicates
        seen = set()
        unique_dates = []
        for d in dates:
            key = d['date_obj'].strftime("%Y-%m-%d") if d.get('date_obj') else d.get('raw')
            if key and key not in seen:
                seen.add(key)
                unique_dates.append(d)
        
        return unique_dates
    
    def _clean_title(self, title: str) -> str:
        """Oyun başlığını temizle"""
        if not title:
            return ""
        
        # Remove common suffixes
        suffixes = [
            ' | Biletinial', ' - Biletinial', ' Tiyatro Biletleri',
            ' Biletleri', ' Bileti', '...', ' Tiyatro Oyunu'
        ]
        
        for suffix in suffixes:
            if title.endswith(suffix):
                title = title[:-len(suffix)]
        
        return title.strip()
    
    def _is_valid_play_title(self, title: str) -> bool:
        """Geçerli oyun başlığı mı kontrol et"""
        if not title or len(title) < 3:
            return False
        
        title_lower = title.lower()
        
        # Invalid keywords
        invalid = [
            'tiyatro oyunları', 'biletleri', 'etkinlik', 'takvim',
            'istanbul', 'ankara', 'izmir', 'adana', 'türkiye',
            'tüm oyunlar', 'kategori', 'filtrele', 'avrupa', 'anadolu',
            'şehir tiyatro', 'devlet tiyatro', 'çocuk tiyatro'
        ]
        
        for inv in invalid:
            if title_lower == inv or title_lower.startswith(inv):
                return False
        
        return True
    
    def _deduplicate_plays(self, plays: List[Dict]) -> List[Dict]:
        """Duplicate oyunları kaldır"""
        seen = set()
        unique = []
        
        for play in plays:
            title_lower = play['title'].lower()
            if title_lower not in seen:
                seen.add(title_lower)
                unique.append(play)
        
        return unique
    
    def _is_cache_valid(self, key: str) -> bool:
        """Cache hala geçerli mi?"""
        if key not in self._cache or key not in self._cache_time:
            return False
        
        elapsed = (datetime.now() - self._cache_time[key]).total_seconds()
        return elapsed < self._cache_duration


# ==================== TEST ====================

def test_scraper():
    """Test the realtime scraper"""
    print("\n" + "="*60)
    print("  🔍 REALTIME SCRAPER TEST")
    print("="*60 + "\n")
    
    scraper = RealtimeScraper()
    
    # Test 1: Get all plays in Istanbul
    print("\n📍 Test 1: Istanbul'daki tüm oyunlar")
    plays = scraper.get_plays_for_city("Istanbul", max_plays=10)
    
    for i, play in enumerate(plays[:5], 1):
        print(f"\n{i}. {play['title']}")
        print(f"   📍 {play['venue']}")
        print(f"   🎫 {play['ticket_url'][:50]}..." if play.get('ticket_url') else "")
    
    # Test 2: Get plays for specific date
    print("\n\n📍 Test 2: 15 Ocak 2026 için oyunlar")
    target = datetime(2026, 1, 15)
    date_plays = scraper.get_plays_for_date("Istanbul", target, max_plays=5)
    
    for i, play in enumerate(date_plays[:5], 1):
        print(f"\n{i}. {play['title']}")
        if play.get('matching_showtime'):
            print(f"   📅 {play['matching_showtime'].get('display')}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    test_scraper()