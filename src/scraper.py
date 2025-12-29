# """
# A focused web scraper using Selenium for biletinial.com.
# """
# import os
# import time
# import json
# from datetime import datetime
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.options import Options
# from selenium.common.exceptions import TimeoutException, NoSuchElementException

# class BiletinialScraper:
#     """A web scraper for biletinial.com theater events in Istanbul."""

#     def __init__(self, headless=True):
#         self.options = Options()
#         if headless:
#             self.options.add_argument('--headless')
#         self.options.add_argument('--no-sandbox')
#         self.options.add_argument('--disable-dev-shm-usage')
#         self.options.add_argument('--disable-blink-features=AutomationControlled')
#         self.options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
#         self.driver = None

#     def start(self):
#         try:
#             self.driver = webdriver.Chrome(options=self.options)
#         except Exception as e:
#             print(f"Error starting WebDriver: {e}")
#             self.driver = None

#     def stop(self):
#         if self.driver:
#             self.driver.quit()

#     def scrape_istanbul_events(self):
#         if not self.driver:
#             print("WebDriver not started.")
#             return []

#         results = []
#         try:
#             url = "https://biletinial.com/tiyatro"
#             print(f"Scraping Biletinial for Istanbul events: {url}")
#             self.driver.get(url)
#             time.sleep(15) # Wait for all elements to load

#             # Select city
#             try:
#                 # Click the city dropdown. The dropdown is identified by its 'Şehir Seçiniz' placeholder.
#                 city_dropdown = WebDriverWait(self.driver, 10).until(
#                     EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'filter-item')]//div[contains(., 'Şehir Seçiniz')]"))
#                 )
#                 city_dropdown.click()
#                 time.sleep(1)

#                 # Click 'Istanbul' from the list
#                 istanbul_option = WebDriverWait(self.driver, 10).until(
#                     EC.element_to_be_clickable((By.XPATH, "//ul/li[text()='İstanbul']"))
#                 )
#                 istanbul_option.click()
#                 print("Selected 'Istanbul' as the city.")
#                 time.sleep(3)  # Wait for events to load after city selection
#             except TimeoutException:
#                 print("Could not find or click the city selection dropdown or 'Istanbul' option.")
#                 raise

#             # Scrape events
#             event_selector = "div.card"
#             title_selector = "h3.card-title"
#             venue_selector = "p.card-text"
            
#             wait = WebDriverWait(self.driver, 20)
#             wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, event_selector)))
            
#             events = self.driver.find_elements(By.CSS_SELECTOR, event_selector)[:15] # Get up to 15 events
#             print(f"Found {len(events)} event elements.")

#             for event in events:
#                 try:
#                     title = event.find_element(By.CSS_SELECTOR, title_selector).text.strip()
#                     # Venue and date might be in the same element, so we get all text parts
#                     details = event.find_elements(By.CSS_SELECTOR, venue_selector)
#                     venue = details[0].text.strip() if len(details) > 0 else "N/A"
#                     date = details[1].text.strip() if len(details) > 1 else "Check website"

#                     if title:
#                         results.append({
#                             "title": title,
#                             "venue": venue,
#                             "date": date,
#                             "source": "Biletinial"
#                         })
#                 except NoSuchElementException:
#                     continue
#         except TimeoutException:
#             print("Timeout while waiting for event elements.")
#             self._save_screenshot("biletinial_failure")
#         except Exception as e:
#             print(f"An unexpected error occurred: {e}")
#             self._save_screenshot("biletinial_error")
        
#         return results

#     def _save_screenshot(self, name):
#         screenshots_dir = "screenshots"
#         if not os.path.exists(screenshots_dir):
#             os.makedirs(screenshots_dir)
#         screenshot_path = os.path.join(screenshots_dir, f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
#         self.driver.save_screenshot(screenshot_path)
#         print(f"Screenshot saved to {screenshot_path}")

#     def run(self):
#         self.start()
#         scraped_data = self.scrape_istanbul_events()
#         self.stop()

#         output_data = {
#             "timestamp": datetime.now().isoformat(),
#             "location": "Istanbul",
#             "source": "Biletinial",
#             "results_found": scraped_data,
#             "total_events_scraped": len(scraped_data)
#         }
        
#         self._save_results(output_data)
#         return output_data

#     def _save_results(self, data):
#         filename = "theater_scraping_results.json"
#         try:
#             with open(filename, 'w', encoding='utf-8') as f:
#                 json.dump([data], f, indent=2, ensure_ascii=False)
#             print(f"\n[Scraping results saved to {filename}]")
#         except Exception as e:
#             print(f"\n[Warning: Could not save results: {e}]")

# if __name__ == "__main__":
#     scraper = BiletinialScraper(headless=False) # Running with browser visible for debugging
#     results = scraper.run()
#     print(f"\nFound {len(results.get('results_found', []))} results.")
#     for result in results.get('results_found', [])[:10]:
#         print(f"- {result['title']} at {result['venue']} on {result['date']}")


#-------------------------------2----------------------- 



# """
# Improved Theater Scraper for Istanbul
# Properly extracts: title, dates, venues, actors
# Fixed version that actually gets the data!
# """

# import json
# import time
# import os
# import re
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.options import Options
# from selenium.common.exceptions import TimeoutException, NoSuchElementException
# import logging

# logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
# logger = logging.getLogger(__name__)


# class ImprovedTheaterScraper:
#     def __init__(self, headless=False):
#         """Initialize scraper"""
#         self.options = Options()
#         if headless:
#             self.options.add_argument('--headless')
#         self.options.add_argument('--no-sandbox')
#         self.options.add_argument('--disable-dev-shm-usage')
#         self.options.add_argument('--window-size=1920,1080')
#         self.options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)')
        
#         self.driver = None
#         self.plays = []
    
#     def start_driver(self):
#         """Start Chrome driver"""
#         try:
#             self.driver = webdriver.Chrome(options=self.options)
#             logger.info("✓ Chrome driver started")
#         except Exception as e:
#             logger.error(f"Failed to start driver: {e}")
#             raise
    
#     def scrape_play_detail_page(self, url, title):
#         """
#         Visit individual play page to get detailed info
#         This is the KEY improvement!
#         """
#         details = {
#             'dates': [],
#             'venues': [],
#             'actors': []
#         }
        
#         try:
#             logger.info(f"  → Visiting detail page...")
#             self.driver.get(url)
#             time.sleep(2)
            
#             # Scroll to load content
#             self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
#             time.sleep(1)
            
#             # METHOD 1: Look for specific date/time elements
#             try:
#                 # Try to find elements with "Kas" (Kasım), "Ara" (Aralık), etc.
#                 date_elements = self.driver.find_elements(By.XPATH, 
#                     "//*[contains(text(), 'Kas') or contains(text(), 'Ara') or contains(text(), 'Oca') or contains(text(), 'Şub')]")
                
#                 for elem in date_elements:
#                     text = elem.text.strip()
#                     # Match pattern like "15 Kasım Cumartesi, 20:00"
#                     if re.search(r'\d{1,2}\s+\w+.*\d{1,2}:\d{2}', text):
#                         details['dates'].append(text)
#             except Exception as e:
#                 logger.debug(f"Date method 1 failed: {e}")
            
