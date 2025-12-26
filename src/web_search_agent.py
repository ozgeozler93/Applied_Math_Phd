"""
StageAgent - Web Search Agent (Agent 8)
Uses Tavily API for real-time theater search

Andrew Ng's Agentic AI Patterns:
- Tool Use: Web search as an external tool
- RAG: Retrieval Augmented Generation with live data
"""

import os
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Try to import Tavily
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    print("⚠️  Tavily not installed. Run: pip install tavily-python")


class WebSearchAgent:
    """
    Agent 8: Web Search using Tavily
    
    Capabilities:
    - Search for current theater plays
    - Find showtimes for specific dates
    - Get venue information
    - Search by city
    """
    
    def __init__(self):
        self.api_key = os.getenv('TAVILY_API_KEY')
        self.client = None
        
        if not self.api_key:
            print("❌ TAVILY_API_KEY not found in .env")
            return
        
        if TAVILY_AVAILABLE:
            self.client = TavilyClient(api_key=self.api_key)
            print("✅ Web Search Agent (Tavily) initialized!")
        else:
            print("❌ Tavily library not available")
    
    def is_available(self):
        """Check if web search is available"""
        return self.client is not None
    
    def search_theaters(self, query, city="İstanbul", date=None, max_results=10):
        """
        Search for theater plays
        
        Args:
            query: Search query (e.g., "komedi tiyatro")
            city: City name (default: İstanbul)
            date: Specific date (e.g., "25 Aralık 2025")
            max_results: Maximum results to return
        
        Returns:
            dict with search results
        """
        if not self.client:
            return {"error": "Web search not available", "results": []}
        
        # Build search query
        search_query = f"{city} tiyatro oyunları"
        
        if date:
            search_query = f"{date} {search_query}"
        
        if query and query.lower() not in ["tiyatro", "oyun", "theater"]:
            search_query = f"{query} {search_query}"
        
        print(f"🔍 Web'de aranıyor: '{search_query}'")
        
        try:
            result = self.client.search(
                query=search_query,
                search_depth="advanced",  # More comprehensive search
                max_results=max_results,
                include_domains=[
                    "biletinial.com",
                    "biletix.com",
                    "passo.com.tr",
                    "sehirtiyatrolari.ibb.istanbul",
                    "tiyatronline.com",
                    "mobilet.com",
                    "zorlupsm.com"
                ]
            )
            
            # Process results
            processed_results = self._process_results(result.get('results', []))
            
            return {
                "success": True,
                "query": search_query,
                "results": processed_results,
                "raw_results": result.get('results', [])
            }
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return {"error": str(e), "results": []}
    
    def _process_results(self, raw_results):
        """
        Process and structure search results
        Extract play names, venues, dates from search results
        """
        processed = []
        
        for r in raw_results:
            processed.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", ""),
                "source": self._extract_source(r.get("url", ""))
            })
        
        return processed
    
    def _extract_source(self, url):
        """Extract source name from URL"""
        if "biletinial" in url:
            return "Biletinial"
        elif "biletix" in url:
            return "Biletix"
        elif "sehirtiyatrolari" in url:
            return "İBB Şehir Tiyatroları"
        elif "zorlupsm" in url:
            return "Zorlu PSM"
        elif "passo" in url:
            return "Passo"
        elif "tiyatronline" in url:
            return "Tiyatro Online"
        else:
            return "Web"
    
    def search_specific_play(self, play_name, city="İstanbul"):
        """
        Search for a specific play
        
        Args:
            play_name: Name of the play
            city: City to search in
        
        Returns:
            dict with play information
        """
        if not self.client:
            return {"error": "Web search not available"}
        
        query = f"{play_name} tiyatro {city} bilet seans"
        
        print(f"🔍 Oyun aranıyor: '{play_name}'")
        
        try:
            result = self.client.search(
                query=query,
                search_depth="advanced",
                max_results=5
            )
            
            return {
                "success": True,
                "play_name": play_name,
                "results": result.get('results', [])
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_weekly_plays(self, city="İstanbul"):
        """
        Get this week's plays in a city
        
        Args:
            city: City name
        
        Returns:
            dict with weekly plays
        """
        if not self.client:
            return {"error": "Web search not available"}
        
        # Get current week
        today = datetime.now()
        query = f"{city} bu hafta tiyatro oyunları programı {today.strftime('%B %Y')}"
        
        print(f"🔍 Haftalık program aranıyor: {city}")
        
        try:
            result = self.client.search(
                query=query,
                search_depth="advanced",
                max_results=10,
                include_domains=[
                    "sehirtiyatrolari.ibb.istanbul",
                    "tiyatronline.com",
                    "biletinial.com",
                    "zorlupsm.com"
                ]
            )
            
            return {
                "success": True,
                "city": city,
                "week": f"{today.strftime('%d %B')} haftası",
                "results": result.get('results', [])
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def format_results_for_llm(self, search_results):
        """
        Format search results for LLM consumption
        
        Args:
            search_results: Results from search_theaters()
        
        Returns:
            Formatted string for LLM context
        """
        if not search_results.get('success'):
            return f"Web araması başarısız: {search_results.get('error', 'Bilinmeyen hata')}"
        
        results = search_results.get('results', [])
        
        if not results:
            return "Web'de sonuç bulunamadı."
        
        formatted = f"🌐 Web'den {len(results)} sonuç bulundu:\n\n"
        
        for i, r in enumerate(results, 1):
            formatted += f"**{i}. {r['title']}**\n"
            formatted += f"   Kaynak: {r['source']}\n"
            formatted += f"   {r['content'][:200]}...\n"
            formatted += f"   🔗 {r['url']}\n\n"
        
        return formatted
    
    def format_results_for_user(self, search_results):
        """
        Format search results for user-friendly display
        
        Args:
            search_results: Results from search_theaters()
        
        Returns:
            Formatted string for user
        """
        if not search_results.get('success'):
            return f"❌ Arama başarısız: {search_results.get('error', 'Bilinmeyen hata')}"
        
        results = search_results.get('results', [])
        
        if not results:
            return "😔 Web'de sonuç bulunamadı. Farklı bir arama deneyin."
        
        formatted = f"🌐 **Web'den Güncel Sonuçlar** ({len(results)} sonuç)\n\n"
        
        for i, r in enumerate(results[:5], 1):  # Show top 5
            formatted += f"**{i}. {r['title']}**\n"
            formatted += f"   📍 Kaynak: {r['source']}\n"
            
            # Truncate content nicely
            content = r['content']
            if len(content) > 150:
                content = content[:150] + "..."
            formatted += f"   📝 {content}\n"
            formatted += f"   🔗 [Detaylar]({r['url']})\n\n"
        
        return formatted

    def search_with_preferences(self, city, date, genre=None, origin=None, max_results=10):
        """
        Search with user preferences and filter results
        
        Args:
            city: City name
            date: Date string
            genre: Genre preference (dram, komedi, etc.)
            origin: Origin preference (yerli, yabancı)
            max_results: Max results
        
        Returns:
            Filtered search results
        """
        # Build focused query
        query_parts = []
        
        if genre:
            query_parts.append(genre)
        if origin:
            query_parts.append(origin)
        
        query_parts.extend(["tiyatro", city])
        
        if date:
            query_parts.insert(0, date)
        
        query = " ".join(query_parts)
        
        print(f"🔍 Tercihlerle aranıyor: '{query}'")
        
        return self.search_theaters(
            query=query,
            city=city,
            date=date,
            max_results=max_results
        )


def demo():
    """Demo the web search agent"""
    print("\n" + "="*70)
    print("  🔍 STAGEAGENT - WEB SEARCH AGENT (Tavily)")
    print("  Andrew Ng's Tool Use Pattern")
    print("="*70 + "\n")
    
    agent = WebSearchAgent()
    
    if not agent.is_available():
        print("❌ Web search not available. Check TAVILY_API_KEY.")
        return
    
    # Test 1: Search for plays on a specific date
    print("\n📋 Test 1: 25 Aralık İstanbul tiyatro")
    print("-" * 50)
    results = agent.search_theaters(
        query="tiyatro",
        city="İstanbul",
        date="25 Aralık 2025",
        max_results=5
    )
    print(agent.format_results_for_user(results))
    
    # Test 2: Weekly plays
    print("\n📋 Test 2: Bu hafta İstanbul")
    print("-" * 50)
    results = agent.get_weekly_plays("İstanbul")
    if results.get('success'):
        for r in results.get('results', [])[:3]:
            print(f"  • {r.get('title', 'No title')}")
    
    # Test 3: Specific play search
    print("\n📋 Test 3: Belirli oyun arama")
    print("-" * 50)
    results = agent.search_specific_play("Hamlet", "İstanbul")
    if results.get('success'):
        for r in results.get('results', [])[:2]:
            print(f"  • {r.get('title', 'No title')}")


if __name__ == "__main__":
    demo()