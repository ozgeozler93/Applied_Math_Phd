"""
StageAgent - AI Theater Planning Assistant
STAGE 1: Zero-Shot MVP (Most Basic Working Version)

This is the simplest possible version that works!
- Loads mock theater data
- Uses zero-shot prompting to recommend a play
- No fancy features yet
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv
from litellm import completion

# Load environment variables
load_dotenv()

# Check if API key exists
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("❌ ERROR: ANTHROPIC_API_KEY not found in .env file")
    print("Please copy .env.example to .env and add your API key")
    exit(1)

print("✅ API Key loaded successfully\n")


def load_plays():
    """Load mock theater data from JSON file"""
    data_file = Path("data/sample_plays.json")
    
    if not data_file.exists():
        print(f"❌ ERROR: {data_file} not found")
        exit(1)
    
    with open(data_file, 'r', encoding='utf-8') as f:
        plays = json.load(f)
    
    print(f"✅ Loaded {len(plays)} plays from database\n")
    return plays


def format_plays_for_prompt(plays):
    """Format plays into readable text for LLM"""
    plays_text = ""
    for play in plays:
        plays_text += f"""
Play #{play['id']}: {play['title']}
Genre: {play['genre']}
Director: {play['director']}
Venue: {play['venue']} ({play['address']})
Date: {play['date']} at {play['time']}
Description: {play['description']}
---
"""
    return plays_text


def recommend_play_zero_shot(user_query, plays):
    """
    STAGE 1: Zero-Shot Recommendation
    
    Simplest possible approach:
    - Give LLM all plays
    - Ask it to recommend one
    - No examples, no complex reasoning
    """
    
    plays_text = format_plays_for_prompt(plays)
    
    prompt = f"""You are a theater recommendation assistant.

Available plays:
{plays_text}

User request: "{user_query}"

Recommend ONE play that best matches the request.
Keep your response concise and helpful.

Format your response as:
**Recommended Play:** [Title]
**Why:** [Brief explanation]
**Details:** [Venue, date, time]
"""
    
    print("🤖 Asking AI for recommendation...\n")
    
    try:
        response = completion(
            model="claude-3-5-haiku-20241022",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            api_key=ANTHROPIC_API_KEY
        )
        
        recommendation = response.choices[0].message.content
        return recommendation
        
    except Exception as e:
        return f"❌ Error: {str(e)}"


def main():
    """Main function - STAGE 1 MVP"""
    
    print("=" * 60)
    print("🎭 STAGEAGENT - AI THEATER PLANNER")
    print("=" * 60)
    print("STAGE 1: Zero-Shot MVP (Simplest Version)")
    print("=" * 60)
    print()
    
    # Load theater data
    plays = load_plays()
    
    # Example queries to test
    test_queries = [
        "I want to see a Shakespearean tragedy",
        "Something funny for tonight",
        "A play at Şehir Tiyatroları"
    ]
    
    print("📋 Test Queries:\n")
    for i, query in enumerate(test_queries, 1):
        print(f"{i}. {query}")
    print()
    
    # Get user choice
    try:
        choice = input("Choose a query (1-3) or type your own: ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= 3:
            user_query = test_queries[int(choice) - 1]
        else:
            user_query = choice
        
        if not user_query:
            print("❌ No query provided, exiting...")
            return
        
        print(f"\n🎯 Your query: '{user_query}'\n")
        print("-" * 60)
        
        # Get recommendation
        recommendation = recommend_play_zero_shot(user_query, plays)
        
        print("\n📢 RECOMMENDATION:\n")
        print(recommendation)
        print("\n" + "=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()