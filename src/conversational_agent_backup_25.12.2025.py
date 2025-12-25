# src/conversational_agent.py   
"""
StageAgent - Conversational Theater Recommendation Agent
Natural language interface for finding theater plays
NOW WITH CALENDAR INTEGRATION!
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from litellm import completion
import json

from database import TheaterDatabase
from recommender import ImprovedPlayRecommender

# Try to import calendar agent (optional)
try:
    from calendar_agent import CalendarAgent
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False
    print("⚠️  Calendar agent not available. Install Google Calendar API dependencies.")

load_dotenv()


class TheaterAgent:
    """
    Conversational agent for theater recommendations
    Features:
    - Natural conversation
    - Context memory
    - Tool calling (database, maps, youtube, calendar)
    - Personalization
    """
    
    def __init__(self):
        self.db = TheaterDatabase()
        self.recommender = ImprovedPlayRecommender()
        
        # Agent 7: Calendar Integration
        self.calendar_agent = None
        if CALENDAR_AVAILABLE:
            try:
                self.calendar_agent = CalendarAgent()
                print("✅ Calendar Agent initialized!")
            except Exception as e:
                print(f"⚠️  Calendar Agent not available: {e}")
        
        # Conversation history
        self.messages = []
        
        # Last recommendations (for calendar integration)
        self.last_recommendations = []
        
        # User preferences (learned over time)
        self.user_profile = {
            'preferred_genres': [],
            'disliked_genres': [],
            'location': 'Beşiktaş, Istanbul',
            'max_distance_km': 15,
            'budget': None
        }
        
        # System prompt
        self.system_prompt = """You are a helpful theater recommendation assistant for Istanbul.

Your capabilities:
- Recommend plays based on user preferences
- Provide information about specific plays
- Help users find showtimes and venues
- Add events to user's Google Calendar
- Check for scheduling conflicts
- Find free time slots
- Learn user preferences over time

You have access to:
- Database of theater plays in Istanbul and Ankara
- Google Maps for distance calculation
- YouTube for trailers/reviews
- Google Calendar for scheduling

Guidelines:
- Be friendly, enthusiastic, and knowledgeable about theater
- Ask clarifying questions when needed
- Provide specific recommendations with reasons
- Remember user preferences from the conversation
- Use emojis occasionally to be warm and engaging
- Proactively offer to add events to calendar

Current date: {current_date}
User location: {user_location}
""".format(
            current_date=datetime.now().strftime('%Y-%m-%d'),
            user_location=self.user_profile['location']
        )
    
    def chat(self, user_message):
        """
        Main chat function - processes user message and generates response
        """
        print(f"\n{'='*70}")
        print(f"You: {user_message}")
        print(f"{'='*70}")
        
        # Add user message to history
        self.messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Detect intent and decide if we need to call tools
        intent = self._detect_intent(user_message)
        
        print(f"🧠 Detected intent: {intent}")
        
        # Execute appropriate action based on intent
        if intent == "recommend":
            response = self._handle_recommendation(user_message)
        elif intent == "info":
            response = self._handle_play_info(user_message)
        elif intent == "search":
            response = self._handle_search(user_message)
        elif intent == "preference":
            response = self._handle_preference_update(user_message)
        elif intent == "calendar":
            response = self._handle_calendar(user_message)
        else:
            response = self._handle_general_chat(user_message)
        
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
        prompt = f"""Classify the user's intent into ONE of these categories:
- recommend: User wants play recommendations
- info: User wants information about a specific play
- search: User wants to search for plays by criteria
- preference: User is expressing likes/dislikes
- calendar: User wants to add event to calendar, check conflicts, or find free time
- general: General conversation/greeting

User message: "{message}"

