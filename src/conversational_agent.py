# src/conversational_agent.py   
"""
StageAgent - Conversational Theater Recommendation Agent
Natural language interface for finding theater plays
NOW WITH CALENDAR INTEGRATION!

v2.0 - Added:
- City detection from user messages
- Conversation memory (remembers date, city from previous messages)
- Multi-city support (Istanbul, Ankara, Adana, etc.)
"""

import os
import re
import warnings
from datetime import datetime, timedelta
from dotenv import load_dotenv
from litellm import completion
import json

from database import TheaterDatabase
from src.recommender import ImprovedPlayRecommender

# Suppress pydantic warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# Try to import calendar agent (optional)
try:
    from calendar_agent import CalendarAgent
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False
    print("⚠️  Calendar agent not available. Install Google Calendar API dependencies.")



try:
    from web_search_agent import WebSearchAgent 
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False
    print("⚠️  Web Search agent not available. Install Tavily dependencies.")   

load_dotenv()


# ==================== CONVERSATION MEMORY MODULE ====================

# Supported cities with their default locations
SUPPORTED_CITIES = {
    'istanbul': {'name': 'Istanbul', 'location': 'Beşiktaş, Istanbul, Turkey'},
    'ankara': {'name': 'Ankara', 'location': 'Kızılay, Ankara, Turkey'},
    'izmir': {'name': 'İzmir', 'location': 'Konak, İzmir, Turkey'},
    'adana': {'name': 'Adana', 'location': 'Seyhan, Adana, Turkey'},
    'bursa': {'name': 'Bursa', 'location': 'Osmangazi, Bursa, Turkey'},
    'antalya': {'name': 'Antalya', 'location': 'Muratpaşa, Antalya, Turkey'},
    'konya': {'name': 'Konya', 'location': 'Selçuklu, Konya, Turkey'},
    'sakarya': {'name': 'Sakarya', 'location': 'Adapazarı, Sakarya, Turkey'},
}

# Turkish month names for date parsing
TURKISH_MONTHS = {
    'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4,
    'mayıs': 5, 'haziran': 6, 'temmuz': 7, 'ağustos': 8,
    'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12,
    # ASCII versions
    'subat': 2, 'mayis': 5, 'agustos': 8, 'eylul': 9, 'aralik': 12
}


def detect_city_from_message(message):
    """
    Detect city from user message
    Returns: city_name or None
    """
    message_lower = message.lower()
    
    # Normalize Turkish characters
    normalized = message_lower
    replacements = {'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c'}
    for tr_char, ascii_char in replacements.items():
        normalized = normalized.replace(tr_char, ascii_char)
    
    for city_key, city_info in SUPPORTED_CITIES.items():
        if city_key in message_lower or city_key in normalized:
            return city_info['name']
    
    # Check Turkish İstanbul with different i variations
    if 'i̇stanbul' in message_lower or 'İstanbul' in message:
        return 'Istanbul'
    
    return None


def detect_date_from_message(message):
    """
    Detect date from user message
    Returns: dict with 'date_str' and 'date_obj' or None
    """
    message_lower = message.lower()
    
    # Pattern 1: DD.MM.YYYY
    match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', message)
    if match:
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
        try:
            date_obj = datetime(year, month, day)
            return {
                'date_str': f"{day}.{month}.{year}",
                'date_obj': date_obj,
                'display': date_obj.strftime("%d %B %Y")
            }
        except ValueError:
            pass
    
    # Pattern 2: DD Month YYYY (Turkish)
    for month_name, month_num in TURKISH_MONTHS.items():
        pattern = rf'(\d{{1,2}})\s+{month_name}\s*(\d{{4}})?'
        match = re.search(pattern, message_lower)
        if match:
            day = int(match.group(1))
            year = int(match.group(2)) if match.group(2) else datetime.now().year
            try:
                date_obj = datetime(year, month_num, day)
                return {
                    'date_str': f"{day}.{month_num}.{year}",
                    'date_obj': date_obj,
                    'display': f"{day} {month_name.capitalize()} {year}"
                }
            except ValueError:
                pass
    
    # Pattern 3: "bugün", "yarın"
    if 'bugün' in message_lower or 'bugun' in message_lower:
        date_obj = datetime.now()
        return {
            'date_str': date_obj.strftime("%d.%m.%Y"),
            'date_obj': date_obj,
            'display': "Bugün"
        }
    
    if 'yarın' in message_lower or 'yarin' in message_lower:
        date_obj = datetime.now() + timedelta(days=1)
        return {
            'date_str': date_obj.strftime("%d.%m.%Y"),
            'date_obj': date_obj,
            'display': "Yarın"
        }
    
    if 'bu hafta' in message_lower:
        return {
            'date_str': None,
            'date_obj': None,
            'display': "Bu hafta"
        }
    
    return None


