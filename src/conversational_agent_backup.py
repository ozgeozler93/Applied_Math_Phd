"""
StageAgent - Conversational Theater Recommendation Agent
Natural language interface for finding theater plays
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from litellm import completion
import json

from database import TheaterDatabase
from recommender import ImprovedPlayRecommender

load_dotenv()


class TheaterAgent:
    """
    Conversational agent for theater recommendations
    Features:
    - Natural conversation
    - Context memory
    - Tool calling (database, maps, youtube)
    - Personalization
    """
    
    def __init__(self):
        self.db = TheaterDatabase()
        self.recommender = ImprovedPlayRecommender()
        
        # Conversation history
        self.messages = []
        
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
            - Learn user preferences over time

            You have access to:
            - Database of theater plays in Istanbul and Ankara
            - Google Maps for distance calculation
            - YouTube for trailers/reviews

            Guidelines:
            - Be friendly, enthusiastic, and knowledgeable about theater
            - Ask clarifying questions when needed
            - Provide specific recommendations with reasons
            - Remember user preferences from the conversation
            - Use emojis occasionally to be warm and engaging

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
        Returns: recommend, info, search, preference, general
        """
        prompt = f"""Classify the user's intent into ONE of these categories:
- recommend: User wants play recommendations
- info: User wants information about a specific play
- search: User wants to search for plays by criteria
- preference: User is expressing likes/dislikes
- general: General conversation/greeting

User message: "{message}"

Reply with ONLY one word: recommend, info, search, preference, or general
"""
        
        try:
            response = completion(
                model="gemini/gemini-2.5-flash",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            intent = response.choices[0].message.content.strip().lower()
            
            # Validate intent
            valid_intents = ['recommend', 'info', 'search', 'preference', 'general']
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
    print("="*70)
    print("  Type 'quit' to exit")
    print("="*70 + "\n")
    
    agent = TheaterAgent()
    
    # Sample conversation flow
    print("🎭 Agent: Merhaba! Ben StageAgent, tiyatro asistanınız! 🎭")
    print("         Size İstanbul'daki harika oyunları önermek için buradayım.")
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
    print("  🧪 QUICK TEST - CONVERSATIONAL AGENT")
    print("="*70 + "\n")
    
    agent = TheaterAgent()
    
    test_messages = [
        "Merhaba!",
        "Bu hafta sonu komedi öner",
        "Drakula hakkında bilgi ver",
        "Romantik bir şey istiyorum"
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