#             # METHOD 2: Find all text containing dates
#             if not details['dates']:
#                 try:
#                     page_text = self.driver.find_element(By.TAG_NAME, 'body').text
#                     # Turkish months
#                     months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
#                              'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
                    
#                     for month in months:
#                         pattern = rf'\d{{1,2}}\s+{month}\s+\w+,?\s*\d{{1,2}}:\d{{2}}'
#                         matches = re.findall(pattern, page_text)
#                         details['dates'].extend(matches[:5])  # Limit to 5
#                 except Exception as e:
#                     logger.debug(f"Date method 2 failed: {e}")
            
#             # Extract venues
#             try:
#                 # Look for common venue indicators
#                 venue_keywords = ['Sahne', 'Salon', 'Tiyatro', 'KKM', 'Sanat', 'Kültür']
                
#                 for keyword in venue_keywords:
#                     elements = self.driver.find_elements(By.XPATH, 
#                         f"//*[contains(text(), '{keyword}')]")
                    
#                     for elem in elements:
#                         text = elem.text.strip()
#                         # Venue names are usually 10-80 chars
#                         if 10 < len(text) < 80 and keyword in text:
#                             if text not in details['venues']:
#                                 details['venues'].append(text)
#                                 if len(details['venues']) >= 2:
#                                     break
                    
#                     if details['venues']:
#                         break
#             except Exception as e:
#                 logger.debug(f"Venue extraction failed: {e}")
            
#             # Remove duplicates and limit
#             details['dates'] = list(dict.fromkeys(details['dates']))[:5]
#             details['venues'] = list(dict.fromkeys(details['venues']))[:2]
            
#             logger.info(f"  ✓ Extracted: {len(details['dates'])} dates, {len(details['venues'])} venues")
            
#         except Exception as e:
#             logger.warning(f"  ✗ Error on detail page: {e}")
        
#         return details
    
#     def scrape_biletinial(self, max_plays=20, get_details=True):
#         """
#         Scrape theater plays from biletinial.com
#         Now with PROPER detail extraction!
#         """
#         try:
#             url = "https://www.biletinial.com/tr-tr/tiyatro"
#             logger.info(f"Navigating to {url}")
#             self.driver.get(url)
#             time.sleep(3)
            
#             # Scroll to load content
#             logger.info("Scrolling to load plays...")
#             for i in range(5):
#                 self.driver.execute_script(f"window.scrollTo(0, {(i+1)*500});")
#                 time.sleep(1)
            
#             # Find all play links
#             logger.info("Finding play links...")
#             all_links = self.driver.find_elements(By.TAG_NAME, 'a')
            
#             play_links = []
#             seen_titles = set()
            
#             for link in all_links:
#                 try:
#                     href = link.get_attribute('href')
#                     text = link.text.strip()
                    
#                     if (href and 
#                         'biletinial.com/tr-tr/' in href and 
#                         ('tiyatro' in href or 'muzikali' in href.lower()) and
#                         text and 
#                         len(text) > 3 and 
#                         text not in seen_titles):
                        
#                         # Try to get image
#                         img_url = ''
#                         try:
#                             img = link.find_element(By.TAG_NAME, 'img')
#                             img_url = img.get_attribute('src')
#                         except:
#                             pass
                        
#                         play_links.append({
#                             'title': text,
#                             'url': href,
#                             'image': img_url
#                         })
#                         seen_titles.add(text)
                        
#                         if len(play_links) >= max_plays:
#                             break
                            
#                 except Exception as e:
#                     continue
            
#             logger.info(f"Found {len(play_links)} unique plays")
            
#             # Process each play
#             for idx, play_info in enumerate(play_links, 1):
#                 logger.info(f"\n[{idx}/{len(play_links)}] {play_info['title']}")
                
#                 play_data = {
#                     'title': play_info['title'],
#                     'url': play_info['url'],
#                     'image': play_info['image'],
#                     'dates': [],
#                     'venues': [],
#                     'actors': [],
#                     'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
#                 }
                
#                 # Get detailed info by visiting play page
#                 if get_details:
#                     details = self.scrape_play_detail_page(play_info['url'], play_info['title'])
#                     play_data.update(details)
                    
#                     # Go back to main page
#                     self.driver.back()
#                     time.sleep(1)
                
#                 self.plays.append(play_data)
            
#             logger.info(f"\n✓ Successfully scraped {len(self.plays)} plays")
            
#         except Exception as e:
#             logger.error(f"Error during scraping: {e}")
#             import traceback
#             traceback.print_exc()
    
#     def save_to_json(self, filename='theater_scraping_results.json'):
#         """Save to JSON"""
#         try:
#             output_path = os.path.join(os.getcwd(), filename)
            
#             output_data = {
#                 'total_plays': len(self.plays),
#                 'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
#                 'location': 'Istanbul, Turkey',
#                 'source': 'biletinial.com',
#                 'plays': self.plays
#             }
            
#             with open(output_path, 'w', encoding='utf-8') as f:
#                 json.dump(output_data, f, ensure_ascii=False, indent=2)
            
#             logger.info(f"\n✓ Saved to {output_path}")
            
#             # Print summary
#             print(f"\n{'='*70}")
#             print(f"SCRAPING SUMMARY")
#             print(f"{'='*70}")
#             print(f"Total plays: {len(self.plays)}")
#             print(f"With dates: {sum(1 for p in self.plays if p.get('dates'))}")
#             print(f"With venues: {sum(1 for p in self.plays if p.get('venues'))}")
#             print(f"With images: {sum(1 for p in self.plays if p.get('image'))}")
#             print(f"{'='*70}\n")
            
#             return output_path
            
#         except Exception as e:
#             logger.error(f"Error saving JSON: {e}")
#             return None
    
#     def close(self):
#         """Close browser"""
#         if self.driver:
#             self.driver.quit()
#             logger.info("Browser closed")
    
#     def run(self, max_plays=20, get_details=True):
#         """Main execution"""
#         try:
#             self.start_driver()
            
#             logger.info(f"\nStarting scrape (max {max_plays} plays)...")
#             logger.info("This will take 3-5 minutes...\n")
            
#             self.scrape_biletinial(max_plays=max_plays, get_details=get_details)
            
#             output_file = self.save_to_json()
            
#             # Show sample
#             if self.plays:
#                 print("\nSample of first 3 plays:")
#                 print("-" * 70)
#                 for i, play in enumerate(self.plays[:3], 1):
#                     print(f"\n{i}. {play['title']}")
#                     if play.get('dates'):
#                         print(f"   📅 {len(play['dates'])} dates: {play['dates'][0]}")
#                     if play.get('venues'):
#                         print(f"   📍 {play['venues'][0]}")
#                     print(f"   🔗 {play['url'][:60]}...")
#                 print("-" * 70)
            
#             return output_file
            
#         except Exception as e:
#             logger.error(f"Fatal error: {e}")
#             import traceback
#             traceback.print_exc()
#             return None
#         finally:
#             self.close()


# def main():
#     """Main function"""
#     print("\n" + "=" * 70)
#     print("  IMPROVED ISTANBUL THEATER SCRAPER")
#     print("=" * 70)
#     print("  This version properly extracts dates and venues!")
#     print("=" * 70 + "\n")
    
