# # -------------------------------1------------------------------

# """
# StageAgent - Database Module
# SQLite database for storing theater plays, showtimes, and user preferences
# Location: src/database.py
# """

# import sqlite3
# import json
# from datetime import datetime
# from pathlib import Path

# # Database will be stored in data/ folder
# DB_PATH = Path(__file__).parent.parent / "data" / "theater_agent.db"

# class TheaterDatabase:
#     def __init__(self, db_path=None):
#         """Initialize database connection"""
#         self.db_path = db_path or DB_PATH
        
#         # Ensure data directory exists
#         self.db_path.parent.mkdir(exist_ok=True)
        
#         self.conn = sqlite3.connect(str(self.db_path))
#         self.cursor = self.conn.cursor()
#         self.create_tables()
    
#     def create_tables(self):
#         """Create necessary tables if they don't exist"""
        
#         # PLAYS TABLE
#         self.cursor.execute('''
#             CREATE TABLE IF NOT EXISTS plays (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 title TEXT NOT NULL,
#                 venue TEXT,
#                 city TEXT DEFAULT 'Istanbul',
#                 genre TEXT,
#                 description TEXT,
#                 duration_minutes INTEGER,
#                 language TEXT DEFAULT 'Turkish',
#                 image_url TEXT,
#                 ticket_url TEXT,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 UNIQUE(title, venue)
#             )
#         ''')
        
#         # SHOWTIMES TABLE
#         self.cursor.execute('''
#             CREATE TABLE IF NOT EXISTS showtimes (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 play_id INTEGER NOT NULL,
#                 show_date TEXT NOT NULL,
#                 show_time TEXT NOT NULL,
#                 price REAL,
#                 available_seats INTEGER,
#                 FOREIGN KEY (play_id) REFERENCES plays(id),
#                 UNIQUE(play_id, show_date, show_time)
#             )
#         ''')
        
#         # USERS TABLE
#         self.cursor.execute('''
#             CREATE TABLE IF NOT EXISTS users (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 user_id TEXT UNIQUE NOT NULL,
#                 name TEXT,
#                 email TEXT,
#                 preferred_genres TEXT,
#                 max_distance_km INTEGER DEFAULT 30,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
        
#         # USER_RATINGS TABLE
#         self.cursor.execute('''
#             CREATE TABLE IF NOT EXISTS user_ratings (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 user_id TEXT NOT NULL,
#                 play_id INTEGER NOT NULL,
#                 rating INTEGER CHECK(rating >= 1 AND rating <= 5),
#                 attended BOOLEAN DEFAULT 0,
#                 review_text TEXT,
#                 rated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 FOREIGN KEY (play_id) REFERENCES plays(id)
#             )
#         ''')
        
#         self.conn.commit()
#         print(f"✓ Database initialized: {self.db_path}")
    
#     def add_play(self, title, venue=None, genre=None, description=None, 
#                  image_url=None, ticket_url=None):
#         """Add a new play to the database (or update if exists)"""
#         try:
#             self.cursor.execute('''
#                 INSERT OR REPLACE INTO plays 
#                 (title, venue, genre, description, image_url, ticket_url, updated_at)
#                 VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
#             ''', (title, venue, genre, description, image_url, ticket_url))
            
#             self.conn.commit()
            
#             # Get the play_id
#             self.cursor.execute('''
#                 SELECT id FROM plays WHERE title = ? AND venue = ?
#             ''', (title, venue))
            
#             result = self.cursor.fetchone()
#             return result[0] if result else None
            
#         except Exception as e:
#             print(f"❌ Error adding play '{title}': {e}")
#             return None
    
#     def add_showtime(self, play_id, show_date, show_time, price=None):
#         """Add a showtime for a play"""
#         try:
#             self.cursor.execute('''
#                 INSERT OR IGNORE INTO showtimes 
#                 (play_id, show_date, show_time, price)
#                 VALUES (?, ?, ?, ?)
#             ''', (play_id, show_date, show_time, price))
            
#             self.conn.commit()
#             return self.cursor.lastrowid
            
#         except Exception as e:
#             print(f"❌ Error adding showtime: {e}")
#             return None
    
#     def get_all_plays(self):
#         """Get all plays with their showtimes"""
#         self.cursor.execute('''
#             SELECT 
#                 p.id, p.title, p.venue, p.genre,
#                 GROUP_CONCAT(s.show_date || ' ' || s.show_time, '; ') as showtimes,
#                 p.ticket_url
#             FROM plays p
#             LEFT JOIN showtimes s ON p.id = s.play_id
#             GROUP BY p.id
#             ORDER BY p.title
#         ''')
        
