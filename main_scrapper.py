#!/usr/bin/env python3
"""
Theater Plays Scraper for Istanbul - FINAL VERSION
Scrapes play information including dates and venues from biletinial.com
"""

import json
import time
import os
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TheaterScraper:
    def __init__(self, headless=False):
        """Initialize the scraper with Chrome options"""
        self.options = Options()
        if headless:
            self.options.add_argument('--headless')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_argument('--window-size=1920,1080')
        self.options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = None
        self.plays = []
        
        # Words to exclude (UI elements, filters, etc.)
        self.exclude_keywords = [
            'şehir', 'mekan', 'etkinlik tarihi', 'kategori', 'filtre',
            'seçiniz', 'ara', 'bul', 'göster', 'tümü', 'login', 'sign',
            'my season', 'my tickets', 'account', 'highlights', 'menu',
            'atölye', 'workshop', 'diyalog', 'gastronomi',
            'dialog', 'mozaik', 'parfüm'
        ]

    def start_driver(self):
        """Start the Chrome driver"""
        try:
            self.driver = webdriver.Chrome(options=self.options)
            logger.info("Chrome driver started successfully")
        except Exception as e:
            logger.error(f"Failed to start Chrome driver: {e}")
            raise

    def is_valid_play(self, title):
        """Check if the title is a valid play and not a UI element"""
        if not title or len(title) < 4:
            return False
        
        title_lower = title.lower()
        
        # Exclude UI elements and non-theater content
        for keyword in self.exclude_keywords:
            if keyword in title_lower:
                return False
        
        # Exclude very short generic words
        if len(title) < 10 and title.lower() in ['events', 'istanbul', 'theater', 'tiyatro']:
            return False
        
        return True

    def scrape_play_details(self, play_url):
        """Navigate to play detail page and extract dates, venues, actors"""
        details = {
            'dates': [],
            'venues': [],
            'actors': []
        }
        
        try:
            logger.info(f"  → Visiting detail page...")
            self.driver.get(play_url)
            time.sleep(2)
            
            # Scroll to load all content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            
            # Extract dates - looking for date patterns
            try:
                # Look for elements with date information
                date_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    "div[class*='date'], div[class*='tarih'], span[class*='date'], span[class*='tarih']")
                
                for elem in date_elements:
                    text = elem.text.strip()
                    # Match Turkish date format: "15 Kasım Cumartesi, 15:00"
                    if re.search(r'\d{1,2}\s+(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)', text):
                        details['dates'].append(text)
                    # Match date format with year: "29 Kasım Cumartesi, 20:00"
                    elif re.search(r'\d{1,2}\s+\w+\s+\w+,\s+\d{1,2}:\d{2}', text):
                        details['dates'].append(text)
                
                # Also try to find dates in the page source
                if not details['dates']:
                    page_source = self.driver.page_source
                    # Find Turkish month patterns
                    date_matches = re.findall(r'\d{1,2}\s+(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+\w+,\s+\d{1,2}:\d{2}', page_source)
                    details['dates'].extend(date_matches[:5])  # Limit to 5
                    
            except Exception as e:
                logger.debug(f"  Error extracting dates: {e}")
            
            # Extract venues - looking for venue/location information
            try:
                venue_elements = self.driver.find_elements(By.CSS_SELECTOR,
                    "div[class*='venue'], div[class*='mekan'], span[class*='venue'], span[class*='mekan'], div[class*='salon']")
                
                for elem in venue_elements:
                    text = elem.text.strip()
                    # Look for venue patterns (usually contains "Sahne", "Salon", "KKM", "Tiyatro", etc.)
                    if text and len(text) > 5 and len(text) < 100:
                        if any(word in text for word in ['Sahne', 'Salon', 'KKM', 'Tiyatro', 'Sanat', 'Kültür', 'Merinos', 'Atatürk']):
                            details['venues'].append(text)
                
                # Also check location markers
                location_elements = self.driver.find_elements(By.CSS_SELECTOR, "*[class*='location']")
                for elem in location_elements:
                    text = elem.text.strip()
                    if text and 5 < len(text) < 100:
                        if text not in details['venues']:
                            details['venues'].append(text)
                            
            except Exception as e:
                logger.debug(f"  Error extracting venues: {e}")
            
            # Extract actors/cast
            try:
                actor_elements = self.driver.find_elements(By.CSS_SELECTOR,
                    "div[class*='cast'], div[class*='oyuncu'], span[class*='actor'], div[class*='performer']")
                
                for elem in actor_elements:
                    text = elem.text.strip()
                    if text and 3 < len(text) < 50:
                        details['actors'].append(text)
                        
            except Exception as e:
                logger.debug(f"  Error extracting actors: {e}")
            
            # Remove duplicates
            details['dates'] = list(dict.fromkeys(details['dates']))[:5]
            details['venues'] = list(dict.fromkeys(details['venues']))[:3]
            details['actors'] = list(dict.fromkeys(details['actors']))[:10]
            
            logger.info(f"  → Extracted: {len(details['dates'])} dates, {len(details['venues'])} venues, {len(details['actors'])} actors")
            
        except Exception as e:
            logger.warning(f"  Error scraping play details: {e}")
        
        return details

    def scrape_biletinial(self, get_details=True):
        """Scrape theater plays from biletinial.com"""
        try:
            url = "https://www.biletinial.com/tr-tr/tiyatro"
            logger.info(f"Navigating to {url}")
            self.driver.get(url)
            
            time.sleep(3)
            
            # Scroll down to load more content
            logger.info("Scrolling to load content...")
            for i in range(5):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/5 * {});".format(i+1))
                time.sleep(1)
            
            # Look for all play links
            play_links = []
            
            # Find all links containing "tiyatro" or "muzikali"
            all_links = self.driver.find_elements(By.TAG_NAME, 'a')
            for link in all_links:
                try:
                    href = link.get_attribute('href')
                    if href and 'biletinial.com/tr-tr/' in href and ('tiyatro' in href or 'muzikali' in href.lower()):
                        text = link.text.strip()
                        if self.is_valid_play(text):
                            # Try to get image from parent
                            img_url = ''
                            try:
                                parent = link.find_element(By.XPATH, './..')
                                img = parent.find_element(By.TAG_NAME, 'img')
                                img_url = img.get_attribute('src')
                            except:
                                pass
                            
                            play_links.append({
                                'title': text,
                                'url': href,
                                'image': img_url
                            })
                except:
                    continue
            
            # Remove duplicates by URL
            seen_urls = set()
            unique_plays = []
            for play in play_links:
                if play['url'] not in seen_urls:
                    seen_urls.add(play['url'])
                    unique_plays.append(play)
            
            logger.info(f"Found {len(unique_plays)} unique theater plays")
            
            # Process each play
            for idx, play_info in enumerate(unique_plays[:30], 1):  # Limit to 30 plays
                logger.info(f"\n[{idx}/{min(30, len(unique_plays))}] {play_info['title']}")
                
                play_data = {
                    'title': play_info['title'],
                    'url': play_info['url'],
                    'image': play_info['image'],
                    'dates': [],
                    'venues': [],
                    'actors': [],
                    'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Get detailed information if requested
                if get_details:
                    details = self.scrape_play_details(play_info['url'])
                    play_data.update(details)
                    
                    # Go back to main page
                    self.driver.back()
                    time.sleep(1)
                
                self.plays.append(play_data)
                logger.info(f"✓ Saved: {play_data['title']}")
            
            logger.info(f"\n✓ Successfully scraped {len(self.plays)} plays from biletinial")
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            import traceback
            traceback.print_exc()

    def save_to_json(self, filename='theater_scraping_results.json'):
        """Save scraped data to JSON file in current directory"""
        try:
            # Save to current directory
            output_path = os.path.join(os.getcwd(), filename)
            
            output_data = {
                'total_plays': len(self.plays),
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'location': 'Istanbul, Turkey',
                'source': 'biletinial.com',
                'plays': self.plays
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"\n✓ Results saved to {output_path}")
            
            # Print summary
            print(f"\n{'='*70}")
            print(f"SCRAPING SUMMARY")
            print(f"{'='*70}")
            print(f"Total plays: {len(self.plays)}")
            print(f"With dates: {sum(1 for p in self.plays if p.get('dates'))}")
            print(f"With venues: {sum(1 for p in self.plays if p.get('venues'))}")
            print(f"With actors: {sum(1 for p in self.plays if p.get('actors'))}")
            print(f"With images: {sum(1 for p in self.plays if p.get('image'))}")
            print(f"Saved to: {output_path}")
            print(f"{'='*70}\n")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
            return None

    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")

    def run(self, get_details=True):
        """Main execution method"""
        try:
            self.start_driver()
            
            # Scrape from biletinial
            logger.info("Starting scraping from biletinial.com...")
            logger.info("This will take a few minutes as we visit each play's page...\n")
            
            self.scrape_biletinial(get_details=get_details)
            
            # Save results
            output_file = self.save_to_json('theater_scraping_results.json')
            
            # Print sample of plays
            if self.plays:
                print("Sample of scraped plays:")
                print("-" * 70)
                for i, play in enumerate(self.plays[:5], 1):
                    print(f"\n{i}. {play['title']}")
                    if play.get('dates'):
                        print(f"   📅 Dates: {', '.join(play['dates'][:3])}")
                    if play.get('venues'):
                        print(f"   📍 Venues: {', '.join(play['venues'][:2])}")
                    if play.get('actors'):
                        print(f"   🎭 Actors: {', '.join(play['actors'][:3])}")
                print("-" * 70)
            
            return output_file
            
        except Exception as e:
            logger.error(f"Fatal error during scraping: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            self.close()


def main():
    """Main function"""
    print("\n" + "=" * 70)
    print("  ISTANBUL THEATER PLAYS SCRAPER - FINAL VERSION")
    print("=" * 70)
    print("  This scraper will:")
    print("  - Find all theater plays on biletinial.com")
    print("  - Visit each play's detail page")
    print("  - Extract dates, venues, and actors")
    print("  - Save everything to JSON")
    print("=" * 70 + "\n")
    
    # Ask user if they want to get detailed info
    print("Options:")
    print("  1. Quick scan (titles and URLs only) - ~30 seconds")
    print("  2. Full details (dates, venues, actors) - ~5 minutes")
    
    choice = input("\nEnter choice (1 or 2, default=2): ").strip()
    get_details = choice != '1'
    
    print()
    
    # Run scraper
    scraper = TheaterScraper(headless=False)
    output_file = scraper.run(get_details=get_details)
    
    print("\n" + "=" * 70)
    if output_file:
        print("  ✓ SCRAPING COMPLETED!")
        print(f"  → Saved to: {output_file}")
    else:
        print("  ✗ SCRAPING FAILED - Check errors above")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()