#     print("Options:")
#     print("  1. Quick test (5 plays, ~2 min)")
#     print("  2. Full scrape (20 plays, ~5 min)")
#     print("  3. Custom amount\n")
    
#     choice = input("Choose option (1-3): ").strip()
    
#     if choice == "1":
#         max_plays = 5
#     elif choice == "3":
#         max_plays = int(input("How many plays? "))
#     else:
#         max_plays = 20
    
#     print(f"\nScraping {max_plays} plays...\n")
    
#     scraper = ImprovedTheaterScraper(headless=False)
#     scraper.run(max_plays=max_plays, get_details=True)
    
#     print("\n" + "=" * 70)
#     print("  ✓ DONE!")
#     print("  → Now run: python database.py (option 3 to reset and import)")
#     print("=" * 70 + "\n")


# if __name__ == "__main__":
#     main()


    # -------------------------------3------------------------------

# """
# Theater Scraper v3.0 - NOW WITH CITY DETECTION!
# Extracts: title, dates, venues, city, actors
# """

# import json
# import time
# import os
# import re
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.options import Options
# import logging

# logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
# logger = logging.getLogger(__name__)


# class TheaterScraperV3:
#     """
#     Version 3: Now with CITY detection!
#     """
    
#     def __init__(self, headless=False):
#         self.options = Options()
#         if headless:
#             self.options.add_argument('--headless')
#         self.options.add_argument('--no-sandbox')
#         self.options.add_argument('--disable-dev-shm-usage')
#         self.options.add_argument('--window-size=1920,1080')
#         self.options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)')
        
#         self.driver = None
#         self.plays = []
        
#         # Turkish cities to detect
#         self.turkish_cities = [
#             'Istanbul', 'Ankara', 'İzmir', 'Bursa', 'Antalya',
#             'Adana', 'Gaziantep', 'Konya', 'Eskişehir', 'Kayseri',
#             'Mersin', 'Diyarbakır', 'Samsun', 'Denizli', 'Adapazarı'
#         ]
    
#     def start_driver(self):
#         """Start Chrome driver"""
#         try:
#             self.driver = webdriver.Chrome(options=self.options)
#             logger.info("✓ Chrome driver started")
#         except Exception as e:
#             logger.error(f"Failed to start driver: {e}")
#             raise
    
#     def detect_city_from_text(self, text):
#         """
#         Detect city from text using multiple methods
#         Returns city name or None
#         """
#         if not text:
#             return None
        
#         text_lower = text.lower()
        
#         # Method 1: Direct city name match
#         for city in self.turkish_cities:
#             if city.lower() in text_lower:
#                 return city
        
#         # Method 2: Common venue patterns
#         city_patterns = {
#             'Ankara': ['yenimahalle', 'çankaya', 'gölbaşı', 'ted ankara', 'nazım hikmet km'],
#             'Istanbul': ['kadıköy', 'beşiktaş', 'beyoğlu', 'taksim', 'şişli', 'zorlu', 
#                         'moda sahnesi', 'dragos', 'pera', 'satsuma'],
#             'İzmir': ['karşıyaka', 'konak', 'bornova'],
#             'Bursa': ['nilüfer', 'osmangazi', 'merinos'],
#             'Antalya': ['muratpaşa', 'kepez'],
#             'Konya': ['selçuklu', 'meram']
#         }
        
#         for city, keywords in city_patterns.items():
#             for keyword in keywords:
#                 if keyword.lower() in text_lower:
#                     return city
        
#         return None
    
#     def scrape_play_detail_page(self, url, title):
#         """
#         Visit play detail page and extract:
#         - Dates/times
#         - Venue name
#         - City (NEW!)
#         - Actors
#         """
#         details = {
#             'dates': [],
#             'venues': [],
#             'city': None,
#             'actors': []
#         }
        
#         try:
#             logger.info(f"  → Visiting detail page...")
#             self.driver.get(url)
#             time.sleep(2)
            
#             # Scroll to load content
#             self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
#             time.sleep(1)
            
#             # Get full page text for analysis
#             page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            
#             # EXTRACT CITY (NEW!)
#             detected_city = self.detect_city_from_text(page_text)
#             if detected_city:
#                 details['city'] = detected_city
#                 logger.info(f"  ✓ Detected city: {detected_city}")
            
#             # Extract dates
#             try:
#                 months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
#                          'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
                
#                 for month in months:
#                     # Pattern: "15 Kasım Cumartesi, 20:00"
#                     pattern = rf'\d{{1,2}}\s+{month}\s+\w+,?\s*\d{{1,2}}:\d{{2}}'
#                     matches = re.findall(pattern, page_text)
#                     details['dates'].extend(matches[:5])
                
#                 # Remove duplicates
#                 details['dates'] = list(dict.fromkeys(details['dates']))[:5]
                
#             except Exception as e:
#                 logger.debug(f"Date extraction error: {e}")
            
#             # Extract venues
#             try:
#                 venue_keywords = ['Sahne', 'Salon', 'Tiyatro', 'KKM', 'Sanat', 
#                                  'Kültür', 'Merkezi', 'PSM']
                
#                 for keyword in venue_keywords:
#                     elements = self.driver.find_elements(By.XPATH, 
#                         f"//*[contains(text(), '{keyword}')]")
                    
#                     for elem in elements:
#                         text = elem.text.strip()
                        
#                         # Venue names are 10-100 chars
#                         if 10 < len(text) < 100 and keyword in text:
#                             # Clean up venue name
#                             text = text.replace('\n', ' ').strip()
                            
#                             if text not in details['venues']:
#                                 details['venues'].append(text)
                                
#                                 # If city not detected yet, try from venue
#                                 if not details['city']:
#                                     city = self.detect_city_from_text(text)
#                                     if city:
#                                         details['city'] = city
                                
#                                 if len(details['venues']) >= 2:
#                                     break
                    
#                     if details['venues']:
#                         break
                
#             except Exception as e:
#                 logger.debug(f"Venue extraction error: {e}")
            
#             # If still no city, try URL
#             if not details['city']:
#                 city_from_url = self.detect_city_from_text(url)
#                 if city_from_url:
#                     details['city'] = city_from_url
            
#             # Default to Istanbul if no city detected (most plays are there)
#             if not details['city']:
#                 details['city'] = 'Istanbul'
#                 logger.info(f"  ⚠️  No city detected, defaulting to Istanbul")
            
#             logger.info(f"  ✓ Extracted: {len(details['dates'])} dates, " 
#                        f"{len(details['venues'])} venues, city: {details['city']}")
            
#         except Exception as e:
#             logger.warning(f"  ✗ Error on detail page: {e}")
#             details['city'] = 'Istanbul'  # Safe default
        
#         return details
    
#     def scrape_biletinial(self, max_plays=20, get_details=True):
#         """
#         Scrape theater plays with CITY information
#         """
#         try:
#             url = "https://www.biletinial.com/tr-tr/tiyatro"
#             logger.info(f"Navigating to {url}")
#             self.driver.get(url)
#             time.sleep(3)
            
#             # Scroll to load content
#             logger.info("Scrolling to load plays...")
#             for i in range(5):
#                 self.driver.execute_script(f"window.scrollTo(0, {(i+1)*500});")
#                 time.sleep(1)
            
#             # Find all play links
#             logger.info("Finding play links...")
#             all_links = self.driver.find_elements(By.TAG_NAME, 'a')
            
