# src/hybrid_search_agent.py
"""
HybridSearchAgent - Scraping + Tavily Zenginleştirme

Andrew Ng Pattern: Multi-Agent Tool Use with Fallback

Strateji:
1. Database'den kontrol et (en hızlı)
2. Biletinial'dan real-time scrape et (en güvenilir)
3. Tavily ile zenginleştir (YouTube, eleştiriler)

Bu yaklaşım:
✅ %100 doğru oyun isimleri (scraping'den)
✅ Güncel tarih/mekan bilgisi
✅ YouTube röportajları (Tavily'den)
✅ Fallback mekanizması
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Import our modules
try:
    from realtime_scraper import RealtimeScraper
    SCRAPER_AVAILABLE = True
except ImportError:
    SCRAPER_AVAILABLE = False
    print("⚠️  RealtimeScraper not available")

try:
    from tavily_agent import TavilySearchAgent
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    print("⚠️  TavilySearchAgent not available")


class HybridSearchAgent:
    """
    Hibrit arama agent'ı - En güvenilir sonuçlar için
    
    Scraping (güvenilir veri) + Tavily (zenginleştirme)
    """
    
    def __init__(self):
        # Initialize scraper
        self.scraper = None
        if SCRAPER_AVAILABLE:
            try:
                self.scraper = RealtimeScraper()
                print("✅ Realtime Scraper initialized!")
            except Exception as e:
                print(f"⚠️  Scraper init failed: {e}")
        
        # Initialize Tavily (for enrichment only)
        self.tavily = None
        if TAVILY_AVAILABLE:
            try:
                self.tavily = TavilySearchAgent()
                if self.tavily.is_available():
                    print("✅ Tavily Enrichment Agent initialized!")
                else:
                    self.tavily = None
            except Exception as e:
                print(f"⚠️  Tavily init failed: {e}")
    
    def is_available(self) -> bool:
        """Check if at least scraper is available"""
        return self.scraper is not None
    
    def search_plays(self, city: str, date_str: str = None, target_date: datetime = None, 
                    max_results: int = 10, enrich: bool = True) -> Dict:
        """
        Ana arama fonksiyonu
        
        Args:
            city: Şehir adı
            date_str: Tarih string'i (yarın, bu hafta sonu, vs.)
            target_date: datetime objesi (spesifik tarih)
            max_results: Maximum sonuç sayısı
            enrich: Tavily ile zenginleştir mi?
            
        Returns:
            {
                'success': bool,
                'plays': List[Dict],
                'source': str,  # 'scraper', 'tavily', 'database'
                'enriched': bool
            }
        """
        print(f"\n🔍 HybridSearch: {city}, date={date_str or target_date}")
        
        # ==================== STEP 1: SCRAPE ====================
        plays = []
        source = 'unknown'
        
        if self.scraper:
            print("1️⃣ Attempting real-time scrape...")
            
            try:
                if target_date:
                    # Specific date search
                    plays = self.scraper.get_plays_for_date(city, target_date, max_plays=max_results)
                    
                    # If no plays for specific date, get all plays and show alternatives
                    if not plays:
                        print(f"   ⚠️ No plays found for {target_date.strftime('%Y-%m-%d')}")
                        print("   📋 Getting all available plays...")
                        all_plays = self.scraper.get_plays_for_city(city, max_plays=max_results)
                        plays = all_plays
                        
                elif date_str:
                    # Parse date string
                    parsed_date = self._parse_date_string(date_str)
                    
                    if parsed_date.get('is_range'):
                        # Date range (hafta sonu, bu hafta, etc.)
                        plays = self.scraper.get_plays_for_date_range(
                            city,
                            parsed_date['start'],
                            parsed_date['end'],
                            max_plays=max_results
                        )
                    elif parsed_date.get('date'):
                        # Specific date
                        plays = self.scraper.get_plays_for_date(city, parsed_date['date'], max_plays=max_results)
                        
                        if not plays:
                            plays = self.scraper.get_plays_for_city(city, max_plays=max_results)
                    else:
                        # No specific date, get all
                        plays = self.scraper.get_plays_for_city(city, max_plays=max_results)
                else:
                    # No date specified, get all plays
                    plays = self.scraper.get_plays_for_city(city, max_plays=max_results)
                
                source = 'scraper'
                print(f"   ✅ Scraper found {len(plays)} plays")
                
            except Exception as e:
                print(f"   ❌ Scraper error: {e}")
                plays = []
        
        # ==================== STEP 2: FALLBACK TO TAVILY ====================
        if not plays and self.tavily:
            print("2️⃣ Scraper failed, falling back to Tavily...")
            
            try:
                tavily_result = self.tavily.search_plays(city, date_str, max_results=max_results)
                
                if tavily_result.get('success') and tavily_result.get('plays'):
                    plays = self._convert_tavily_plays(tavily_result['plays'])
                    source = 'tavily'
                    print(f"   ✅ Tavily found {len(plays)} plays")
            except Exception as e:
                print(f"   ❌ Tavily error: {e}")
        
        # ==================== STEP 3: ENRICH WITH TAVILY ====================
        enriched = False
        
        if plays and enrich and self.tavily:
            print("3️⃣ Enriching with Tavily (YouTube videos)...")
            plays = self._enrich_plays(plays[:5])  # Only enrich top 5
            enriched = True
        
        # ==================== FORMAT RESULTS ====================
        formatted_plays = self._format_plays(plays, city, target_date or self._parse_date_string(date_str).get('date') if date_str else None)
        
        return {
            'success': len(formatted_plays) > 0,
            'plays': formatted_plays[:max_results],
            'source': source,
            'enriched': enriched,
            'city': city,
            'date_query': date_str
        }
    
    def _parse_date_string(self, date_str: str) -> Dict:
        """Parse Turkish date string"""
        if not date_str:
            return {}
        
        date_lower = date_str.lower()
        today = datetime.now()
        
        # Yarın
        if 'yarın' in date_lower or 'yarin' in date_lower:
            return {'date': today + timedelta(days=1)}
        
        # Bugün
        if 'bugün' in date_lower or 'bugun' in date_lower:
            return {'date': today}
        
        # Bu hafta sonu
        if 'hafta sonu' in date_lower:
            days_until_saturday = (5 - today.weekday()) % 7
            if days_until_saturday == 0 and today.weekday() != 5:
                days_until_saturday = 7
            saturday = today + timedelta(days=days_until_saturday)
            sunday = saturday + timedelta(days=1)
            return {
                'is_range': True,
                'start': saturday,
                'end': sunday
            }
        
        # Önümüzdeki hafta
        if 'önümüzdeki hafta' in date_lower or 'gelecek hafta' in date_lower or 'haftaya' in date_lower:
            days_until_monday = (7 - today.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            next_monday = today + timedelta(days=days_until_monday)
            next_sunday = next_monday + timedelta(days=6)
            return {
                'is_range': True,
                'start': next_monday,
                'end': next_sunday,
                'date': next_monday  # Also provide single date for display
            }
        
        # Bu hafta
        if 'bu hafta' in date_lower:
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            return {
                'is_range': True,
                'start': start_of_week,
                'end': end_of_week
            }
        
        return {}
    
    def _convert_tavily_plays(self, tavily_plays: List[Dict]) -> List[Dict]:
        """Convert Tavily format to our standard format"""
        converted = []
        for p in tavily_plays:
            converted.append({
                'title': p.get('title', ''),
                'venue': p.get('venue', ''),
                'city': p.get('city', ''),
                'ticket_url': p.get('ticket_url'),
                'dates': [],
                'source': 'tavily'
            })
        return converted
    
    def _enrich_plays(self, plays: List[Dict]) -> List[Dict]:
        """Enrich plays with YouTube videos from Tavily"""
        if not self.tavily:
            return plays
        
        for play in plays[:3]:  # Only first 3 to save API quota
            try:
                print(f"   🎬 Enriching: {play['title']}")
                
                # Search for YouTube videos
                video_result = self.tavily.search_play_interviews(play['title'], max_results=2)
                
                if video_result.get('success') and video_result.get('videos'):
                    play['videos'] = video_result['videos']
                    print(f"      ✓ Found {len(play['videos'])} videos")
                else:
                    play['videos'] = []
                    
            except Exception as e:
                print(f"      ❌ Enrichment failed: {e}")
                play['videos'] = []
        
        return plays
    
    def _format_plays(self, plays: List[Dict], city: str, target_date: Optional[datetime]) -> List[Dict]:
        """Format plays for display"""
        formatted = []
        
        for play in plays:
            formatted_play = {
                'title': play.get('title', 'Unknown'),
                'venue': play.get('venue') or f"{city} Tiyatroları",
                'city': city,
                'ticket_url': play.get('ticket_url'),
                'videos': play.get('videos', []),
                'source': play.get('source', 'unknown')
            }
            
            # Format showtimes
            if play.get('matching_showtime'):
                formatted_play['showtimes'] = play['matching_showtime'].get('display')
            elif play.get('dates'):
                # Get first few dates as string
                date_strs = [d.get('display', '') for d in play['dates'][:3] if d.get('display')]
                formatted_play['showtimes'] = '; '.join(date_strs)
            else:
                formatted_play['showtimes'] = None
            
            formatted.append(formatted_play)
        
        return formatted
    
    def get_play_details(self, play_title: str, city: str) -> Dict:
        """Get detailed info about a specific play"""
        result = {
            'title': play_title,
            'found': False
        }
        
        # Try scraper first
        if self.scraper:
            plays = self.scraper.get_plays_for_city(city, max_plays=50)
            
            for play in plays:
                if play['title'].lower() == play_title.lower():
                    result['found'] = True
                    result.update(play)
                    
                    # Get details from play page
                    if play.get('ticket_url'):
                        details = self.scraper.get_play_details(play['ticket_url'])
                        if details:
                            result.update(details)
                    break
        
        # Enrich with Tavily
        if result['found'] and self.tavily:
            video_result = self.tavily.search_play_interviews(play_title, max_results=3)
            if video_result.get('success'):
                result['videos'] = video_result.get('videos', [])
        
        return result


# ==================== DEMO ====================

def demo():
    """Test the hybrid agent"""
    print("\n" + "="*70)
    print("  🔍 HYBRID SEARCH AGENT - SCRAPING + TAVILY")
    print("="*70 + "\n")
    
    agent = HybridSearchAgent()
    
    if not agent.is_available():
        print("❌ Agent not available!")
        return
    
    # Test 1: General search
    print("\n" + "-"*50)
    print("TEST 1: Istanbul'daki oyunlar")
    print("-"*50)
    
    result = agent.search_plays("Istanbul", max_results=5)
    
    if result['success']:
        print(f"\n✅ Found {len(result['plays'])} plays (source: {result['source']})")
        print(f"   Enriched: {result['enriched']}")
        
        for i, play in enumerate(result['plays'], 1):
            print(f"\n{i}. {play['title']}")
            print(f"   📍 {play['venue']}")
            if play.get('showtimes'):
                print(f"   📅 {play['showtimes']}")
            if play.get('ticket_url'):
                print(f"   🎫 {play['ticket_url'][:50]}...")
            if play.get('videos'):
                print(f"   🎬 {len(play['videos'])} video(s)")
                for v in play['videos'][:1]:
                    print(f"      • {v['title'][:40]}...")
    
    # Test 2: Specific date
    print("\n" + "-"*50)
    print("TEST 2: 15 Ocak 2026 için oyunlar")
    print("-"*50)
    
    result2 = agent.search_plays("Istanbul", target_date=datetime(2026, 1, 15), max_results=5)
    
    if result2['success']:
        print(f"\n✅ Found {len(result2['plays'])} plays")
        for i, play in enumerate(result2['plays'][:3], 1):
            print(f"\n{i}. {play['title']}")
    
    # Test 3: Date string
    print("\n" + "-"*50)
    print("TEST 3: 'önümüzdeki hafta' Adana")
    print("-"*50)
    
    result3 = agent.search_plays("Adana", date_str="önümüzdeki hafta", max_results=5)
    
    if result3['success']:
        print(f"\n✅ Found {len(result3['plays'])} plays")
        for i, play in enumerate(result3['plays'][:3], 1):
            print(f"\n{i}. {play['title']}")


if __name__ == "__main__":
    demo()