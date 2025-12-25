"""
Database Inspector - See what's in your database
Run this to check database contents
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "theater_agent.db"

def inspect_database():
    """Show what's in the database"""
    
    if not DB_PATH.exists():
        print(f"❌ Database not found at: {DB_PATH}")
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    print(f"\n{'='*70}")
    print(f"DATABASE INSPECTION")
    print(f"{'='*70}")
    print(f"Location: {DB_PATH}\n")
    
    # 1. PLAYS TABLE
    print(f"📊 PLAYS TABLE:")
    print(f"{'='*70}")
    
    cursor.execute("SELECT id, title, venue FROM plays LIMIT 10")
    plays = cursor.fetchall()
    
    if plays:
        for play_id, title, venue in plays:
            print(f"{play_id:3d}. {title}")
            if venue:
                print(f"     └─ Venue: {venue}")
    else:
        print("  (empty)")
    
    cursor.execute("SELECT COUNT(*) FROM plays")
    total = cursor.fetchone()[0]
    print(f"\nTotal plays: {total}")
    
    # 2. SHOWTIMES TABLE
    print(f"\n{'='*70}")
    print(f"📅 SHOWTIMES TABLE:")
    print(f"{'='*70}")
    
    cursor.execute("""
        SELECT p.title, s.show_date, s.show_time 
        FROM showtimes s
        JOIN plays p ON s.play_id = p.id
        LIMIT 10
    """)
    showtimes = cursor.fetchall()
    
    if showtimes:
        for title, date, time in showtimes:
            print(f"  • {title}: {date} at {time}")
    else:
        print("  (empty)")
    
    cursor.execute("SELECT COUNT(*) FROM showtimes")
    total = cursor.fetchone()[0]
    print(f"\nTotal showtimes: {total}")
    
    # 3. VENUES
    print(f"\n{'='*70}")
    print(f"📍 VENUES:")
    print(f"{'='*70}")
    
    cursor.execute("SELECT DISTINCT venue FROM plays WHERE venue IS NOT NULL")
    venues = cursor.fetchall()
    
    if venues:
        for i, (venue,) in enumerate(venues[:10], 1):
            print(f"{i:2d}. {venue}")
    else:
        print("  (none)")
    
    print(f"\n{'='*70}\n")
    
    conn.close()


def reset_and_reimport():
    """Delete everything and reimport from scratch"""
    import json
    
    if not DB_PATH.exists():
        print("❌ Database doesn't exist yet")
        return
    
    print(f"\n⚠️  WARNING: This will DELETE all data and reimport from scratch")
    confirm = input("Continue? (yes/no): ").strip().lower()
    
    if confirm != "yes":
        print("Cancelled.")
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Delete all data
    print("\n🗑️  Deleting all data...")
    cursor.execute("DELETE FROM showtimes")
    cursor.execute("DELETE FROM plays")
    cursor.execute("DELETE FROM user_ratings")
    cursor.execute("DELETE FROM users")
    conn.commit()
    print("✓ Database cleared")
    
    conn.close()
    
    # Now reimport
    print("\n📥 Reimporting from JSON...")
    from database import import_from_scraper_json
    import_from_scraper_json()


def show_json_sample():
    """Show what's in the JSON file"""
    import json
    from pathlib import Path
    
    json_path = Path(__file__).parent.parent / "theater_scraping_results.json"
    
    if not json_path.exists():
        print(f"❌ JSON file not found at: {json_path}")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n{'='*70}")
    print(f"JSON FILE CONTENTS")
    print(f"{'='*70}")
    print(f"Total plays: {data.get('total_plays', 0)}")
    print(f"Location: {data.get('location', 'N/A')}")
    print(f"\nFirst 3 plays:\n")
    
    for i, play in enumerate(data.get('plays', [])[:3], 1):
        print(f"{i}. {play.get('title', 'N/A')}")
        print(f"   URL: {play.get('url', 'N/A')[:60]}...")
        print(f"   Venues: {play.get('venues', [])}")
        print(f"   Dates: {play.get('dates', [])}")
        print()


if __name__ == "__main__":
    print("\n🔍 Database Inspector\n")
    print("1. Inspect database contents")
    print("2. Show JSON file contents")
    print("3. Reset database and reimport")
    print("4. Exit\n")
    
    choice = input("Choose option (1-4): ").strip()
    
    if choice == "1":
        inspect_database()
    elif choice == "2":
        show_json_sample()
    elif choice == "3":
        reset_and_reimport()
    else:
        print("Bye!")