#             play_links = []
#             seen_titles = set()
            
#             for link in all_links:
#                 try:
#                     href = link.get_attribute('href')
#                     text = link.text.strip()
                    
#                     if (href and 
#                         'biletinial.com/tr-tr/' in href and 
#                         ('tiyatro' in href or 'muzikali' in href.lower()) and
#                         text and 
#                         len(text) > 3 and 
#                         text not in seen_titles):
                        
#                         # Get image
#                         img_url = ''
#                         try:
#                             img = link.find_element(By.TAG_NAME, 'img')
#                             img_url = img.get_attribute('src')
#                         except:
#                             pass
                        
#                         play_links.append({
#                             'title': text,
#                             'url': href,
#                             'image': img_url
#                         })
#                         seen_titles.add(text)
                        
#                         if len(play_links) >= max_plays:
#                             break
                            
#                 except Exception as e:
#                     continue
            
#             logger.info(f"Found {len(play_links)} unique plays")
            
#             # Process each play
#             for idx, play_info in enumerate(play_links, 1):
#                 logger.info(f"\n[{idx}/{len(play_links)}] {play_info['title']}")
                
#                 play_data = {
#                     'title': play_info['title'],
#                     'url': play_info['url'],
#                     'image': play_info['image'],
#                     'city': 'Istanbul',  # Default
#                     'dates': [],
#                     'venues': [],
#                     'actors': [],
#                     'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
#                 }
                
#                 # Get detailed info
#                 if get_details:
#                     details = self.scrape_play_detail_page(play_info['url'], play_info['title'])
#                     play_data.update(details)
                    
#                     # Go back
#                     self.driver.back()
#                     time.sleep(1)
                
#                 self.plays.append(play_data)
#                 logger.info(f"  ✓ Saved: {play_data['title']} ({play_data['city']})")
            
#             logger.info(f"\n✓ Successfully scraped {len(self.plays)} plays")
            
#         except Exception as e:
#             logger.error(f"Error during scraping: {e}")
#             import traceback
#             traceback.print_exc()
    
#     def save_to_json(self, filename='theater_scraping_results.json'):
#         """Save to JSON"""
#         try:
#             output_path = os.path.join(os.getcwd(), filename)
            
#             output_data = {
#                 'total_plays': len(self.plays),
#                 'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
#                 'source': 'biletinial.com',
#                 'plays': self.plays
#             }
            
#             with open(output_path, 'w', encoding='utf-8') as f:
#                 json.dump(output_data, f, ensure_ascii=False, indent=2)
            
#             logger.info(f"\n✓ Saved to {output_path}")
            
#             # Print summary by city
#             print(f"\n{'='*70}")
#             print(f"SCRAPING SUMMARY")
#             print(f"{'='*70}")
#             print(f"Total plays: {len(self.plays)}")
            
#             # Count by city
#             city_counts = {}
#             for play in self.plays:
#                 city = play.get('city', 'Unknown')
#                 city_counts[city] = city_counts.get(city, 0) + 1
            
#             print(f"\nPlays by city:")
#             for city, count in sorted(city_counts.items()):
#                 print(f"  • {city}: {count} plays")
            
#             print(f"\nWith dates: {sum(1 for p in self.plays if p.get('dates'))}")
#             print(f"With venues: {sum(1 for p in self.plays if p.get('venues'))}")
#             print(f"With images: {sum(1 for p in self.plays if p.get('image'))}")
#             print(f"{'='*70}\n")
            
#             return output_path
            
#         except Exception as e:
#             logger.error(f"Error saving JSON: {e}")
#             return None
    
#     def close(self):
#         """Close browser"""
#         if self.driver:
#             self.driver.quit()
#             logger.info("Browser closed")
    
#     def run(self, max_plays=20, get_details=True):
#         """Main execution"""
#         try:
#             self.start_driver()
            
#             logger.info(f"\n🎭 Starting scrape (max {max_plays} plays)...")
#             logger.info("Version 3.0: NOW WITH CITY DETECTION!")
#             logger.info("This will take 3-5 minutes...\n")
            
#             self.scrape_biletinial(max_plays=max_plays, get_details=get_details)
            
#             output_file = self.save_to_json()
            
#             # Show sample
#             if self.plays:
#                 print("\n📋 Sample of first 5 plays:")
#                 print("-" * 70)
#                 for i, play in enumerate(self.plays[:5], 1):
#                     print(f"\n{i}. {play['title']}")
#                     print(f"   🏙️  City: {play['city']}")
#                     if play.get('venues'):
#                         print(f"   📍 Venue: {play['venues'][0]}")
#                     if play.get('dates'):
#                         print(f"   📅 Dates: {len(play['dates'])} showtimes")
#                 print("-" * 70)
            
#             return output_file
            
#         except Exception as e:
#             logger.error(f"Fatal error: {e}")
#             import traceback
#             traceback.print_exc()
#             return None
#         finally:
#             self.close()


# def main():
#     """Main function"""
#     print("\n" + "=" * 70)
#     print("  THEATER SCRAPER v3.0 - WITH CITY DETECTION!")
#     print("=" * 70)
#     print("  Now properly extracts city information!")
#     print("=" * 70 + "\n")
    
#     print("Options:")
#     print("  1. Quick test (5 plays, ~2 min)")
#     print("  2. Full scrape (20 plays, ~5 min)")
#     print("  3. Custom amount\n")
    
#     choice = input("Choose option (1-3): ").strip()
    
#     if choice == "1":
#         max_plays = 5
#     elif choice == "3":
#         max_plays = int(input("How many plays? "))
#     else:
#         max_plays = 20
    
#     print(f"\n🎭 Scraping {max_plays} plays with CITY detection...\n")
    
#     scraper = TheaterScraperV3(headless=False)
#     scraper.run(max_plays=max_plays, get_details=True)
    
#     print("\n" + "=" * 70)
#     print("  ✓ DONE!")
#     print("  → Now run:")
#     print("     cd src")
#     print("     python inspect_db.py")
#     print("     Choose option 3 (Reset and reimport)")
#     print("=" * 70 + "\n")


# if __name__ == "__main__":
#     main()



# # -----------------------------4-------------------------

# """
# Theater Scraper v4.0 - ROBUST VERSION
# Fixes the timeout issue with driver.back()
# Uses fresh navigation instead of browser back button
# """

# import json
# import time
# import os
# import re
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException, WebDriverException
# import logging

# logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
# logger = logging.getLogger(__name__)


# class TheaterScraperV4:
#     """
#     Version 4: Robust version that handles timeouts gracefully
#     - No more driver.back() - uses direct navigation instead
#     - Better error handling and retry logic
#     - Collects all links first, then visits each
#     """
    
#     BASE_URL = "https://www.biletinial.com/tr-tr/tiyatro"
    
#     def __init__(self, headless=False):
#         self.options = Options()
#         if headless:
#             self.options.add_argument('--headless=new')  # New headless mode
#         self.options.add_argument('--no-sandbox')
#         self.options.add_argument('--disable-dev-shm-usage')
#         self.options.add_argument('--disable-gpu')
#         self.options.add_argument('--window-size=1920,1080')
#         self.options.add_argument('--disable-extensions')
#         self.options.add_argument('--disable-infobars')
#         self.options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
#         # Performance optimizations
#         self.options.add_argument('--disable-blink-features=AutomationControlled')
#         self.options.add_experimental_option('excludeSwitches', ['enable-automation'])
#         self.options.add_experimental_option('useAutomationExtension', False)
        
