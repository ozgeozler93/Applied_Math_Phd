"""
FIXED Recommendation Engine
Now properly filters by city and improves distance calculations
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from litellm import completion
import requests
import re

from database import TheaterDatabase

load_dotenv()


class ImprovedPlayRecommender:
    """
    FIXED: Now properly handles Istanbul vs Ankara filtering
    """
    
    def __init__(self):
        self.db = TheaterDatabase()
        self.user_location = "Beşiktaş, Istanbul, Turkey"  # More specific!
        self.user_city = "Istanbul"  # City filter
    
    def get_plays_in_city(self, city="Istanbul"):
        """
        Get plays in specific city only - FIXED to use city column!
        """
        # Query database directly by city
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
        
        city_plays = self.db.cursor.fetchall()
        
        return city_plays
    
    def calculate_distance(self, venue_name):
        """
        IMPROVED: Better distance calculation with city validation
        """
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        
        if not api_key:
            return None, None
        
        try:
            # Make destination more specific
            destination = f"{venue_name}, {self.user_city}, Turkey"
            
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
                    
                    # VALIDATION: If distance > 100km, probably wrong city
                    if distance_km > 100:
                        print(f"      ⚠️  Skipping {venue_name} - too far ({distance_km:.0f} km)")
                        return None, None
                    
                    return distance_km, duration_min
            
            return None, None
            
        except Exception as e:
            print(f"      Distance error for {venue_name}: {e}")
            return None, None
    
    def filter_by_distance(self, plays, max_distance_km=30):
        """
        IMPROVED: Better filtering with validation
        """
        filtered_plays = []
        
        print(f"   Checking distances for {len(plays)} venues...")
        
        for play in plays:
            play_id, title, venue, genre, showtimes, ticket_url = play
            
            if not venue:
                continue
            
            # Calculate distance
            distance_km, duration_min = self.calculate_distance(venue)
            
            if distance_km and distance_km <= max_distance_km:
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
        
        return filtered_plays
    
    def score_play_with_llm(self, play, user_preference):
        """Score play with LLM"""
        prompt = f"""
            You are a theater expert. Score how well this play matches the user's preference.

            USER PREFERENCE: {user_preference}

            PLAY INFORMATION:
            - Title: {play['title']}
            - Genre: {play.get('genre', 'Unknown')}
            - Venue: {play['venue']}
            - Distance: {play['distance_km']} km ({play['duration_min']} min)

            Provide:
            1. A score from 0-10 (10 = perfect match)
            2. Brief reasoning (2-3 sentences)

            Format:
            SCORE: [number]
            REASONING: [text]
            """
        
        try:
            response = completion(
                model="gemini/gemini-2.5-flash",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            
            score = 5
            reasoning = result
            
            if "SCORE:" in result:
                lines = result.split('\n')
                for line in lines:
                    if line.startswith('SCORE:'):
                        try:
                            score = float(line.split(':')[1].strip())
                        except:
                            pass
                    elif line.startswith('REASONING:'):
                        reasoning = line.split(':', 1)[1].strip()
            
            return score, reasoning
            
        except Exception as e:
            print(f"      LLM error: {e}")
            return 5, "Unable to score"
    
    def recommend(self, user_preference, max_distance_km=30, top_n=5):
        """
        FIXED: Now only recommends plays in user's city
        """
        print(f"\n🎭 Finding recommendations for: '{user_preference}'")
        print(f"📍 Your location: {self.user_location}")
        print(f"🏙️  Filtering city: {self.user_city}")
        print(f"🚗 Max distance: {max_distance_km} km")
        print("="*70)
        
        # Step 1: Get plays in user's city ONLY
        print(f"\n1️⃣ Fetching plays in {self.user_city}...")
        plays = self.get_plays_in_city(self.user_city)
        print(f"   Found {len(plays)} plays in {self.user_city}")
        
        if not plays:
            print(f"\n❌ No plays found in {self.user_city}")
            return []
        
        # Step 2: Filter by distance
        print(f"\n2️⃣ Filtering by distance (max {max_distance_km} km)...")
        nearby_plays = self.filter_by_distance(plays, max_distance_km)
        print(f"\n   ✓ {len(nearby_plays)} plays within {max_distance_km} km")
        
        if not nearby_plays:
            print(f"\n❌ No plays found within {max_distance_km} km")
            print(f"   Try increasing max distance or checking other cities")
            return []
        
        # Step 3: Score with LLM
        print(f"\n3️⃣ Scoring plays with AI...")
        scored_plays = []
        
        for play in nearby_plays[:10]:  # Limit to 10 to save API calls
            print(f"   Analyzing: {play['title']}...")
            score, reasoning = self.score_play_with_llm(play, user_preference)
            
            play['score'] = score
            play['reasoning'] = reasoning
            scored_plays.append(play)
        
        # Step 4: Sort and return top N
        scored_plays.sort(key=lambda x: x['score'], reverse=True)
        top_plays = scored_plays[:top_n]
        
        print(f"\n✅ Generated {len(top_plays)} recommendations")
        print("="*70)
        
        return top_plays
    
    def display_recommendations(self, recommendations):
        """Pretty print recommendations"""
        if not recommendations:
            print("\n😕 No recommendations found.")
            print("   Try:")
            print("   - Increasing max_distance_km")
            print("   - Changing your preference")
            print("   - Scraping more plays from different venues")
            return
        
        print("\n" + "="*70)
        print("🎭 YOUR PERSONALIZED RECOMMENDATIONS")
        print("="*70)
        
        for i, play in enumerate(recommendations, 1):
            print(f"\n{i}. {play['title']} ⭐ {play['score']:.1f}/10")
            print(f"   📍 {play['venue']}")
            print(f"   🚗 {play['distance_km']} km away (~{play['duration_min']:.0f} min)")
            
            if play.get('showtimes'):
                times = play['showtimes'].split('; ')[:3]
                print(f"   📅 Showtimes: {', '.join(times)}")
            
            print(f"   💭 Why: {play['reasoning']}")
            
            if play.get('ticket_url'):
                print(f"   🎫 Tickets: {play['ticket_url']}")
        
        print("\n" + "="*70 + "\n")
    
    def set_user_location(self, location, city="Istanbul"):
        """Set user location and city"""
        self.user_location = location
        self.user_city = city
        print(f"✓ Location set to: {location} ({city})")
    
    def close(self):
        """Close database"""
        self.db.close()


def demo():
    """
    FIXED DEMO - Now with proper Istanbul filtering
    """
    print("\n" + "="*70)
    print("  FIXED STAGEAGENT RECOMMENDATION ENGINE")
    print("  Now properly filters by city!")
    print("="*70)
    
    recommender = ImprovedPlayRecommender()
    
    # Set correct location
    recommender.set_user_location("Beşiktaş, Istanbul, Turkey", "Istanbul")
    
    print("\n📝 SCENARIO: Comedy Lover in Beşiktaş")
    print("-" * 70)
    
    recommendations = recommender.recommend(
        user_preference="light comedy, something fun",
        max_distance_km=15,  # 15km radius from Beşiktaş
        top_n=3
    )
    
    recommender.display_recommendations(recommendations)
    
    recommender.close()


if __name__ == "__main__":
    demo()