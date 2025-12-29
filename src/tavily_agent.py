# # src/tavily_agent.py
# """
# TavilySearchAgent - Web Search for Theater Information
# Fallback when database doesn't have results

# Andrew Ng Pattern: Tool Use Agent
# - Searches web for current theater information
# - Enriches play data with reviews, news
# - Finds plays not in database
# """

# import os
# import re
# from datetime import datetime, timedelta
# from dotenv import load_dotenv

# load_dotenv()

# # Try to import tavily
# try:
#     from tavily import TavilyClient
#     TAVILY_AVAILABLE = True
# except ImportError:
#     TAVILY_AVAILABLE = False
#     print("⚠️  Tavily not installed. Run: pip install tavily-python")


# class TavilySearchAgent:
#     """
#     Web search agent for theater information
    
#     Use cases:
#     1. Fallback when database has no results for a city/date
#     2. Enrich play information (reviews, cast news)
#     3. Find alternative ticket sources
#     4. Get current theater news
#     """
    
#     def __init__(self):
#         self.api_key = os.getenv("TAVILY_API_KEY")
#         self.client = None
        
#         if not self.api_key:
#             print("⚠️  TAVILY_API_KEY not found in .env")
#             return
        
#         if TAVILY_AVAILABLE:
#             try:
#                 self.client = TavilyClient(api_key=self.api_key)
#                 print("✅ Tavily Search Agent initialized!")
#             except Exception as e:
#                 print(f"⚠️  Tavily initialization failed: {e}")
#         else:
#             print("⚠️  Tavily library not available")
    
#     def is_available(self):
#         """Check if Tavily is ready to use"""
#         return self.client is not None
    
#     def search_plays(self, city: str, date_str: str = None, genre: str = None, max_results: int = 5):
#         """
#         Search for theater plays in a city
        
#         Args:
#             city: City name (Istanbul, Ankara, etc.)
#             date_str: Date string (e.g., "30 Aralık 2025" or "yarın")
#             genre: Optional genre filter
#             max_results: Maximum number of results
            
#         Returns:
#             dict with 'success', 'plays', 'source_urls'
#         """
#         if not self.client:
#             return {'success': False, 'error': 'Tavily not available', 'plays': []}
        
#         # Build search query
#         query_parts = [f"{city} tiyatro oyunları"]
        
#         if date_str:
#             query_parts.append(date_str)
#         else:
#             # Default to this week
#             query_parts.append("bu hafta")
        
#         if genre:
#             query_parts.append(genre)
        
#         query = " ".join(query_parts)
        
#         print(f"🔍 Tavily searching: '{query}'")
        
#         try:
#             response = self.client.search(
#                 query=query,
#                 search_depth="advanced",
#                 max_results=max_results,
#                 include_domains=["biletinial.com", "biletix.com", "passo.com.tr", 
#                                 "tiyatrolar.com.tr", "mobilet.com", "bubilet.com"],
#                 include_answer=True
#             )
            
#             plays = self._parse_search_results(response, city)
            
#             return {
#                 'success': True,
#                 'plays': plays,
#                 'answer': response.get('answer', ''),
#                 'source_urls': [r.get('url') for r in response.get('results', [])],
#                 'query': query
#             }
            
#         except Exception as e:
#             print(f"❌ Tavily search error: {e}")
#             return {'success': False, 'error': str(e), 'plays': []}
    
#     def _parse_search_results(self, response, city):
#         """
#         Parse Tavily results into play objects
#         """
#         plays = []
#         seen_titles = set()
        
#         for result in response.get('results', []):
#             title = result.get('title', '')
#             content = result.get('content', '')
#             url = result.get('url', '')
            
#             # Try to extract play info from title/content
#             play_info = self._extract_play_info(title, content, url, city)
            
#             if play_info and play_info['title'] not in seen_titles:
#                 plays.append(play_info)
#                 seen_titles.add(play_info['title'])
        
#         return plays
    
#     def _extract_play_info(self, title, content, url, city):
#         """
#         Extract structured play info from search result
#         """
#         # Skip non-play results
#         skip_keywords = ['hakkında', 'tarihçe', 'adres', 'iletişim', 'blog', 'haber']
#         if any(kw in title.lower() for kw in skip_keywords):
#             return None
        
#         # Try to identify play title
#         # Pattern: "Play Name | Biletinial" or "Play Name Tiyatro Biletleri"
#         play_title = None
        
#         # Clean up title
#         title_clean = title.split('|')[0].strip()
#         title_clean = title_clean.replace('Tiyatro Biletleri', '').strip()
#         title_clean = title_clean.replace('Tiyatro Oyunu', '').strip()
#         title_clean = title_clean.replace('biletleri', '').strip()
        
#         if len(title_clean) > 3 and len(title_clean) < 100:
#             play_title = title_clean
        
#         if not play_title:
#             return None
        
#         # Extract venue from content if possible
#         venue = self._extract_venue(content)
        
#         # Extract dates from content
#         dates = self._extract_dates(content)
        
#         return {
#             'title': play_title,
#             'venue': venue or f"{city} (web araması)",
#             'city': city,
#             'showtimes': '; '.join(dates) if dates else None,
#             'ticket_url': url,
#             'source': 'tavily_search',
#             'content_snippet': content[:200] if content else None
#         }
    
#     def _extract_venue(self, content):
#         """Extract venue name from content"""
#         venue_keywords = ['Sahne', 'Salon', 'Tiyatro', 'Merkezi', 'KKM', 'AKM', 'PSM']
        
#         for keyword in venue_keywords:
#             # Look for "at Venue Name" patterns
#             pattern = rf'({keyword}[^,.\n]*)'
#             match = re.search(pattern, content, re.IGNORECASE)
#             if match:
#                 venue = match.group(1).strip()
#                 if 10 < len(venue) < 80:
#                     return venue
        
#         return None
    
#     def _extract_dates(self, content):
#         """Extract dates from content"""
#         dates = []
        
#         # Turkish months
#         months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
#                  'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
        
#         for month in months:
#             # Pattern: "15 Ocak 20:30" or "15 Ocak Cumartesi 20:30"
#             pattern = rf'(\d{{1,2}}\s+{month}[^,\n]*\d{{1,2}}:\d{{2}})'
#             matches = re.findall(pattern, content, re.IGNORECASE)
#             dates.extend(matches[:3])  # Max 3 per month
        
#         return dates[:5]  # Return max 5 dates
    
#     def enrich_play(self, play_title: str, city: str = None):
#         """
#         Enrich play information with web search
#         Gets reviews, cast info, news
        
#         Args:
#             play_title: Name of the play
#             city: Optional city for context
            
#         Returns:
#             dict with additional info
#         """
#         if not self.client:
#             return {'success': False, 'error': 'Tavily not available'}
        
#         query = f'"{play_title}" tiyatro'
#         if city:
#             query += f" {city}"
        
#         print(f"🔍 Enriching: '{play_title}'")
        
#         try:
#             response = self.client.search(
#                 query=query,
#                 search_depth="basic",
#                 max_results=3,
#                 include_answer=True
#             )
            
#             return {
#                 'success': True,
#                 'summary': response.get('answer', ''),
#                 'sources': [
#                     {
#                         'title': r.get('title'),
#                         'url': r.get('url'),
#                         'snippet': r.get('content', '')[:200]
#                     }
#                     for r in response.get('results', [])
#                 ]
#             }
            
#         except Exception as e:
#             return {'success': False, 'error': str(e)}
    
#     def search_theater_news(self, city: str = None, max_results: int = 5):
#         """
#         Get latest theater news
        
#         Args:
#             city: Optional city filter
#             max_results: Maximum results
            
#         Returns:
#             dict with news items
#         """
#         if not self.client:
#             return {'success': False, 'error': 'Tavily not available'}
        
#         query = "tiyatro haberleri"
#         if city:
#             query = f"{city} {query}"
        
#         query += " 2025"  # Current year for recency
        
#         try:
#             response = self.client.search(
#                 query=query,
#                 search_depth="basic",
#                 max_results=max_results,
#                 include_domains=["haberturk.com", "hurriyet.com.tr", "milliyet.com.tr",
#                                "tiyatrolar.com.tr", "kultursanat.com"]
#             )
            
#             news = []
#             for result in response.get('results', []):
#                 news.append({
#                     'title': result.get('title'),
#                     'url': result.get('url'),
#                     'snippet': result.get('content', '')[:200],
#                     'published_date': result.get('published_date')
#                 })
            
#             return {
#                 'success': True,
#                 'news': news,
#                 'answer': response.get('answer', '')
#             }
            
#         except Exception as e:
#             return {'success': False, 'error': str(e)}
    
#     def find_alternative_tickets(self, play_title: str, city: str):
#         """
#         Find alternative ticket sources for a play
        
#         Args:
#             play_title: Name of the play
#             city: City
            
#         Returns:
#             dict with ticket sources
#         """
#         if not self.client:
#             return {'success': False, 'error': 'Tavily not available'}
        
#         query = f'"{play_title}" bilet {city}'
        
#         try:
#             response = self.client.search(
#                 query=query,
#                 search_depth="basic",
#                 max_results=5,
#                 include_domains=["biletinial.com", "biletix.com", "passo.com.tr",
#                                "mobilet.com", "bubilet.com", "biletino.com"]
#             )
            
#             tickets = []
#             for result in response.get('results', []):
#                 # Identify the ticket platform
#                 url = result.get('url', '')
#                 platform = 'Diğer'
                
#                 if 'biletinial' in url:
#                     platform = 'Biletinial'
#                 elif 'biletix' in url:
#                     platform = 'Biletix'
#                 elif 'passo' in url:
#                     platform = 'Passo'
#                 elif 'mobilet' in url:
#                     platform = 'Mobilet'
#                 elif 'bubilet' in url:
#                     platform = 'BuBilet'
                
#                 tickets.append({
#                     'platform': platform,
#                     'url': url,
#                     'title': result.get('title'),
#                     'snippet': result.get('content', '')[:150]
#                 })
            
#             return {
#                 'success': True,
#                 'tickets': tickets
#             }
            
#         except Exception as e:
#             return {'success': False, 'error': str(e)}


# # ==================== DEMO ====================

# def demo():
#     """Demo the Tavily search agent"""
#     print("\n" + "="*70)
#     print("  🔍 TAVILY SEARCH AGENT DEMO")
#     print("="*70 + "\n")
    
#     agent = TavilySearchAgent()
    
#     if not agent.is_available():
#         print("❌ Tavily not available. Check your API key.")
#         return
    
#     # Test 1: Search for plays
#     print("\n📍 Test 1: Searching for plays in Istanbul...")
#     result = agent.search_plays("Istanbul", "bu hafta", max_results=3)
    
#     if result['success']:
#         print(f"✅ Found {len(result['plays'])} plays")
#         for play in result['plays']:
#             print(f"   🎭 {play['title']}")
#             print(f"      📍 {play['venue']}")
#             print(f"      🎫 {play['ticket_url']}")
#     else:
#         print(f"❌ Error: {result.get('error')}")
    
#     # Test 2: Theater news
#     print("\n📰 Test 2: Getting theater news...")
#     news_result = agent.search_theater_news("Istanbul", max_results=3)
    
#     if news_result['success']:
#         print(f"✅ Found {len(news_result['news'])} news items")
#         for item in news_result['news']:
#             print(f"   📰 {item['title'][:50]}...")
    
#     print("\n" + "="*70)
#     print("  ✅ Demo complete!")
#     print("="*70 + "\n")


# if __name__ == "__main__":
#     demo()



# ----------------------2------------------------

# # src/tavily_agent.py
# """
# TavilySearchAgent v2.0 - IMPROVED Web Search for Theater Information
# Better query construction and result parsing

# Andrew Ng Pattern: Tool Use Agent with Reflection
# - Smarter search queries
# - Uses AI-generated answers
# - Filters out category pages
# - Two-phase search when needed
# """

# import os
# import re
# from datetime import datetime, timedelta
# from dotenv import load_dotenv

# load_dotenv()

# # Try to import tavily
# try:
#     from tavily import TavilyClient
#     TAVILY_AVAILABLE = True
# except ImportError:
#     TAVILY_AVAILABLE = False
#     print("⚠️  Tavily not installed. Run: pip install tavily-python")


# class TavilySearchAgent:
#     """
#     Web search agent for theater information - IMPROVED VERSION
    
#     Key improvements:
#     1. Better search queries (specific, not generic)
#     2. Uses Tavily's AI answer feature
#     3. Filters out category/list pages
#     4. Extracts actual play names from results
#     """
    
#     def __init__(self):
#         self.api_key = os.getenv("TAVILY_API_KEY")
#         self.client = None
        
#         if not self.api_key:
#             print("⚠️  TAVILY_API_KEY not found in .env")
#             return
        
#         if TAVILY_AVAILABLE:
#             try:
#                 self.client = TavilyClient(api_key=self.api_key)
#                 print("✅ Tavily Search Agent initialized!")
#             except Exception as e:
#                 print(f"⚠️  Tavily initialization failed: {e}")
#         else:
#             print("⚠️  Tavily library not available")
    
#     def is_available(self):
#         """Check if Tavily is ready to use"""
#         return self.client is not None
    
#     def search_plays(self, city: str, date_str: str = None, genre: str = None, max_results: int = 5):
#         """
#         Search for theater plays - IMPROVED VERSION
        
#         Strategy:
#         1. Build a specific query asking for actual play names
#         2. Use Tavily's AI answer for a summary
#         3. Parse results to extract real plays (not category pages)
#         """
#         if not self.client:
#             return {'success': False, 'error': 'Tavily not available', 'plays': []}
        
#         # ==================== BUILD SMART QUERY ====================
#         # Instead of generic "tiyatro oyunları", ask for specific plays
        
#         # Convert date to Turkish format for better results
#         date_query = ""
#         if date_str:
#             if date_str.lower() in ['yarın', 'yarin', 'tomorrow']:
#                 tomorrow = datetime.now() + timedelta(days=1)
#                 date_query = tomorrow.strftime("%d %B %Y")  # "30 Aralık 2025"
#             elif date_str.lower() in ['bugün', 'bugun', 'today']:
#                 date_query = datetime.now().strftime("%d %B %Y")
#             elif 'hafta sonu' in date_str.lower():
#                 date_query = "bu hafta sonu Cumartesi Pazar"
#             else:
#                 date_query = date_str
        
#         # Build specific query
#         if date_query:
#             query = f"{city} tiyatro {date_query} hangi oyunlar var bilet"
#         else:
#             query = f"{city} tiyatro bu hafta gösterimde olan oyunlar bilet"
        
#         print(f"🔍 Tavily searching: '{query}'")
        
#         try:
#             # ==================== SEARCH WITH AI ANSWER ====================
#             response = self.client.search(
#                 query=query,
#                 search_depth="advanced",
#                 max_results=max_results + 3,  # Get extra to filter
#                 include_domains=[
#                     "biletinial.com", 
#                     "biletix.com", 
#                     "passo.com.tr", 
#                     "tiyatrolar.com.tr", 
#                     "mobilet.com"
#                 ],
#                 exclude_domains=[
#                     "twitter.com",
#                     "facebook.com",
#                     "instagram.com"
#                 ],
#                 include_answer=True,  # Get AI-generated summary!
#                 include_raw_content=False
#             )
            
#             # ==================== EXTRACT AI ANSWER ====================
#             ai_answer = response.get('answer', '')
            
#             # ==================== PARSE RESULTS ====================
#             plays = self._parse_search_results_v2(response, city, date_str)
            
#             # ==================== EXTRACT PLAYS FROM AI ANSWER ====================
#             if ai_answer and len(plays) < 3:
#                 answer_plays = self._extract_plays_from_answer(ai_answer, city)
#                 # Add plays from answer that aren't already in list
#                 existing_titles = {p['title'].lower() for p in plays}
#                 for ap in answer_plays:
#                     if ap['title'].lower() not in existing_titles:
#                         plays.append(ap)
            
#             return {
#                 'success': True,
#                 'plays': plays[:max_results],
#                 'ai_summary': ai_answer,  # Include AI summary!
#                 'source_urls': [r.get('url') for r in response.get('results', [])[:3]],
#                 'query': query
#             }
            
#         except Exception as e:
#             print(f"❌ Tavily search error: {e}")
#             return {'success': False, 'error': str(e), 'plays': []}
    
#     def _parse_search_results_v2(self, response, city, date_str):
#         """
#         Parse Tavily results - IMPROVED VERSION
#         Filters out category pages, extracts actual play info
#         """
#         plays = []
#         seen_titles = set()
        
#         # Keywords that indicate a category/list page (NOT a specific play)
#         category_indicators = [
#             'tiyatro oyunları', 'biletleri', 'etkinlik takvimi', 
#             'istanbul avrupa', 'istanbul anadolu', 'ankara tiyatro',
#             'şehir tiyatroları', 'devlet tiyatroları', 'tüm oyunlar',
#             'kategori', 'filtrele', 'sırala'
#         ]
        
#         for result in response.get('results', []):
#             url = result.get('url', '')
#             title = result.get('title', '')
#             content = result.get('content', '')
            
#             # Skip category/list pages
#             title_lower = title.lower()
#             if any(cat in title_lower for cat in category_indicators):
#                 continue
            
