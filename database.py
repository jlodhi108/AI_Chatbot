# Database management for personalized chat storage
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import hashlib

class ChatDatabase:
    def __init__(self, db_path: str = "chat_database.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                profile_picture TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                preferences TEXT DEFAULT '{}'
            )
        ''')
        
        # Chat sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Chat messages table (store last 100 messages per session)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
            )
        ''')
        
        # User preferences/personalization data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_personalization (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                personality_type TEXT DEFAULT 'girlfriend',
                custom_prompt TEXT,
                favorite_topics TEXT DEFAULT '[]',
                conversation_style TEXT DEFAULT 'casual',
                emoji_preference TEXT DEFAULT 'rare',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_or_get_user(self, email: str, name: str, profile_picture: str = None) -> int:
        """Create new user or get existing user ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Try to get existing user
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if user:
            # Update last login
            cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE email = ?", (email,))
            user_id = user[0]
        else:
            # Create new user
            cursor.execute('''
                INSERT INTO users (email, name, profile_picture, last_login) 
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (email, name, profile_picture))
            user_id = cursor.lastrowid
            
            # Create default personalization
            cursor.execute('''
                INSERT INTO user_personalization (user_id) VALUES (?)
            ''', (user_id,))
        
        conn.commit()
        conn.close()
        return user_id
    
    def create_chat_session(self, user_id: int, session_name: str = None) -> int:
        """Create a new chat session for user"""
        if not session_name:
            session_name = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO chat_sessions (user_id, session_name) VALUES (?, ?)
        ''', (user_id, session_name))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return session_id
    
    def get_user_chat_sessions(self, user_id: int) -> List[Dict]:
        """Get all chat sessions for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, session_name, created_at, updated_at 
            FROM chat_sessions 
            WHERE user_id = ? 
            ORDER BY updated_at DESC
        ''', (user_id,))
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'id': row[0],
                'name': row[1],
                'created_at': row[2],
                'updated_at': row[3]
            })
        
        conn.close()
        return sessions
    
    def add_message(self, session_id: int, role: str, content: str):
        """Add a message to chat session (keep only last 100 messages)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Add new message
        cursor.execute('''
            INSERT INTO chat_messages (session_id, role, content) VALUES (?, ?, ?)
        ''', (session_id, role, content))
        
        # Keep only last 100 messages per session
        cursor.execute('''
            DELETE FROM chat_messages 
            WHERE session_id = ? AND id NOT IN (
                SELECT id FROM chat_messages 
                WHERE session_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 100
            )
        ''', (session_id, session_id))
        
        # Update session timestamp
        cursor.execute('''
            UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?
        ''', (session_id,))
        
        conn.commit()
        conn.close()
    
    def get_chat_history(self, session_id: int, limit: int = 100) -> List[Dict]:
        """Get chat history for a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT role, content, timestamp 
            FROM chat_messages 
            WHERE session_id = ? 
            ORDER BY timestamp ASC 
            LIMIT ?
        ''', (session_id, limit))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'role': row[0],
                'content': row[1],
                'timestamp': row[2]
            })
        
        conn.close()
        return messages
    
    def get_user_personalization(self, user_id: int) -> Dict:
        """Get user's personalization settings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT personality_type, custom_prompt, favorite_topics, 
                   conversation_style, emoji_preference 
            FROM user_personalization 
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'personality_type': result[0],
                'custom_prompt': result[1],
                'favorite_topics': json.loads(result[2]) if result[2] else [],
                'conversation_style': result[3],
                'emoji_preference': result[4]
            }
        return {}
    
    def update_user_personalization(self, user_id: int, **kwargs):
        """Update user's personalization settings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build dynamic UPDATE query
        fields = []
        values = []
        
        for key, value in kwargs.items():
            if key in ['personality_type', 'custom_prompt', 'conversation_style', 'emoji_preference']:
                fields.append(f"{key} = ?")
                values.append(value)
            elif key == 'favorite_topics':
                fields.append("favorite_topics = ?")
                values.append(json.dumps(value))
        
        if fields:
            fields.append("updated_at = CURRENT_TIMESTAMP")
            values.append(user_id)
            
            query = f"UPDATE user_personalization SET {', '.join(fields)} WHERE user_id = ?"
            cursor.execute(query, values)
            conn.commit()
        
        conn.close()
    
    def delete_chat_session(self, session_id: int, user_id: int):
        """Delete a chat session and its messages"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verify session belongs to user
        cursor.execute("SELECT id FROM chat_sessions WHERE id = ? AND user_id = ?", (session_id, user_id))
        if cursor.fetchone():
            # Delete messages first
            cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
            # Delete session
            cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
            conn.commit()
        
        conn.close()
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get user statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total sessions
        cursor.execute("SELECT COUNT(*) FROM chat_sessions WHERE user_id = ?", (user_id,))
        total_sessions = cursor.fetchone()[0]
        
        # Total messages
        cursor.execute('''
            SELECT COUNT(*) FROM chat_messages cm
            JOIN chat_sessions cs ON cm.session_id = cs.id
            WHERE cs.user_id = ?
        ''', (user_id,))
        total_messages = cursor.fetchone()[0]
        
        # Days since joining
        cursor.execute("SELECT created_at FROM users WHERE id = ?", (user_id,))
        created_at = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_sessions': total_sessions,
            'total_messages': total_messages,
            'member_since': created_at
        }

# Global database instance
db = ChatDatabase()