#         self.driver = None
#         self.plays = []
        
#         # Turkish cities to detect
#         self.turkish_cities = [
#             'Istanbul', 'İstanbul', 'Ankara', 'İzmir', 'Izmir', 'Bursa', 'Antalya',
#             'Adana', 'Gaziantep', 'Konya', 'Eskişehir', 'Eskisehir', 'Kayseri',
#             'Mersin', 'Diyarbakır', 'Samsun', 'Denizli', 'Adapazarı'
#         ]
        
#         # City keyword patterns
#         self.city_patterns = {
#             'Ankara': ['ankara', 'yenimahalle', 'çankaya', 'gölbaşı', 'nazım hikmet', 'kkm', 'csm'],
#             'Istanbul': ['istanbul', 'İstanbul', 'kadıköy', 'beşiktaş', 'beyoğlu', 'taksim', 'şişli', 
#                         'zorlu', 'moda', 'dragos', 'pera', 'üsküdar', 'bakırköy', 'ataşehir',
#                         'trump', 'uniq', 'maximum', 'bostancı'],
#             'İzmir': ['izmir', 'İzmir', 'karşıyaka', 'konak', 'bornova', 'alsancak'],
#             'Bursa': ['bursa', 'nilüfer', 'osmangazi', 'merinos'],
#             'Antalya': ['antalya', 'muratpaşa', 'kepez', 'lara'],
#             'Konya': ['konya', 'selçuklu', 'meram'],
#             'Eskişehir': ['eskişehir', 'eskisehir', 'tepebaşı'],
#             'Adana': ['adana', 'seyhan', 'çukurova'],
#         }
    
#     def start_driver(self):
#         """Start Chrome driver with extended timeout"""
#         try:
#             self.driver = webdriver.Chrome(options=self.options)
#             self.driver.set_page_load_timeout(60)  # 60 second page load timeout
#             self.driver.implicitly_wait(5)  # 5 second implicit wait
#             logger.info("✓ Chrome driver started")
#             return True
#         except Exception as e:
#             logger.error(f"Failed to start driver: {e}")
#             return False
    
#     def safe_get(self, url, retries=3):
#         """Safely navigate to URL with retries"""
#         for attempt in range(retries):
#             try:
#                 self.driver.get(url)
#                 time.sleep(2)
#                 return True
#             except TimeoutException:
#                 logger.warning(f"  ⚠️ Timeout loading {url[:50]}... (attempt {attempt+1}/{retries})")
#                 if attempt < retries - 1:
#                     # Restart driver if needed
#                     try:
#                         self.driver.quit()
#                     except:
#                         pass
#                     time.sleep(2)
#                     self.start_driver()
#             except Exception as e:
#                 logger.warning(f"  ⚠️ Error loading page: {e}")
#                 if attempt < retries - 1:
#                     time.sleep(2)
#         return False
    
#     def detect_city_from_text(self, text):
#         """Detect city from text"""
#         if not text:
#             return None
        
#         text_lower = text.lower()
        
#         # Check city patterns
#         for city, keywords in self.city_patterns.items():
#             for keyword in keywords:
#                 if keyword.lower() in text_lower:
#                     return city
        
#         return None
    
#     def collect_play_links(self, max_plays=20):
#         """
#         PHASE 1: Collect all play links from main page
#         This avoids the back() issue by collecting everything first
#         """
#         play_links = []
        
#         if not self.safe_get(self.BASE_URL):
#             logger.error("Could not load main page")
#             return []
        
#         # Scroll to load more content
#         logger.info("Scrolling to load plays...")
#         for i in range(6):
#             try:
#                 self.driver.execute_script(f"window.scrollTo(0, {(i+1)*600});")
#                 time.sleep(0.8)
#             except:
#                 pass
        
#         # Scroll back up
#         self.driver.execute_script("window.scrollTo(0, 0);")
#         time.sleep(1)
        
#         # Find all links
#         logger.info("Finding play links...")
#         try:
#             all_links = self.driver.find_elements(By.TAG_NAME, 'a')
#             seen_urls = set()
            
#             for link in all_links:
#                 try:
#                     href = link.get_attribute('href')
#                     text = link.text.strip()
                    
#                     # Filter for play links
#                     if not href or not text:
#                         continue
#                     if href in seen_urls:
#                         continue
#                     if 'biletinial.com/tr-tr/' not in href:
#                         continue
#                     if '/tiyatro' not in href and '/muzikali' not in href.lower():
#                         continue
#                     if len(text) < 3 or len(text) > 100:
#                         continue
#                     # Skip navigation/filter links
#                     if any(skip in text.lower() for skip in ['şehir', 'filtre', 'kategori', 'tarih']):
#                         continue
                    
#                     # Try to get image
#                     img_url = ''
#                     try:
#                         img = link.find_element(By.TAG_NAME, 'img')
#                         img_url = img.get_attribute('src') or ''
#                     except:
#                         pass
                    
#                     play_links.append({
#                         'title': text,
#                         'url': href,
#                         'image': img_url
#                     })
#                     seen_urls.add(href)
                    
#                     if len(play_links) >= max_plays:
#                         break
                        
#                 except Exception as e:
#                     continue
            
#             logger.info(f"Found {len(play_links)} unique plays")
            
#         except Exception as e:
#             logger.error(f"Error collecting links: {e}")
        
#         return play_links
    
#     def scrape_play_detail(self, url, title):
#         """
#         PHASE 2: Visit each play's detail page
#         Fresh navigation each time - no back() needed!
#         """
#         details = {
#             'dates': [],
#             'venues': [],
#             'city': None,
#         }
        
#         if not self.safe_get(url, retries=2):
#             logger.warning(f"  ⚠️ Could not load detail page")
#             details['city'] = 'Istanbul'  # Default
#             return details
        
#         try:
#             # Scroll to load content
#             self.driver.execute_script("window.scrollTo(0, 400);")
#             time.sleep(1)
            
#             # Get page text
#             page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            
#             # DETECT CITY
#             detected_city = self.detect_city_from_text(page_text)
#             if detected_city:
#                 details['city'] = detected_city
#                 logger.info(f"  ✓ City: {detected_city}")
#             else:
#                 details['city'] = 'Istanbul'  # Default
            
#             # EXTRACT DATES
#             months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
#                      'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
            
#             for month in months:
#                 # Pattern: "15 Kasım Cumartesi, 20:00" or "15 Kasım 20:00"
#                 pattern = rf'\d{{1,2}}\s+{month}[^0-9]*\d{{1,2}}:\d{{2}}'
#                 matches = re.findall(pattern, page_text, re.IGNORECASE)
#                 for match in matches[:3]:  # Limit per month
#                     clean_match = match.strip()
#                     if clean_match and clean_match not in details['dates']:
#                         details['dates'].append(clean_match)
            
#             details['dates'] = details['dates'][:5]  # Max 5 dates
            
#             # EXTRACT VENUES
#             venue_keywords = ['Sahne', 'Salon', 'Tiyatro', 'Sahnesi', 'Merkezi', 
#                             'KKM', 'PSM', 'AKM', 'CSM', 'Kültür']
            