#             # Skip if URL is a category page
#             if url.endswith('/tiyatro') or url.endswith('/tiyatro/'):
#                 continue
#             if '/istanbul-avrupa' in url or '/istanbul-anadolu' in url:
#                 continue
#             if '/etkinlik-takvimi/' in url and not re.search(r'/\d+$', url):
#                 continue
            
#             # Try to extract play info
#             play_info = self._extract_play_from_result(title, content, url, city)
            
#             if play_info and play_info['title'] not in seen_titles:
#                 # Additional validation: title should look like a play name
#                 if self._is_valid_play_title(play_info['title']):
#                     plays.append(play_info)
#                     seen_titles.add(play_info['title'])
        
#         return plays
    
#     def _is_valid_play_title(self, title):
#         """Check if a title looks like an actual play name"""
#         if not title or len(title) < 3:
#             return False
        
#         # Reject generic titles
#         generic_titles = [
#             'tiyatro oyunları', 'biletleri', 'etkinlik', 'takvim',
#             'istanbul', 'ankara', 'izmir', 'türkiye', 'sahne',
#             'biletinial', 'biletix', 'passo'
#         ]
        
#         title_lower = title.lower()
#         for generic in generic_titles:
#             if title_lower == generic or title_lower.startswith(generic + ' '):
#                 return False
        
#         # Should have at least one capital letter (play names are usually capitalized)
#         if not any(c.isupper() for c in title):
#             return False
        
#         return True
    
#     def _extract_play_from_result(self, title, content, url, city):
#         """Extract structured play info from a search result"""
        
#         # Clean title - remove common suffixes
#         clean_title = title
#         remove_suffixes = [
#             ' | biletinial', ' | Biletinial', ' - biletinial',
#             ' Tiyatro Biletleri', ' Tiyatro Oyunu', ' biletleri',
#             ' | tiyatrolar.com.tr', ' - Bilet', ' Bilet'
#         ]
#         for suffix in remove_suffixes:
#             if clean_title.endswith(suffix):
#                 clean_title = clean_title[:-len(suffix)]
#             clean_title = clean_title.replace(suffix, '')
        
#         clean_title = clean_title.strip()
        
#         if len(clean_title) < 3 or len(clean_title) > 80:
#             return None
        
#         # Extract venue from content
#         venue = self._extract_venue_v2(content, url)
        
#         # Extract dates from content
#         dates = self._extract_dates_v2(content)
        
#         return {
#             'title': clean_title,
#             'venue': venue or f"{city} - Web araması",
#             'city': city,
#             'showtimes': '; '.join(dates) if dates else None,
#             'ticket_url': url,
#             'source': 'tavily_web',
#             'description': content[:150] if content else None
#         }
    
#     def _extract_venue_v2(self, content, url):
#         """Extract venue name - improved version"""
#         if not content:
#             return None
        
#         # Common venue patterns
#         venue_patterns = [
#             r'([\w\s]+ Sahnesi)',
#             r'([\w\s]+ Salonu)',
#             r'([\w\s]+ Tiyatrosu)',
#             r'(Zorlu PSM[\w\s]*)',
#             r'(DasDas[\w\s]*)',
#             r'(Trump[\w\s]*Sahne)',
#             r'(AKM[\w\s]*)',
#             r'(Harbiye[\w\s]*)',
#             r'(Caddebostan KKM[\w\s]*)',
#             r'(Moda Sahnesi)',
#             r'(Pera[\w\s]*)',
#         ]
        
#         for pattern in venue_patterns:
#             match = re.search(pattern, content, re.IGNORECASE)
#             if match:
#                 venue = match.group(1).strip()
#                 if 10 < len(venue) < 60:
#                     return venue
        
#         return None
    
#     def _extract_dates_v2(self, content):
#         """Extract dates - improved version"""
#         if not content:
#             return []
        
#         dates = []
        
#         # Turkish months
#         months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
#                  'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
        
#         for month in months:
#             # Pattern: "15 Ocak 2025" or "15 Ocak Cumartesi 20:30"
#             patterns = [
#                 rf'(\d{{1,2}}\s+{month}\s+\d{{4}})',
#                 rf'(\d{{1,2}}\s+{month}\s+\w+\s+\d{{2}}:\d{{2}})',
#                 rf'(\d{{1,2}}\s+{month})'
#             ]
            
#             for pattern in patterns:
#                 matches = re.findall(pattern, content, re.IGNORECASE)
#                 dates.extend(matches[:2])
        
#         # Remove duplicates while preserving order
#         seen = set()
#         unique_dates = []
#         for d in dates:
#             if d not in seen:
#                 seen.add(d)
#                 unique_dates.append(d)
        
#         return unique_dates[:3]
    
#     def _extract_plays_from_answer(self, ai_answer, city):
#         """
#         Extract play names from Tavily's AI-generated answer
#         The AI answer often mentions specific play names
#         """
#         plays = []
        
#         if not ai_answer:
#             return plays
        
#         # Look for patterns like "X oyunu", "X tiyatro oyunu", quoted names
#         patterns = [
#             r'"([^"]+)"',  # Quoted names
#             r"'([^']+)'",  # Single quoted
#             r'„([^"]+)"',  # German quotes sometimes used
#             r'«([^»]+)»',  # French quotes
#         ]
        
#         for pattern in patterns:
#             matches = re.findall(pattern, ai_answer)
#             for match in matches:
#                 if 5 < len(match) < 60 and self._is_valid_play_title(match):
#                     plays.append({
#                         'title': match,
#                         'venue': f"{city} - AI önerisi",
#                         'city': city,
#                         'showtimes': None,
#                         'ticket_url': None,
#                         'source': 'tavily_ai_answer',
#                         'description': f"AI özeti: {ai_answer[:100]}..."
#                     })
        
#         return plays[:3]  # Max 3 from AI answer
    
#     def search_specific_play(self, play_name: str, city: str):
#         """
#         Search for a specific play by name
#         Use this for enrichment or finding ticket links
#         """
#         if not self.client:
#             return {'success': False, 'error': 'Tavily not available'}
        
#         query = f'"{play_name}" tiyatro {city} bilet seans'
        
#         print(f"🔍 Searching for specific play: '{play_name}'")
        
#         try:
#             response = self.client.search(
#                 query=query,
#                 search_depth="basic",
#                 max_results=3,
#                 include_domains=["biletinial.com", "biletix.com", "passo.com.tr"],
#                 include_answer=True
#             )
            
#             # Find the best matching result
#             best_match = None
#             play_name_lower = play_name.lower()
            
#             for result in response.get('results', []):
#                 if play_name_lower in result.get('title', '').lower():
#                     best_match = result
#                     break
            
#             if not best_match and response.get('results'):
#                 best_match = response['results'][0]
            
#             if best_match:
#                 return {
#                     'success': True,
#                     'title': play_name,
#                     'ticket_url': best_match.get('url'),
#                     'venue': self._extract_venue_v2(best_match.get('content', ''), ''),
#                     'dates': self._extract_dates_v2(best_match.get('content', '')),
#                     'description': best_match.get('content', '')[:200],
#                     'ai_summary': response.get('answer', '')
#                 }
            
#             return {'success': False, 'error': 'Play not found'}
            
#         except Exception as e:
#             return {'success': False, 'error': str(e)}
    
#     def enrich_play(self, play_title: str, city: str = None):
#         """Enrich play information with web search"""
#         return self.search_specific_play(play_title, city or 'Istanbul')
    
#     def search_theater_news(self, city: str = None, max_results: int = 5):
#         """Get latest theater news"""
#         if not self.client:
#             return {'success': False, 'error': 'Tavily not available'}
        
#         query = "tiyatro haberleri güncel"
#         if city:
#             query = f"{city} {query}"
        
#         try:
#             response = self.client.search(
#                 query=query,
#                 search_depth="basic",
#                 max_results=max_results,
#                 include_answer=True
#             )
            
#             news = []
#             for result in response.get('results', []):
#                 news.append({
#                     'title': result.get('title'),
#                     'url': result.get('url'),
#                     'snippet': result.get('content', '')[:200],
#                 })
            
#             return {
#                 'success': True,
#                 'news': news,
#                 'summary': response.get('answer', '')
#             }
            
#         except Exception as e:
#             return {'success': False, 'error': str(e)}


# # ==================== DEMO ====================

# def demo():
#     """Demo the improved Tavily search agent"""
#     print("\n" + "="*70)
#     print("  🔍 TAVILY SEARCH AGENT v2.0 - IMPROVED")
#     print("="*70 + "\n")
    
#     agent = TavilySearchAgent()
    
#     if not agent.is_available():
#         print("❌ Tavily not available. Check your API key.")
#         return
    
#     # Test: Search for plays tomorrow in Istanbul
#     print("\n📍 Test: Searching for plays in Istanbul tomorrow...")
#     result = agent.search_plays("Istanbul", "yarın", max_results=5)
    
#     if result['success']:
#         print(f"\n✅ Found {len(result['plays'])} plays")
        
#         if result.get('ai_summary'):
#             print(f"\n🤖 AI Summary:\n{result['ai_summary'][:300]}...")
        
#         print("\n📋 Plays found:")
#         for i, play in enumerate(result['plays'], 1):
#             print(f"\n{i}. {play['title']}")
#             print(f"   📍 {play['venue']}")
#             if play.get('showtimes'):
#                 print(f"   📅 {play['showtimes']}")
#             if play.get('ticket_url'):
#                 print(f"   🎫 {play['ticket_url'][:50]}...")
#     else:
#         print(f"❌ Error: {result.get('error')}")
    
#     print("\n" + "="*70)


# if __name__ == "__main__":
#     demo()


# ------------------------- 3-----------------------

# # src/tavily_agent.py
# """
# TavilySearchAgent v2.0 - IMPROVED Web Search for Theater Information
# Better query construction and result parsing

# Andrew Ng Pattern: Tool Use Agent with Reflection
# - Smarter search queries
# - Uses AI-generated answers
# - Filters out category pages
# - Two-phase search when needed
# """

# import os
# import re
# from datetime import datetime, timedelta
# from dotenv import load_dotenv

# load_dotenv()

# # Try to import tavily
# try:
#     from tavily import TavilyClient
#     TAVILY_AVAILABLE = True
# except ImportError:
#     TAVILY_AVAILABLE = False
#     print("⚠️  Tavily not installed. Run: pip install tavily-python")


# class TavilySearchAgent:
#     """
#     Web search agent for theater information - IMPROVED VERSION
    
#     Key improvements:
#     1. Better search queries (specific, not generic)
#     2. Uses Tavily's AI answer feature
#     3. Filters out category/list pages
#     4. Extracts actual play names from results
#     """
    
#     def __init__(self):
#         self.api_key = os.getenv("TAVILY_API_KEY")
#         self.client = None
        
#         if not self.api_key:
#             print("⚠️  TAVILY_API_KEY not found in .env")
#             return
        
#         if TAVILY_AVAILABLE:
#             try:
#                 self.client = TavilyClient(api_key=self.api_key)
#                 print("✅ Tavily Search Agent initialized!")
#             except Exception as e:
#                 print(f"⚠️  Tavily initialization failed: {e}")
#         else:
#             print("⚠️  Tavily library not available")
    
#     def is_available(self):
#         """Check if Tavily is ready to use"""
#         return self.client is not None
    
#     def search_plays(self, city: str, date_str: str = None, genre: str = None, max_results: int = 5):
#         """
#         Search for theater plays - IMPROVED VERSION
        
#         Strategy:
#         1. Build a specific query asking for actual play names
#         2. Use Tavily's AI answer for a summary
#         3. Parse results to extract real plays (not category pages)
#         """
#         if not self.client:
#             return {'success': False, 'error': 'Tavily not available', 'plays': []}
        
#         # ==================== BUILD SMART QUERY ====================
#         # Turkish month names for proper date formatting
#         turkish_months = {
#             1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan',
#             5: 'Mayıs', 6: 'Haziran', 7: 'Temmuz', 8: 'Ağustos',
#             9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
#         }
        
#         # Convert date to TURKISH format for better results
#         date_query = ""
#         if date_str:
#             if date_str.lower() in ['yarın', 'yarin', 'tomorrow']:
#                 tomorrow = datetime.now() + timedelta(days=1)
#                 month_tr = turkish_months[tomorrow.month]
#                 date_query = f"{tomorrow.day} {month_tr} {tomorrow.year}"
#             elif date_str.lower() in ['bugün', 'bugun', 'today']:
#                 today = datetime.now()
#                 month_tr = turkish_months[today.month]
#                 date_query = f"{today.day} {month_tr} {today.year}"
#             elif 'hafta sonu' in date_str.lower():
#                 date_query = "bu hafta sonu Cumartesi Pazar"
#             elif 'bu hafta' in date_str.lower():
#                 date_query = "bu hafta"
#             else:
#                 date_query = date_str
        
#         # Build specific query - ASK FOR PLAY NAMES EXPLICITLY
#         if date_query:
#             query = f"{city} tiyatro {date_query} oyun listesi seans"
#         else:
#             query = f"{city} tiyatro bu hafta oyun listesi gösterim"
        
#         print(f"🔍 Tavily searching: '{query}'")
        
#         try:
#             # ==================== SEARCH WITH AI ANSWER ====================
#             response = self.client.search(
#                 query=query,
#                 search_depth="advanced",
#                 max_results=max_results + 3,  # Get extra to filter
#                 include_domains=[
#                     "biletinial.com", 
#                     "biletix.com", 
#                     "passo.com.tr", 
#                     "tiyatrolar.com.tr", 
#                     "mobilet.com"
#                 ],
#                 exclude_domains=[
#                     "twitter.com",
#                     "facebook.com",
#                     "instagram.com"
#                 ],
#                 include_answer=True,  # Get AI-generated summary!
#                 include_raw_content=False
#             )
            
#             # ==================== EXTRACT AI ANSWER ====================
#             ai_answer = response.get('answer', '')
            
#             # ==================== PARSE RESULTS ====================
#             plays = self._parse_search_results_v2(response, city, date_str)
            
#             # ==================== EXTRACT PLAYS FROM AI ANSWER ====================
#             if ai_answer and len(plays) < 3:
#                 answer_plays = self._extract_plays_from_answer(ai_answer, city)
#                 # Add plays from answer that aren't already in list
#                 existing_titles = {p['title'].lower() for p in plays}
#                 for ap in answer_plays:
#                     if ap['title'].lower() not in existing_titles:
#                         plays.append(ap)
            
#             return {
#                 'success': True,
#                 'plays': plays[:max_results],
#                 'ai_summary': ai_answer,  # Include AI summary!
#                 'source_urls': [r.get('url') for r in response.get('results', [])[:3]],
#                 'query': query
#             }
            
#         except Exception as e:
#             print(f"❌ Tavily search error: {e}")
#             return {'success': False, 'error': str(e), 'plays': []}
    
#     def _parse_search_results_v2(self, response, city, date_str):
#         """
#         Parse Tavily results - IMPROVED VERSION
#         Filters out category pages, extracts actual play info
#         """
#         plays = []
#         seen_titles = set()
        
#         # Keywords that indicate a category/list page (NOT a specific play)
#         category_indicators = [
#             'tiyatro oyunları', 'biletleri', 'etkinlik takvimi', 
#             'istanbul avrupa', 'istanbul anadolu', 'ankara tiyatro',
#             'şehir tiyatroları', 'devlet tiyatroları', 'tüm oyunlar',
#             'kategori', 'filtrele', 'sırala'
#         ]
        
#         for result in response.get('results', []):
#             url = result.get('url', '')
#             title = result.get('title', '')
#             content = result.get('content', '')
            
#             # Skip category/list pages
#             title_lower = title.lower()
#             if any(cat in title_lower for cat in category_indicators):
#                 continue
            
#             # Skip if URL is a category page
#             if url.endswith('/tiyatro') or url.endswith('/tiyatro/'):
#                 continue
#             if '/istanbul-avrupa' in url or '/istanbul-anadolu' in url:
#                 continue
#             if '/etkinlik-takvimi/' in url and not re.search(r'/\d+$', url):
#                 continue
            
#             # Try to extract play info
#             play_info = self._extract_play_from_result(title, content, url, city)
            
#             if play_info and play_info['title'] not in seen_titles:
#                 # Additional validation: title should look like a play name
#                 if self._is_valid_play_title(play_info['title']):
#                     plays.append(play_info)
#                     seen_titles.add(play_info['title'])
        
#         return plays
    
#     def _is_valid_play_title(self, title):
#         """Check if a title looks like an actual play name"""
#         if not title or len(title) < 3:
#             return False
        
#         # Reject generic titles
#         generic_titles = [
#             'tiyatro oyunları', 'biletleri', 'etkinlik', 'takvim',
#             'istanbul', 'ankara', 'izmir', 'türkiye', 'sahne',
#             'biletinial', 'biletix', 'passo'
#         ]
        
#         title_lower = title.lower()
#         for generic in generic_titles:
#             if title_lower == generic or title_lower.startswith(generic + ' '):
#                 return False
        
#         # Should have at least one capital letter (play names are usually capitalized)
#         if not any(c.isupper() for c in title):
#             return False
        
#         return True
    
#     def _extract_play_from_result(self, title, content, url, city):
#         """Extract structured play info from a search result"""
        
