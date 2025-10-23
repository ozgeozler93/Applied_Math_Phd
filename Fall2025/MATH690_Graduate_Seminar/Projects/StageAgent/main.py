#!/usr/bin/env python3
"""
StageAgent - AI Theater Planning Assistant
STAGE 2: Few-Shot Learning + Rating System

New Features:
- User can rate plays (1-5 stars)
- Rating history stored in SQLite
- Few-shot prompting using past ratings
- Zero-shot still available as option
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv
from litellm import completion
from database import Database

# Load environment variables
load_dotenv()

# Check API key
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("❌ ERROR: ANTHROPIC_API_KEY not found in .env file")
    exit(1)

# Initialize database
db = Database()


def load_plays():
    """Load mock theater data from JSON file"""
    data_file = Path("data/sample_plays.json")
    
    if not data_file.exists():
        print(f"❌ ERROR: {data_file} not found")
        exit(1)
    
    with open(data_file, 'r', encoding='utf-8') as f:
        plays = json.load(f)
    
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


def format_ratings_for_few_shot(ratings):
    """
    Format user ratings as few-shot examples
    
    Args:
        ratings: List of tuples (play_title, rating, review, created_at)
    
    Returns:
        Formatted string for prompt
    """
    if not ratings:
        return "No rating history yet."
    
    examples = ""
    for play_title, rating, review, created_at in ratings:
        examples += f"""