#             for keyword in venue_keywords:
#                 try:
#                     elements = self.driver.find_elements(By.XPATH, 
#                         f"//*[contains(text(), '{keyword}')]")
                    
#                     for elem in elements[:5]:
#                         text = elem.text.strip()
#                         text = text.replace('\n', ' ').strip()
                        
#                         if 10 < len(text) < 100 and keyword in text:
#                             if text not in details['venues']:
#                                 details['venues'].append(text)
#                             if len(details['venues']) >= 2:
#                                 break
                    
#                     if details['venues']:
#                         break
#                 except:
#                     continue
            
#             logger.info(f"  ✓ {len(details['dates'])} dates, {len(details['venues'])} venues")
            
#         except Exception as e:
#             logger.warning(f"  ⚠️ Error extracting details: {e}")
#             if not details['city']:
#                 details['city'] = 'Istanbul'
        
#         return details
    
#     def run(self, max_plays=20):
#         """
#         Main execution - Two phase approach:
#         1. Collect all links from main page
#         2. Visit each detail page (fresh navigation, no back())
#         """
#         try:
#             if not self.start_driver():
#                 return None
            
#             logger.info(f"\n🎭 Starting scrape (max {max_plays} plays)...")
#             logger.info("Version 4.0: ROBUST - No more timeout issues!")
#             logger.info("Phase 1: Collecting links...")
            
#             # PHASE 1: Collect links
#             play_links = self.collect_play_links(max_plays)
            
#             if not play_links:
#                 logger.error("No plays found!")
#                 return None
            
#             # PHASE 2: Visit each play
#             logger.info(f"\nPhase 2: Visiting {len(play_links)} play pages...")
            
#             for idx, play_info in enumerate(play_links, 1):
#                 logger.info(f"\n[{idx}/{len(play_links)}] {play_info['title'][:50]}")
                
#                 play_data = {
#                     'title': play_info['title'],
#                     'url': play_info['url'],
#                     'image': play_info['image'],
#                     'city': 'Istanbul',
#                     'dates': [],
#                     'venues': [],
#                     'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
#                 }
                
#                 # Get details
#                 details = self.scrape_play_detail(play_info['url'], play_info['title'])
#                 play_data.update(details)
                
#                 self.plays.append(play_data)
                
#                 # Small delay between requests
#                 time.sleep(1)
            
#             logger.info(f"\n✓ Successfully scraped {len(self.plays)} plays")
            
#             # Save results
#             return self.save_to_json()
            
#         except Exception as e:
#             logger.error(f"Fatal error: {e}")
#             import traceback
#             traceback.print_exc()
#             return None
#         finally:
#             self.close()
    
#     def save_to_json(self, filename='theater_scraping_results.json'):
#         """Save results to JSON"""
#         try:
#             output_data = {
#                 'total_plays': len(self.plays),
#                 'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
#                 'source': 'biletinial.com',
#                 'plays': self.plays
#             }
            
#             with open(filename, 'w', encoding='utf-8') as f:
#                 json.dump(output_data, f, ensure_ascii=False, indent=2)
            
#             logger.info(f"\n✓ Saved to {filename}")
            
#             # Print summary
#             print(f"\n{'='*70}")
#             print("SCRAPING SUMMARY")
#             print(f"{'='*70}")
#             print(f"Total plays: {len(self.plays)}")
            
#             # Count by city
#             city_counts = {}
#             for play in self.plays:
#                 city = play.get('city', 'Unknown')
#                 city_counts[city] = city_counts.get(city, 0) + 1
            
#             print(f"\nPlays by city:")
#             for city, count in sorted(city_counts.items(), key=lambda x: -x[1]):
#                 print(f"  • {city}: {count} plays")
            
#             print(f"\nWith dates: {sum(1 for p in self.plays if p.get('dates'))}")
#             print(f"With venues: {sum(1 for p in self.plays if p.get('venues'))}")
#             print(f"With images: {sum(1 for p in self.plays if p.get('image'))}")
#             print(f"{'='*70}\n")
            
#             # Show sample
#             if self.plays:
#                 print("📋 Sample plays:")
#                 print("-" * 70)
#                 for i, play in enumerate(self.plays[:5], 1):
#                     print(f"\n{i}. {play['title']}")
#                     print(f"   🏙️  City: {play['city']}")
#                     if play.get('venues'):
#                         print(f"   📍 Venue: {play['venues'][0][:50]}")
#                     if play.get('dates'):
#                         print(f"   📅 Dates: {len(play['dates'])} showtimes")
#                 print("-" * 70)
            
#             return filename
            
#         except Exception as e:
#             logger.error(f"Error saving: {e}")
#             return None
    
#     def close(self):
#         """Close browser safely"""
#         if self.driver:
#             try:
#                 self.driver.quit()
#                 logger.info("Browser closed")
#             except:
#                 pass


# def main():
#     """Main function"""
#     print("\n" + "=" * 70)
#     print("  THEATER SCRAPER v4.0 - ROBUST VERSION")
#     print("=" * 70)
#     print("  ✓ Fixed timeout issues")
#     print("  ✓ No more driver.back() problems")
#     print("  ✓ Better error handling")
#     print("=" * 70 + "\n")
    
#     print("Options:")
#     print("  1. Quick test (5 plays)")
#     print("  2. Medium (10 plays)")
#     print("  3. Full scrape (20 plays)")
#     print("  4. Custom amount\n")
    
#     choice = input("Choose option (1-4): ").strip()
    
#     if choice == "1":
#         max_plays = 5
#     elif choice == "2":
#         max_plays = 10
#     elif choice == "4":
#         try:
#             max_plays = int(input("How many plays? "))
#         except:
#             max_plays = 10
#     else:
#         max_plays = 20
    
#     print(f"\n🎭 Scraping {max_plays} plays...\n")
    
#     # Use headless=True if you want faster/invisible scraping
#     scraper = TheaterScraperV4(headless=False)
#     result = scraper.run(max_plays=max_plays)
    
#     if result:
#         print("\n" + "=" * 70)
#         print("  ✓ DONE!")
#         print(f"  → Results saved to: {result}")
#         print("=" * 70 + "\n")
#     else:
#         print("\n⚠️ Scraping failed. Check the errors above.\n")


# if __name__ == "__main__":
#     main()



# -----------------------------4.1-------------------------

"""
Theater Scraper v4.1 - FIXED DATE EXTRACTION
Now correctly extracts dates in format: "04 Şubat Çarşamba 2026, 20:30"
"""