#         # Clean title - remove common suffixes
#         clean_title = title
#         remove_suffixes = [
#             ' | biletinial', ' | Biletinial', ' - biletinial',
#             ' Tiyatro Biletleri', ' Tiyatro Oyunu', ' biletleri',
#             ' | tiyatrolar.com.tr', ' - Bilet', ' Bilet'
#         ]
#         for suffix in remove_suffixes:
#             if clean_title.endswith(suffix):
#                 clean_title = clean_title[:-len(suffix)]
#             clean_title = clean_title.replace(suffix, '')
        
#         clean_title = clean_title.strip()
        
#         if len(clean_title) < 3 or len(clean_title) > 80:
#             return None
        
#         # Extract venue from content
#         venue = self._extract_venue_v2(content, url)
        
#         # Extract dates from content
#         dates = self._extract_dates_v2(content)
        
#         return {
#             'title': clean_title,
#             'venue': venue or f"{city} - Web araması",
#             'city': city,
#             'showtimes': '; '.join(dates) if dates else None,
#             'ticket_url': url,
#             'source': 'tavily_web',
#             'description': content[:150] if content else None
#         }
    
#     def _extract_venue_v2(self, content, url):
#         """Extract venue name - improved version"""
#         if not content:
#             return None
        
#         # Common venue patterns
#         venue_patterns = [
#             r'([\w\s]+ Sahnesi)',
#             r'([\w\s]+ Salonu)',
#             r'([\w\s]+ Tiyatrosu)',
#             r'(Zorlu PSM[\w\s]*)',
#             r'(DasDas[\w\s]*)',
#             r'(Trump[\w\s]*Sahne)',
#             r'(AKM[\w\s]*)',
#             r'(Harbiye[\w\s]*)',
#             r'(Caddebostan KKM[\w\s]*)',
#             r'(Moda Sahnesi)',
#             r'(Pera[\w\s]*)',
#         ]
        
#         for pattern in venue_patterns:
#             match = re.search(pattern, content, re.IGNORECASE)
#             if match:
#                 venue = match.group(1).strip()
#                 if 10 < len(venue) < 60:
#                     return venue
        
#         return None
    
#     def _extract_dates_v2(self, content):
#         """Extract dates - improved version"""
#         if not content:
#             return []
        
#         dates = []
        
#         # Turkish months
#         months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
#                  'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
        
#         for month in months:
#             # Pattern: "15 Ocak 2025" or "15 Ocak Cumartesi 20:30"
#             patterns = [
#                 rf'(\d{{1,2}}\s+{month}\s+\d{{4}})',
#                 rf'(\d{{1,2}}\s+{month}\s+\w+\s+\d{{2}}:\d{{2}})',
#                 rf'(\d{{1,2}}\s+{month})'
#             ]
            
#             for pattern in patterns:
#                 matches = re.findall(pattern, content, re.IGNORECASE)
#                 dates.extend(matches[:2])
        
#         # Remove duplicates while preserving order
#         seen = set()
#         unique_dates = []
#         for d in dates:
#             if d not in seen:
#                 seen.add(d)
#                 unique_dates.append(d)
        
#         return unique_dates[:3]
    
#     def _extract_plays_from_answer(self, ai_answer, city):
#         """
#         Extract play names from Tavily's AI-generated answer
#         IMPROVED: Better cleaning and optional follow-up search
#         """
#         plays = []
        
#         if not ai_answer:
#             return plays
        
#         extracted_names = set()
        
#         # Method 1: Look for quoted names
#         patterns = [
#             r'"([^"]+)"',  # "Play Name"
#             r"'([^']+)'",  # 'Play Name'
#             r'„([^"]+)"',  # „Play Name"
#             r'«([^»]+)»',  # «Play Name»
#         ]
        
#         for pattern in patterns:
#             matches = re.findall(pattern, ai_answer)
#             for match in matches:
#                 # Clean the name
#                 clean_name = match.strip().strip(',').strip('.').strip()
#                 if 5 < len(clean_name) < 60 and self._is_valid_play_title(clean_name):
#                     extracted_names.add(clean_name)
        
#         # Method 2: Look for "X oyunu" or "X adlı oyun" patterns
#         oyun_patterns = [
#             r'([A-ZÇĞİÖŞÜ][^,."]+?)\s+oyunu',
#             r'([A-ZÇĞİÖŞÜ][^,."]+?)\s+adlı\s+oyun',
#             r'([A-ZÇĞİÖŞÜ][^,."]+?)\s+tiyatro\s+oyunu',
#         ]
        
#         for pattern in oyun_patterns:
#             matches = re.findall(pattern, ai_answer)
#             for match in matches:
#                 clean_name = match.strip().strip(',').strip('.').strip()
#                 if 5 < len(clean_name) < 60 and self._is_valid_play_title(clean_name):
#                     extracted_names.add(clean_name)
        
#         # Method 3: If answer contains a list with commas, try to parse it
#         # Pattern: "showing X, Y, Z, and W" or "X, Y, Z gibi oyunlar"
#         list_patterns = [
#             r'showing\s+(.+?)(?:\.|$)',
#             r'sahneleniyor[:\s]+(.+?)(?:\.|$)',
#             r'gösterimde[:\s]+(.+?)(?:\.|$)',
#             r'oyunları[:\s]+(.+?)(?:\.|$)',
#         ]
        
#         for pattern in list_patterns:
#             match = re.search(pattern, ai_answer, re.IGNORECASE)
#             if match:
#                 list_text = match.group(1)
#                 # Split by comma or "and"/"ve"
#                 items = re.split(r',\s*|\s+and\s+|\s+ve\s+', list_text)
#                 for item in items:
#                     clean_name = item.strip().strip('"').strip("'").strip(',').strip('.').strip()
#                     # Remove trailing punctuation
#                     clean_name = re.sub(r'[,.\s]+$', '', clean_name)
#                     if 5 < len(clean_name) < 60 and self._is_valid_play_title(clean_name):
#                         extracted_names.add(clean_name)
        
#         # Convert to play objects
#         for name in list(extracted_names)[:5]:  # Max 5
#             plays.append({
#                 'title': name,
#                 'venue': f"{city} Devlet Tiyatrosu",  # Better default
#                 'city': city,
#                 'showtimes': None,
#                 'ticket_url': None,
#                 'source': 'tavily_ai_answer',
#                 'description': None  # Don't repeat the AI summary for each
#             })
        
#         # ==================== FOLLOW-UP SEARCH FOR TICKET LINKS ====================
#         # If we found plays from AI answer, try to get their ticket links
#         if plays and self.client:
#             print(f"   🔍 Found {len(plays)} plays from AI, searching for ticket links...")
#             for play in plays[:3]:  # Only first 3 to save quota
#                 try:
#                     ticket_result = self._quick_ticket_search(play['title'], city)
#                     if ticket_result:
#                         play['ticket_url'] = ticket_result.get('url')
#                         play['venue'] = ticket_result.get('venue') or play['venue']
#                 except:
#                     pass
        
#         return plays
    
#     def _quick_ticket_search(self, play_name, city):
#         """Quick search to find ticket link for a play"""
#         try:
#             response = self.client.search(
#                 query=f'"{play_name}" bilet {city}',
#                 search_depth="basic",
#                 max_results=2,
#                 include_domains=["biletinial.com", "biletix.com", "passo.com.tr"],
#                 include_answer=False
#             )
            
#             for result in response.get('results', []):
#                 url = result.get('url', '')
#                 # Skip category pages
#                 if '/tiyatro/' in url and not url.endswith('/tiyatro/') and not url.endswith('/tiyatro'):
#                     venue = self._extract_venue_v2(result.get('content', ''), url)
#                     return {
#                         'url': url,
#                         'venue': venue
#                     }
#             return None
#         except:
#             return None
    
#     def search_specific_play(self, play_name: str, city: str):
#         """
#         Search for a specific play by name
#         Use this for enrichment or finding ticket links
#         """
#         if not self.client:
#             return {'success': False, 'error': 'Tavily not available'}
        
#         query = f'"{play_name}" tiyatro {city} bilet seans'
        
#         print(f"🔍 Searching for specific play: '{play_name}'")
        
#         try:
#             response = self.client.search(
#                 query=query,
#                 search_depth="basic",
#                 max_results=3,
#                 include_domains=["biletinial.com", "biletix.com", "passo.com.tr"],
#                 include_answer=True
#             )
            
#             # Find the best matching result
#             best_match = None
#             play_name_lower = play_name.lower()
            
#             for result in response.get('results', []):
#                 if play_name_lower in result.get('title', '').lower():
#                     best_match = result
#                     break
            
#             if not best_match and response.get('results'):
#                 best_match = response['results'][0]
            
#             if best_match:
#                 return {
#                     'success': True,
#                     'title': play_name,
#                     'ticket_url': best_match.get('url'),
#                     'venue': self._extract_venue_v2(best_match.get('content', ''), ''),
#                     'dates': self._extract_dates_v2(best_match.get('content', '')),
#                     'description': best_match.get('content', '')[:200],
#                     'ai_summary': response.get('answer', '')
#                 }
            
#             return {'success': False, 'error': 'Play not found'}
            
#         except Exception as e:
#             return {'success': False, 'error': str(e)}
    
#     def enrich_play(self, play_title: str, city: str = None):
#         """Enrich play information with web search"""
#         return self.search_specific_play(play_title, city or 'Istanbul')
    
#     def search_theater_news(self, city: str = None, max_results: int = 5):
#         """Get latest theater news"""
#         if not self.client:
#             return {'success': False, 'error': 'Tavily not available'}
        
#         query = "tiyatro haberleri güncel"
#         if city:
#             query = f"{city} {query}"
        
#         try:
#             response = self.client.search(
#                 query=query,
#                 search_depth="basic",
#                 max_results=max_results,
#                 include_answer=True
#             )
            
#             news = []
#             for result in response.get('results', []):
#                 news.append({
#                     'title': result.get('title'),
#                     'url': result.get('url'),
#                     'snippet': result.get('content', '')[:200],
#                 })
            
#             return {
#                 'success': True,
#                 'news': news,
#                 'summary': response.get('answer', '')
#             }
            
#         except Exception as e:
#             return {'success': False, 'error': str(e)}


# # ==================== DEMO ====================

# def demo():
#     """Demo the improved Tavily search agent"""
#     print("\n" + "="*70)
#     print("  🔍 TAVILY SEARCH AGENT v2.0 - IMPROVED")
#     print("="*70 + "\n")
    
#     agent = TavilySearchAgent()
    
#     if not agent.is_available():
#         print("❌ Tavily not available. Check your API key.")
#         return
    
#     # Test: Search for plays tomorrow in Istanbul
#     print("\n📍 Test: Searching for plays in Istanbul tomorrow...")
#     result = agent.search_plays("Istanbul", "yarın", max_results=5)
    
#     if result['success']:
#         print(f"\n✅ Found {len(result['plays'])} plays")
        
#         if result.get('ai_summary'):
#             print(f"\n🤖 AI Summary:\n{result['ai_summary'][:300]}...")
        
#         print("\n📋 Plays found:")
#         for i, play in enumerate(result['plays'], 1):
#             print(f"\n{i}. {play['title']}")
#             print(f"   📍 {play['venue']}")
#             if play.get('showtimes'):
#                 print(f"   📅 {play['showtimes']}")
#             if play.get('ticket_url'):
#                 print(f"   🎫 {play['ticket_url'][:50]}...")
#     else:
#         print(f"❌ Error: {result.get('error')}")
    
#     print("\n" + "="*70)


# if __name__ == "__main__":
#     demo()


# -------------------------4---------------------

# # src/tavily_agent.py
# """
# TavilySearchAgent v2.0 - IMPROVED Web Search for Theater Information
# Better query construction and result parsing

# Andrew Ng Pattern: Tool Use Agent with Reflection
# - Smarter search queries
# - Uses AI-generated answers
# - Filters out category pages
# - Two-phase search when needed
# """

# import os
# import re
# from datetime import datetime, timedelta
# from dotenv import load_dotenv

# load_dotenv()

# # Try to import tavily
# try:
#     from tavily import TavilyClient
#     TAVILY_AVAILABLE = True
# except ImportError:
#     TAVILY_AVAILABLE = False
#     print("⚠️  Tavily not installed. Run: pip install tavily-python")


# class TavilySearchAgent:
#     """
#     Web search agent for theater information - IMPROVED VERSION
    
#     Key improvements:
#     1. Better search queries (specific, not generic)
#     2. Uses Tavily's AI answer feature
#     3. Filters out category/list pages
#     4. Extracts actual play names from results
#     """
    
#     def __init__(self):
#         self.api_key = os.getenv("TAVILY_API_KEY")
#         self.client = None
        
#         if not self.api_key:
#             print("⚠️  TAVILY_API_KEY not found in .env")
#             return
        
#         if TAVILY_AVAILABLE:
#             try:
#                 self.client = TavilyClient(api_key=self.api_key)
#                 print("✅ Tavily Search Agent initialized!")
#             except Exception as e:
#                 print(f"⚠️  Tavily initialization failed: {e}")
#         else:
#             print("⚠️  Tavily library not available")
    
#     def is_available(self):
#         """Check if Tavily is ready to use"""
#         return self.client is not None
    
#     def search_plays(self, city: str, date_str: str = None, genre: str = None, max_results: int = 5):
#         """
#         Search for theater plays - IMPROVED VERSION
        
#         Strategy:
#         1. Build a specific query asking for actual play names
#         2. Use Tavily's AI answer for a summary
#         3. Parse results to extract real plays (not category pages)
#         """
#         if not self.client:
#             return {'success': False, 'error': 'Tavily not available', 'plays': []}
        
#         # ==================== BUILD SMART QUERY ====================
#         # Turkish month names for proper date formatting
#         turkish_months = {
#             1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan',
#             5: 'Mayıs', 6: 'Haziran', 7: 'Temmuz', 8: 'Ağustos',
#             9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
#         }
        
#         # Convert date to TURKISH format for better results
#         date_query = ""
#         if date_str:
#             if date_str.lower() in ['yarın', 'yarin', 'tomorrow']:
#                 tomorrow = datetime.now() + timedelta(days=1)
#                 month_tr = turkish_months[tomorrow.month]
#                 date_query = f"{tomorrow.day} {month_tr} {tomorrow.year}"
#             elif date_str.lower() in ['bugün', 'bugun', 'today']:
#                 today = datetime.now()
#                 month_tr = turkish_months[today.month]
#                 date_query = f"{today.day} {month_tr} {today.year}"
#             elif 'hafta sonu' in date_str.lower():
#                 date_query = "bu hafta sonu Cumartesi Pazar"
#             elif 'bu hafta' in date_str.lower():
#                 date_query = "bu hafta"
#             else:
#                 date_query = date_str
        
#         # Build specific query - ASK FOR PLAY NAMES EXPLICITLY
#         if date_query:
#             query = f"{city} tiyatro {date_query} oyun listesi seans"
#         else:
#             query = f"{city} tiyatro bu hafta oyun listesi gösterim"
        
#         print(f"🔍 Tavily searching: '{query}'")
        
#         try:
#             # ==================== SEARCH WITH AI ANSWER ====================
#             response = self.client.search(
#                 query=query,
#                 search_depth="advanced",
#                 max_results=max_results + 3,  # Get extra to filter
#                 include_domains=[
#                     "biletinial.com", 
#                     "biletix.com", 
#                     "passo.com.tr", 
#                     "tiyatrolar.com.tr", 
#                     "mobilet.com"
#                 ],
#                 exclude_domains=[
#                     "twitter.com",
#                     "facebook.com",
#                     "instagram.com"
#                 ],
#                 include_answer=True,  # Get AI-generated summary!
#                 include_raw_content=False
#             )
            
#             # ==================== EXTRACT AI ANSWER ====================
#             ai_answer = response.get('answer', '')
            
#             # ==================== PARSE RESULTS ====================
#             plays = self._parse_search_results_v2(response, city, date_str)
            
#             # ==================== EXTRACT PLAYS FROM AI ANSWER ====================
#             if ai_answer and len(plays) < 3:
#                 answer_plays = self._extract_plays_from_answer(ai_answer, city)
#                 # Add plays from answer that aren't already in list
#                 existing_titles = {p['title'].lower() for p in plays}
#                 for ap in answer_plays:
#                     if ap['title'].lower() not in existing_titles:
#                         plays.append(ap)
            
#             return {
#                 'success': True,
#                 'plays': plays[:max_results],
#                 'ai_summary': ai_answer,  # Include AI summary!
#                 'source_urls': [r.get('url') for r in response.get('results', [])[:3]],
#                 'query': query
#             }
            
#         except Exception as e:
#             print(f"❌ Tavily search error: {e}")
#             return {'success': False, 'error': str(e), 'plays': []}
    
#     def _parse_search_results_v2(self, response, city, date_str):
#         """
#         Parse Tavily results - IMPROVED VERSION
#         Filters out category pages, extracts actual play info
#         """
#         plays = []
#         seen_titles = set()
        
#         # Keywords that indicate a category/list page (NOT a specific play)
#         category_indicators = [
#             'tiyatro oyunları', 'biletleri', 'etkinlik takvimi', 
#             'istanbul avrupa', 'istanbul anadolu', 'ankara tiyatro',
#             'şehir tiyatroları', 'devlet tiyatroları', 'tüm oyunlar',
#             'kategori', 'filtrele', 'sırala', 'etkinlikleri',
#             'sahne', 'mekan', 'alan kadıköy', 'pax sahne',
#             'akm etkinlik', 'sehir tiyatro'
#         ]
        