#         return self.cursor.fetchall()
    
#     def get_plays_by_date_range(self, start_date, end_date):
#         """Get plays showing between two dates"""
#         self.cursor.execute('''
#             SELECT DISTINCT 
#                 p.id, p.title, p.venue, p.genre,
#                 s.show_date, s.show_time, s.price
#             FROM plays p
#             JOIN showtimes s ON p.id = s.play_id
#             WHERE s.show_date BETWEEN ? AND ?
#             ORDER BY s.show_date, s.show_time
#         ''', (start_date, end_date))
        
#         return self.cursor.fetchall()
    
#     def search_plays(self, keyword):
#         """Search plays by title or venue"""
#         self.cursor.execute('''
#             SELECT id, title, venue, genre, ticket_url
#             FROM plays
#             WHERE title LIKE ? OR venue LIKE ?
#             ORDER BY title
#         ''', (f'%{keyword}%', f'%{keyword}%'))
        
#         return self.cursor.fetchall()
    
#     def get_database_stats(self):
#         """Get database statistics"""
#         stats = {}
        
#         # Total plays
#         self.cursor.execute('SELECT COUNT(*) FROM plays')
#         stats['total_plays'] = self.cursor.fetchone()[0]
        
#         # Total showtimes
#         self.cursor.execute('SELECT COUNT(*) FROM showtimes')
#         stats['total_showtimes'] = self.cursor.fetchone()[0]
        
#         # Unique venues
#         self.cursor.execute('SELECT COUNT(DISTINCT venue) FROM plays WHERE venue IS NOT NULL')
#         stats['unique_venues'] = self.cursor.fetchone()[0]
        
#         return stats
    
#     def close(self):
#         """Close database connection"""
#         self.conn.close()


# def import_from_scraper_json(json_file='theater_scraping_results.json'):
#     """
#     Import scraped data from JSON into database
#     This is the bridge between your scraper and database
#     """
#     import re
#     from pathlib import Path
    
#     # Find the JSON file
#     json_path = Path(json_file)
#     if not json_path.exists():
#         # Try in parent directory
#         json_path = Path.cwd() / json_file
    
#     if not json_path.exists():
#         print(f"❌ Could not find {json_file}")
#         return
    
#     # Load JSON data
#     with open(json_path, 'r', encoding='utf-8') as f:
#         data = json.load(f)
    
#     print(f"\n{'='*60}")
#     print(f"IMPORTING DATA FROM SCRAPER")
#     print(f"{'='*60}")
#     print(f"Source: {json_path}")
#     print(f"Total plays to import: {data.get('total_plays', 0)}")
#     print(f"{'='*60}\n")
    
#     # Initialize database
#     db = TheaterDatabase()
    
#     imported_count = 0
#     skipped_count = 0
    
#     for play_data in data.get('plays', []):
#         title = play_data.get('title', '').strip()
        
#         if not title or len(title) < 3:
#             skipped_count += 1
#             continue
        
#         # Get venue (first one if multiple)
#         venues = play_data.get('venues', [])
#         venue = venues[0] if venues else None
        
#         # Add play to database
#         play_id = db.add_play(
#             title=title,
#             venue=venue,
#             image_url=play_data.get('image', ''),
#             ticket_url=play_data.get('url', '')
#         )
        
#         if play_id:
#             # Add showtimes
#             dates = play_data.get('dates', [])
#             for date_str in dates:
#                 try:
#                     # Simple date parsing (you'll improve this)
#                     # Format: "15 Kasım Cumartesi, 15:00"
#                     date_parts = date_str.split(',')
#                     if len(date_parts) >= 2:
#                         show_date = date_parts[0].strip()  # "15 Kasım Cumartesi"
#                         show_time = date_parts[1].strip()  # "15:00"
                        
#                         db.add_showtime(
#                             play_id=play_id,
#                             show_date=show_date,
#                             show_time=show_time
#                         )
#                 except Exception as e:
#                     pass  # Skip invalid dates
            
#             imported_count += 1
#             print(f"✓ [{imported_count}] {title}")
#             if venue:
#                 print(f"  └─ Venue: {venue}")
#             if dates:
#                 print(f"  └─ Showtimes: {len(dates)}")
    
#     print(f"\n{'='*60}")
#     print(f"IMPORT COMPLETE")
#     print(f"{'='*60}")
#     print(f"✓ Imported: {imported_count} plays")
#     print(f"⊘ Skipped: {skipped_count} invalid entries")
    