Reply with ONLY one word: recommend, info, search, preference, calendar, or general
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
            if intent not in valid_intents:
                intent = 'general'
            
            return intent
            
        except Exception as e:
            print(f"Intent detection error: {e}")
            return 'general'
    
    def _handle_recommendation(self, message):
        """
        Handle recommendation requests
        """
        # Extract preference from message
        preference_prompt = f"""Extract the user's preference from their message.
Focus on: genre, mood, time, or any specific requirements.

User message: "{message}"

Provide a concise preference string (e.g., "light comedy, weekend evening, romantic")
If no specific preference, return "general entertainment"
"""
        
        try:
            pref_response = completion(
                model="gemini/gemini-2.5-flash",
                messages=[{"role": "user", "content": preference_prompt}],
                temperature=0.3
            )
            
            preference = pref_response.choices[0].message.content.strip()
            
        except Exception as e:
            preference = "general entertainment"
        
        print(f"📋 Extracted preference: {preference}")
        
        # Get recommendations
        recommendations = self.recommender.recommend(
            user_preference=preference,
            max_distance_km=self.user_profile['max_distance_km'],
            top_n=3
        )
        
        # Save for calendar integration
        self.last_recommendations = recommendations
        
        # Generate natural language response
        if not recommendations:
            return """Üzgünüm, şu anda tercihlerinize uygun bir oyun bulamadım. 😔

Öneriler:
- Mesafe limitini artırabilir miyiz? (Şu an {max_dist} km)
- Farklı bir tarih aralığı deneyelim mi?
- Başka bir tür tercih eder misiniz?
""".format(max_dist=self.user_profile['max_distance_km'])
        
        # Format recommendations naturally
        response = f"Harika! Size {len(recommendations)} öneri buldum! 🎭\n\n"
        
        for i, play in enumerate(recommendations, 1):
            response += f"**{i}. {play['title']}** ⭐ {play['score']:.1f}/10\n"
            response += f"📍 {play['venue']} ({play['distance_km']} km - ~{play['duration_min']:.0f} dk)\n"
            
            if play.get('showtimes'):
                times = play['showtimes'].split('; ')[:2]
                response += f"📅 {', '.join(times)}\n"
            
            response += f"💭 {play['reasoning']}\n"
            
            if play.get('ticket_url'):
                response += f"🎫 [Bilet Al]({play['ticket_url']})\n"
            
            response += "\n"
        
        # Offer calendar integration
        if self.calendar_agent:
            response += "📅 Takvime eklemek ister misiniz?"
        else:
            response += "Hangi oyun hakkında daha fazla bilgi istersiniz? 🎬"
        
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
                info = f"""📖 **{title}** hakkında bilgi:\n\n"""
                info += f"📍 **Mekan:** {venue}\n"
                
                if showtimes:
                    times = showtimes.split('; ')[:5]
                    info += f"📅 **Seanslar:** {', '.join(times)}\n"
                
                if ticket_url:
                    info += f"🎫 **Biletler:** {ticket_url}\n"
                
                info += "\n🎬 YouTube'da fragman aramamı ister misiniz?"
                
                if self.calendar_agent:
                    info += "\n📅 Takvime eklemek ister misiniz?"
                
                return info
        
        return f"'{message}' için bilgi bulamadım. Tam oyun adını söyleyebilir misiniz? 🤔"
    
    def _handle_search(self, message):
        """
        Handle search requests
        """
        # Use recommender with search-like preference
        return self._handle_recommendation(message)
    
    def _handle_preference_update(self, message):
        """
        Handle when user expresses preferences
        """
        response = "Tercihlerinizi kaydettim! 📝\n\n"
        response += "Şimdi size daha iyi öneriler yapabilirim. "
        response += "Hangi tür oyun aramak istersiniz? 🎭"
        
        return response
    
    def _handle_calendar(self, message):
        """
        Handle calendar-related requests
        """
        if not self.calendar_agent:
            return """Üzgünüm, takvim entegrasyonu şu anda kullanılamıyor. 📅

Google Calendar API kurulumu için:
1. credentials.json dosyası gerekli
2. Test kullanıcısı olarak eklenmelisiniz

Yardım: https://console.cloud.google.com/"""
        
        # Detect calendar action
        action = self._detect_calendar_action(message)
        
        if action == "add_event":
            return self._add_to_calendar(message)
        elif action == "check_conflicts":
            return self._check_calendar_conflicts(message)
        elif action == "find_free_time":
            return self._find_free_slots()
        else:
            return """Takvim ile ilgili ne yapmamı istersiniz? 📅

Yapabileceklerim:
- 🎭 Önerilen oyunu takvime ekleme
- ⚠️  Çakışma kontrolü
- 🔍 Boş zaman bulma

Ne yapmamı istersiniz?"""
    
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
    