#         # URL patterns that indicate category pages
#         category_url_patterns = [
#             r'/tiyatro/?$',
#             r'/tiyatro/istanbul',
#             r'/tiyatro/ankara',
#             r'/tiyatro/adana',
#             r'/etkinlikleri/',
#             r'/mekan/',
#             r'/sahne/',
#             r'/sehrineozel/',
#         ]
        
#         for result in response.get('results', []):
#             url = result.get('url', '')
#             title = result.get('title', '')
#             content = result.get('content', '')
            
#             # Skip category/list pages by title
#             title_lower = title.lower()
#             if any(cat in title_lower for cat in category_indicators):
#                 print(f"   ⏭️ Skipping category page: {title[:40]}...")
#                 continue
            
#             # Skip category pages by URL pattern
#             is_category_url = False
#             for pattern in category_url_patterns:
#                 if re.search(pattern, url):
#                     is_category_url = True
#                     break
            
#             if is_category_url:
#                 print(f"   ⏭️ Skipping category URL: {url[:50]}...")
#                 continue
            
#             # Try to extract play info
#             play_info = self._extract_play_from_result(title, content, url, city)
            
#             if play_info and play_info['title'] not in seen_titles:
#                 # Additional validation: title should look like a play name
#                 if self._is_valid_play_title(play_info['title']):
#                     plays.append(play_info)
#                     seen_titles.add(play_info['title'])
#                     print(f"   ✅ Valid play found: {play_info['title']}")
        
#         return plays
    
#     def _is_valid_play_title(self, title):
#         """Check if a title looks like an actual play name"""
#         if not title or len(title) < 3:
#             return False
        
#         # Reject generic titles
#         generic_titles = [
#             'tiyatro oyunları', 'biletleri', 'etkinlik', 'takvim',
#             'istanbul', 'ankara', 'izmir', 'türkiye', 'sahne',
#             'biletinial', 'biletix', 'passo'
#         ]
        
#         title_lower = title.lower()
#         for generic in generic_titles:
#             if title_lower == generic or title_lower.startswith(generic + ' '):
#                 return False
        
#         # Should have at least one capital letter (play names are usually capitalized)
#         if not any(c.isupper() for c in title):
#             return False
        
#         return True
    
#     def _extract_play_from_result(self, title, content, url, city):
#         """Extract structured play info from a search result"""
        
#         # Clean title - remove common suffixes
#         clean_title = title
#         remove_suffixes = [
#             ' | biletinial', ' | Biletinial', ' - biletinial',
#             ' Tiyatro Biletleri', ' Tiyatro Oyunu', ' biletleri',
#             ' | tiyatrolar.com.tr', ' - Bilet', ' Bilet'
#         ]
#         for suffix in remove_suffixes:
#             if clean_title.endswith(suffix):
#                 clean_title = clean_title[:-len(suffix)]
#             clean_title = clean_title.replace(suffix, '')
        
#         clean_title = clean_title.strip()
        
#         if len(clean_title) < 3 or len(clean_title) > 80:
#             return None
        
#         # Extract venue from content
#         venue = self._extract_venue_v2(content, url)
        
#         # Extract dates from content
#         dates = self._extract_dates_v2(content)
        
#         return {
#             'title': clean_title,
#             'venue': venue or f"{city} - Web araması",
#             'city': city,
#             'showtimes': '; '.join(dates) if dates else None,
#             'ticket_url': url,
#             'source': 'tavily_web',
#             'description': content[:150] if content else None
#         }
    
#     def _extract_venue_v2(self, content, url):
#         """Extract venue name - improved version"""
#         if not content:
#             return None
        
#         # Common venue patterns
#         venue_patterns = [
#             r'([\w\s]+ Sahnesi)',
#             r'([\w\s]+ Salonu)',
#             r'([\w\s]+ Tiyatrosu)',
#             r'(Zorlu PSM[\w\s]*)',
#             r'(DasDas[\w\s]*)',
#             r'(Trump[\w\s]*Sahne)',
#             r'(AKM[\w\s]*)',
#             r'(Harbiye[\w\s]*)',
#             r'(Caddebostan KKM[\w\s]*)',
#             r'(Moda Sahnesi)',
#             r'(Pera[\w\s]*)',
#         ]
        
#         for pattern in venue_patterns:
#             match = re.search(pattern, content, re.IGNORECASE)
#             if match:
#                 venue = match.group(1).strip()
#                 if 10 < len(venue) < 60:
#                     return venue
        
#         return None
    
#     def _extract_dates_v2(self, content):
#         """Extract dates - improved version"""
#         if not content:
#             return []
        
#         dates = []
        
#         # Turkish months
#         months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
#                  'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
        
#         for month in months:
#             # Pattern: "15 Ocak 2025" or "15 Ocak Cumartesi 20:30"
#             patterns = [
#                 rf'(\d{{1,2}}\s+{month}\s+\d{{4}})',
#                 rf'(\d{{1,2}}\s+{month}\s+\w+\s+\d{{2}}:\d{{2}})',
#                 rf'(\d{{1,2}}\s+{month})'
#             ]
            
#             for pattern in patterns:
#                 matches = re.findall(pattern, content, re.IGNORECASE)
#                 dates.extend(matches[:2])
        
#         # Remove duplicates while preserving order
#         seen = set()
#         unique_dates = []
#         for d in dates:
#             if d not in seen:
#                 seen.add(d)
#                 unique_dates.append(d)
        
#         return unique_dates[:3]
    
#     def _extract_plays_from_answer(self, ai_answer, city):
#         """
#         Extract play names from Tavily's AI-generated answer
#         IMPROVED: Better extraction for English AI responses
#         """
#         plays = []
        
#         if not ai_answer:
#             return plays
        
#         extracted_names = set()
        
#         # Method 1: Look for quoted names (various quote styles)
#         quote_patterns = [
#             r'"([^"]+)"',      # "Play Name"
#             r'"([^"]+)"',      # "Play Name" (curly quotes)
#             r"'([^']+)'",      # 'Play Name'
#             r'„([^"]+)"',      # „Play Name"
#             r'«([^»]+)»',      # «Play Name»
#         ]
        
#         for pattern in quote_patterns:
#             matches = re.findall(pattern, ai_answer)
#             for match in matches:
#                 # Clean the name
#                 clean_name = match.strip().strip(',').strip('.').strip()
#                 # Filter out non-play words
#                 skip_words = ['in istanbul', 'december', 'january', 'schedule', 'list', 'available']
#                 if any(sw in clean_name.lower() for sw in skip_words):
#                     continue
#                 if 3 < len(clean_name) < 60:
#                     extracted_names.add(clean_name)
#                     print(f"   📌 Found from quotes: {clean_name}")
        
#         # Method 2: Look for Turkish play name patterns
#         # Pattern: "X oyunu" or "X adlı oyun"
#         oyun_patterns = [
#             r'([A-ZÇĞİÖŞÜ][a-zçğıöşü\']+(?:\s+[A-ZÇĞİÖŞÜa-zçğıöşü\']+)*)\s+oyunu',
#             r'([A-ZÇĞİÖŞÜ][^\s,."]+(?:\s+[^\s,."]+){0,4})\s+adlı',
#         ]
        
#         for pattern in oyun_patterns:
#             matches = re.findall(pattern, ai_answer)
#             for match in matches:
#                 clean_name = match.strip().strip(',').strip('.').strip()
#                 if 3 < len(clean_name) < 60:
#                     extracted_names.add(clean_name)
#                     print(f"   📌 Found from pattern: {clean_name}")
        
#         # Method 3: Parse "includes X and Y" or "showing X, Y, Z" patterns
#         include_patterns = [
#             r'(?:includes?|showing|sahneleniyor|gösterimde)[:\s]+["\']?([^"\']+)["\']?',
#             r'(?:shows include|oyunlar)[:\s]+(.+?)(?:\.|The|$)',
#         ]
        
#         for pattern in include_patterns:
#             match = re.search(pattern, ai_answer, re.IGNORECASE)
#             if match:
#                 list_text = match.group(1)
#                 # Split by common separators
#                 items = re.split(r'[,;]|\s+and\s+|\s+ve\s+', list_text)
#                 for item in items:
#                     # Clean each item
#                     clean_name = item.strip().strip('"').strip("'").strip(',').strip('.').strip()
#                     clean_name = re.sub(r'^["\']+|["\']+$', '', clean_name)
#                     # Skip location/date words
#                     skip_words = ['istanbul', 'ankara', 'december', 'january', 'the', 'schedule']
#                     if any(sw in clean_name.lower() for sw in skip_words):
#                         continue
#                     if 3 < len(clean_name) < 60 and not clean_name.lower().startswith('the '):
#                         extracted_names.add(clean_name)
#                         print(f"   📌 Found from list: {clean_name}")
        
#         # Method 4: Look for capitalized multi-word phrases (likely play names)
#         # Pattern: Two or more capitalized words together
#         title_pattern = r'\b([A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\'[a-zçğıöşü]+)?(?:\s+[A-ZÇĞİÖŞÜa-zçğıöşü]+){1,4})\b'
#         potential_titles = re.findall(title_pattern, ai_answer)
        
#         # Known play name indicators
#         play_indicators = ['Hamlet', 'Gidion', 'Düğümü', 'Kubbe', 'Bernarda', 'Alba']
        
#         for title in potential_titles:
#             clean_name = title.strip()
#             # Check if it contains a known play indicator
#             if any(indicator in clean_name for indicator in play_indicators):
#                 if 3 < len(clean_name) < 60:
#                     extracted_names.add(clean_name)
#                     print(f"   📌 Found known play: {clean_name}")
        
#         print(f"   ✅ Total unique plays extracted: {len(extracted_names)}")
        
#         # Convert to play objects
#         for name in list(extracted_names)[:5]:  # Max 5
#             plays.append({
#                 'title': name,
#                 'venue': f"{city} Tiyatroları",
#                 'city': city,
#                 'showtimes': None,
#                 'ticket_url': None,
#                 'source': 'tavily_ai_answer',
#                 'description': None
#             })
        
#         # ==================== FOLLOW-UP SEARCH FOR TICKET LINKS ====================
#         if plays and self.client:
#             print(f"   🔍 Searching ticket links for {len(plays)} plays...")
#             for play in plays[:3]:
#                 try:
#                     ticket_result = self._quick_ticket_search(play['title'], city)
#                     if ticket_result:
#                         play['ticket_url'] = ticket_result.get('url')
#                         if ticket_result.get('venue'):
#                             play['venue'] = ticket_result.get('venue')
#                         print(f"      ✓ Found ticket for: {play['title']}")
#                 except Exception as e:
#                     print(f"      ✗ Ticket search failed: {e}")
        
#         return plays
    
#     def _quick_ticket_search(self, play_name, city):
#         """Quick search to find ticket link for a play"""
#         try:
#             response = self.client.search(
#                 query=f'"{play_name}" bilet {city}',
#                 search_depth="basic",
#                 max_results=2,
#                 include_domains=["biletinial.com", "biletix.com", "passo.com.tr"],
#                 include_answer=False
#             )
            
#             for result in response.get('results', []):
#                 url = result.get('url', '')
#                 # Skip category pages
#                 if '/tiyatro/' in url and not url.endswith('/tiyatro/') and not url.endswith('/tiyatro'):
#                     venue = self._extract_venue_v2(result.get('content', ''), url)
#                     return {
#                         'url': url,
#                         'venue': venue
#                     }
#             return None
#         except:
#             return None
    
#     def search_specific_play(self, play_name: str, city: str):
#         """
#         Search for a specific play by name
#         Use this for enrichment or finding ticket links
#         """
#         if not self.client:
#             return {'success': False, 'error': 'Tavily not available'}
        
#         query = f'"{play_name}" tiyatro {city} bilet seans'
        
#         print(f"🔍 Searching for specific play: '{play_name}'")
        
#         try:
#             response = self.client.search(
#                 query=query,
#                 search_depth="basic",
#                 max_results=3,
#                 include_domains=["biletinial.com", "biletix.com", "passo.com.tr"],
#                 include_answer=True
#             )
            
#             # Find the best matching result
#             best_match = None
#             play_name_lower = play_name.lower()
            
#             for result in response.get('results', []):
#                 if play_name_lower in result.get('title', '').lower():
#                     best_match = result
#                     break
            
#             if not best_match and response.get('results'):
#                 best_match = response['results'][0]
            
#             if best_match:
#                 return {
#                     'success': True,
#                     'title': play_name,
#                     'ticket_url': best_match.get('url'),
#                     'venue': self._extract_venue_v2(best_match.get('content', ''), ''),
#                     'dates': self._extract_dates_v2(best_match.get('content', '')),
#                     'description': best_match.get('content', '')[:200],
#                     'ai_summary': response.get('answer', '')
#                 }
            
#             return {'success': False, 'error': 'Play not found'}
            
#         except Exception as e:
#             return {'success': False, 'error': str(e)}
    
#     def enrich_play(self, play_title: str, city: str = None):
#         """Enrich play information with web search"""
#         return self.search_specific_play(play_title, city or 'Istanbul')
    
#     def search_theater_news(self, city: str = None, max_results: int = 5):
#         """Get latest theater news"""
#         if not self.client:
#             return {'success': False, 'error': 'Tavily not available'}
        
#         query = "tiyatro haberleri güncel"
#         if city:
#             query = f"{city} {query}"
        
#         try:
#             response = self.client.search(
#                 query=query,
#                 search_depth="basic",
#                 max_results=max_results,
#                 include_answer=True
#             )
            
#             news = []
#             for result in response.get('results', []):
#                 news.append({
#                     'title': result.get('title'),
#                     'url': result.get('url'),
#                     'snippet': result.get('content', '')[:200],
#                 })
            
#             return {
#                 'success': True,
#                 'news': news,
#                 'summary': response.get('answer', '')
#             }
            
#         except Exception as e:
#             return {'success': False, 'error': str(e)}


# # ==================== DEMO ====================

# def demo():
#     """Demo the improved Tavily search agent"""
#     print("\n" + "="*70)
#     print("  🔍 TAVILY SEARCH AGENT v2.0 - IMPROVED")
#     print("="*70 + "\n")
    
#     agent = TavilySearchAgent()
    
#     if not agent.is_available():
#         print("❌ Tavily not available. Check your API key.")
#         return
    
#     # Test: Search for plays tomorrow in Istanbul
#     print("\n📍 Test: Searching for plays in Istanbul tomorrow...")
#     result = agent.search_plays("Istanbul", "yarın", max_results=5)
    
#     if result['success']:
#         print(f"\n✅ Found {len(result['plays'])} plays")
        
#         if result.get('ai_summary'):
#             print(f"\n🤖 AI Summary:\n{result['ai_summary'][:300]}...")
        
#         print("\n📋 Plays found:")
#         for i, play in enumerate(result['plays'], 1):
#             print(f"\n{i}. {play['title']}")
#             print(f"   📍 {play['venue']}")
#             if play.get('showtimes'):
#                 print(f"   📅 {play['showtimes']}")
#             if play.get('ticket_url'):
#                 print(f"   🎫 {play['ticket_url'][:50]}...")
#     else:
#         print(f"❌ Error: {result.get('error')}")
    
#     print("\n" + "="*70)


# if __name__ == "__main__":
#     demo()



# -------------------------5---------------------

# # src/tavily_agent.py
# """
# TavilySearchAgent v2.0 - IMPROVED Web Search for Theater Information
# Better query construction and result parsing

# Andrew Ng Pattern: Tool Use Agent with Reflection
# - Smarter search queries
# - Uses AI-generated answers
# - Filters out category pages
# - Two-phase search when needed
# """

# import os
# import re
# from datetime import datetime, timedelta
# from dotenv import load_dotenv

# load_dotenv()

# # Try to import tavily
# try:
#     from tavily import TavilyClient
#     TAVILY_AVAILABLE = True
# except ImportError:
#     TAVILY_AVAILABLE = False
#     print("⚠️  Tavily not installed. Run: pip install tavily-python")


# class TavilySearchAgent:
#     """
#     Web search agent for theater information - IMPROVED VERSION
    
#     Key improvements:
#     1. Better search queries (specific, not generic)
#     2. Uses Tavily's AI answer feature
#     3. Filters out category/list pages
#     4. Extracts actual play names from results
#     """
    
#     def __init__(self):
#         self.api_key = os.getenv("TAVILY_API_KEY")
#         self.client = None
        
#         if not self.api_key:
#             print("⚠️  TAVILY_API_KEY not found in .env")
#             return
        
#         if TAVILY_AVAILABLE:
#             try:
#                 self.client = TavilyClient(api_key=self.api_key)
#                 print("✅ Tavily Search Agent initialized!")
#             except Exception as e:
#                 print(f"⚠️  Tavily initialization failed: {e}")
#         else:
#             print("⚠️  Tavily library not available")
    
#     def is_available(self):
#         """Check if Tavily is ready to use"""
#         return self.client is not None
    
#     def search_plays(self, city: str, date_str: str = None, genre: str = None, max_results: int = 5):
#         """
#         Search for theater plays - IMPROVED VERSION
        
