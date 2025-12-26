"""
IMPROVED Recommendation Engine v2
- Date filtering
- Better city detection  
- Cleaner LLM scoring
"""

import os
import re
import warnings
from datetime import datetime, timedelta
from dotenv import load_dotenv
from litellm import completion
import requests

from database import TheaterDatabase

# Suppress pydantic warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

load_dotenv()

# Turkish month mapping
TURKISH_MONTHS = {
    'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4,
    'mayıs': 5, 'haziran': 6, 'temmuz': 7, 'ağustos': 8,
    'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12,
    # Without Turkish characters
    'subat': 2, 'mayis': 5, 'agustos': 8, 'eylul': 9, 'aralik': 12
}

# Venues that are NOT in Istanbul (for validation)
NON_ISTANBUL_VENUES = [
    'sapanca', 'kırklareli', 'kirkpinar', 'ankara', 'izmir', 
    'antalya', 'bursa', 'eskişehir', 'konya'
]


class ImprovedPlayRecommender:
    """
    IMPROVED: Date filtering, city validation, cleaner output
    """
    
    def __init__(self):
        self.db = TheaterDatabase()
        self.user_location = "Beşiktaş, Istanbul, Turkey"
        self.user_city = "Istanbul"
        self.maps_api_available = self._check_maps_api()
    
    def _check_maps_api(self):
        """Check if Google Maps API is working"""
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not api_key:
            return False
        
        try:
            url = "https://maps.googleapis.com/maps/api/distancematrix/json"
            params = {
                'origins': 'Istanbul, Turkey',
                'destinations': 'Istanbul, Turkey',
                'key': api_key
            }
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            return data.get('status') == 'OK'
        except:
            return False
    
    def _is_venue_in_istanbul(self, venue_name):
        """Check if venue is actually in Istanbul"""
        if not venue_name:
            return False
        
        venue_lower = venue_name.lower()
        for non_ist in NON_ISTANBUL_VENUES:
            if non_ist in venue_lower:
                return False
        return True
    
    def _parse_turkish_date(self, date_str):
        """
        Parse Turkish date string to datetime
        Examples: "25 Aralık Perşembe", "11 Aralık Perşembe 20:30"
        """
        if not date_str:
            return None
        
        date_lower = date_str.lower()
        
        # Extract day number
        day_match = re.search(r'(\d{1,2})', date_str)
        if not day_match:
            return None
        day = int(day_match.group(1))
        
        # Extract month
        month = None
        for month_name, month_num in TURKISH_MONTHS.items():
            if month_name in date_lower:
                month = month_num
                break
        
        if not month:
            return None
        
        # Assume current year or next year
        year = datetime.now().year
        try:
            parsed_date = datetime(year, month, day)
            # If date is in the past, assume next year
            if parsed_date < datetime.now() - timedelta(days=30):
                parsed_date = datetime(year + 1, month, day)
            return parsed_date
        except ValueError:
            return None
    
    def _extract_date_from_query(self, query):
        """Extract date from user query"""
        query_lower = query.lower()
        
        # Check for "bugün" (today)
        if 'bugün' in query_lower or 'bugun' in query_lower:
            return datetime.now().date()
        
        # Check for "yarın" (tomorrow)
        if 'yarın' in query_lower or 'yarin' in query_lower:
            return (datetime.now() + timedelta(days=1)).date()
        
        # Check for specific date like "25 Aralık" or "25 aralik 2025"
        # Pattern: day + month + optional year
        day_match = re.search(r'(\d{1,2})\s+(\w+)(?:\s+(\d{4}))?', query_lower)
        if day_match:
            day = int(day_match.group(1))
            month_str = day_match.group(2)
            year = int(day_match.group(3)) if day_match.group(3) else datetime.now().year
            
            month = TURKISH_MONTHS.get(month_str)
            if month:
                try:
                    return datetime(year, month, day).date()
                except ValueError:
                    pass
        
        return None
    
    def _filter_by_date(self, plays, target_date):
        """Filter plays that have showtime on target date"""
        if not target_date:
            return plays  # No date filter
        
        filtered = []
        for play in plays:
            showtimes = play.get('showtimes', '') or ''
            
            # Check each showtime
            has_matching_date = False
            matching_showtimes = []
            
            for showtime in showtimes.split('; '):
                parsed = self._parse_turkish_date(showtime)
                if parsed and parsed.date() == target_date:
                    has_matching_date = True
                    matching_showtimes.append(showtime)
            
            if has_matching_date:
                play['matching_showtimes'] = matching_showtimes
                filtered.append(play)
        
        return filtered
    
    def get_plays_in_city(self, city="Istanbul"):
        """Get plays in specific city with venue validation"""
        self.db.cursor.execute('''
            SELECT p.id, title, venue, genre,
                   GROUP_CONCAT(s.show_date || ' ' || s.show_time, '; ') as showtimes,
                   ticket_url
            FROM plays p
            LEFT JOIN showtimes s ON p.id = s.play_id
            WHERE p.city = ?
            GROUP BY p.id
            ORDER BY p.title
        ''', (city,))
        
        plays = self.db.cursor.fetchall()
        
        # Additional venue validation
        validated_plays = []
        for play in plays:
            venue = play[2]  # venue is 3rd column
            if self._is_venue_in_istanbul(venue):
                validated_plays.append(play)
            else:
                print(f"      ⚠️  Skipping {play[1]} - venue '{venue}' not in Istanbul")
        
        return validated_plays
    
    def calculate_distance(self, venue_name):
        """Calculate distance using Google Maps API"""
        if not self.maps_api_available:
            return None, None
        
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        
        try:
            destination = f"{venue_name}, Istanbul, Turkey"
            
            url = "https://maps.googleapis.com/maps/api/distancematrix/json"
            params = {
                'origins': self.user_location,
                'destinations': destination,
                'key': api_key
            }
            
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if data['status'] == 'OK':
                element = data['rows'][0]['elements'][0]
                
                if element['status'] == 'OK':
                    distance_km = element['distance']['value'] / 1000
                    duration_min = element['duration']['value'] / 60
                    
                    # Skip if too far (probably wrong location)
                    if distance_km > 50:
                        return None, None
                    
                    return distance_km, duration_min
            
            return None, None
            
        except Exception as e:
            return None, None
    
    def filter_by_distance(self, plays, max_distance_km=30):
        """Filter plays by distance"""
        filtered_plays = []
        
        print(f"   Checking distances for {len(plays)} venues...")
        
        for play in plays:
            play_id, title, venue, genre, showtimes, ticket_url = play
            
            if not venue:
                continue
            
            distance_km, duration_min = self.calculate_distance(venue)
            
            if distance_km is None:
                # API failed - include anyway for Istanbul venues
                if self._is_venue_in_istanbul(venue):
                    filtered_plays.append({
                        'id': play_id,
                        'title': title,
                        'venue': venue,
                        'genre': genre,
                        'showtimes': showtimes,
                        'ticket_url': ticket_url,
                        'distance_km': None,
                        'duration_min': None
                    })
                    print(f"      ✓ {title} @ {venue} (mesafe bilinmiyor)")
            elif distance_km <= max_distance_km:
                filtered_plays.append({
                    'id': play_id,
                    'title': title,
                    'venue': venue,
                    'genre': genre,
                    'showtimes': showtimes,
                    'ticket_url': ticket_url,
                    'distance_km': round(distance_km, 1),
                    'duration_min': round(duration_min, 0)
                })
                print(f"      ✓ {title}: {distance_km:.1f} km")
            else:
                print(f"      ✗ {title}: {distance_km:.1f} km (çok uzak)")
        
        return filtered_plays
    
    def score_play_with_llm(self, play, user_preference, target_date=None):
        """Score play with LLM - improved prompt"""
        
        # Build context
        distance_info = f"{play['distance_km']} km" if play.get('distance_km') else "Mesafe bilinmiyor"
        
        # Show matching showtimes if available
        if play.get('matching_showtimes'):
            showtime_info = ", ".join(play['matching_showtimes'])
        else:
            showtime_info = play.get('showtimes', 'Tarih bilgisi yok')
        
        date_context = f"Aranan tarih: {target_date}" if target_date else "Tarih belirtilmedi"
        
        prompt = f"""Sen bir tiyatro uzmanısın. Bu oyunun kullanıcının tercihine ne kadar uyduğunu değerlendir.

KULLANICI TERCİHİ: {user_preference}
{date_context}

OYUN BİLGİSİ:
- İsim: {play['title']}
- Tür: {play.get('genre') or 'Belirtilmemiş'}
- Mekan: {play['venue']}
- Mesafe: {distance_info}
- Seanslar: {showtime_info}

Değerlendirme kriterleri:
1. Tarih uyumu (eğer tarih belirtildiyse)
2. Konum uygunluğu
3. Tür/içerik uyumu

SADECE şu formatta yanıt ver:
SCORE: [0-10 arası sayı]
REASONING: [Türkçe 1-2 cümle açıklama]
"""
        
        try:
            response = completion(
                model="gemini/gemini-2.5-flash",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            
            result = response.choices[0].message.content.strip()
            
            score = 5
            reasoning = "Değerlendirme yapıldı"
            
            for line in result.split('\n'):
                if line.startswith('SCORE:'):
                    try:
                        score_str = line.split(':')[1].strip().replace('/10', '')
                        score = float(score_str)
                    except:
                        pass
                elif line.startswith('REASONING:'):
                    reasoning = line.split(':', 1)[1].strip()
            
            return score, reasoning
            
        except Exception as e:
            return 5, "Değerlendirme yapılamadı"
    
    def recommend(self, user_preference, max_distance_km=30, top_n=5):
        """Main recommendation function with date filtering"""
        
        # Extract date from query
        target_date = self._extract_date_from_query(user_preference)
        
        print(f"\n🎭 Öneri aranıyor: '{user_preference}'")
        print(f"📍 Konumunuz: {self.user_location}")
        print(f"🏙️  Şehir: {self.user_city}")
        print(f"🚗 Maksimum mesafe: {max_distance_km} km")
        if target_date:
            print(f"📅 Aranan tarih: {target_date.strftime('%d %B %Y')}")
        print("="*70)
        
        # Step 1: Get plays in city
        print(f"\n1️⃣ {self.user_city} şehrindeki oyunlar getiriliyor...")
        plays = self.get_plays_in_city(self.user_city)
        print(f"   {len(plays)} oyun bulundu")
        
        if not plays:
            print(f"\n❌ {self.user_city} şehrinde oyun bulunamadı")
            return []
        
        # Step 2: Filter by distance
        print(f"\n2️⃣ Mesafe filtresi uygulanıyor ({max_distance_km} km)...")
        nearby_plays = self.filter_by_distance(plays, max_distance_km)
        print(f"\n   ✓ {len(nearby_plays)} oyun mesafe içinde")
        
        if not nearby_plays:
            print(f"\n❌ {max_distance_km} km içinde oyun bulunamadı")
            return []
        
        # Step 3: Filter by date (if specified)
        if target_date:
            print(f"\n3️⃣ Tarih filtresi uygulanıyor ({target_date})...")
            date_filtered = self._filter_by_date(nearby_plays, target_date)
            print(f"   ✓ {len(date_filtered)} oyun bu tarihte mevcut")
            
            if not date_filtered:
                print(f"\n⚠️  {target_date} tarihinde {self.user_city}'da oyun bulunamadı")
                print(f"   Tüm yakın oyunlar gösteriliyor...")
            else:
                nearby_plays = date_filtered
        
        # Step 4: Score with LLM
        print(f"\n4️⃣ Yapay zeka ile değerlendiriliyor...")
        scored_plays = []
        
        for play in nearby_plays[:10]:
            print(f"   Analiz ediliyor: {play['title']}...")
            score, reasoning = self.score_play_with_llm(play, user_preference, target_date)
            
            play['score'] = score
            play['reasoning'] = reasoning
            scored_plays.append(play)
        
        # Step 5: Sort and return
        scored_plays.sort(key=lambda x: x['score'], reverse=True)
        top_plays = scored_plays[:top_n]
        
        print(f"\n✅ {len(top_plays)} öneri hazırlandı")
        print("="*70)
        
        return top_plays
    
    def display_recommendations(self, recommendations):
        """Pretty print recommendations"""
        if not recommendations:
            print("\n😕 Öneri bulunamadı.")
            return
        
        print("\n" + "="*70)
        print("🎭 SİZİN İÇİN ÖNERİLER")
        print("="*70)
        
        for i, play in enumerate(recommendations, 1):
            print(f"\n{i}. {play['title']} ⭐ {play['score']:.1f}/10")
            print(f"   📍 {play['venue']}")
            
            if play.get('distance_km'):
                print(f"   🚗 {play['distance_km']} km (~{play['duration_min']:.0f} dk)")
            
            # Show matching showtimes first, then others
            if play.get('matching_showtimes'):
                print(f"   📅 Seçilen tarih: {', '.join(play['matching_showtimes'])}")
            elif play.get('showtimes'):
                times = play['showtimes'].split('; ')[:3]
                print(f"   📅 Seanslar: {', '.join(times)}")
            
            print(f"   💭 {play['reasoning']}")
            
            if play.get('ticket_url'):
                print(f"   🎫 {play['ticket_url']}")
        
        print("\n" + "="*70 + "\n")
    
    def set_user_location(self, location, city="Istanbul"):
        """Set user location"""
        self.user_location = location
        self.user_city = city
    
    def close(self):
        """Close database"""
        self.db.close()


def demo():
    """Demo function"""
    print("\n" + "="*70)
    print("  STAGEAGENT v2 - İYİLEŞTİRİLMİŞ ÖNERİ MOTORU")
    print("="*70)
    
    recommender = ImprovedPlayRecommender()
    
    # Test with date
    recommendations = recommender.recommend(
        user_preference="25 Aralık 2025 İstanbul tiyatro",
        max_distance_km=15,
        top_n=3
    )
    
    recommender.display_recommendations(recommendations)
    recommender.close()


if __name__ == "__main__":
    demo()