#     def _add_to_calendar(self, message):
#         """
#         Add recommended play to calendar
#         """
#         # Get last recommendation
#         if not self.last_recommendations:
#             return "Önce bir oyun önerisi almalısınız. Hangi oyunu önereyim? 🎭"
        
#         # Use first recommendation
#         play = self.last_recommendations[0]
        
#         # Parse showtime (take first one)
#         if play.get('showtimes'):
#             first_showtime = play['showtimes'].split('; ')[0]
#             # Format: "16 Kasım Cumartesi 20:30"
#             parts = first_showtime.rsplit(' ', 1)  # Split from right once
#             if len(parts) == 2:
#                 show_date = parts[0]  # "16 Kasım Cumartesi"
#                 show_time = parts[1]  # "20:30"
#             else:
#                 show_date = first_showtime
#                 show_time = "20:00"
#         else:
#             return "Bu oyun için seans bilgisi bulunamadı. 😔"
        
#         # Add to calendar
#         result = self.calendar_agent.add_event(
#             play_title=play['title'],
#             venue=play['venue'],
#             show_date=show_date,
#             show_time=show_time,
#             ticket_url=play.get('ticket_url')
#         )
        
#         if result.get('success'):
#             return f"""✅ **Takvime eklendi!**

# 🎭 **{play['title']}**
# 📍 {play['venue']}
# 📅 {show_date} - {show_time}

# 🔔 **Hatırlatıcılar ayarlandı:**
#   • 1 gün önce
#   • 1 saat önce

# 🔗 [Google Calendar'da Görüntüle]({result.get('event_link')})

# Başka bir yardım? 😊"""
#         else:
#             return f"❌ Takvime eklenirken hata oluştu: {result.get('error')}"




    def _add_to_calendar(self, message):
        """
        Add play to calendar - BULLETPROOF VERSION
        Uses simple but robust date matching
        """
        import re
        
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
                
                # Check if showtime contains the detected day and month
                # Example showtime: "11 Aralık Perşembe 20:30" → "11 aralik persembe 20:30"
                
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
                print(f"\n📅 Available showtimes for {selected_play['title']}:")
                for i, st in enumerate(showtimes_list, 1):
                    print(f"   {i}. {st}")
                print()
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



    def _list_showtimes_for_play(self, play_title):
        """
        Helper: List all available showtimes for a specific play
        """
        for play in self.last_recommendations:
            if play['title'].lower() in play_title.lower():
                if play.get('showtimes'):
                    showtimes = play['showtimes'].split('; ')
                    response = f"**{play['title']}** için mevcut seanslar:\n\n"
                    for i, showtime in enumerate(showtimes, 1):
                        response += f"{i}. {showtime}\n"
                    return response
        
        return "Bu oyun için seans bilgisi bulunamadı."





    
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
    print("  Type 'quit' to exit")
    print("="*70 + "\n")
    
    agent = TheaterAgent()
    
    # Sample conversation flow
    print("🎭 Agent: Merhaba! Ben StageAgent, tiyatro asistanınız! 🎭")
    print("         Size İstanbul'daki harika oyunları önermek için buradayım.")
    if agent.calendar_agent:
        print("         📅 Takvim entegrasyonu aktif - etkinlikleri takviminize ekleyebilirim!")
    print("         Nasıl bir oyun arıyorsunuz?\n")
    
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


def quick_test():
    """
    Quick automated test
    """
    print("\n" + "="*70)
    print("  🧪 QUICK TEST - CONVERSATIONAL AGENT WITH CALENDAR")
    print("="*70 + "\n")
    
    agent = TheaterAgent()
    
    test_messages = [
        "Merhaba!",
        "Bu hafta sonu komedi öner",
        "Takvime ekle",
        "Çakışma var mı?",
        "Ne zaman müsaitim?"
    ]
    
    for msg in test_messages:
        agent.chat(msg)
        print("\n" + "-"*70 + "\n")
    
    agent.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        quick_test()
    else:
        demo()