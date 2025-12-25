"""
Database Cleanup - More comprehensive fixes
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "theater_agent.db"

VENUE_TO_CITY = {
    'zorlu psm': 'Istanbul',
    'zorlu': 'Istanbul',
    'moda sahnesi': 'Istanbul',
    'sahne minoa': 'Istanbul',
    'minoa pera': 'Istanbul',
    'satsuma': 'Istanbul',
    'kadıköy': 'Istanbul',
    'beşiktaş': 'Istanbul',
    'beyoğlu': 'Istanbul',
    'dragos': 'Istanbul',
    'sapanca': 'Sakarya',
    'kirkpinar': 'Sakarya',
    'ted ata': 'Ankara',
    'yenimahalle': 'Ankara',
    'nazım hikmet': 'Ankara',
    'çankaya sahne': 'Ankara',
    'ankara çankaya': 'Ankara',
    'trump sahne': 'Ankara',
    'meb şura': 'Ankara',
    'dasdas': 'Ankara',
    'selçuklu': 'Konya',
    'sancaktepe': 'Istanbul',
    'house of performance': 'Istanbul',
}

BAD_VENUE_PATTERNS = [
    'sahnedeki canlı',
    'sahne amiri',
    'sahnenin merkezinde',
    'agatha christie',
    'sahne tasarım',
    'genç bir adam',
    'bize özel',
]

def fix_database():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    print("🔧 Database Cleanup v2")
    print("="*60)
    
    cursor.execute("SELECT id, title, venue, city FROM plays")
    plays = cursor.fetchall()
    
    fixed_city = 0
    fixed_venue = 0
    
    for play_id, title, venue, current_city in plays:
        new_city = current_city
        new_venue = venue
        changes = []
        
        if venue:
            venue_lower = venue.lower()
            
            # Check for bad venue data
            if any(pattern in venue_lower for pattern in BAD_VENUE_PATTERNS):
                new_venue = None
                changes.append(f"venue cleared")
                fixed_venue += 1
            
            # Fix city based on venue
            for keyword, correct_city in VENUE_TO_CITY.items():
                if keyword in venue_lower:
                    if current_city != correct_city:
                        new_city = correct_city
                        changes.append(f"{current_city}→{correct_city}")
                        fixed_city += 1
                    break
        
        if changes:
            print(f"   🔄 {title[:35]}: {', '.join(changes)}")
            cursor.execute(
                "UPDATE plays SET city = ?, venue = ? WHERE id = ?",
                (new_city, new_venue, play_id)
            )
    
    conn.commit()
    
    print(f"\n✅ Fixed {fixed_city} cities, {fixed_venue} venues")
    
    # Show final stats
    cursor.execute("SELECT city, COUNT(*) FROM plays GROUP BY city ORDER BY COUNT(*) DESC")
    print(f"\n📊 Final distribution:")
    for city, count in cursor.fetchall():
        print(f"   {city}: {count}")
    
    cursor.execute("SELECT title, venue FROM plays WHERE city = 'Istanbul'")
    print(f"\n🏙️ Istanbul plays:")
    for title, venue in cursor.fetchall():
        print(f"   • {title[:35]} @ {venue or '?'}")
    
    conn.close()

if __name__ == "__main__":
    fix_database()