#         Strategy:
#         1. Build a specific query asking for actual play names
#         2. Use Tavily's AI answer for a summary
#         3. Parse results to extract real plays (not category pages)
#         """
#         if not self.client:
#             return {'success': False, 'error': 'Tavily not available', 'plays': []}
        
#         # ==================== BUILD SMART QUERY ====================
#         # Turkish month names for proper date formatting
#         turkish_months = {
#             1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan',
#             5: 'Mayıs', 6: 'Haziran', 7: 'Temmuz', 8: 'Ağustos',
#             9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
#         }
        
#         # Convert date to TURKISH format for better results
#         date_query = ""
#         if date_str:
#             date_lower = date_str.lower()
#             if date_lower in ['yarın', 'yarin', 'tomorrow']:
#                 tomorrow = datetime.now() + timedelta(days=1)
#                 month_tr = turkish_months[tomorrow.month]
#                 date_query = f"{tomorrow.day} {month_tr} {tomorrow.year}"
#             elif date_lower in ['bugün', 'bugun', 'today']:
#                 today = datetime.now()
#                 month_tr = turkish_months[today.month]
#                 date_query = f"{today.day} {month_tr} {today.year}"
#             elif 'hafta sonu' in date_lower:
#                 date_query = "bu hafta sonu Cumartesi Pazar"
#             elif 'önümüzdeki hafta' in date_lower or 'gelecek hafta' in date_lower:
#                 # Next week calculation
#                 next_week = datetime.now() + timedelta(days=7)
#                 month_tr = turkish_months[next_week.month]
#                 date_query = f"{next_week.day} {month_tr} haftası"
#             elif 'bu hafta' in date_lower:
#                 date_query = "bu hafta"
#             else:
#                 date_query = date_str
        
#         # Build specific query - ASK FOR PLAY NAMES EXPLICITLY
#         if date_query:
#             query = f"{city} tiyatro {date_query} oyun listesi seans"
#         else:
#             query = f"{city} tiyatro bu hafta oyun listesi gösterim"
        
#         print(f"🔍 Tavily searching: '{query}'")
        
#         try:
#             # ==================== SEARCH WITH AI ANSWER ====================
#             response = self.client.search(
#                 query=query,
#                 search_depth="advanced",
#                 max_results=max_results + 3,  # Get extra to filter
#                 include_domains=[
#                     "biletinial.com", 
#                     "biletix.com", 
#                     "passo.com.tr", 
#                     "tiyatrolar.com.tr", 
#                     "mobilet.com"
#                 ],
#                 exclude_domains=[
#                     "twitter.com",
#                     "facebook.com",
#                     "instagram.com"
#                 ],
#                 include_answer=True,  # Get AI-generated summary!
#                 include_raw_content=False
#             )
            
#             # ==================== EXTRACT AI ANSWER ====================
#             ai_answer = response.get('answer', '')
            
#             # ==================== PARSE RESULTS ====================
#             plays = self._parse_search_results_v2(response, city, date_str)
            
#             # ==================== EXTRACT PLAYS FROM AI ANSWER ====================
#             if ai_answer and len(plays) < 3:
#                 answer_plays = self._extract_plays_from_answer(ai_answer, city)
#                 # Add plays from answer that aren't already in list
#                 existing_titles = {p['title'].lower() for p in plays}
#                 for ap in answer_plays:
#                     if ap['title'].lower() not in existing_titles:
#                         plays.append(ap)
            
#             return {
#                 'success': True,
#                 'plays': plays[:max_results],
#                 'ai_summary': ai_answer,  # Include AI summary!
#                 'source_urls': [r.get('url') for r in response.get('results', [])[:3]],
#                 'query': query
#             }
            
#         except Exception as e:
#             print(f"❌ Tavily search error: {e}")
#             return {'success': False, 'error': str(e), 'plays': []}
    
#     def _parse_search_results_v2(self, response, city, date_str):
#         """
#         Parse Tavily results - IMPROVED VERSION
#         Filters out category pages, extracts actual play info
#         """
#         plays = []
#         seen_titles = set()
        
#         # Keywords that indicate a category/list page (NOT a specific play)
#         category_indicators = [
#             'tiyatro oyunları', 'biletleri', 'etkinlik takvimi', 
#             'istanbul avrupa', 'istanbul anadolu', 'ankara tiyatro',
#             'şehir tiyatroları', 'devlet tiyatroları', 'tüm oyunlar',
#             'kategori', 'filtrele', 'sırala', 'etkinlikleri',
#             'sahne', 'mekan', 'alan kadıköy', 'pax sahne',
#             'akm etkinlik', 'sehir tiyatro'
#         ]
        
#         # URL patterns that indicate category pages
#         category_url_patterns = [
#             r'/tiyatro/?$',
#             r'/tiyatro/istanbul',
#             r'/tiyatro/ankara',
#             r'/tiyatro/adana',
#             r'/etkinlikleri/',
#             r'/mekan/',
#             r'/sahne/',
#             r'/sehrineozel/',
#         ]
        
#         for result in response.get('results', []):
#             url = result.get('url', '')
#             title = result.get('title', '')
#             content = result.get('content', '')
            
#             # Skip category/list pages by title
#             title_lower = title.lower()
#             if any(cat in title_lower for cat in category_indicators):
#                 print(f"   ⏭️ Skipping category page: {title[:40]}...")
#                 continue
            
#             # Skip category pages by URL pattern
#             is_category_url = False
#             for pattern in category_url_patterns:
#                 if re.search(pattern, url):
#                     is_category_url = True
#                     break
            
#             if is_category_url:
#                 print(f"   ⏭️ Skipping category URL: {url[:50]}...")
#                 continue
            
#             # Try to extract play info
#             play_info = self._extract_play_from_result(title, content, url, city)
            
#             if play_info and play_info['title'] not in seen_titles:
#                 # Additional validation: title should look like a play name
#                 if self._is_valid_play_title(play_info['title']):
#                     plays.append(play_info)
#                     seen_titles.add(play_info['title'])
#                     print(f"   ✅ Valid play found: {play_info['title']}")
        
#         return plays
    
#     def _is_valid_play_title(self, title):
#         """Check if a title looks like an actual play name"""
#         if not title or len(title) < 3:
#             return False
        
#         # Reject generic/invalid titles
#         invalid_titles = [
#             'tiyatro oyunları', 'biletleri', 'etkinlik', 'takvim',
#             'istanbul', 'ankara', 'izmir', 'adana', 'türkiye', 'sahne',
#             'biletinial', 'biletix', 'passo', 'mobilet',
#             'gelecek program', 'pek yakında', 'coming soon',
#             'etkinlikleri', 'konser', 'festival', 'mekan',
#             'şehir tiyatroları', 'devlet tiyatroları',
#             'tüm oyunlar', 'tümü', 'tüm etkinlikler'
#         ]
        
#         title_lower = title.lower()
#         for invalid in invalid_titles:
#             if title_lower == invalid or title_lower.startswith(invalid + ' '):
#                 return False
#             # Also check if title IS the invalid word
#             if invalid == title_lower:
#                 return False
        
#         # Reject if title is just a city name
#         cities = ['istanbul', 'ankara', 'izmir', 'adana', 'bursa', 'antalya']
#         if title_lower in cities:
#             return False
        
#         # Reject if too generic (single common word)
#         generic_words = ['program', 'liste', 'takvim', 'bilet', 'sahne', 'salon']
#         if title_lower in generic_words:
#             return False
        
#         # Should have at least one capital letter (play names are usually capitalized)
#         if not any(c.isupper() for c in title):
#             return False
        
#         return True
    
#     def _extract_play_from_result(self, title, content, url, city):
#         """Extract structured play info from a search result"""
        
#         # Clean title - remove common suffixes
#         clean_title = title
#         remove_suffixes = [
#             ' | biletinial', ' | Biletinial', ' - biletinial',
#             ' Tiyatro Biletleri', ' Tiyatro Oyunu', ' biletleri',
#             ' | tiyatrolar.com.tr', ' - Bilet', ' Bilet'
#         ]
#         for suffix in remove_suffixes:
#             if clean_title.endswith(suffix):
#                 clean_title = clean_title[:-len(suffix)]
#             clean_title = clean_title.replace(suffix, '')
        
#         clean_title = clean_title.strip()
        
#         if len(clean_title) < 3 or len(clean_title) > 80:
#             return None
        
#         # Extract venue from content
#         venue = self._extract_venue_v2(content, url)
        
#         # Extract dates from content
#         dates = self._extract_dates_v2(content)
        
#         return {
#             'title': clean_title,
#             'venue': venue or f"{city} - Web araması",
#             'city': city,
#             'showtimes': '; '.join(dates) if dates else None,
#             'ticket_url': url,
#             'source': 'tavily_web',
#             'description': content[:150] if content else None
#         }
    
#     def _extract_venue_v2(self, content, url):
#         """Extract venue name - improved version"""
#         if not content:
#             return None
        
#         # Common venue patterns
#         venue_patterns = [
#             r'([\w\s]+ Sahnesi)',
#             r'([\w\s]+ Salonu)',
#             r'([\w\s]+ Tiyatrosu)',
#             r'(Zorlu PSM[\w\s]*)',
#             r'(DasDas[\w\s]*)',
#             r'(Trump[\w\s]*Sahne)',
#             r'(AKM[\w\s]*)',
#             r'(Harbiye[\w\s]*)',
#             r'(Caddebostan KKM[\w\s]*)',
#             r'(Moda Sahnesi)',
#             r'(Pera[\w\s]*)',
#         ]
        
#         for pattern in venue_patterns:
#             match = re.search(pattern, content, re.IGNORECASE)
#             if match:
#                 venue = match.group(1).strip()
#                 if 10 < len(venue) < 60:
#                     return venue
        
#         return None
    
#     def _extract_dates_v2(self, content):
#         """Extract dates - improved version"""
#         if not content:
#             return []
        
#         dates = []
        
#         # Turkish months
#         months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
#                  'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
        
#         for month in months:
#             # Pattern: "15 Ocak 2025" or "15 Ocak Cumartesi 20:30"
#             patterns = [
#                 rf'(\d{{1,2}}\s+{month}\s+\d{{4}})',
#                 rf'(\d{{1,2}}\s+{month}\s+\w+\s+\d{{2}}:\d{{2}})',
#                 rf'(\d{{1,2}}\s+{month})'
#             ]
            
#             for pattern in patterns:
#                 matches = re.findall(pattern, content, re.IGNORECASE)
#                 dates.extend(matches[:2])
        
#         # Remove duplicates while preserving order
#         seen = set()
#         unique_dates = []
#         for d in dates:
#             if d not in seen:
#                 seen.add(d)
#                 unique_dates.append(d)
        
#         return unique_dates[:3]
    
#     def _extract_plays_from_answer(self, ai_answer, city):
#         """
#         Extract play names from Tavily's AI-generated answer
#         IMPROVED: Better extraction for English AI responses
#         """
#         plays = []
        
#         if not ai_answer:
#             return plays
        
#         extracted_names = set()
        
#         # Method 1: Look for quoted names (various quote styles)
#         quote_patterns = [
#             r'"([^"]+)"',      # "Play Name"
#             r'"([^"]+)"',      # "Play Name" (curly quotes)
#             r"'([^']+)'",      # 'Play Name'
#             r'„([^"]+)"',      # „Play Name"
#             r'«([^»]+)»',      # «Play Name»
#         ]
        
#         for pattern in quote_patterns:
#             matches = re.findall(pattern, ai_answer)
#             for match in matches:
#                 # Clean the name
#                 clean_name = match.strip().strip(',').strip('.').strip()
#                 # Filter out non-play words
#                 skip_words = ['in istanbul', 'december', 'january', 'schedule', 'list', 'available']
#                 if any(sw in clean_name.lower() for sw in skip_words):
#                     continue
#                 if 3 < len(clean_name) < 60:
#                     extracted_names.add(clean_name)
#                     print(f"   📌 Found from quotes: {clean_name}")
        
#         # Method 2: Look for Turkish play name patterns
#         # Pattern: "X oyunu" or "X adlı oyun"
#         oyun_patterns = [
#             r'([A-ZÇĞİÖŞÜ][a-zçğıöşü\']+(?:\s+[A-ZÇĞİÖŞÜa-zçğıöşü\']+)*)\s+oyunu',
#             r'([A-ZÇĞİÖŞÜ][^\s,."]+(?:\s+[^\s,."]+){0,4})\s+adlı',
#         ]
        
#         for pattern in oyun_patterns:
#             matches = re.findall(pattern, ai_answer)
#             for match in matches:
#                 clean_name = match.strip().strip(',').strip('.').strip()
#                 if 3 < len(clean_name) < 60:
#                     extracted_names.add(clean_name)
#                     print(f"   📌 Found from pattern: {clean_name}")
        
#         # Method 3: Parse "includes X and Y" or "showing X, Y, Z" patterns
#         include_patterns = [
#             r'(?:includes?|showing|sahneleniyor|gösterimde)[:\s]+["\']?([^"\']+)["\']?',
#             r'(?:shows include|oyunlar)[:\s]+(.+?)(?:\.|The|$)',
#         ]
        
#         for pattern in include_patterns:
#             match = re.search(pattern, ai_answer, re.IGNORECASE)
#             if match:
#                 list_text = match.group(1)
#                 # Split by common separators
#                 items = re.split(r'[,;]|\s+and\s+|\s+ve\s+', list_text)
#                 for item in items:
#                     # Clean each item
#                     clean_name = item.strip().strip('"').strip("'").strip(',').strip('.').strip()
#                     clean_name = re.sub(r'^["\']+|["\']+$', '', clean_name)
#                     # Skip location/date words
#                     skip_words = ['istanbul', 'ankara', 'december', 'january', 'the', 'schedule']
#                     if any(sw in clean_name.lower() for sw in skip_words):
#                         continue
#                     if 3 < len(clean_name) < 60 and not clean_name.lower().startswith('the '):
#                         extracted_names.add(clean_name)
#                         print(f"   📌 Found from list: {clean_name}")
        
#         # Method 4: Look for capitalized multi-word phrases (likely play names)
#         # Pattern: Two or more capitalized words together
#         title_pattern = r'\b([A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\'[a-zçğıöşü]+)?(?:\s+[A-ZÇĞİÖŞÜa-zçğıöşü]+){1,4})\b'
#         potential_titles = re.findall(title_pattern, ai_answer)
        
#         # Known play name indicators
#         play_indicators = ['Hamlet', 'Gidion', 'Düğümü', 'Kubbe', 'Bernarda', 'Alba']
        
#         for title in potential_titles:
#             clean_name = title.strip()
#             # Check if it contains a known play indicator
#             if any(indicator in clean_name for indicator in play_indicators):
#                 if 3 < len(clean_name) < 60:
#                     extracted_names.add(clean_name)
#                     print(f"   📌 Found known play: {clean_name}")
        
#         print(f"   ✅ Total unique plays extracted: {len(extracted_names)}")
        
#         # Convert to play objects
#         for name in list(extracted_names)[:5]:  # Max 5
#             plays.append({
#                 'title': name,
#                 'venue': f"{city} Tiyatroları",
#                 'city': city,
#                 'showtimes': None,
#                 'ticket_url': None,
#                 'source': 'tavily_ai_answer',
#                 'description': None
#             })
        
#         # ==================== FOLLOW-UP SEARCH FOR TICKET LINKS ====================
#         if plays and self.client:
#             print(f"   🔍 Searching ticket links for {len(plays)} plays...")
#             for play in plays[:3]:
#                 try:
#                     ticket_result = self._quick_ticket_search(play['title'], city)
#                     if ticket_result:
#                         play['ticket_url'] = ticket_result.get('url')
#                         if ticket_result.get('venue'):
#                             play['venue'] = ticket_result.get('venue')
#                         print(f"      ✓ Found ticket for: {play['title']}")
#                 except Exception as e:
#                     print(f"      ✗ Ticket search failed: {e}")
        
#         return plays
    
#     def _quick_ticket_search(self, play_name, city):
#         """Quick search to find ticket link for a play"""
#         try:
#             response = self.client.search(
#                 query=f'"{play_name}" bilet {city}',
#                 search_depth="basic",
#                 max_results=2,
#                 include_domains=["biletinial.com", "biletix.com", "passo.com.tr"],
#                 include_answer=False
#             )
            
#             for result in response.get('results', []):
#                 url = result.get('url', '')
#                 # Skip category pages
#                 if '/tiyatro/' in url and not url.endswith('/tiyatro/') and not url.endswith('/tiyatro'):
#                     venue = self._extract_venue_v2(result.get('content', ''), url)
#                     return {
#                         'url': url,
#                         'venue': venue
#                     }
#             return None
#         except:
#             return None
    
#     def search_specific_play(self, play_name: str, city: str):
#         """
#         Search for a specific play by name
#         Use this for enrichment or finding ticket links
#         """
#         if not self.client:
#             return {'success': False, 'error': 'Tavily not available'}
        
#         query = f'"{play_name}" tiyatro {city} bilet seans'
        
#         print(f"🔍 Searching for specific play: '{play_name}'")
        
#         try:
#             response = self.client.search(
#                 query=query,
#                 search_depth="basic",
#                 max_results=3,
#                 include_domains=["biletinial.com", "biletix.com", "passo.com.tr"],
#                 include_answer=True
#             )
            