import json
import time
import os
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class TheaterScraperV4:
    """
    Version 4.1: Fixed date extraction
    - Dates are in format: "04 Şubat Çarşamba 2026, 20:30"
    - Need to scroll and wait for dynamic content
    """
    
    BASE_URL = "https://www.biletinial.com/tr-tr/tiyatro"
    
    def __init__(self, headless=False):
        self.options = Options()
        if headless:
            self.options.add_argument('--headless=new')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--window-size=1920,1080')
        self.options.add_argument('--disable-extensions')
        self.options.add_argument('--disable-infobars')
        self.options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_experimental_option('excludeSwitches', ['enable-automation'])
        self.options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = None
        self.plays = []
        
        # Turkish cities
        self.turkish_cities = [
            'Istanbul', 'İstanbul', 'Ankara', 'İzmir', 'Izmir', 'Bursa', 'Antalya',
            'Adana', 'Gaziantep', 'Konya', 'Eskişehir', 'Eskisehir', 'Kayseri',
            'Mersin', 'Diyarbakır', 'Samsun', 'Denizli', 'Adapazarı'
        ]
        
        # City keyword patterns
        self.city_patterns = {
            'Ankara': ['ankara', 'yenimahalle', 'çankaya', 'gölbaşı', 'nazım hikmet', 'kkm', 'csm', 'ata sahne'],
            'Istanbul': ['istanbul', 'İstanbul', 'kadıköy', 'beşiktaş', 'beyoğlu', 'taksim', 'şişli', 
                        'zorlu', 'moda', 'dragos', 'pera', 'üsküdar', 'bakırköy', 'ataşehir',
                        'trump', 'uniq', 'maximum', 'bostancı', 'dasdas', 'leyla gencer', 'harbiye'],
            'İzmir': ['izmir', 'İzmir', 'karşıyaka', 'konak', 'bornova', 'alsancak', 'bostanlı', 'suat taşer'],
            'Bursa': ['bursa', 'nilüfer', 'osmangazi', 'merinos'],
            'Antalya': ['antalya', 'muratpaşa', 'kepez', 'lara'],
            'Konya': ['konya', 'selçuklu', 'meram'],
            'Eskişehir': ['eskişehir', 'eskisehir', 'tepebaşı'],
            'Adana': ['adana', 'seyhan', 'çukurova'],
            'Samsun': ['samsun'],
        }
        
        # Turkish months for date parsing
        self.turkish_months = [
            'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
            'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'
        ]
    
    def start_driver(self):
        """Start Chrome driver"""
        try:
            self.driver = webdriver.Chrome(options=self.options)
            self.driver.set_page_load_timeout(60)
            self.driver.implicitly_wait(5)
            logger.info("✓ Chrome driver started")
            return True
        except Exception as e:
            logger.error(f"Failed to start driver: {e}")
            return False
    
    def safe_get(self, url, retries=3):
        """Safely navigate to URL with retries"""
        for attempt in range(retries):
            try:
                self.driver.get(url)
                time.sleep(2)
                return True
            except TimeoutException:
                logger.warning(f"  ⚠️ Timeout (attempt {attempt+1}/{retries})")
                if attempt < retries - 1:
                    try:
                        self.driver.quit()
                    except:
                        pass
                    time.sleep(2)
                    self.start_driver()
            except Exception as e:
                logger.warning(f"  ⚠️ Error: {e}")
                if attempt < retries - 1:
                    time.sleep(2)
        return False
    
    def detect_city_from_text(self, text):
        """Detect city from text"""
        if not text:
            return None
        
        text_lower = text.lower()
        
        for city, keywords in self.city_patterns.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return city
        
        return None
    
    def extract_dates_from_page(self):
        """
        Extract dates from the page - FIXED VERSION
        Biletinial format: "04 Şubat Çarşamba 2026, 20:30"
        """
        dates = []
        
        try:
            # Scroll down to load date cards
            self.driver.execute_script("window.scrollTo(0, 800);")
            time.sleep(1)
            
            # Get page text
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            
            # Pattern 1: "04 Şubat Çarşamba 2026, 20:30" (full format)
            for month in self.turkish_months:
                # Match: DD Month DayName YYYY, HH:MM
                pattern = rf'(\d{{1,2}}\s+{month}\s+\w+\s+\d{{4}},?\s*\d{{1,2}}:\d{{2}})'
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    clean = match.strip()
                    if clean and clean not in dates:
                        dates.append(clean)
            
            # Pattern 2: Try to find date cards by looking for specific elements
            try:
                # Look for elements containing month names and times
                date_elements = self.driver.find_elements(By.XPATH, 
                    "//*[contains(text(), ':00') or contains(text(), ':30')]")
                
                for elem in date_elements[:20]:  # Limit to first 20
                    text = elem.text.strip()
                    # Check if it looks like a date
                    for month in self.turkish_months:
                        if month in text and re.search(r'\d{1,2}:\d{2}', text):
                            # Extract just the date part
                            if len(text) < 50 and text not in dates:
                                dates.append(text)
                                break
            except Exception as e:
                logger.debug(f"Date element search failed: {e}")
            
            # Pattern 3: Look for date box structure (Oca 03, etc.)
            try:
                # Find short month abbreviations followed by day numbers
                short_pattern = r'(Oca|Şub|Mar|Nis|May|Haz|Tem|Ağu|Eyl|Eki|Kas|Ara)\s*(\d{1,2})'
                short_matches = re.findall(short_pattern, page_text)
                
                # These are just day indicators, look for full info nearby
                for match in short_matches[:5]:
                    month_abbr, day = match
                    # Try to find the full date string near this
                    full_pattern = rf'{day}\s+\w+\s+\w+\s+\d{{4}},?\s*\d{{1,2}}:\d{{2}}'
                    full_matches = re.findall(full_pattern, page_text)
                    for fm in full_matches:
                        if fm not in dates:
                            dates.append(fm)
            except Exception as e:
                logger.debug(f"Short pattern search failed: {e}")
            
            # Remove duplicates while preserving order
            seen = set()
            unique_dates = []
            for d in dates:
                if d not in seen:
                    seen.add(d)
                    unique_dates.append(d)
            
            return unique_dates[:10]  # Return max 10 dates
            
        except Exception as e:
            logger.debug(f"Date extraction error: {e}")
            return []
    
    def extract_venues_from_page(self):
        """Extract venues from the page"""
        venues = []
        
        try:
            # Look for venue links and text
            venue_keywords = ['Sahne', 'Salon', 'Tiyatro', 'Sahnesi', 'Merkezi', 
                            'KKM', 'PSM', 'AKM', 'CSM', 'Kültür', 'K M', 'K.M.']
            
            for keyword in venue_keywords:
                try:
                    elements = self.driver.find_elements(By.XPATH, 
                        f"//*[contains(text(), '{keyword}')]")
                    
                    for elem in elements[:10]:
                        text = elem.text.strip()
                        text = text.replace('\n', ' ').strip()
                        
                        # Venue names are typically 10-100 chars
                        if 10 < len(text) < 100:
                            # Check it's actually a venue name
                            if any(k in text for k in venue_keywords):
                                if text not in venues:
                                    venues.append(text)
                                if len(venues) >= 3:
                                    break
                    
                    if len(venues) >= 2:
                        break
                except:
                    continue
            
            return venues[:3]
            
        except Exception as e:
            logger.debug(f"Venue extraction error: {e}")
            return []
    
    def collect_play_links(self, max_plays=20):
        """Collect all play links from main page"""
        play_links = []
        
        if not self.safe_get(self.BASE_URL):
            logger.error("Could not load main page")
            return []
        
        # Scroll to load more content
        logger.info("Scrolling to load plays...")
        for i in range(6):
            try:
                self.driver.execute_script(f"window.scrollTo(0, {(i+1)*600});")
                time.sleep(0.8)
            except:
                pass
        
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Find all links
        logger.info("Finding play links...")
        try:
            all_links = self.driver.find_elements(By.TAG_NAME, 'a')
            seen_urls = set()
            
            for link in all_links:
                try:
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    
                    if not href or not text:
                        continue
                    if href in seen_urls:
                        continue
                    if 'biletinial.com/tr-tr/' not in href:
                        continue
                    if '/tiyatro' not in href and '/muzikali' not in href.lower():
                        continue
                    if len(text) < 3 or len(text) > 100:
                        continue
                    if any(skip in text.lower() for skip in ['şehir', 'filtre', 'kategori', 'tarih', 'tümü']):
                        continue
                    
                    # Get image
                    img_url = ''
                    try:
                        img = link.find_element(By.TAG_NAME, 'img')
                        img_url = img.get_attribute('src') or ''
                    except:
                        pass
                    
                    play_links.append({
                        'title': text,
                        'url': href,
                        'image': img_url
                    })
                    seen_urls.add(href)
                    
                    if len(play_links) >= max_plays:
                        break
                        
                except Exception as e:
                    continue
            
            logger.info(f"Found {len(play_links)} unique plays")
            
        except Exception as e:
            logger.error(f"Error collecting links: {e}")
        
        return play_links
    
    def scrape_play_detail(self, url, title):
        """Visit each play's detail page and extract info"""
        details = {
            'dates': [],
            'venues': [],
            'city': None,
        }
        
        if not self.safe_get(url, retries=2):
            logger.warning(f"  ⚠️ Could not load detail page")
            details['city'] = 'Istanbul'
            return details
        
        try:
            # Wait for content to load
            time.sleep(2)
            
            # Scroll to load dynamic content (dates are often below fold)
            self.driver.execute_script("window.scrollTo(0, 600);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, 1200);")
            time.sleep(1)
            
            # Get page text for city detection
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            
            # EXTRACT DATES (fixed method)
            details['dates'] = self.extract_dates_from_page()
            
            # EXTRACT VENUES
            details['venues'] = self.extract_venues_from_page()
            
            # DETECT CITY from venues first, then page text
            detected_city = None
            for venue in details['venues']:
                detected_city = self.detect_city_from_text(venue)
                if detected_city:
                    break
            
            if not detected_city:
                detected_city = self.detect_city_from_text(page_text)
            
            details['city'] = detected_city or 'Istanbul'
            
            logger.info(f"  ✓ City: {details['city']}, {len(details['dates'])} dates, {len(details['venues'])} venues")
            
        except Exception as e:
            logger.warning(f"  ⚠️ Error: {e}")
            if not details['city']:
                details['city'] = 'Istanbul'
        
        return details
    
    def run(self, max_plays=20):
        """Main execution"""
        try:
            if not self.start_driver():
                return None
            
            logger.info(f"\n🎭 Starting scrape (max {max_plays} plays)...")
            logger.info("Version 4.1: FIXED DATE EXTRACTION!")
            logger.info("Phase 1: Collecting links...")
            
            # PHASE 1: Collect links
            play_links = self.collect_play_links(max_plays)
            
            if not play_links:
                logger.error("No plays found!")
                return None
            
            # PHASE 2: Visit each play
            logger.info(f"\nPhase 2: Visiting {len(play_links)} play pages...")
            
            for idx, play_info in enumerate(play_links, 1):
                logger.info(f"\n[{idx}/{len(play_links)}] {play_info['title'][:50]}")
                
                play_data = {
                    'title': play_info['title'],
                    'url': play_info['url'],
                    'image': play_info['image'],
                    'city': 'Istanbul',
                    'dates': [],
                    'venues': [],
                    'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Get details
                details = self.scrape_play_detail(play_info['url'], play_info['title'])
                play_data.update(details)
                
                self.plays.append(play_data)
                
                time.sleep(1)
            
            logger.info(f"\n✓ Successfully scraped {len(self.plays)} plays")
            
            return self.save_to_json()
            
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            self.close()
    
    def save_to_json(self, filename='theater_scraping_results.json'):
        """Save results to JSON"""
        try:
            output_data = {
                'total_plays': len(self.plays),
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'biletinial.com',
                'plays': self.plays
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"\n✓ Saved to {filename}")
            
            # Print summary
            print(f"\n{'='*70}")
            print("SCRAPING SUMMARY")
            print(f"{'='*70}")
            print(f"Total plays: {len(self.plays)}")
            
            # Count by city
            city_counts = {}
            for play in self.plays:
                city = play.get('city', 'Unknown')
                city_counts[city] = city_counts.get(city, 0) + 1
            
            print(f"\nPlays by city:")
            for city, count in sorted(city_counts.items(), key=lambda x: -x[1]):
                print(f"  • {city}: {count} plays")
            
            with_dates = sum(1 for p in self.plays if p.get('dates'))
            with_venues = sum(1 for p in self.plays if p.get('venues'))
            with_images = sum(1 for p in self.plays if p.get('image'))
            
            print(f"\nWith dates: {with_dates} ({with_dates*100//len(self.plays)}%)")
            print(f"With venues: {with_venues} ({with_venues*100//len(self.plays)}%)")
            print(f"With images: {with_images} ({with_images*100//len(self.plays)}%)")
            print(f"{'='*70}\n")
            
            # Show sample with dates
            if self.plays:
                print("📋 Sample plays:")
                print("-" * 70)
                for i, play in enumerate(self.plays[:5], 1):
                    print(f"\n{i}. {play['title']}")
                    print(f"   🏙️  City: {play['city']}")
                    if play.get('venues'):
                        print(f"   📍 Venue: {play['venues'][0][:50]}")
                    if play.get('dates'):
                        print(f"   📅 Dates ({len(play['dates'])}):")
                        for date in play['dates'][:3]:
                            print(f"      - {date}")
                    else:
                        print(f"   📅 No dates found")
                print("-" * 70)
            
            return filename
            
        except Exception as e:
            logger.error(f"Error saving: {e}")
            return None
    
    def close(self):
        """Close browser safely"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed")
            except:
                pass


def main():
    """Main function"""
    print("\n" + "=" * 70)
    print("  THEATER SCRAPER v4.1 - FIXED DATE EXTRACTION")
    print("=" * 70)
    print("  ✓ Fixed date format matching")
    print("  ✓ Better scroll to load dynamic content")
    print("  ✓ Extracts: DD Month DayName YYYY, HH:MM")
    print("=" * 70 + "\n")
    
    print("Options:")
    print("  1. Quick test (5 plays)")
    print("  2. Medium (10 plays)")
    print("  3. Full scrape (20 plays)")
    print("  4. Custom amount\n")
    
    choice = input("Choose option (1-4): ").strip()
    
    if choice == "1":
        max_plays = 5
    elif choice == "2":
        max_plays = 10
    elif choice == "4":
        try:
            max_plays = int(input("How many plays? "))
        except:
            max_plays = 10
    else:
        max_plays = 20
    
    print(f"\n🎭 Scraping {max_plays} plays...\n")
    
    scraper = TheaterScraperV4(headless=False)
    result = scraper.run(max_plays=max_plays)
    
    if result:
        print("\n" + "=" * 70)
        print("  ✓ DONE!")
        print(f"  → Results saved to: {result}")
        print("=" * 70 + "\n")
    else:
        print("\n⚠️ Scraping failed. Check the errors above.\n")


if __name__ == "__main__":
    main()