#     # Show database stats
#     stats = db.get_database_stats()
#     print(f"\n📊 DATABASE STATS:")
#     print(f"  • Total plays: {stats['total_plays']}")
#     print(f"  • Total showtimes: {stats['total_showtimes']}")
#     print(f"  • Unique venues: {stats['unique_venues']}")
#     print(f"{'='*60}\n")
    
#     db.close()


# if __name__ == "__main__":
#     print("\n🎭 StageAgent Database Setup\n")
    
#     # Option 1: Just create empty database
#     print("Option 1: Create empty database")
#     print("Option 2: Import from scraper JSON\n")
    
#     choice = input("Enter choice (1 or 2): ").strip()
    
#     if choice == "2":
#         import_from_scraper_json()
#     else:
#         db = TheaterDatabase()
#         stats = db.get_database_stats()
#         print(f"\n✓ Database created at: {db.db_path}")
#         print(f"  • Plays: {stats['total_plays']}")
#         print(f"  • Showtimes: {stats['total_showtimes']}")
#         db.close()



        # -------------------------------2------------------------------


"""
StageAgent - Database Module
SQLite database for storing theater plays, showtimes, and user preferences
Location: src/database.py
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

# Database will be stored in data/ folder
DB_PATH = Path(__file__).parent.parent / "data" / "theater_agent.db"

class TheaterDatabase:
    def __init__(self, db_path=None):
        """Initialize database connection"""
        self.db_path = db_path or DB_PATH
        
        # Ensure data directory exists
        self.db_path.parent.mkdir(exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path))
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        """Create necessary tables if they don't exist"""
        
        # PLAYS TABLE
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS plays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                venue TEXT,
                city TEXT DEFAULT 'Istanbul',
                genre TEXT,
                description TEXT,
                duration_minutes INTEGER,
                language TEXT DEFAULT 'Turkish',
                image_url TEXT,
                ticket_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(title, venue)
            )
        ''')
        
        # SHOWTIMES TABLE
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS showtimes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                play_id INTEGER NOT NULL,
                show_date TEXT NOT NULL,
                show_time TEXT NOT NULL,
                price REAL,
                available_seats INTEGER,
                FOREIGN KEY (play_id) REFERENCES plays(id),
                UNIQUE(play_id, show_date, show_time)
            )
        ''')
        
        # USERS TABLE
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                name TEXT,
                email TEXT,
                preferred_genres TEXT,
                max_distance_km INTEGER DEFAULT 30,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # USER_RATINGS TABLE
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                play_id INTEGER NOT NULL,
                rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                attended BOOLEAN DEFAULT 0,
                review_text TEXT,
                rated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (play_id) REFERENCES plays(id)
            )
        ''')
        
        self.conn.commit()
        print(f"✓ Database initialized: {self.db_path}")
    
    def add_play(self, title, venue=None, city='Istanbul', genre=None, description=None, 
                 image_url=None, ticket_url=None):
        """Add a new play to the database (or update if exists)"""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO plays 
                (title, venue, city, genre, description, image_url, ticket_url, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (title, venue, city, genre, description, image_url, ticket_url))
            
            self.conn.commit()
            
            # Get the play_id
            self.cursor.execute('''
                SELECT id FROM plays WHERE title = ? AND venue = ?
            ''', (title, venue))
            
            result = self.cursor.fetchone()
            return result[0] if result else None
            
        except Exception as e:
            print(f"❌ Error adding play '{title}': {e}")
            return None
    
    def add_showtime(self, play_id, show_date, show_time, price=None):
        """Add a showtime for a play"""
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO showtimes 
                (play_id, show_date, show_time, price)
                VALUES (?, ?, ?, ?)
            ''', (play_id, show_date, show_time, price))
            
            self.conn.commit()
            return self.cursor.lastrowid
            
        except Exception as e:
            print(f"❌ Error adding showtime: {e}")
            return None
    
    def get_all_plays(self):
        """Get all plays with their showtimes"""
        self.cursor.execute('''
            SELECT 
                p.id, p.title, p.venue, p.genre,
                GROUP_CONCAT(s.show_date || ' ' || s.show_time, '; ') as showtimes,
                p.ticket_url
            FROM plays p
            LEFT JOIN showtimes s ON p.id = s.play_id
            GROUP BY p.id
            ORDER BY p.title
        ''')
        
        return self.cursor.fetchall()
    
    def get_plays_by_date_range(self, start_date, end_date):
        """Get plays showing between two dates"""
        self.cursor.execute('''
            SELECT DISTINCT 
                p.id, p.title, p.venue, p.genre,
                s.show_date, s.show_time, s.price
            FROM plays p
            JOIN showtimes s ON p.id = s.play_id
            WHERE s.show_date BETWEEN ? AND ?
            ORDER BY s.show_date, s.show_time
        ''', (start_date, end_date))
        
        return self.cursor.fetchall()
    
    def search_plays(self, keyword):
        """Search plays by title or venue"""
        self.cursor.execute('''
            SELECT id, title, venue, genre, ticket_url
            FROM plays
            WHERE title LIKE ? OR venue LIKE ?
            ORDER BY title
        ''', (f'%{keyword}%', f'%{keyword}%'))
        
        return self.cursor.fetchall()
    
    def get_database_stats(self):
        """Get database statistics"""
        stats = {}
        
        # Total plays
        self.cursor.execute('SELECT COUNT(*) FROM plays')
        stats['total_plays'] = self.cursor.fetchone()[0]
        
        # Total showtimes
        self.cursor.execute('SELECT COUNT(*) FROM showtimes')
        stats['total_showtimes'] = self.cursor.fetchone()[0]
        
        # Unique venues
        self.cursor.execute('SELECT COUNT(DISTINCT venue) FROM plays WHERE venue IS NOT NULL')
        stats['unique_venues'] = self.cursor.fetchone()[0]
        
        return stats
    
    def close(self):
        """Close database connection"""
        self.conn.close()