Example:
Play: "{play_title}"
Your Rating: {rating}/5 stars
Your Review: "{review if review else 'No review'}"
---
"""
    return examples


def recommend_play_zero_shot(user_query, plays):
    """
    STAGE 1: Zero-Shot Recommendation
    No examples, just the request
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
    
    print("🤖 Asking AI for recommendation (Zero-Shot)...\n")
    
    try:
        response = completion(
            model="claude-3-5-haiku-20241022",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            api_key=ANTHROPIC_API_KEY
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"❌ Error: {str(e)}"


def recommend_play_few_shot(user_query, plays):
    """
    STAGE 2: Few-Shot Recommendation
    Uses past ratings as examples
    """
    # Get recent ratings
    recent_ratings = db.get_recent_ratings(limit=5)
    
    if not recent_ratings:
        print("⚠️  No rating history found. Using zero-shot instead.\n")
        return recommend_play_zero_shot(user_query, plays)
    
    plays_text = format_plays_for_prompt(plays)
    examples = format_ratings_for_few_shot(recent_ratings)
    
    prompt = f"""You are a personalized theater recommendation assistant.

Here are the user's past ratings:
{examples}

Available plays:
{plays_text}

User request: "{user_query}"

Based on their past preferences, recommend ONE play that they will most likely enjoy.
Consider:
- Genres they liked/disliked
- Similar themes or directors
- Their rating patterns

Format your response as:
**Recommended Play:** [Title]
**Why:** [Explain based on their taste]
**Predicted Rating:** [1-5 stars]
**Details:** [Venue, date, time]
"""
    
    print("🤖 Asking AI for recommendation (Few-Shot with your preferences)...\n")
    
    try:
        response = completion(
            model="claude-3-5-haiku-20241022",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            api_key=ANTHROPIC_API_KEY
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"❌ Error: {str(e)}"


def rate_play(plays):
    """
    Allow user to rate a play they've seen
    """
    print("\n" + "=" * 60)
    print("⭐ RATE A PLAY")
    print("=" * 60)
    
    # Show available plays
    print("\nAvailable plays:\n")
    for i, play in enumerate(plays, 1):
        print(f"{i}. {play['title']} ({play['genre']})")
    
    # Get play selection
    try:
        choice = input("\nWhich play did you see? (1-{}): ".format(len(plays))).strip()
        
        if not choice.isdigit() or not (1 <= int(choice) <= len(plays)):
            print("❌ Invalid choice!")
            return
        
        selected_play = plays[int(choice) - 1]
        
        # Get rating
        rating = input(f"\nRate '{selected_play['title']}' (1-5 stars): ").strip()
        
        if not rating.isdigit() or not (1 <= int(rating) <= 5):
            print("❌ Invalid rating! Must be 1-5.")
            return
        
        # Get optional review
        review = input("Optional review (or press Enter to skip): ").strip()
        
        # Save to database
        success = db.add_rating(
            selected_play['id'],
            selected_play['title'],
            int(rating),
            review if review else None
        )
        
        if success:
            print(f"\n✅ Rating saved! You rated '{selected_play['title']}' {rating}/5 stars.")
        else:
            print("\n❌ Failed to save rating.")
        
    except KeyboardInterrupt:
        print("\n\n❌ Rating cancelled.")
    except Exception as e:
        print(f"\n❌ Error: {e}")


def view_rating_history():
    """
    Display user's rating history
    """
    print("\n" + "=" * 60)
    print("📊 YOUR RATING HISTORY")
    print("=" * 60)
    
    ratings = db.get_all_ratings()
    
    if not ratings:
        print("\n❌ No ratings yet. Watch some plays and rate them!")
        return
    
    print(f"\nTotal ratings: {len(ratings)}\n")
    
    for rating in ratings:
        rating_id, play_id, play_title, stars, review, created_at = rating
        
        print(f"🎭 {play_title}")
        print(f"   Rating: {'⭐' * stars} ({stars}/5)")
        if review:
            print(f"   Review: \"{review}\"")
        print(f"   Date: {created_at}")
        print()
    
    # Show stats
    high_rated = db.get_high_rated_plays(min_rating=4)
    low_rated = db.get_low_rated_plays(max_rating=2)
    
    if high_rated:
        print("\n✨ YOUR FAVORITES (4+ stars):")
        for play_title, stars, review in high_rated:
            print(f"   - {play_title} ({stars}⭐)")
    
    if low_rated:
        print("\n👎 NOT YOUR TASTE (1-2 stars):")
        for play_title, stars, review in low_rated:
            print(f"   - {play_title} ({stars}⭐)")


def show_menu():
    """Display main menu"""
    print("\n" + "=" * 60)
    print("MAIN MENU")
    print("=" * 60)
    print("\n1. Get recommendation (Zero-Shot)")
    print("2. Get recommendation (Few-Shot)")
    print("3. Rate a play")
    print("4. View rating history")
    print("5. Exit")


def main():
    """Main function - STAGE 2"""
    
    print("=" * 60)
    print("🎭 STAGEAGENT - AI THEATER PLANNER")
    print("=" * 60)
    print("STAGE 2: Few-Shot Learning + Rating System")
    print("=" * 60)
    print()
    
    # Load theater data
    plays = load_plays()
    print(f"✅ Loaded {len(plays)} plays from database")
    
    # Main loop
    try:
        while True:
            show_menu()
            
            choice = input("\nYour choice: ").strip()
            
            if choice == "1":
                # Zero-shot recommendation
                print("\n" + "=" * 60)
                user_query = input("What are you looking for? ").strip()
                
                if not user_query:
                    print("❌ No query provided!")
                    continue
                
                print(f"\n🎯 Your query: '{user_query}'\n")
                print("-" * 60)
                
                recommendation = recommend_play_zero_shot(user_query, plays)
                
                print("\n📢 RECOMMENDATION:\n")
                print(recommendation)
                print("\n" + "=" * 60)
            
            elif choice == "2":
                # Few-shot recommendation
                print("\n" + "=" * 60)
                user_query = input("What are you looking for? ").strip()
                
                if not user_query:
                    print("❌ No query provided!")
                    continue
                
                print(f"\n🎯 Your query: '{user_query}'\n")
                print("-" * 60)
                
                recommendation = recommend_play_few_shot(user_query, plays)
                
                print("\n📢 RECOMMENDATION:\n")
                print(recommendation)
                print("\n" + "=" * 60)
            
            elif choice == "3":
                # Rate a play
                rate_play(plays)
            
            elif choice == "4":
                # View history
                view_rating_history()
            
            elif choice == "5":
                # Exit
                print("\n👋 Thank you for using StageAgent!")
                break
            
            else:
                print("❌ Invalid choice! Please enter 1-5.")
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    finally:
        db.close()


if __name__ == "__main__":
    main()