#             # Find the best matching result
#             best_match = None
#             play_name_lower = play_name.lower()
            
#             for result in response.get('results', []):
#                 if play_name_lower in result.get('title', '').lower():
#                     best_match = result
#                     break
            
#             if not best_match and response.get('results'):
#                 best_match = response['results'][0]
            
#             if best_match:
#                 return {
#                     'success': True,
#                     'title': play_name,
#                     'ticket_url': best_match.get('url'),
#                     'venue': self._extract_venue_v2(best_match.get('content', ''), ''),
#                     'dates': self._extract_dates_v2(best_match.get('content', '')),
#                     'description': best_match.get('content', '')[:200],
#                     'ai_summary': response.get('answer', '')
#                 }
            
#             return {'success': False, 'error': 'Play not found'}
            
#         except Exception as e:
#             return {'success': False, 'error': str(e)}
    
#     def enrich_play(self, play_title: str, city: str = None):
#         """Enrich play information with web search"""
#         return self.search_specific_play(play_title, city or 'Istanbul')
    
#     def search_theater_news(self, city: str = None, max_results: int = 5):
#         """Get latest theater news"""
#         if not self.client:
#             return {'success': False, 'error': 'Tavily not available'}
        
#         query = "tiyatro haberleri güncel"
#         if city:
#             query = f"{city} {query}"
        
#         try:
#             response = self.client.search(
#                 query=query,
#                 search_depth="basic",
#                 max_results=max_results,
#                 include_answer=True
#             )
            
#             news = []
#             for result in response.get('results', []):
#                 news.append({
#                     'title': result.get('title'),
#                     'url': result.get('url'),
#                     'snippet': result.get('content', '')[:200],
#                 })
            
#             return {
#                 'success': True,
#                 'news': news,
#                 'summary': response.get('answer', '')
#             }
            
#         except Exception as e:
#             return {'success': False, 'error': str(e)}
    
#     def search_play_interviews(self, play_name: str, max_results: int = 3):
#         """
#         Search for YouTube interviews and videos about a specific play
#         Returns video links with titles
#         """
#         if not self.client:
#             return {'success': False, 'error': 'Tavily not available', 'videos': []}
        
#         # Search for interviews on YouTube
#         query = f'"{play_name}" tiyatro röportaj youtube'
        
#         print(f"   🎬 Searching YouTube for: {play_name}")
        
#         try:
#             response = self.client.search(
#                 query=query,
#                 search_depth="basic",
#                 max_results=max_results + 2,
#                 include_domains=["youtube.com", "youtu.be"],
#                 include_answer=False
#             )
            
#             videos = []
#             seen_urls = set()
            
#             for result in response.get('results', []):
#                 url = result.get('url', '')
#                 title = result.get('title', '')
                
#                 # Only YouTube links
#                 if 'youtube.com' not in url and 'youtu.be' not in url:
#                     continue
                
#                 # Skip duplicates
#                 if url in seen_urls:
#                     continue
#                 seen_urls.add(url)
                
#                 # Clean title
#                 clean_title = title.replace(' - YouTube', '').strip()
                
#                 videos.append({
#                     'title': clean_title,
#                     'url': url,
#                     'platform': 'YouTube'
#                 })
                
#                 if len(videos) >= max_results:
#                     break
            
#             print(f"   🎬 Found {len(videos)} videos")
            
#             return {
#                 'success': True,
#                 'videos': videos,
#                 'play_name': play_name
#             }
            
#         except Exception as e:
#             print(f"   ❌ Video search error: {e}")
#             return {'success': False, 'error': str(e), 'videos': []}
    
#     def search_play_with_videos(self, city: str, date_str: str = None, genre: str = None, max_results: int = 5):
#         """
#         Search for plays AND their related YouTube videos
#         Combines play search with video search for top results
#         """
#         # First, search for plays
#         play_result = self.search_plays(city, date_str, genre, max_results)
        
#         if not play_result['success']:
#             return play_result
        
#         # Then, search for videos for top 2 plays
#         plays_with_videos = []
        
#         for play in play_result['plays'][:2]:
#             play_name = play['title']
            
#             # Search for interviews/videos
#             video_result = self.search_play_interviews(play_name, max_results=2)
            
#             if video_result['success'] and video_result['videos']:
#                 play['videos'] = video_result['videos']
#             else:
#                 play['videos'] = []
            
#             plays_with_videos.append(play)
        
#         # Add remaining plays without video search (to save quota)
#         for play in play_result['plays'][2:]:
#             play['videos'] = []
#             plays_with_videos.append(play)
        
#         play_result['plays'] = plays_with_videos
        
#         return play_result


# # ==================== DEMO ====================

# def demo():
#     """Demo the improved Tavily search agent"""
#     print("\n" + "="*70)
#     print("  🔍 TAVILY SEARCH AGENT v2.0 - IMPROVED")
#     print("="*70 + "\n")
    
#     agent = TavilySearchAgent()
    
#     if not agent.is_available():
#         print("❌ Tavily not available. Check your API key.")
#         return
    
#     # Test: Search for plays tomorrow in Istanbul
#     print("\n📍 Test: Searching for plays in Istanbul tomorrow...")
#     result = agent.search_plays("Istanbul", "yarın", max_results=5)
    
#     if result['success']:
#         print(f"\n✅ Found {len(result['plays'])} plays")
        
#         if result.get('ai_summary'):
#             print(f"\n🤖 AI Summary:\n{result['ai_summary'][:300]}...")
        
#         print("\n📋 Plays found:")
#         for i, play in enumerate(result['plays'], 1):
#             print(f"\n{i}. {play['title']}")
#             print(f"   📍 {play['venue']}")
#             if play.get('showtimes'):
#                 print(f"   📅 {play['showtimes']}")
#             if play.get('ticket_url'):
#                 print(f"   🎫 {play['ticket_url'][:50]}...")
#     else:
#         print(f"❌ Error: {result.get('error')}")
    
#     print("\n" + "="*70)


# if __name__ == "__main__":
#     demo()


# ---------------------- 6-------------------

# # src/tavily_agent.py
# """
# TavilySearchAgent v2.0 - IMPROVED Web Search for Theater Information
# Better query construction and result parsing

# Andrew Ng Pattern: Tool Use Agent with Reflection
# - Smarter search queries
# - Uses AI-generated answers
# - Filters out category pages
# - Two-phase search when needed
# """

# import os
# import re
# from datetime import datetime, timedelta
# from dotenv import load_dotenv

# load_dotenv()

# # Try to import tavily
# try:
#     from tavily import TavilyClient
#     TAVILY_AVAILABLE = True
# except ImportError:
#     TAVILY_AVAILABLE = False
#     print("⚠️  Tavily not installed. Run: pip install tavily-python")


# class TavilySearchAgent:
#     """
#     Web search agent for theater information - IMPROVED VERSION
    
#     Key improvements:
#     1. Better search queries (specific, not generic)
#     2. Uses Tavily's AI answer feature
#     3. Filters out category/list pages
#     4. Extracts actual play names from results
#     """
    
#     def __init__(self):
#         self.api_key = os.getenv("TAVILY_API_KEY")
#         self.client = None
        
#         if not self.api_key:
#             print("⚠️  TAVILY_API_KEY not found in .env")
#             return
        
#         if TAVILY_AVAILABLE:
#             try:
#                 self.client = TavilyClient(api_key=self.api_key)
#                 print("✅ Tavily Search Agent initialized!")
#             except Exception as e:
#                 print(f"⚠️  Tavily initialization failed: {e}")
#         else:
#             print("⚠️  Tavily library not available")
    
#     def is_available(self):
#         """Check if Tavily is ready to use"""
#         return self.client is not None
    
#     def search_plays(self, city: str, date_str: str = None, genre: str = None, max_results: int = 5):
#         """
#         Search for theater plays - IMPROVED VERSION
        
#         Strategy:
#         1. Build a specific query asking for actual play names
#         2. Use Tavily's AI answer for a summary
#         3. Parse results to extract real plays (not category pages)
#         """
#         if not self.client:
#             return {'success': False, 'error': 'Tavily not available', 'plays': []}
        
#         # ==================== BUILD SMART QUERY ====================
#         # Turkish month names for proper date formatting
#         turkish_months = {
#             1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan',
#             5: 'Mayıs', 6: 'Haziran', 7: 'Temmuz', 8: 'Ağustos',
#             9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
#         }
        
#         # Convert date to TURKISH format for better results
#         date_query = ""
#         if date_str:
#             date_lower = date_str.lower()
#             if date_lower in ['yarın', 'yarin', 'tomorrow']:
#                 tomorrow = datetime.now() + timedelta(days=1)
#                 month_tr = turkish_months[tomorrow.month]
#                 date_query = f"{tomorrow.day} {month_tr} {tomorrow.year}"
#             elif date_lower in ['bugün', 'bugun', 'today']:
#                 today = datetime.now()
#                 month_tr = turkish_months[today.month]
#                 date_query = f"{today.day} {month_tr} {today.year}"
#             elif 'hafta sonu' in date_lower:
#                 date_query = "bu hafta sonu Cumartesi Pazar"
#             elif 'önümüzdeki hafta' in date_lower or 'gelecek hafta' in date_lower:
#                 # Next week calculation
#                 next_week = datetime.now() + timedelta(days=7)
#                 month_tr = turkish_months[next_week.month]
#                 date_query = f"{next_week.day} {month_tr} haftası"
#             elif 'bu hafta' in date_lower:
#                 date_query = "bu hafta"
#             else:
#                 date_query = date_str
        
#         # Build specific query - ASK FOR PLAY NAMES EXPLICITLY
#         if date_query:
#             query = f"{city} tiyatro {date_query} oyun listesi seans"
#         else:
#             query = f"{city} tiyatro bu hafta oyun listesi gösterim"
        
#         print(f"🔍 Tavily searching: '{query}'")
        
#         try:
#             # ==================== SEARCH WITH AI ANSWER ====================
#             response = self.client.search(
#                 query=query,
#                 search_depth="advanced",
#                 max_results=max_results + 3,  # Get extra to filter
#                 include_domains=[
#                     "biletinial.com", 
#                     "biletix.com", 
#                     "passo.com.tr", 
#                     "tiyatrolar.com.tr", 
#                     "mobilet.com"
#                 ],
#                 exclude_domains=[
#                     "twitter.com",
#                     "facebook.com",
#                     "instagram.com"
#                 ],
#                 include_answer=True,  # Get AI-generated summary!
#                 include_raw_content=False
#             )
            
#             # ==================== EXTRACT AI ANSWER ====================
#             ai_answer = response.get('answer', '')
            
#             # ==================== PARSE RESULTS ====================
#             plays = self._parse_search_results_v2(response, city, date_str)
            
#             # ==================== EXTRACT PLAYS FROM AI ANSWER ====================
#             if ai_answer and len(plays) < 3:
#                 answer_plays = self._extract_plays_from_answer(ai_answer, city)
#                 # Add plays from answer that aren't already in list
#                 existing_titles = {p['title'].lower() for p in plays}
#                 for ap in answer_plays:
#                     if ap['title'].lower() not in existing_titles:
#                         plays.append(ap)
            
#             # ==================== REMOVE DUPLICATES ====================
#             # Remove plays with very similar names (e.g., "X" and "X Seans Seçimi")
#             unique_plays = []
#             seen_base_titles = set()
            
#             for play in plays:
#                 # Get base title (remove common suffixes for comparison)
#                 base_title = play['title'].lower()
#                 for suffix in [' seans seçimi', ' tiyatro', ' bilet', ' oyunu']:
#                     base_title = base_title.replace(suffix, '')
#                 base_title = base_title.strip()
                
#                 if base_title not in seen_base_titles:
#                     seen_base_titles.add(base_title)
#                     unique_plays.append(play)
#                 else:
#                     print(f"   ⏭️ Removing duplicate: {play['title']}")
            
#             return {
#                 'success': True,
#                 'plays': unique_plays[:max_results],
#                 'ai_summary': ai_answer,
#                 'source_urls': [r.get('url') for r in response.get('results', [])[:3]],
#                 'query': query
#             }
            
#         except Exception as e:
#             print(f"❌ Tavily search error: {e}")
#             return {'success': False, 'error': str(e), 'plays': []}
    
#     def _parse_search_results_v2(self, response, city, date_str):
#         """
#         Parse Tavily results - IMPROVED VERSION
#         Filters out category pages, extracts actual play info
#         """
#         plays = []
#         seen_titles = set()
        
#         # Keywords that indicate a category/list page (NOT a specific play)
#         category_indicators = [
#             'tiyatro oyunları', 'biletleri', 'etkinlik takvimi', 
#             'istanbul avrupa', 'istanbul anadolu', 'ankara tiyatro',
#             'şehir tiyatroları', 'devlet tiyatroları', 'tüm oyunlar',
#             'kategori', 'filtrele', 'sırala', 'etkinlikleri',
#             'sahne', 'mekan', 'alan kadıköy', 'pax sahne',
#             'akm etkinlik', 'sehir tiyatro'
#         ]
        
#         # URL patterns that indicate category pages
#         category_url_patterns = [
#             r'/tiyatro/?$',
#             r'/tiyatro/istanbul',
#             r'/tiyatro/ankara',
#             r'/tiyatro/adana',
#             r'/etkinlikleri/',
#             r'/mekan/',
#             r'/sahne/',
#             r'/sehrineozel/',
#         ]
        
#         for result in response.get('results', []):
#             url = result.get('url', '')
#             title = result.get('title', '')
#             content = result.get('content', '')
            
#             # Skip category/list pages by title
#             title_lower = title.lower()
#             if any(cat in title_lower for cat in category_indicators):
#                 print(f"   ⏭️ Skipping category page: {title[:40]}...")
#                 continue
            
#             # Skip category pages by URL pattern
#             is_category_url = False
#             for pattern in category_url_patterns:
#                 if re.search(pattern, url):
#                     is_category_url = True
#                     break
            
#             if is_category_url:
#                 print(f"   ⏭️ Skipping category URL: {url[:50]}...")
#                 continue
            
#             # Try to extract play info
#             play_info = self._extract_play_from_result(title, content, url, city)
            
#             if play_info and play_info['title'] not in seen_titles:
#                 # Additional validation: title should look like a play name
#                 if self._is_valid_play_title(play_info['title']):
#                     plays.append(play_info)
#                     seen_titles.add(play_info['title'])
#                     print(f"   ✅ Valid play found: {play_info['title']}")
        
#         return plays
    
#     def _is_valid_play_title(self, title):
#         """Check if a title looks like an actual play name"""
#         if not title or len(title) < 3:
#             return False
        
#         # Reject generic/invalid titles
#         invalid_titles = [
#             'tiyatro oyunları', 'biletleri', 'etkinlik', 'takvim',
#             'istanbul', 'ankara', 'izmir', 'adana', 'türkiye', 'sahne',
#             'biletinial', 'biletix', 'passo', 'mobilet',
#             'gelecek program', 'pek yakında', 'coming soon',
#             'etkinlikleri', 'konser', 'festival', 'mekan',
#             'şehir tiyatroları', 'devlet tiyatroları',
#             'tüm oyunlar', 'tümü', 'tüm etkinlikler'
#         ]
        
#         title_lower = title.lower()
#         for invalid in invalid_titles:
#             if title_lower == invalid or title_lower.startswith(invalid + ' '):
#                 return False
#             # Also check if title IS the invalid word
#             if invalid == title_lower:
#                 return False
        
#         # Reject if title is just a city name
#         cities = ['istanbul', 'ankara', 'izmir', 'adana', 'bursa', 'antalya']
#         if title_lower in cities:
#             return False
        
#         # Reject if too generic (single common word)
#         generic_words = ['program', 'liste', 'takvim', 'bilet', 'sahne', 'salon']
#         if title_lower in generic_words:
#             return False
        
#         # Should have at least one capital letter (play names are usually capitalized)
#         if not any(c.isupper() for c in title):
#             return False
        
#         return True
    
#     def _extract_play_from_result(self, title, content, url, city):
#         """Extract structured play info from a search result"""
        
#         # Clean title - remove common suffixes
#         clean_title = title
#         remove_suffixes = [
#             ' | biletinial', ' | Biletinial', ' - biletinial',
#             ' Tiyatro Biletleri', ' Tiyatro Oyunu', ' biletleri',
#             ' | tiyatrolar.com.tr', ' - Bilet', ' Bilet',
#             ' Tiyatro Seans Seçimi', ' Seans Seçimi', ' - Seans'
#         ]
#         for suffix in remove_suffixes:
#             if clean_title.endswith(suffix):
#                 clean_title = clean_title[:-len(suffix)]
#             clean_title = clean_title.replace(suffix, '')
        
#         clean_title = clean_title.strip()
        
#         if len(clean_title) < 3 or len(clean_title) > 80:
#             return None
        
#         # Extract venue from content - IMPROVED
#         venue = self._extract_venue_v2(content, url)
        
#         # Clean venue - remove line breaks and extra whitespace
#         if venue:
#             venue = ' '.join(venue.split())  # Normalize whitespace
#             venue = venue.replace('\n', ' ').replace('\r', ' ')
#             # Remove leading numbers/times
#             venue = re.sub(r'^\d{2}[:\s]*', '', venue).strip()
        