def detect_reference_to_previous(message):
    """
    Detect if user is referring to previous context
    Returns: dict with what they're referring to
    """
    message_lower = message.lower()
    
    references = {
        'same_date': False,
        'same_city': False,
    }
    
    # Date references
    date_refs = ['aynı tarih', 'ayni tarih', 'o tarih', 'bu tarih', 
                 'aynı gün', 'ayni gun', 'o gün', 'o gun']
    for ref in date_refs:
        if ref in message_lower:
            references['same_date'] = True
            break
    
    # City references  
    city_refs = ['aynı şehir', 'ayni sehir', 'orada', 'aynı yer', 'ayni yer']
    for ref in city_refs:
        if ref in message_lower:
            references['same_city'] = True
            break
    
    return references


def detect_web_search_intent(message):
    """
    Detect if user wants web search for current info
    Returns: True/False
    """
    message_lower = message.lower()
    
    web_indicators = [
           'güncel', 'guncel', 'şu an', 'su an', 'bugün', 'bugun',
           'bu hafta', 'bu ay', 'yeni', 'son', 'web', 'internet',
            'ara', 'arama', 'bul', 'search', 'gerçek', 'gercek',
            'canlı', 'canli', 'live', 'şimdi', 'simdi',
           'haftalık program', 'bu hafta tiyatro', 'gösterim programı'
    ]
    
    return any(indicator in message_lower for indicator in web_indicators)


class ConversationMemory:
        """
        Enhanced Conversation Memory
        Tracks: city, date, genre, preferences across turns
        Andrew Ng's "Context Preservation" Pattern
        """
    
        GENRES = ['komedi', 'dram', 'müzikal', 'muzikal', 'trajedi', 'stand-up', 
              'standup', 'çocuk', 'cocuk', 'aile', 'romantik', 'gerilim']
    
        ORIGIN_KEYWORDS = {
            'yerli': 'yerli', 'türk': 'yerli', 'turk': 'yerli',
            'yabancı': 'yabancı', 'yabanci': 'yabancı', 'adaptasyon': 'adaptasyon',
        }
        def __init__(self):
            self.city = 'Istanbul'
            self.city_location = 'Beşiktaş, Istanbul, Turkey'
            self.date = None
            self.date_display = None
            self.genre = None
            self.origin = None  # yerli/yabancı
            self.preferences = []
            self.turn_count = 0


        def extract_genre(self, message):
            """Extract genre from message"""
            msg_lower = message.lower()
            for genre in self.GENRES:
                if genre in msg_lower:
                    return genre
            return None

        def extract_origin(self, message):
            """Extract origin (yerli/yabancı) from message"""
            msg_lower = message.lower()
            for keyword, origin in self.ORIGIN_KEYWORDS.items():
                if keyword in msg_lower:
                    return origin
            return None
    
        def update(self, city=None, date_info=None, message=None):    
            """Update memory with new context"""
            self.turn_count += 1
            
            if city:
                self.city = city
                # Update location based on city
                city_key = city.lower()
                if city_key in SUPPORTED_CITIES:
                    self.city_location = SUPPORTED_CITIES[city_key]['location']
            
            if date_info and date_info.get('date_obj'): 
                self.date = date_info.get('date_obj')
                self.date_display = date_info.get('display')
            
            # Extract genre from message
            if message:
                genre = self.extract_genre(message)
                if genre:
                    self.genre = genre
                
                origin = self.extract_origin(message)
                if origin:
                    self.origin = origin


    
        def get_context(self, message):
            """
            Analyze message and return context, filling in from memory if needed
            """
            # Detect new values from message
            new_city = detect_city_from_message(message)
            new_date = detect_date_from_message(message)
            
            # Check for references to previous context
            refs = detect_reference_to_previous(message)
            
            # Use new values if found, otherwise use memory based on references
            city = new_city if new_city else self.city

            # Determine final date
            if new_date:
                date_info = new_date
            elif self.date:
                date_info = {
                    'date_obj': self.date,
                    'display': self.date_display
                }
            else:
                date_info = None
            
            # Get location for city
            city_key = city.lower()
            location = SUPPORTED_CITIES.get(city_key, {}).get('location', self.city_location)

            return {
                'city': city,
                'location': location,
                'date_info': date_info,
                'used_memory_for_date': refs['same_date'] and not new_date,
                'used_memory_for_city': refs['same_city'] and not new_city
            }
    
        def get_preference_string(self):
                """Return a summary of current preferences"""
                parts = []
                if self.genre:
                    parts.append(f"Tür: {self.genre}")
                if self.origin:
                    parts.append(f"Menşei: {self.origin}")
                if self.date_display:
                    parts.append(f"Tarih: {self.date_display}")
                parts.append(f"Şehir: {self.city}")
                return ", ".join(parts) if parts else "Genel eğlence"


        def get_status(self):
            """Return current memory status for debugging"""
            return {
                'city': self.city,
                'date': self.date_display if self.date else None,
                'genre': self.genre,
                'origin': self.origin,
                'turns': self.turn_count
            }