def import_from_scraper_json(json_file='theater_scraping_results.json'):
    """
    Import scraped data from JSON into database
    This is the bridge between your scraper and database
    """
    import re
    from pathlib import Path
    
    # Find the JSON file
    json_path = Path(json_file)
    if not json_path.exists():
        # Try in parent directory
        json_path = Path.cwd() / json_file
    
    if not json_path.exists():
        print(f"❌ Could not find {json_file}")
        return
    
    # Load JSON data
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n{'='*60}")
    print(f"IMPORTING DATA FROM SCRAPER")
    print(f"{'='*60}")
    print(f"Source: {json_path}")
    print(f"Total plays to import: {data.get('total_plays', 0)}")
    print(f"{'='*60}\n")
    
    # Initialize database
    db = TheaterDatabase()
    
    imported_count = 0
    skipped_count = 0
    
    for play_data in data.get('plays', []):
        title = play_data.get('title', '').strip()
        
        if not title or len(title) < 3:
            skipped_count += 1
            continue
        
        # Get venue (first one if multiple)
        venues = play_data.get('venues', [])
        venue = venues[0] if venues else None
        
        # Get city from JSON
        city = play_data.get('city', 'Istanbul')
        
        # Add play to database
        play_id = db.add_play(
            title=title,
            venue=venue,
            city=city,  # NOW PROPERLY IMPORTS CITY!
            image_url=play_data.get('image', ''),
            ticket_url=play_data.get('url', '')
        )
        
        if play_id:
            # Add showtimes
            dates = play_data.get('dates', [])
            for date_str in dates:
                try:
                    # Simple date parsing (you'll improve this)
                    # Format: "15 Kasım Cumartesi, 15:00"
                    date_parts = date_str.split(',')
                    if len(date_parts) >= 2:
                        show_date = date_parts[0].strip()  # "15 Kasım Cumartesi"
                        show_time = date_parts[1].strip()  # "15:00"
                        
                        db.add_showtime(
                            play_id=play_id,
                            show_date=show_date,
                            show_time=show_time
                        )
                except Exception as e:
                    pass  # Skip invalid dates
            
            imported_count += 1
            print(f"✓ [{imported_count}] {title}")
            if venue:
                print(f"  └─ Venue: {venue}")
            if dates:
                print(f"  └─ Showtimes: {len(dates)}")
    
    print(f"\n{'='*60}")
    print(f"IMPORT COMPLETE")
    print(f"{'='*60}")
    print(f"✓ Imported: {imported_count} plays")
    print(f"⊘ Skipped: {skipped_count} invalid entries")
    
    # Show database stats
    stats = db.get_database_stats()
    print(f"\n📊 DATABASE STATS:")
    print(f"  • Total plays: {stats['total_plays']}")
    print(f"  • Total showtimes: {stats['total_showtimes']}")
    print(f"  • Unique venues: {stats['unique_venues']}")
    print(f"{'='*60}\n")
    
    db.close()


if __name__ == "__main__":
    print("\n🎭 StageAgent Database Setup\n")
    
    # Option 1: Just create empty database
    print("Option 1: Create empty database")
    print("Option 2: Import from scraper JSON\n")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "2":
        import_from_scraper_json()
    else:
        db = TheaterDatabase()
        stats = db.get_database_stats()
        print(f"\n✓ Database created at: {db.db_path}")
        print(f"  • Plays: {stats['total_plays']}")
        print(f"  • Showtimes: {stats['total_showtimes']}")
        db.close()