#         # Extract dates from content
#         dates = self._extract_dates_v2(content)
        
#         return {
#             'title': clean_title,
#             'venue': venue or f"{city} Tiyatroları",
#             'city': city,
#             'showtimes': '; '.join(dates) if dates else None,
#             'ticket_url': url,
#             'source': 'tavily_web',
#             'description': content[:150] if content else None
#         }
    
#     def _extract_venue_v2(self, content, url):
#         """Extract venue name - improved version"""
#         if not content:
#             return None
        
#         # Common venue patterns
#         venue_patterns = [
#             r'([\w\s]+ Sahnesi)',
#             r'([\w\s]+ Salonu)',
#             r'([\w\s]+ Tiyatrosu)',
#             r'(Zorlu PSM[\w\s]*)',
#             r'(DasDas[\w\s]*)',
#             r'(Trump[\w\s]*Sahne)',
#             r'(AKM[\w\s]*)',
#             r'(Harbiye[\w\s]*)',
#             r'(Caddebostan KKM[\w\s]*)',
#             r'(Moda Sahnesi)',
#             r'(Pera[\w\s]*)',
#         ]
        
#         for pattern in venue_patterns:
#             match = re.search(pattern, content, re.IGNORECASE)
#             if match:
#                 venue = match.group(1).strip()
#                 if 10 < len(venue) < 60:
#                     return venue
        
#         return None
    
#     def _extract_dates_v2(self, content):
#         """Extract dates - improved version"""
#         if not content:
#             return []
        
#         dates = []
        
#         # Turkish months
#         months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
#                  'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
        
#         for month in months:
#             # Pattern: "15 Ocak 2025" or "15 Ocak Cumartesi 20:30"
#             patterns = [
#                 rf'(\d{{1,2}}\s+{month}\s+\d{{4}})',
#                 rf'(\d{{1,2}}\s+{month}\s+\w+\s+\d{{2}}:\d{{2}})',
#                 rf'(\d{{1,2}}\s+{month})'
#             ]
            
#             for pattern in patterns:
#                 matches = re.findall(pattern, content, re.IGNORECASE)
#                 dates.extend(matches[:2])
        
#         # Remove duplicates while preserving order
#         seen = set()
#         unique_dates = []
#         for d in dates:
#             if d not in seen:
#                 seen.add(d)
#                 unique_dates.append(d)
        
#         return unique_dates[:3]
    
#     def _extract_plays_from_answer(self, ai_answer, city):
#         """
#         Extract play names from Tavily's AI-generated answer
#         IMPROVED: Better extraction for English AI responses
#         """
#         plays = []
        
#         if not ai_answer:
#             return plays
        
#         extracted_names = set()
        
#         # Method 1: Look for quoted names (various quote styles)
#         quote_patterns = [
#             r'"([^"]+)"',      # "Play Name"
#             r'"([^"]+)"',      # "Play Name" (curly quotes)
#             r"'([^']+)'",      # 'Play Name'
#             r'„([^"]+)"',      # „Play Name"
#             r'«([^»]+)»',      # «Play Name»
#         ]
        
#         for pattern in quote_patterns:
#             matches = re.findall(pattern, ai_answer)
#             for match in matches:
#                 # Clean the name
#                 clean_name = match.strip().strip(',').strip('.').strip()
#                 # Filter out non-play words
#                 skip_words = ['in istanbul', 'december', 'january', 'schedule', 'list', 'available']
#                 if any(sw in clean_name.lower() for sw in skip_words):
#                     continue
#                 if 3 < len(clean_name) < 60:
#                     extracted_names.add(clean_name)
#                     print(f"   📌 Found from quotes: {clean_name}")
        
#         # Method 2: Look for Turkish play name patterns
#         # Pattern: "X oyunu" or "X adlı oyun"
#         oyun_patterns = [
#             r'([A-ZÇĞİÖŞÜ][a-zçğıöşü\']+(?:\s+[A-ZÇĞİÖŞÜa-zçğıöşü\']+)*)\s+oyunu',
#             r'([A-ZÇĞİÖŞÜ][^\s,."]+(?:\s+[^\s,."]+){0,4})\s+adlı',
#         ]
        
#         for pattern in oyun_patterns:
#             matches = re.findall(pattern, ai_answer)
#             for match in matches:
#                 clean_name = match.strip().strip(',').strip('.').strip()
#                 if 3 < len(clean_name) < 60:
#                     extracted_names.add(clean_name)
#                     print(f"   📌 Found from pattern: {clean_name}")
        
#         # Method 3: Parse "includes X and Y" or "showing X, Y, Z" patterns
#         include_patterns = [
#             r'(?:includes?|showing|sahneleniyor|gösterimde)[:\s]+["\']?([^"\']+)["\']?',
#             r'(?:shows include|oyunlar)[:\s]+(.+?)(?:\.|The|$)',
#         ]
        
#         for pattern in include_patterns:
#             match = re.search(pattern, ai_answer, re.IGNORECASE)
#             if match:
#                 list_text = match.group(1)
#                 # Split by common separators
#                 items = re.split(r'[,;]|\s+and\s+|\s+ve\s+', list_text)
#                 for item in items:
#                     # Clean each item
#                     clean_name = item.strip().strip('"').strip("'").strip(',').strip('.').strip()
#                     clean_name = re.sub(r'^["\']+|["\']+$', '', clean_name)
#                     # Skip location/date words
#                     skip_words = ['istanbul', 'ankara', 'december', 'january', 'the', 'schedule']
#                     if any(sw in clean_name.lower() for sw in skip_words):
#                         continue
#                     if 3 < len(clean_name) < 60 and not clean_name.lower().startswith('the '):
#                         extracted_names.add(clean_name)
#                         print(f"   📌 Found from list: {clean_name}")
        
#         # Method 4: Look for capitalized multi-word phrases (likely play names)
#         # Pattern: Two or more capitalized words together
#         title_pattern = r'\b([A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\'[a-zçğıöşü]+)?(?:\s+[A-ZÇĞİÖŞÜa-zçğıöşü]+){1,4})\b'
#         potential_titles = re.findall(title_pattern, ai_answer)
        
#         # Known play name indicators
#         play_indicators = ['Hamlet', 'Gidion', 'Düğümü', 'Kubbe', 'Bernarda', 'Alba']
        
#         for title in potential_titles:
#             clean_name = title.strip()
#             # Check if it contains a known play indicator
#             if any(indicator in clean_name for indicator in play_indicators):
#                 if 3 < len(clean_name) < 60:
#                     extracted_names.add(clean_name)
#                     print(f"   📌 Found known play: {clean_name}")
        
#         print(f"   ✅ Total unique plays extracted: {len(extracted_names)}")
        
#         # Convert to play objects
#         for name in list(extracted_names)[:5]:  # Max 5
#             plays.append({
#                 'title': name,
#                 'venue': f"{city} Tiyatroları",
#                 'city': city,
#                 'showtimes': None,
#                 'ticket_url': None,
#                 'source': 'tavily_ai_answer',
#                 'description': None
#             })
        
#         # ==================== FOLLOW-UP SEARCH FOR TICKET LINKS ====================
#         if plays and self.client:
#             print(f"   🔍 Searching ticket links for {len(plays)} plays...")
#             for play in plays[:3]:
#                 try:
#                     ticket_result = self._quick_ticket_search(play['title'], city)
#                     if ticket_result:
#                         play['ticket_url'] = ticket_result.get('url')
#                         if ticket_result.get('venue'):
#                             play['venue'] = ticket_result.get('venue')
#                         print(f"      ✓ Found ticket for: {play['title']}")
#                 except Exception as e:
#                     print(f"      ✗ Ticket search failed: {e}")
        
#         return plays
    
#     def _quick_ticket_search(self, play_name, city):
#         """Quick search to find ticket link for a play"""
#         try:
#             response = self.client.search(
#                 query=f'"{play_name}" bilet {city}',
#                 search_depth="basic",
#                 max_results=2,
#                 include_domains=["biletinial.com", "biletix.com", "passo.com.tr"],
#                 include_answer=False
#             )
            
#             for result in response.get('results', []):
#                 url = result.get('url', '')
#                 # Skip category pages
#                 if '/tiyatro/' in url and not url.endswith('/tiyatro/') and not url.endswith('/tiyatro'):
#                     venue = self._extract_venue_v2(result.get('content', ''), url)
#                     return {
#                         'url': url,
#                         'venue': venue
#                     }
#             return None
#         except:
#             return None
    
#     def search_specific_play(self, play_name: str, city: str):
#         """
#         Search for a specific play by name
#         Use this for enrichment or finding ticket links
#         """
#         if not self.client:
#             return {'success': False, 'error': 'Tavily not available'}
        
#         query = f'"{play_name}" tiyatro {city} bilet seans'
        
#         print(f"🔍 Searching for specific play: '{play_name}'")
        
#         try:
#             response = self.client.search(
#                 query=query,
#                 search_depth="basic",
#                 max_results=3,
#                 include_domains=["biletinial.com", "biletix.com", "passo.com.tr"],
#                 include_answer=True
#             )
            
#             # Find the best matching result
#             best_match = None
#             play_name_lower = play_name.lower()
            
#             for result in response.get('results', []):
#                 if play_name_lower in result.get('title', '').lower():
#                     best_match = result
#                     break
            
#             if not best_match and response.get('results'):
#                 best_match = response['results'][0]
            
#             if best_match:
#                 return {
#                     'success': True,
#                     'title': play_name,
#                     'ticket_url': best_match.get('url'),
#                     'venue': self._extract_venue_v2(best_match.get('content', ''), ''),
#                     'dates': self._extract_dates_v2(best_match.get('content', '')),
#                     'description': best_match.get('content', '')[:200],
#                     'ai_summary': response.get('answer', '')
#                 }
            
#             return {'success': False, 'error': 'Play not found'}
            
#         except Exception as e:
#             return {'success': False, 'error': str(e)}
    
#     def enrich_play(self, play_title: str, city: str = None):
#         """Enrich play information with web search"""
#         return self.search_specific_play(play_title, city or 'Istanbul')
    
#     def search_theater_news(self, city: str = None, max_results: int = 5):
#         """Get latest theater news"""
#         if not self.client:
#             return {'success': False, 'error': 'Tavily not available'}
        
#         query = "tiyatro haberleri güncel"
#         if city:
#             query = f"{city} {query}"
        
#         try:
#             response = self.client.search(
#                 query=query,
#                 search_depth="basic",
#                 max_results=max_results,
#                 include_answer=True
#             )
            
#             news = []
#             for result in response.get('results', []):
#                 news.append({
#                     'title': result.get('title'),
#                     'url': result.get('url'),
#                     'snippet': result.get('content', '')[:200],
#                 })
            
#             return {
#                 'success': True,
#                 'news': news,
#                 'summary': response.get('answer', '')
#             }
            
#         except Exception as e:
#             return {'success': False, 'error': str(e)}
    
#     def search_play_interviews(self, play_name: str, max_results: int = 3):
#         """
#         Search for YouTube interviews and videos about a specific play
#         IMPROVED: More specific search to avoid irrelevant videos
#         """
#         if not self.client:
#             return {'success': False, 'error': 'Tavily not available', 'videos': []}
        
#         # More specific query - include "tiyatro" and "oyun" to filter better
#         query = f'"{play_name}" tiyatro oyunu röportaj OR tanıtım OR fragman site:youtube.com'
        
#         print(f"   🎬 Searching YouTube for: {play_name}")
        
#         try:
#             response = self.client.search(
#                 query=query,
#                 search_depth="basic",
#                 max_results=max_results + 2,
#                 include_domains=["youtube.com", "youtu.be"],
#                 include_answer=False
#             )
            
#             videos = []
#             seen_urls = set()
            
#             for result in response.get('results', []):
#                 url = result.get('url', '')
#                 title = result.get('title', '').lower()
#                 content = result.get('content', '').lower()
                
#                 # Only YouTube links
#                 if 'youtube.com' not in url and 'youtu.be' not in url:
#                     continue
                
#                 # Skip duplicates
#                 if url in seen_urls:
#                     continue
                
#                 # IMPROVED: Check if video is actually related to the play
#                 play_name_lower = play_name.lower()
#                 play_words = play_name_lower.split()
                
#                 # At least one significant word from play name should be in title or content
#                 is_relevant = False
#                 for word in play_words:
#                     if len(word) > 3 and (word in title or word in content):
#                         is_relevant = True
#                         break
                
#                 # Also check for theater-related keywords
#                 theater_keywords = ['tiyatro', 'oyun', 'sahne', 'oyuncu', 'röportaj', 'fragman']
#                 has_theater_keyword = any(kw in title or kw in content for kw in theater_keywords)
                
#                 if not is_relevant and not has_theater_keyword:
#                     print(f"      ⏭️ Skipping irrelevant video: {result.get('title', '')[:40]}...")
#                     continue
                
#                 seen_urls.add(url)
                
#                 # Clean title
#                 clean_title = result.get('title', '').replace(' - YouTube', '').strip()
                
#                 videos.append({
#                     'title': clean_title,
#                     'url': url,
#                     'platform': 'YouTube'
#                 })
                
#                 if len(videos) >= max_results:
#                     break
            
#             print(f"   🎬 Found {len(videos)} relevant videos")
            
#             return {
#                 'success': True,
#                 'videos': videos,
#                 'play_name': play_name
#             }
            
#         except Exception as e:
#             print(f"   ❌ Video search error: {e}")
#             return {'success': False, 'error': str(e), 'videos': []}
    
#     def search_play_with_videos(self, city: str, date_str: str = None, genre: str = None, max_results: int = 5):
#         """
#         Search for plays AND their related YouTube videos
#         Combines play search with video search for top results
#         """
#         # First, search for plays
#         play_result = self.search_plays(city, date_str, genre, max_results)
        
#         if not play_result['success']:
#             return play_result
        
#         # Then, search for videos for top 2 plays
#         plays_with_videos = []
        
#         for play in play_result['plays'][:2]:
#             play_name = play['title']
            
#             # Search for interviews/videos
#             video_result = self.search_play_interviews(play_name, max_results=2)
            
#             if video_result['success'] and video_result['videos']:
#                 play['videos'] = video_result['videos']
#             else:
#                 play['videos'] = []
            
#             plays_with_videos.append(play)
        
#         # Add remaining plays without video search (to save quota)
#         for play in play_result['plays'][2:]:
#             play['videos'] = []
#             plays_with_videos.append(play)
        
#         play_result['plays'] = plays_with_videos
        
#         return play_result


# # ==================== DEMO ====================

# def demo():
#     """Demo the improved Tavily search agent"""
#     print("\n" + "="*70)
#     print("  🔍 TAVILY SEARCH AGENT v2.0 - IMPROVED")
#     print("="*70 + "\n")
    
#     agent = TavilySearchAgent()
    
#     if not agent.is_available():
#         print("❌ Tavily not available. Check your API key.")
#         return
    
#     # Test: Search for plays tomorrow in Istanbul
#     print("\n📍 Test: Searching for plays in Istanbul tomorrow...")
#     result = agent.search_plays("Istanbul", "yarın", max_results=5)
    
#     if result['success']:
#         print(f"\n✅ Found {len(result['plays'])} plays")
        
#         if result.get('ai_summary'):
#             print(f"\n🤖 AI Summary:\n{result['ai_summary'][:300]}...")
        
#         print("\n📋 Plays found:")
#         for i, play in enumerate(result['plays'], 1):
#             print(f"\n{i}. {play['title']}")
#             print(f"   📍 {play['venue']}")
#             if play.get('showtimes'):
#                 print(f"   📅 {play['showtimes']}")
#             if play.get('ticket_url'):
#                 print(f"   🎫 {play['ticket_url'][:50]}...")
#     else:
#         print(f"❌ Error: {result.get('error')}")
    
#     print("\n" + "="*70)


# if __name__ == "__main__":
#     demo()


# ---------------------- 7-------------------

# src/tavily_agent.py
"""
TavilySearchAgent v3.0 - MORE RELIABLE Web Search for Theater Information

Key Improvements:
1. Multiple query strategies (try different queries if first fails)
2. Better date formatting (Turkish dates work better)
3. Fallback to general search if specific date fails
4. Improved relevance filtering for YouTube
5. Better extraction from AI answers
"""

import os
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Try to import tavily
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    print("⚠️  Tavily not installed. Run: pip install tavily-python")


