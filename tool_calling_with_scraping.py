#!/usr/bin/env python3
"""
Theater Plays Scraper for Istanbul
Scrapes play information from biletinial.com
Based on actual HTML structure analysis
"""

import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
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

    def start_driver(self):
        """Start the Chrome driver"""
        try:
            self.driver = webdriver.Chrome(options=self.options)
            logger.info("Chrome driver started successfully")
        except Exception as e:
            logger.error(f"Failed to start Chrome driver: {e}")
            raise

    def select_istanbul(self):
        """Select Istanbul from city filter"""
        try:
            logger.info("Attempting to select Istanbul...")
            time.sleep(2)
            
            # Try to find and click the city selector
            city_selectors = [
                "//span[contains(text(), 'ŞEHİR')]",
                "//span[contains(text(), 'Şehir')]",
                "//*[@class='cateorySeciliSehirText']",
                "//b[contains(text(), 'Şehir Seçiniz')]"
            ]
            
            for selector in city_selectors:
                try:
                    city_button = self.driver.find_element(By.XPATH, selector)
                    city_button.click()
                    logger.info("Clicked city selector")
                    time.sleep(1)
                    break
                except NoSuchElementException:
                    continue
            
            # Try to click Istanbul
            istanbul_selectors = [
                "//li[contains(text(), 'İstanbul')]",
                "//a[contains(text(), 'İstanbul')]",
                "//*[contains(@class, 'city')][contains(text(), 'İstanbul')]"
            ]
            
            for selector in istanbul_selectors:
                try:
                    istanbul_option = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    istanbul_option.click()
                    logger.info("Selected Istanbul")
                    time.sleep(2)
                    return True
                except:
                    continue
                    
            logger.warning("Could not find Istanbul selector, continuing with default location")
            return False
            
        except Exception as e:
            logger.warning(f"Error selecting Istanbul: {e}")
            return False

    def scrape_biletinial(self):
        """Scrape theater plays from biletinial.com"""
        try:
            url = "https://www.biletinial.com/tr-tr/tiyatro"
            logger.info(f"Navigating to {url}")
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Try to select Istanbul
            self.select_istanbul()
            
            # Scroll down to load more content
            logger.info("Scrolling to load content...")
            for i in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3 * {});".format(i+1))
                time.sleep(1)
            
            # Wait for event listings
            wait = WebDriverWait(self.driver, 10)
            
            # Try multiple possible selectors for event cards
            event_selectors = [
                "div[class*='etkinlik']",
                "div[class*='event']",
                "a[href*='etkinlik']",
                "div.index-etkinlik-list-item",
                ".etkinlik-item",
                "[class*='theatre']",
                "[class*='tiyatro']"
            ]
            
            play_elements = []
            for selector in event_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        play_elements = elements
                        logger.info(f"Found {len(elements)} elements with selector: {selector}")
                        break
                except:
                    continue
            
            if not play_elements:
                logger.warning("No event elements found, trying alternative approach...")
                # Try finding all links that might be events
                play_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/tr-tr/']")
            
            logger.info(f"Processing {len(play_elements)} potential play elements")
            
            seen_titles = set()
            
            for idx, element in enumerate(play_elements[:100]):  # Process first 100 elements
                try:
                    play_data = self.extract_play_info(element, idx)
                    
                    # Only add if we have a title and haven't seen it before
                    if play_data and play_data.get('title') and play_data['title'] not in seen_titles:
                        # Filter for theater-related content
                        title_lower = play_data['title'].lower()
                        if len(play_data['title']) > 3:  # Avoid very short titles
                            self.plays.append(play_data)
                            seen_titles.add(play_data['title'])
                            logger.info(f"Scraped #{len(self.plays)}: {play_data['title']}")
                            
                except Exception as e:
                    logger.debug(f"Error extracting play {idx}: {e}")
                    continue
            
            logger.info(f"Successfully scraped {len(self.plays)} unique plays")
            
        except TimeoutException:
            logger.error("Timeout waiting for page elements")
        except Exception as e:
            logger.error(f"Error during scraping: {e}")

    def extract_play_info(self, element, idx):
        """Extract play information from a single element"""
        play_data = {
            'title': '',
            'dates': [],
            'venues': [],
            'actors': [],
            'url': '',
            'image': '',
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            # Get the entire text content first
            element_text = element.text.strip()
            
            # Try to get URL first
            try:
                if element.tag_name == 'a':
                    href = element.get_attribute('href')
                else:
                    link = element.find_element(By.TAG_NAME, 'a')
                    href = link.get_attribute('href')
                
                if href and ('etkinlik' in href or 'event' in href or 'tiyatro' in href):
                    play_data['url'] = href
            except:
                pass
            
            # Try different selectors for title
            title_selectors = [
                'h1', 'h2', 'h3', 'h4',
                '.title', '[class*="title"]',
                '[class*="name"]', '[class*="baslik"]',
                'span.etkinlik-adi', 'div.etkinlik-adi'
            ]
            
            for selector in title_selectors:
                try:
                    title_elem = element.find_element(By.CSS_SELECTOR, selector)
                    title_text = title_elem.text.strip()
                    if title_text and len(title_text) > 2:
                        play_data['title'] = title_text
                        break
                except:
                    continue
            
            # If no title found with selectors, try to extract from element text or href
            if not play_data['title']:
                if element_text and len(element_text) > 3 and len(element_text) < 200:
                    # Take first line as title
                    first_line = element_text.split('\n')[0].strip()
                    if first_line:
                        play_data['title'] = first_line
                elif play_data['url']:
                    # Try to extract title from URL
                    url_parts = play_data['url'].split('/')
                    for part in reversed(url_parts):
                        if part and len(part) > 3 and not part.isdigit():
                            play_data['title'] = part.replace('-', ' ').title()
                            break
            
            # Try to find venue/location
            venue_selectors = [
                '[class*="mekan"]', '[class*="venue"]', '[class*="salon"]',
                '[class*="location"]', 'span.venue', 'div.venue'
            ]
            
            for selector in venue_selectors:
                try:
                    venue_elems = element.find_elements(By.CSS_SELECTOR, selector)
                    for venue_elem in venue_elems:
                        venue_text = venue_elem.text.strip()
                        if venue_text and len(venue_text) > 2:
                            play_data['venues'].append(venue_text)
                except:
                    continue
            
            # Try to find date
            date_selectors = [
                '[class*="tarih"]', '[class*="date"]', 
                'time', 'span.date', '[class*="gun"]'
            ]
            
            for selector in date_selectors:
                try:
                    date_elems = element.find_elements(By.CSS_SELECTOR, selector)
                    for date_elem in date_elems:
                        date_text = date_elem.text.strip()
                        if date_text:
                            play_data['dates'].append(date_text)
                except:
                    continue
            
            # Try to find actors/cast
            actor_selectors = [
                '[class*="oyuncu"]', '[class*="actor"]', '[class*="cast"]',
                '[class*="sanatci"]', 'span.cast', 'div.performers'
            ]
            
            for selector in actor_selectors:
                try:
                    actor_elems = element.find_elements(By.CSS_SELECTOR, selector)
                    for actor_elem in actor_elems:
                        actor_text = actor_elem.text.strip()
                        if actor_text and len(actor_text) > 2:
                            play_data['actors'].append(actor_text)
                except:
                    continue
            
            # Try to find image
            try:
                img = element.find_element(By.TAG_NAME, 'img')
                img_src = img.get_attribute('src')
                if img_src:
                    play_data['image'] = img_src
            except:
                pass
            
        except Exception as e:
            logger.debug(f"Error extracting info from element {idx}: {e}")
        
        return play_data

    def scrape_alternative_sites(self):
        """Try alternative theater websites if biletinial doesn't work well"""
        alternative_urls = [
            ("https://www.biletix.com/search/ISTANBUL/tr", "biletix"),
            ("https://www.passo.com.tr/tr/etkinlikler/tiyatro", "passo"),
        ]
        
        for url, site_name in alternative_urls:
            try:
                logger.info(f"Trying alternative source: {site_name}")
                self.driver.get(url)
                time.sleep(4)
                
                # Scroll to load content
                for i in range(2):
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2 * {});".format(i+1))
                    time.sleep(1)
                
                # Generic scraping logic
                elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    "div[class*='event'], div[class*='show'], article, a[href*='etkinlik'], a[href*='event']")
                
                logger.info(f"Found {len(elements)} elements on {site_name}")
                
                seen_titles = {play['title'] for play in self.plays}
                
                for idx, element in enumerate(elements[:50]):
                    try:
                        play_data = self.extract_play_info(element, idx)
                        if play_data and play_data.get('title') and play_data['title'] not in seen_titles:
                            if len(play_data['title']) > 3:
                                self.plays.append(play_data)
                                seen_titles.add(play_data['title'])
                                logger.info(f"Scraped from {site_name}: {play_data['title']}")
                    except Exception as e:
                        continue
                
                if len(self.plays) > 5:
                    logger.info(f"Successfully scraped {len(self.plays)} total plays")
                    break
                    
            except Exception as e:
                logger.error(f"Error with alternative source {site_name}: {e}")
                continue

    def save_to_json(self, filename='theater_scraping_results.json'):
        """Save scraped data to JSON file"""
        try:
            # Clean up data before saving
            cleaned_plays = []
            for play in self.plays:
                # Remove duplicates from venues and dates
                if play.get('venues'):
                    play['venues'] = list(dict.fromkeys(play['venues']))
                if play.get('dates'):
                    play['dates'] = list(dict.fromkeys(play['dates']))
                if play.get('actors'):
                    play['actors'] = list(dict.fromkeys(play['actors']))
                
                # Only include plays with titles
                if play.get('title'):
                    cleaned_plays.append(play)
            
            output_data = {
                'total_plays': len(cleaned_plays),
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'location': 'Istanbul, Turkey',
                'source': 'biletinial.com and alternative sources',
                'plays': cleaned_plays
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✓ Results saved to {filename}")
            logger.info(f"✓ Total plays scraped: {len(cleaned_plays)}")
            
            # Print summary
            print(f"\n{'='*60}")
            print(f"SCRAPING SUMMARY")
            print(f"{'='*60}")
            print(f"Total plays found: {len(cleaned_plays)}")
            print(f"With venues: {sum(1 for p in cleaned_plays if p.get('venues'))}")
            print(f"With dates: {sum(1 for p in cleaned_plays if p.get('dates'))}")
            print(f"With actors: {sum(1 for p in cleaned_plays if p.get('actors'))}")
            print(f"With images: {sum(1 for p in cleaned_plays if p.get('image'))}")
            print(f"{'='*60}\n")
            
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")

    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")

    def run(self):
        """Main execution method"""
        try:
            self.start_driver()
            
            # Try primary source
            logger.info("Starting scraping from biletinial.com...")
            self.scrape_biletinial()
            
            # If we have very few results, try alternative sources
            if len(self.plays) < 5:
                logger.warning(f"Only found {len(self.plays)} plays from primary source, trying alternatives...")
                self.scrape_alternative_sites()
            
            # Save results
            output_path = '/mnt/user-data/outputs/theater_scraping_results.json'
            self.save_to_json(output_path)
            
            # Also print first few plays as sample
            if self.plays:
                print("\nSample of scraped plays:")
                print("-" * 60)
                for i, play in enumerate(self.plays[:5], 1):
                    print(f"\n{i}. {play['title']}")
                    if play.get('venues'):
                        print(f"   Venue: {', '.join(play['venues'][:2])}")
                    if play.get('dates'):
                        print(f"   Dates: {', '.join(play['dates'][:2])}")
                    if play.get('url'):
                        print(f"   URL: {play['url'][:70]}...")
                print("-" * 60)
            
        except Exception as e:
            logger.error(f"Fatal error during scraping: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.close()


def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("  ISTANBUL THEATER PLAYS SCRAPER")
    print("=" * 60)
    print("  Source: biletinial.com")
    print("  Target: Istanbul theaters")
    print("=" * 60 + "\n")
    
    # Set headless=False to see the browser in action
    # Set headless=True to run in background
    scraper = TheaterScraper(headless=False)
    scraper.run()
    
    print("\n" + "=" * 60)
    print("  ✓ SCRAPING COMPLETED!")
    print("  → Check: theater_scraping_results.json")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()