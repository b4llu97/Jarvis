"""
Feedback Database Module for Continuous Learning
Stores user feedback, corrections, and learned patterns
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Any
import json


class FeedbackDB:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize feedback database with tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Feedback table for user ratings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT,
                model TEXT,
                provider TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Corrections table for user-provided corrections
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                wrong_response TEXT NOT NULL,
                correct_response TEXT NOT NULL,
                context TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Learned patterns table for extracted knowledge
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learned_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                query_pattern TEXT NOT NULL,
                response_pattern TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                usage_count INTEGER DEFAULT 0,
                last_used DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preference_key TEXT UNIQUE NOT NULL,
                preference_value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_feedback(
        self, 
        query: str, 
        response: str, 
        rating: int,
        comment: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None
    ) -> int:
        """
        Add user feedback for a conversation
        
        Args:
            query: User's query
            response: Assistant's response
            rating: 1-5 rating (1=very bad, 5=excellent)
            comment: Optional user comment
            model: LLM model used
            provider: LLM provider used
            
        Returns:
            Feedback ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO feedback (query, response, rating, comment, model, provider)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (query, response, rating, comment, model, provider))
        
        feedback_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return feedback_id
    
    def add_correction(
        self,
        query: str,
        wrong_response: str,
        correct_response: str,
        context: Optional[str] = None
    ) -> int:
        """
        Add a user correction
        
        Args:
            query: Original query
            wrong_response: The incorrect response
            correct_response: The correct response
            context: Additional context
            
        Returns:
            Correction ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO corrections (query, wrong_response, correct_response, context)
            VALUES (?, ?, ?, ?)
        """, (query, wrong_response, correct_response, context))
        
        correction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return correction_id
    
    def get_negative_feedback(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get feedback with low ratings (1-2 stars)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, query, response, rating, comment, model, provider, timestamp
            FROM feedback
            WHERE rating <= 2
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "query": row[1],
                "response": row[2],
                "rating": row[3],
                "comment": row[4],
                "model": row[5],
                "provider": row[6],
                "timestamp": row[7]
            }
            for row in rows
        ]
    
    def get_corrections(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all corrections"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, query, wrong_response, correct_response, context, timestamp
            FROM corrections
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "query": row[1],
                "wrong_response": row[2],
                "correct_response": row[3],
                "context": row[4],
                "timestamp": row[5]
            }
            for row in rows
        ]
    
    def get_learning_context(self, query: str, limit: int = 5) -> str:
        """
        Get relevant learning context for a query
        Includes corrections and negative feedback
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get relevant corrections
        cursor.execute("""
            SELECT query, wrong_response, correct_response
            FROM corrections
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        corrections = cursor.fetchall()
        
        # Get negative feedback with comments
        cursor.execute("""
            SELECT query, response, comment
            FROM feedback
            WHERE rating <= 2 AND comment IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        negative_feedback = cursor.fetchall()
        conn.close()
        
        # Build context string
        context_parts = []
        
        if corrections:
            context_parts.append("## Frühere Korrekturen (lerne daraus):")
            for i, (q, wrong, correct) in enumerate(corrections, 1):
                context_parts.append(f"\n{i}. Frage: {q}")
                context_parts.append(f"   Falsche Antwort: {wrong[:100]}...")
                context_parts.append(f"   Richtige Antwort: {correct[:100]}...")
        
        if negative_feedback:
            context_parts.append("\n## Negatives Feedback (vermeide solche Antworten):")
            for i, (q, resp, comment) in enumerate(negative_feedback, 1):
                context_parts.append(f"\n{i}. Frage: {q}")
                context_parts.append(f"   Problematische Antwort: {resp[:100]}...")
                if comment:
                    context_parts.append(f"   Feedback: {comment}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get feedback statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total feedback count
        cursor.execute("SELECT COUNT(*) FROM feedback")
        total_feedback = cursor.fetchone()[0]
        
        # Average rating
        cursor.execute("SELECT AVG(rating) FROM feedback")
        avg_rating = cursor.fetchone()[0] or 0
        
        # Rating distribution
        cursor.execute("""
            SELECT rating, COUNT(*) as count
            FROM feedback
            GROUP BY rating
            ORDER BY rating
        """)
        rating_distribution = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Total corrections
        cursor.execute("SELECT COUNT(*) FROM corrections")
        total_corrections = cursor.fetchone()[0]
        
        # Recent feedback (last 7 days)
        cursor.execute("""
            SELECT COUNT(*) FROM feedback
            WHERE timestamp >= datetime('now', '-7 days')
        """)
        recent_feedback = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_feedback": total_feedback,
            "average_rating": round(avg_rating, 2),
            "rating_distribution": rating_distribution,
            "total_corrections": total_corrections,
            "recent_feedback_7d": recent_feedback
        }
    
    def set_preference(self, key: str, value: str):
        """Set or update a user preference"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO user_preferences (preference_key, preference_value)
            VALUES (?, ?)
            ON CONFLICT(preference_key) 
            DO UPDATE SET preference_value = ?, updated_at = CURRENT_TIMESTAMP
        """, (key, value, value))
        
        conn.commit()
        conn.close()
    
    def get_preference(self, key: str) -> Optional[str]:
        """Get a user preference"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT preference_value FROM user_preferences
            WHERE preference_key = ?
        """, (key,))
        
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row else None
    
    def get_all_preferences(self) -> Dict[str, str]:
        """Get all user preferences"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT preference_key, preference_value FROM user_preferences")
        rows = cursor.fetchall()
        conn.close()
        
        return {row[0]: row[1] for row in rows}