class TavilySearchAgent:
    """
    Web search agent for theater information - v3.0 MORE RELIABLE
    """
    
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        self.client = None
        
        if not self.api_key:
            print("⚠️  TAVILY_API_KEY not found in .env")
            return
        
        if TAVILY_AVAILABLE:
            try:
                self.client = TavilyClient(api_key=self.api_key)
                print("✅ Tavily Search Agent initialized!")
            except Exception as e:
                print(f"⚠️  Tavily initialization failed: {e}")
        else:
            print("⚠️  Tavily library not available")
    
    def is_available(self):
        """Check if Tavily is ready to use"""
        return self.client is not None
    
    def search_plays(self, city: str, date_str: str = None, genre: str = None, max_results: int = 5):
        """
        Search for theater plays - v3.0 with MULTIPLE QUERY STRATEGIES
        """
        if not self.client:
            return {'success': False, 'error': 'Tavily not available', 'plays': []}
        
        # Turkish month names
        turkish_months = {
            1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan',
            5: 'Mayıs', 6: 'Haziran', 7: 'Temmuz', 8: 'Ağustos',
            9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
        }
        
        # Parse date for query building
        target_date = None
        date_display = ""
        
        if date_str:
            date_lower = date_str.lower()
            if date_lower in ['yarın', 'yarin', 'tomorrow']:
                target_date = datetime.now() + timedelta(days=1)
            elif date_lower in ['bugün', 'bugun', 'today']:
                target_date = datetime.now()
            elif 'hafta sonu' in date_lower:
                today = datetime.now()
                days_until_saturday = (5 - today.weekday()) % 7
                if days_until_saturday == 0 and today.weekday() != 5:
                    days_until_saturday = 7
                target_date = today + timedelta(days=days_until_saturday)
            elif 'önümüzdeki hafta' in date_lower or 'gelecek hafta' in date_lower:
                target_date = datetime.now() + timedelta(days=7)
            
            if target_date:
                month_tr = turkish_months[target_date.month]
                date_display = f"{target_date.day} {month_tr} {target_date.year}"
        
        # ==================== STRATEGY 1: Specific date query ====================
        plays = []
        ai_summary = ""
        query_used = ""
        
        if date_display:
            query1 = f"{city} tiyatro {date_display} hangi oyunlar var"
            print(f"🔍 Strategy 1: '{query1}'")
            
            result1 = self._execute_search(query1, max_results + 3)
            if result1['success']:
                plays = self._parse_all_results(result1, city)
                ai_summary = result1.get('ai_answer', '')
                query_used = query1
        
        # ==================== STRATEGY 2: Month-based query (if strategy 1 fails) ====================
        if len(plays) < 2 and target_date:
            month_tr = turkish_months[target_date.month]
            query2 = f"{city} tiyatro {month_tr} {target_date.year} oyunlar program"
            print(f"🔍 Strategy 2: '{query2}'")
            
            result2 = self._execute_search(query2, max_results + 3)
            if result2['success']:
                new_plays = self._parse_all_results(result2, city)
                # Merge results
                existing_titles = {p['title'].lower() for p in plays}
                for p in new_plays:
                    if p['title'].lower() not in existing_titles:
                        plays.append(p)
                if not ai_summary:
                    ai_summary = result2.get('ai_answer', '')
                query_used = query2
        
        # ==================== STRATEGY 3: General city query (fallback) ====================
        if len(plays) < 2:
            query3 = f"{city} tiyatro bu hafta sahnelenecek oyunlar bilet"
            print(f"🔍 Strategy 3 (fallback): '{query3}'")
            
            result3 = self._execute_search(query3, max_results + 5)
            if result3['success']:
                new_plays = self._parse_all_results(result3, city)
                existing_titles = {p['title'].lower() for p in plays}
                for p in new_plays:
                    if p['title'].lower() not in existing_titles:
                        plays.append(p)
                if not ai_summary:
                    ai_summary = result3.get('ai_answer', '')
                query_used = query3
        
        # ==================== STRATEGY 4: Site-specific search ====================
        if len(plays) < 2:
            query4 = f"site:biletinial.com {city} tiyatro oyun"
            print(f"🔍 Strategy 4 (site-specific): '{query4}'")
            
            result4 = self._execute_search(query4, max_results + 5, use_domains=False)
            if result4['success']:
                new_plays = self._parse_all_results(result4, city)
                existing_titles = {p['title'].lower() for p in plays}
                for p in new_plays:
                    if p['title'].lower() not in existing_titles:
                        plays.append(p)
                query_used = query4
        
        # ==================== REMOVE DUPLICATES ====================
        unique_plays = self._deduplicate_plays(plays)
        
        return {
            'success': True,
            'plays': unique_plays[:max_results],
            'ai_summary': ai_summary,
            'source_urls': [],
            'query': query_used,
            'strategies_tried': 4 if len(plays) < 2 else 1
        }
    
    def _execute_search(self, query: str, max_results: int, use_domains: bool = True):
        """Execute a single Tavily search"""
        try:
            search_params = {
                'query': query,
                'search_depth': "advanced",
                'max_results': max_results,
                'include_answer': True,
                'include_raw_content': False
            }
            
            if use_domains:
                search_params['include_domains'] = [
                    "biletinial.com", 
                    "biletix.com", 
                    "passo.com.tr", 
                    "tiyatrolar.com.tr",
                    "mobilet.com"
                ]
            
            response = self.client.search(**search_params)
            
            return {
                'success': True,
                'results': response.get('results', []),
                'ai_answer': response.get('answer', '')
            }
        except Exception as e:
            print(f"   ❌ Search error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _parse_all_results(self, search_result, city):
        """Parse search results and extract plays"""
        plays = []
        seen_titles = set()
        
        # Parse from search results
        for result in search_result.get('results', []):
            play = self._extract_play_from_result(result, city)
            if play and play['title'].lower() not in seen_titles:
                if self._is_valid_play_title(play['title']):
                    plays.append(play)
                    seen_titles.add(play['title'].lower())
                    print(f"   ✅ Found: {play['title']}")
                else:
                    print(f"   ⏭️ Skipping invalid: {play['title'][:40]}...")
        
        # Parse from AI answer
        ai_answer = search_result.get('ai_answer', '')
        if ai_answer:
            ai_plays = self._extract_plays_from_ai_answer(ai_answer, city)
            for p in ai_plays:
                if p['title'].lower() not in seen_titles:
                    plays.append(p)
                    seen_titles.add(p['title'].lower())
        
        return plays
    
    def _extract_play_from_result(self, result, city):
        """Extract play info from a single search result"""
        url = result.get('url', '')
        title = result.get('title', '')
        content = result.get('content', '')
        
        # Skip category pages
        if self._is_category_page(title, url):
            return None
        
        # Clean title
        clean_title = self._clean_title(title)
        
        if not clean_title or len(clean_title) < 3 or len(clean_title) > 80:
            return None
        
        # Extract venue
        venue = self._extract_venue(content)
        if venue:
            venue = ' '.join(venue.split())  # Normalize whitespace
        
        # Extract dates
        dates = self._extract_dates(content)
        
        return {
            'title': clean_title,
            'venue': venue or f"{city} Tiyatroları",
            'city': city,
            'showtimes': '; '.join(dates) if dates else None,
            'ticket_url': url,
            'source': 'tavily_web'
        }
    
    def _is_category_page(self, title, url):
        """Check if this is a category/list page"""
        title_lower = title.lower()
        
        # Category indicators in title
        category_words = [
            'tiyatro oyunları', 'biletleri', 'etkinlik takvimi',
            'istanbul avrupa', 'istanbul anadolu', 'ankara tiyatro',
            'şehir tiyatroları', 'devlet tiyatroları', 'tüm oyunlar',
            'etkinlikleri', 'mekan', 'sahne |', 'alan kadıköy',
            'akm etkinlik', 'çocuk tiyatrosu', 'sahnedeki', 
            'profesyonel tiyatro', 'sahne sanatları'
        ]
        
        if any(cat in title_lower for cat in category_words):
            return True
        
        # Category URL patterns
        category_url_patterns = [
            r'/tiyatro/?$',
            r'/tiyatro/istanbul',
            r'/tiyatro/ankara',
            r'/tiyatro/adana',
            r'/tiyatro/izmir',
            r'/etkinlikleri/',
            r'/mekan/',
            r'/sahne/',
            r'/sehrineozel/',
            r'/cocuk-tiyatro',
            r'/profesyonel-dt',
        ]
        
        for pattern in category_url_patterns:
            if re.search(pattern, url):
                return True
        
        return False
    
    def _clean_title(self, title):
        """Clean and normalize play title"""
        clean = title
        
        # Remove common suffixes
        suffixes = [
            ' | biletinial', ' | Biletinial', ' - biletinial',
            ' | tiyatrolar.com.tr', ' | Biletix',
            ' Tiyatro Biletleri', ' Tiyatro Oyunu Biletleri',
            ' Biletleri', ' biletleri', ' Bilet',
            ' Tiyatro Seans Seçimi', ' Seans Seçimi',
            ' Tiyatro Oyunu', '...'
        ]
        
        for suffix in suffixes:
            if clean.endswith(suffix):
                clean = clean[:-len(suffix)]
            clean = clean.replace(suffix, '')
        
        return clean.strip()
    
    def _is_valid_play_title(self, title):
        """Check if title is a valid play name"""
        if not title or len(title) < 3:
            return False
        
        title_lower = title.lower()
        
        # Invalid titles
        invalid = [
            'tiyatro oyunları', 'biletleri', 'etkinlik', 'takvim',
            'istanbul', 'ankara', 'izmir', 'adana', 'türkiye',
            'biletinial', 'biletix', 'passo', 'mobilet',
            'gelecek program', 'pek yakında', 'coming soon',
            'şehir tiyatroları', 'devlet tiyatroları',
            'tüm oyunlar', 'sahne', 'mekan', 'salon',
            'program', 'liste', 'kategori'
        ]
        
        for inv in invalid:
            if title_lower == inv:
                return False
        
        # Must have at least one uppercase letter
        if not any(c.isupper() for c in title):
            return False
        
        return True
    
    def _extract_venue(self, content):
        """Extract venue from content"""
        if not content:
            return None
        
        patterns = [
            r'([\w\s]+ Sahnesi)',
            r'([\w\s]+ Salonu)',
            r'([\w\s]+ Tiyatrosu)',
            r'(Zorlu PSM[^,.\n]*)',
            r'(DasDas[^,.\n]*)',
            r'(Trump Sahne[^,.\n]*)',
            r'(AKM[^,.\n]*)',
            r'(Harbiye[^,.\n]*)',
            r'(KKM[^,.\n]*)',
            r'(Moda Sahnesi)',
            r'(Alan Kadıköy)',
            r'(Jolly Joker[^,.\n]*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                venue = match.group(1).strip()
                if 5 < len(venue) < 60:
                    return venue
        
        return None
    
    def _extract_dates(self, content):
        """Extract dates from content"""
        if not content:
            return []
        
        dates = []
        months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
                 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
        
        for month in months:
            patterns = [
                rf'(\d{{1,2}}\s+{month}\s+\d{{4}})',
                rf'(\d{{1,2}}\s+{month}\s+\w+\s+\d{{2}}:\d{{2}})',
            ]
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                dates.extend(matches[:2])
        
        # Deduplicate
        seen = set()
        unique = []
        for d in dates:
            if d not in seen:
                seen.add(d)
                unique.append(d)
        
        return unique[:3]
    
    def _extract_plays_from_ai_answer(self, ai_answer, city):
        """Extract play names from AI summary"""
        plays = []
        if not ai_answer:
            return plays
        
        extracted = set()
        
        # Method 1: Quoted names
        quote_patterns = [r'"([^"]+)"', r'"([^"]+)"', r"'([^']+)'"]
        
        for pattern in quote_patterns:
            matches = re.findall(pattern, ai_answer)
            for match in matches:
                clean = match.strip().strip(',').strip('.')
                # Skip non-play words
                skip = ['istanbul', 'ankara', 'december', 'january', 'february',
                       'schedule', 'available', 'tickets', 'check', 'visit']
                if any(s in clean.lower() for s in skip):
                    continue
                if 3 < len(clean) < 60:
                    extracted.add(clean)
                    print(f"   📌 From AI: {clean}")
        
        # Method 2: "X oyunu" pattern
        oyun_match = re.findall(r'([A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s+\w+){0,3})\s+oyunu', ai_answer)
        for m in oyun_match:
            if 3 < len(m) < 60:
                extracted.add(m.strip())
        
        # Convert to play objects
        for name in list(extracted)[:5]:
            plays.append({
                'title': name,
                'venue': f"{city} Tiyatroları",
                'city': city,
                'showtimes': None,
                'ticket_url': None,
                'source': 'tavily_ai'
            })
        
        # Try to find tickets for extracted plays
        for play in plays[:2]:
            ticket = self._find_ticket_link(play['title'], city)
            if ticket:
                play['ticket_url'] = ticket.get('url')
                if ticket.get('venue'):
                    play['venue'] = ticket['venue']
        
        return plays
    
    def _find_ticket_link(self, play_name, city):
        """Quick search to find ticket link"""
        try:
            response = self.client.search(
                query=f'"{play_name}" bilet {city}',
                search_depth="basic",
                max_results=2,
                include_domains=["biletinial.com", "biletix.com", "passo.com.tr"]
            )
            
            for r in response.get('results', []):
                url = r.get('url', '')
                if '/tiyatro/' in url and not self._is_category_page('', url):
                    return {
                        'url': url,
                        'venue': self._extract_venue(r.get('content', ''))
                    }
            return None
        except:
            return None
    
    def _deduplicate_plays(self, plays):
        """Remove duplicate plays"""
        unique = []
        seen_base = set()
        
        for play in plays:
            base = play['title'].lower()
            # Remove common suffixes for comparison
            for suffix in [' seans seçimi', ' tiyatro', ' bilet', ' oyunu']:
                base = base.replace(suffix, '')
            base = base.strip()
            
            if base not in seen_base:
                seen_base.add(base)
                unique.append(play)
        
        return unique
    
    def search_play_interviews(self, play_name: str, max_results: int = 2):
        """Search for YouTube videos - STRICT relevance check"""
        if not self.client:
            return {'success': False, 'videos': []}
        
        # More specific query - exact play name required
        query = f'"{play_name}" tiyatro oyunu'
        
        print(f"   🎬 YouTube search: {play_name}")
        
        try:
            response = self.client.search(
                query=query,
                search_depth="basic",
                max_results=max_results + 5,  # Get more to filter
                include_domains=["youtube.com", "youtu.be"]
            )
            
            videos = []
            
            # Normalize play name for comparison
            play_name_lower = play_name.lower()
            play_words = [w for w in play_name_lower.split() if len(w) > 2]
            
            for r in response.get('results', []):
                url = r.get('url', '')
                title = r.get('title', '').lower()
                content = r.get('content', '').lower()
                
                if 'youtube.com' not in url and 'youtu.be' not in url:
                    continue
                
                # STRICT relevance check:
                # At least 2 words from play name must be in title OR
                # The exact play name (or close variant) must be in title/content
                matching_words = sum(1 for w in play_words if w in title or w in content)
                
                # Check for exact match (with some flexibility)
                exact_match = play_name_lower in title or play_name_lower in content
                
                # Also check for partial exact match (first 2-3 words)
                partial_match = False
                if len(play_words) >= 2:
                    partial = ' '.join(play_words[:2])
                    partial_match = partial in title or partial in content
                
                if not (matching_words >= 2 or exact_match or partial_match):
                    print(f"      ⏭️ Skipping (not relevant): {r.get('title', '')[:35]}...")
                    continue
                
                # Additional filter: must have theater-related content
                theater_keywords = ['tiyatro', 'oyun', 'sahne', 'perde', 'oyuncu', 'fragman', 'trailer']
                has_theater = any(kw in title or kw in content for kw in theater_keywords)
                
                # If no theater keyword, require stronger match
                if not has_theater and matching_words < 3 and not exact_match:
                    print(f"      ⏭️ Skipping (no theater context): {r.get('title', '')[:35]}...")
                    continue
                
                videos.append({
                    'title': r.get('title', '').replace(' - YouTube', '').strip(),
                    'url': url
                })
                
                if len(videos) >= max_results:
                    break
            
            print(f"   🎬 Found {len(videos)} relevant videos")
            return {'success': True, 'videos': videos}
            
        except Exception as e:
            return {'success': False, 'videos': []}
    
    def search_play_with_videos(self, city: str, date_str: str = None, genre: str = None, max_results: int = 5):
        """Search plays with video enrichment"""
        result = self.search_plays(city, date_str, genre, max_results)
        
        if not result['success']:
            return result
        
        # Add videos for top 2 plays only
        for play in result['plays'][:2]:
            video_result = self.search_play_interviews(play['title'], max_results=2)
            play['videos'] = video_result.get('videos', [])
        
        for play in result['plays'][2:]:
            play['videos'] = []
        
        return result
    
    def search_theater_news(self, city: str = None, max_results: int = 5):
        """Get theater news"""
        if not self.client:
            return {'success': False}
        
        query = f"{city} tiyatro haberleri güncel" if city else "tiyatro haberleri güncel"
        
        try:
            response = self.client.search(
                query=query,
                search_depth="basic",
                max_results=max_results,
                include_answer=True
            )
            
            news = [{
                'title': r.get('title'),
                'url': r.get('url'),
                'snippet': r.get('content', '')[:200]
            } for r in response.get('results', [])]
            
            return {
                'success': True,
                'news': news,
                'summary': response.get('answer', '')
            }
        except:
            return {'success': False}
    
    def enrich_play(self, play_title: str, city: str = None):
        """Get more info about a specific play"""
        return self._find_ticket_link(play_title, city or 'Istanbul')


# Demo
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  🔍 TAVILY AGENT v3.0 - MULTI-STRATEGY SEARCH")
    print("="*60)
    
    agent = TavilySearchAgent()
    
    if agent.is_available():
        result = agent.search_plays("Istanbul", "15 Ocak 2026")
        print(f"\n✅ Found {len(result['plays'])} plays")
        for p in result['plays']:
            print(f"   • {p['title']}")

