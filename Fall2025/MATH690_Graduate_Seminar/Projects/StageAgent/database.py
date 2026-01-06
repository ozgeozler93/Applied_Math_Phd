"""
Database module for StageAgent
Handles user ratings storage in SQLite
"""

import sqlite3
from pathlib import Path
from datetime import datetime


class Database:
    """Simple SQLite database for user ratings"""
    
    def __init__(self, db_path="data/ratings.db"):
        """Initialize database connection"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()
    
    def _create_tables(self):
        """Create ratings table if not exists"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                play_id INTEGER NOT NULL,
                play_title TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
                review TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
    
    def add_rating(self, play_id, play_title, rating, review=None):
        """
        Add a new rating
        
        Args:
            play_id: ID of the play
            play_title: Title of the play
            rating: Rating (1-5 stars)
            review: Optional text review
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute("""
                INSERT INTO ratings (play_id, play_title, rating, review)
                VALUES (?, ?, ?, ?)
            """, (play_id, play_title, rating, review))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"❌ Error adding rating: {e}")
            return False
    
    def get_all_ratings(self):
        """
        Get all ratings ordered by date (newest first)
        
        Returns:
            List of tuples: (id, play_id, play_title, rating, review, created_at)
        """
        self.cursor.execute("""
            SELECT id, play_id, play_title, rating, review, created_at
            FROM ratings
            ORDER BY created_at DESC
        """)
        return self.cursor.fetchall()
    
    def get_rating_by_play_id(self, play_id):
        """
        Get rating for a specific play
        
        Returns:
            Tuple or None
        """
        self.cursor.execute("""
            SELECT rating, review, created_at
            FROM ratings
            WHERE play_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (play_id,))
        return self.cursor.fetchone()
    
    def get_recent_ratings(self, limit=5):
        """
        Get N most recent ratings
        
        Returns:
            List of tuples
        """
        self.cursor.execute("""
            SELECT play_title, rating, review, created_at
            FROM ratings
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        return self.cursor.fetchall()
    
    def get_high_rated_plays(self, min_rating=4):
        """
        Get plays with rating >= min_rating
        
        Returns:
            List of tuples: (play_title, rating, review)
        """
        self.cursor.execute("""
            SELECT play_title, rating, review
            FROM ratings
            WHERE rating >= ?
            ORDER BY rating DESC, created_at DESC
        """, (min_rating,))
        return self.cursor.fetchall()
    
    def get_low_rated_plays(self, max_rating=2):
        """
        Get plays with rating <= max_rating
        
        Returns:
            List of tuples: (play_title, rating, review)
        """
        self.cursor.execute("""
            SELECT play_title, rating, review
            FROM ratings
            WHERE rating <= ?
            ORDER BY rating ASC, created_at DESC
        """, (max_rating,))
        return self.cursor.fetchall()
    
    def close(self):
        """Close database connection"""
        self.conn.close()


# Test function
if __name__ == "__main__":
    # Test database
    db = Database()
    
    # Add sample ratings
    db.add_rating(1, "Hamlet", 5, "Amazing performance! Loved every minute.")
    db.add_rating(4, "Comedy Club Night", 2, "Not funny at all.")
    db.add_rating(5, "Macbeth", 4, "Great directing, solid cast.")
    
    # Print all ratings
    print("\n📊 ALL RATINGS:")
    for rating in db.get_all_ratings():
        print(f"- {rating[2]}: {rating[3]}⭐ ({rating[4]})")
    
    # Print high rated
    print("\n⭐ HIGH RATED (4+ stars):")
    for play in db.get_high_rated_plays():
        print(f"- {play[0]}: {play[1]}⭐")
    
    db.close()
    print("\n✅ Database test completed!")