# ==================== MAIN AGENT CLASS ====================

class TheaterAgent:
    """
    Conversational agent for theater recommendations
    
    Agents:
    - Agent 1: Conversation Manager (this class)
    - Agent 2: Intent Classifier
    - Agent 3: Preference Extractor
    - Agent 4: Data Retrieval (Database+ Location)
    - Agent 5: Scoring and Ranking
    - Agent 7: Calendar Integration
    - Agent 8: Web Search (Tavily) --- NEW!

    Features:
    - Natural conversation
    - Context memory (city, date)
    - Multi-city support
    - Tool calling (database, maps, youtube, calendar)
    - Personalization
    """
    
    def __init__(self):
        self.db = TheaterDatabase()
        self.recommender = ImprovedPlayRecommender()
        self.memory = ConversationMemory()

        
        # Agent 7: Calendar Integration
        self.calendar_agent = None
        if CALENDAR_AVAILABLE:
            try:
                self.calendar_agent = CalendarAgent()
                print(" Calendar Agent initialized!")
            except Exception as e:
                print(f" Calendar Agent not available: {e}")
        

        # Agent 8: Web Search Integration
        self.web_search_agent = None
        if WEB_SEARCH_AVAILABLE:
            try:
                self.web_search_agent = WebSearchAgent()
                if self.web_search_agent.is_available():
                    print(" Web Search Agent initialized!")
                else:
                    self.web_search_agent = None
            except Exception as e:
                print(f" Web Search Agent not available: {e}")

        # Conversation history
        self.messages = []
        
        # Last recommendations (for calendar integration)
        self.last_recommendations = []
        
        # User preferences (learned over time)
        self.user_profile = {
            'preferred_genres': [],
            'disliked_genres': [],
            'location': [],
            'city': [],
            'max_distance_km': 15,
            'budget': None
        }
        
        # System prompt
        self.system_prompt = """You are a helpful theater and film festival recommendation assistant for Turkey. 
        You can search the web for current theater information and film festival information using Tavily.
        

Your capabilities:
- Recommend plays based on user preferences
- Support multiple cities (Istanbul, Ankara, Adana, İzmir, Bursa, etc.)
- Provide information about specific plays
- Help users find showtimes and venues
- Add events to user's Google Calendar
- Check for scheduling conflicts
- Find free time slots
- Learn user preferences over time

You have access to:
- Database of theater plays in Turkish cities
- Google Maps for distance calculation
- YouTube for trailers/reviews
- Google Calendar for scheduling

Guidelines:
- Be friendly, enthusiastic, and knowledgeable about theater
- Ask clarifying questions when needed
- Provide specific recommendations with reasons
- Remember user preferences from the conversation
- Remember the city and date from previous messages
- Use emojis occasionally to be warm and engaging
- Proactively offer to add events to calendar

Current date: {current_date}
""".format(current_date=datetime.now().strftime('%Y-%m-%d'))
    
    def chat(self, user_message):
        """
        Main chat function - processes user message and generates response
        """
        print(f"\n{'='*70}")
        print(f"You: {user_message}")
        print(f"{'='*70}")
        
        # Get context from memory - NEW!
        context = self.memory.get_context(user_message)
        
        # Update user profile with context
        self.user_profile['city'] = context['city']
        self.user_profile['location'] = context['location']
        
        # Update recommender with new city/location
        self.recommender.user_city = context['city']
        self.recommender.user_location = context['location']
        
        # Add user message to history
        self.messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Detect intent and decide if we need to call tools
        intent = self._detect_intent(user_message)
        
        print(f" Detected intent: {intent}")

        # Check if user wants web search
        wants_web_search = detect_web_search_intent(user_message)
        if wants_web_search:
            print(f"Web search requested by user.") 

        if context.get('used_memory_for_date'):
            print(f" Using remembered date: {self.memory.last_date_display}")   


        # Execute appropriate action based on intent
        if intent == "recommend":
            response = self._handle_recommendation(user_message, context)
        # Continue web search if previous action was web_search and user is refining
        continue_web = (hasattr(self, 'last_action') and 
                       self.last_action == 'web_search' and 
                       intent in ["search", "recommend"])
        
        if intent == "web_search" or wants_web_search or continue_web:
            response = self._handle_web_search(user_message, context)
            self.last_action = 'web_search' 
        elif intent == "info":
            response = self._handle_play_info(user_message)
        elif intent == "search":
            response = self._handle_recommendation(user_message, context)  # Same as recommend
        elif intent == "preference":
            response = self._handle_preference_update(user_message)
        elif intent == "calendar":
            response = self._handle_calendar(user_message)
        else:
            response = self._handle_general_chat(user_message)
        

    
        # Update memory with this turn's context
        self.memory.update(message=user_message, 
            city=context['city'],
            date_info=context['date_info']
        )
        
        # Add assistant response to history
        self.messages.append({
            "role": "assistant",
            "content": response
        })
        
        print(f"\n🎭 Agent: {response}\n")
        
        return response
    
    def _detect_intent(self, message):
        """
        Detect user intent using LLM
        Returns: recommend, info, search, preference, calendar, general
        """

        message_lower = message.lower()

        if any(word in message_lower for word in ['web', 'internet','guncel ara', 'canli', 'online' ]):
            return 'web_search'
        
        prompt = f"""Classify the user's intent into at least one of these categories:
- recommend: User wants play recommendations
- info: User wants information about a specific play
- search: User wants to search for plays by criteria (date, city, genre)
- preference: User is expressing likes/dislikes
- calendar: User wants to add event to calendar, check conflicts, or find free time
- general: General conversation/greeting

User message: "{message}"

Reply with at least one word: recommend, info, search, preference, calendar, or general
"""
        
        try:
            response = completion(
                model="gemini/gemini-2.5-flash",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            intent = response.choices[0].message.content.strip().lower()
            
            # Validate intent
            valid_intents = ['recommend', 'info', 'search', 'preference', 'calendar', 'general']
            return intent if intent in valid_intents else 'general'            
        except:
            return 'general'
        
    
    def _handle_web_search(self, message, context):
        """
        Handle web search requests using Tavily
        Andrew Ng's Tool Use Pattern in action!
        """
        if not self.web_search_agent:
            return "Üzgünüm, web arama aracı şu anda kullanılamıyor. " \
                   "Alternatif olarak veritabanindaki oyunları önerebilirim. " \
                   "Ne tür bir oyun arıyorsunuz?"""

        city = context.get('city', 'Istanbul')
        date_display = context.get('date_info', {}).get('display') if context.get('date_info') else None

        # Update memory with current message to extract preferences
        self.memory.update(message=message)
        
        # Get preferences from memory
        genre = getattr(self.memory, 'genre', None)
        origin = getattr(self.memory, 'origin', None)
        
        # Build clean search query - don't repeat the full message
        results = self.web_search_agent.search_theaters(
            query="tiyatro oyunları",  # Simple base query
            city=city,
            date=date_display,
            max_results=10)
        

        if not results.get('success'):
            return f" Web araması başarısız: {results.get('error')}"
        web_results = results.get('results', [])

        if not web_results:
            return f""" Web'de **{city}** için sonuç bulunamadı. Farklı bir arama deneyebilirsiniz.
            Ya da veritabanindaki oyunları önerebilirim. Ne tür bir oyun arıyorsunuz?"""

        # Show user what preferences we're using
        pref_info = []
        if genre:
            pref_info.append(f"Tür: {genre}")
        if origin:
            pref_info.append(f"Yapım: {origin}")
        
        response = f"🌐 Web'de **{city}** için güncel sonuçlar\n"

        if date_display:
            response += f"({date_display})"
        response += f"\n\n"


        for i, r in enumerate(web_results[:5], 1): 
            title = r.get("title", "Başlık yok")
            content = r.get("content", " ")[:150]
            url = r.get("url", " ")
            source = r.get("source", "Web ")

            response += f"**{i}. {title}**\n"
            response += f"    Kaynak: {source}\n"
            response += f"    Icerik: {content}...\n"
            response += f"   [Detaylar]({url})\n\n"
        
        response += "---\n"
        response += "Veritabanindaki oyunlari da önerebilirim. Ne tür bir oyun arıyorsunuz?\n\n"

        return response


    def _handle_recommendation(self, message, context):
        """
        Handle recommendation requests - NOW WITH CONTEXT!
        """
        # Build preference string including context
        preference_parts = []
        
        # Extract preference from message
        preference_prompt = f"""Extract the user's theater or festival film preference from their message.
            Focus on: genre, mood, time, or any specific requirements.

            User message: "{message}"

            Provide a short and concise preference description (example: "dram","comedy", "yerli yapım","Istanbul" ).
            If no specific preference, return "general entertainment".
            """
        
        try:
            pref_response = completion(
                model="gemini/gemini-2.5-flash",
                messages=[{"role": "user", "content": preference_prompt}],
                temperature=0.3
            )
            
            preference = pref_response.choices[0].message.content.strip()
            preference_parts.append(preference)
        except:
            preference_parts.append("general entertainment")


        # Add date context if available
        if context.get('date_info'):
            preference_parts.append(context['date_info']['display'])
        
        # Add city context
        preference_parts.append(context['city'])
        
        # Add genre and origin from memory
        if self.memory.genre:
            preference_parts.insert(0, self.memory.genre)
        if self.memory.origin:
            preference_parts.insert(1, self.memory.origin)
        
        full_preference = ", ".join(preference_parts)
        print(f"📋 Extracted preference: {full_preference}")
        
        # Check if we have plays in the requested city
        self.db.cursor.execute("SELECT COUNT(*) FROM plays WHERE city = ?", (context['city'],))
        city_count = self.db.cursor.fetchone()[0]
        
        if city_count == 0:
            # Offer web search as alternative
            if self.web_search_agent:
                return f"""Üzgünüm, şu anda **{context['city']}** şehrinde kayıtlı oyun bulunmuyor. 
                **Web'de arama yapmamı ister misiniz?**
                "Evet, web'de ara" yazın. 
                Veritabanımda mevcut şehirler: 
                Istanbul, 
                Ankara, 
                İzmir,
                Bursa, 
                Konya"""
            else:
                return f""" Uzgünüm, şu anda **{context['city']}** şehrinde kayıtlı oyun bulunmuyor. 
                Veritabanımda mevcut şehirler: Istanbul, Ankara, İzmir, Bursa, Konya"""

        
        # Get recommendations
        recommendations = self.recommender.recommend(
            user_preference=full_preference,
            max_distance_km=self.user_profile['max_distance_km'],
            top_n=3
        )
        
        # Save for calendar integration
        self.last_recommendations = recommendations
        
        # Generate natural language response
        if not recommendations:
            if self.web_search_agent:
                return f"""Üzgünüm, veritabanimda uygun bir oyun bulamadım.

Öneriler:
- Mesafe limitini artırabilir miyiz? (Şu an {self.user_profile['max_distance_km']} km)
- Farklı bir tarih deneyelim mi?
- Başka bir şehir denemek ister misiniz?
"""
        
        # Format recommendations naturally
        city_display = context['city']
        date_display = context.get('date_info', {}).get('display') if context.get('date_info') else None
        
        if date_display:
            response = f"**{city_display}** şehrinde **{date_display}** için {len(recommendations)} öneri buldum! 🎭\n\n"
        else:
            response = f"**{city_display}** şehrinde {len(recommendations)} öneri buldum! 🎭\n\n"
        
        for i, play in enumerate(recommendations, 1):
            response += f"**{i}. {play['title']}** ⭐ {play['score']:.1f}/10\n"
            
            # Handle None distance
            if play.get('distance_km') is not None:
                response += f"📍 {play['venue']} ({play['distance_km']} km - ~{play['duration_min']:.0f} dk)\n"
            else:
                response += f"📍 {play['venue']}\n"
            
            if play.get('showtimes'):
                times = play['showtimes'].split('; ')[:2]
                response += f"📅 {', '.join(times)}\n"
            
            response += f"💭 {play['reasoning']}\n"
            
            if play.get('ticket_url'):
                response += f"🎫 [Bilet Al]({play['ticket_url']})\n"
            
            response += "\n"
        
        options = []
        # Offer calendar integration
        if self.calendar_agent:
            options.append("Takvime ekle")
        if self.web_search_agent:
            options.append("Web'de daha fazla ara")
        
        if options:
            response += " | ".join(options)
        
        return response
    
    def _handle_play_info(self, message):
        """
        Handle requests for information about specific plays
        """
        # Extract play name from message
        plays = self.db.get_all_plays()
        
        # Simple keyword matching (can be improved with LLM)
        message_lower = message.lower()
        
        for play in plays:
            play_id, title, venue, genre, showtimes, ticket_url = play
            
            if title.lower() in message_lower or any(word in message_lower for word in title.lower().split()[:3]):
                info = f""" **{title}** hakkında bilgi:\n\n"""
                info += f" **Mekan:** {venue}\n"
                
                if showtimes:
                    times = showtimes.split('; ')[:5]
                    info += f" **Seanslar:** {', '.join(times)}\n"
                
                if ticket_url:
                    info += f" **Biletler:** {ticket_url}\n"
                
                info += "\n YouTube'da fragman aramamı ister misiniz?"
                
                if self.calendar_agent:
                    info += "\n Takvime eklemek ister misiniz?"
                
                return info
        
        return f"'{message}' için bilgi bulamadım. Tam oyun adını söyleyebilir misiniz? 🤔"
    
    def _handle_preference_update(self, message):
        """
        Handle when user expresses preferences
        """
        response = "Tercihlerinizi kaydettim! \n\n"
        response += "Şimdi size daha iyi öneriler yapabilirim. "
        response += "Hangi tür oyun aramak istersiniz? "
        
        return response
    
    def _handle_calendar(self, message):
        """
        Handle calendar-related requests
        """
        if not self.calendar_agent:
            return """Üzgünüm, takvim entegrasyonu şu anda kullanılamıyor. 

                Google Calendar API kurulumu için:
                1. credentials.json dosyası gerekli
                2. Test kullanıcısı olarak eklenmelisiniz

                Yardım: https://console.cloud.google.com/"""
        
        if not self.last_recommendations:
            return "Önce bir oyun önerisi almalısınız. Hangi oyunu önereyim? "
        

        # Use first recommendation as default
        play = self.last_recommendations[0]

        if play.get('showtimes'):
            showtime = play['showtimes'].split('; ')
            parts = showtime.rsplit(' ',1)
            show_date = parts[0] if len(parts) ==2 else showtime
            show_time = parts[1] if len(parts) ==2 else "20:00"
        else:
            return "Bu oyun icin seans bilgisi yok. Takvime ekleyemem. "
        
        result= self.calendar_agent.add_event(
            play_title=play['title'],
            venue=play['venue'],
            show_date=show_date,
            show_time=show_time,
            ticket_url=play.get('ticket_url')
        )
        if result.get('success'):
            return f""" **{play['title']}** oyunu takviminize eklendi! 
                            {play['venue']}
                            {show_date} - {show_time}
                            [Calender'da Gör]({result.get('event_link')})"""
        return f"Hata: Takvime ekleme başarısız oldu: {result.get('error')}"


    
    def _detect_calendar_action(self, message):
        """
        Detect what calendar action user wants
        """
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['ekle', 'takvim', 'calendar', 'kaydet', 'add']):
            return 'add_event'
        elif any(word in message_lower for word in ['çakış', 'müsait', 'conflict', 'busy', 'meşgul']):
            return 'check_conflicts'
        elif any(word in message_lower for word in ['boş', 'serbest', 'free', 'ne zaman']):
            return 'find_free_time'
        else:
            return 'unknown'
    
    def _add_to_calendar(self, message):
        """
        Add play to calendar - BULLETPROOF VERSION
        Uses simple but robust date matching
        """
        def normalize_text(text):
            """Remove Turkish characters and normalize"""
            text = text.lower()
            replacements = {
                'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c',
                'İ': 'i', 'Ğ': 'g', 'Ü': 'u', 'Ş': 's', 'Ö': 'o', 'Ç': 'c'
            }
            for tr_char, ascii_char in replacements.items():
                text = text.replace(tr_char, ascii_char)
            return text
        
        # Get last recommendations
        if not self.last_recommendations:
            return "Önce bir oyun önerisi almalısınız. Hangi oyunu önereyim? 🎭"
        
        # ==================== STEP 1: DETECT PLAY ====================
        selected_play = None
        message_normalized = normalize_text(message)
        
        print(f"🔍 Searching for play...")
        
        for play in self.last_recommendations:
            play_title_normalized = normalize_text(play['title'])
            
            # Count matching words (3+ chars)
            title_words = [w for w in play_title_normalized.split() if len(w) >= 3]
            matches = sum(1 for word in title_words if word in message_normalized)
            
            if matches >= 2 or play_title_normalized in message_normalized:
                selected_play = play
                print(f"✓ Detected play: {play['title']}")
                break
        
        if not selected_play:
            selected_play = self.last_recommendations[0]
            print(f"⚠️  Using first recommendation: {selected_play['title']}")
        
        # ==================== STEP 2: DETECT DATE ====================
        selected_showtime = None
        
        # Month patterns (both Turkish and ASCII)
        month_patterns = {
            'ocak': ['ocak'],
            'subat': ['subat', 'şubat'],
            'mart': ['mart'],
            'nisan': ['nisan'],
            'mayis': ['mayis', 'mayıs'],
            'haziran': ['haziran'],
            'temmuz': ['temmuz'],
            'agustos': ['agustos', 'ağustos'],
            'eylul': ['eylul', 'eylül'],
            'ekim': ['ekim'],
            'kasim': ['kasim', 'kasım'],
            'aralik': ['aralik', 'aralık']
        }
        
        print(f"🔍 Searching for date...")
        
        # Extract day and month from user message
        detected_day = None
        detected_month_key = None
        
        # Try each month
        for month_key, month_variations in month_patterns.items():
            for month_var in month_variations:
                # Look for pattern: "number month" with flexible spacing
                pattern = r'(\d{1,2})\s+' + month_var
                match = re.search(pattern, message.lower())
                if match:
                    detected_day = int(match.group(1))
                    detected_month_key = month_key
                    print(f"✓ Detected date: {detected_day} {month_var}")
                    break
            if detected_day:
                break
        
        # ==================== STEP 3: MATCH SHOWTIME ====================
        if detected_day and detected_month_key and selected_play.get('showtimes'):
            print(f"🔍 Matching against showtimes...")
            
            showtimes = selected_play['showtimes'].split('; ')
            
            for showtime in showtimes:
                showtime_normalized = normalize_text(showtime)
                
                # Extract day from showtime (first number)
                showtime_day_match = re.match(r'(\d{1,2})', showtime_normalized)
                if showtime_day_match:
                    showtime_day = int(showtime_day_match.group(1))
                    
                    # Check if day matches
                    if showtime_day == detected_day:
                        # Check if month matches
                        if detected_month_key in showtime_normalized:
                            selected_showtime = showtime
                            print(f"✅ MATCHED showtime: {showtime}")
                            break
        
        # ==================== STEP 4: FALLBACK ====================
        if not selected_showtime:
            if selected_play.get('showtimes'):
                showtimes_list = selected_play['showtimes'].split('; ')
                selected_showtime = showtimes_list[0]
                
                print(f"❌ Could not match '{detected_day if detected_day else '?'} {detected_month_key if detected_month_key else '?'}'")
                print(f"⚠️  Using first available showtime: {selected_showtime}")
            else:
                return "Bu oyun için seans bilgisi bulunamadı. 😔"
        
        # ==================== STEP 5: PARSE & ADD ====================
        # Parse showtime: "11 Aralık Perşembe 20:30"
        parts = selected_showtime.rsplit(' ', 1)
        if len(parts) == 2:
            show_date = parts[0]  # "11 Aralık Perşembe"
            show_time = parts[1]  # "20:30"
        else:
            show_date = selected_showtime
            show_time = "20:00"
        
        print(f"➡️  Adding to calendar:")
        print(f"   Play: {selected_play['title']}")
        print(f"   Date: {show_date}")
        print(f"   Time: {show_time}\n")
        
        # Add to calendar
        result = self.calendar_agent.add_event(
            play_title=selected_play['title'],
            venue=selected_play['venue'],
            show_date=show_date,
            show_time=show_time,
            ticket_url=selected_play.get('ticket_url')
        )
        
        if result.get('success'):
            return f"""✅ **Takvime eklendi!**

🎭 **{selected_play['title']}**
📍 {selected_play['venue']}
📅 {show_date} - {show_time}

🔔 **Hatırlatıcılar ayarlandı:**
• 1 gün önce
• 1 saat önce

🔗 [Google Calendar'da Görüntüle]({result.get('event_link')})

Başka bir yardım? 😊"""
        else:
            return f"❌ Takvime eklenirken hata oluştu: {result.get('error')}"
    
    def _check_calendar_conflicts(self, message):
        """
        Check if user has conflicts for recommended plays
        """
        if not self.last_recommendations:
            return "Önce bir oyun önerisi almalısınız. 🎭"
        
        conflicts_found = []
        
        for play in self.last_recommendations[:3]:  # Check top 3
            if play.get('showtimes'):
                first_showtime = play['showtimes'].split('; ')[0]
                parts = first_showtime.rsplit(' ', 1)
                
                if len(parts) == 2:
                    show_date = parts[0]
                    show_time = parts[1]
                    
                    result = self.calendar_agent.check_conflicts(show_date, show_time)
                    
                    if result.get('has_conflict'):
                        conflicts_found.append({
                            'play': play['title'],
                            'date': show_date,
                            'time': show_time,
                            'conflicts': result.get('conflicts', [])
                        })
        
        if not conflicts_found:
            return "✅ **Önerilen oyunların hepsi için takvimde çakışma yok!**\n\nMüsaitsiniz! 🎉"
        else:
            response = "⚠️  **Bazı oyunlar için takvimde çakışma var:**\n\n"
            for conflict in conflicts_found:
                response += f"🎭 **{conflict['play']}**\n"
                response += f"📅 {conflict['date']} {conflict['time']}\n"
                response += f"❌ **Çakışan etkinlikler:**\n"
                for event in conflict['conflicts'][:2]:
                    response += f"   • {event['title']}\n"
                response += "\n"
            
            response += "Başka tarihler önerebilirim! 📅"
            return response
    
    def _find_free_slots(self):
        """
        Find free time slots for theater
        """
        result = self.calendar_agent.find_free_slots(datetime.now(), days=7)
        
        if result.get('error'):
            return f"❌ Hata: {result['error']}"
        
        free_slots = result.get('free_slots', [])
        
        if not free_slots:
            return "Önümüzdeki 7 gün içinde akşam saatlerinde boş slot bulunamadı. 😔"
        
        response = f"✅ **Önümüzdeki 7 günde {len(free_slots)} boş akşam slotu bulundu:**\n\n"
        
        for slot in free_slots[:10]:  # Show first 10
            response += f"📅 {slot['date']} ({slot['day_name']}) - {slot['time']}\n"
        
        response += "\n🎭 Bu saatler için oyun önerisi istiyorsanız söyleyin!"
        
        return response
    
    def _handle_general_chat(self, message):
        """
        Handle general conversation
        """
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.messages
        
        try:
            response = completion(
                model="gemini/gemini-2.5-flash",
                messages=messages,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return "Özür dilerim, bir hata oluştu. Lütfen tekrar dener misiniz? 🙏"
    
    def close(self):
        """Clean up"""
        self.db.close()


def demo():
    """
    Interactive demo of the conversational agent
    """
    print("\n" + "="*70)
    print("  🎭 STAGEAGENT - CONVERSATIONAL THEATER ASSISTANT")
    print("  NOW WITH CALENDAR INTEGRATION! 📅")
    print("="*70)
    print("  Type '\\quit' to exit")
    print("="*70 + "\n")
    
    agent = TheaterAgent()
    
    # Sample conversation flow
    print("🎭 Agent: Merhaba! Ben StageAgent, tiyatro ve film festivali asistanınız! 🎭")
    print("         Size Türkiye'deki harika oyunları ve festival filmlerini önermek için buradayım.")
    print("         🏙️  (Simdilik) Desteklenen şehirler: İstanbul, Ankara, İzmir, Adana, Bursa...")
    if agent.calendar_agent:
        print("         📅 Takvim entegrasyonu aktif - etkinlikleri takviminize ekleyebilirim!")
    print("         Nasıl bir oyun ya da festival filmi arıyorsunuz?\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'bye', 'çıkış']:
                print("\n🎭 Agent: Görüşmek üzere! İyi seyirler! 🎬\n")
                break
            
            agent.chat(user_input)
            
        except KeyboardInterrupt:
            print("\n\n🎭 Agent: Görüşmek üzere! İyi seyirler! 🎬\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
    
    agent.close()


if __name__ == "__main__":
    import sys
    
    # if len(sys.argv) > 1 and sys.argv[1] == "--test":
    #     # Quick test
    #     agent = TheaterAgent()
    #     agent.chat("25.12.2025 tarihinde İstanbul'da hangi oyunlar var?")
    #     agent.chat("Aynı tarih için Adana'da hangi oyunlar var?")
    #     agent.close()
    # else:
    #     demo()

    demo()
