# Authentication module for the chatbot
import streamlit as st
import hashlib
import secrets
from typing import Optional, Dict

class SimpleAuth:
    """Simple authentication system for the chatbot"""
    
    def __init__(self):
        # In a real app, this would be stored in a secure database
        self.users_db = {
            "demo@chatbot.com": {
                "name": "Demo User",
                "password_hash": self._hash_password("demo123"),
                "profile_picture": None
            }
        }
    
    def _hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = "chatbot_salt_2025"  # In production, use random salt per user
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def authenticate(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate user with email and password"""
        if email in self.users_db:
            stored_hash = self.users_db[email]["password_hash"]
            if self._hash_password(password) == stored_hash:
                return {
                    "email": email,
                    "name": self.users_db[email]["name"],
                    "profile_picture": self.users_db[email].get("profile_picture")
                }
        return None
    
    def register(self, email: str, name: str, password: str) -> bool:
        """Register a new user"""
        if email in self.users_db:
            return False  # User already exists
        
        self.users_db[email] = {
            "name": name,
            "password_hash": self._hash_password(password),
            "profile_picture": None
        }
        return True
    
    def guest_login(self) -> Dict:
        """Create a guest session"""
        guest_id = secrets.token_hex(8)
        return {
            "email": f"guest_{guest_id}@chatbot.local",
            "name": f"Guest_{guest_id}",
            "profile_picture": None,
            "is_guest": True
        }

# Google OAuth integration (placeholder for real implementation)
class GoogleAuth:
    """Google OAuth authentication (mock implementation)"""
    
    @staticmethod
    def get_authorization_url() -> str:
        """Get Google OAuth authorization URL"""
        # In a real implementation, this would return the actual Google OAuth URL
        return "https://accounts.google.com/oauth/authorize"
    
    @staticmethod
    def exchange_code_for_token(code: str) -> Optional[Dict]:
        """Exchange authorization code for access token"""
        # Mock implementation - in real app, this would call Google's token endpoint
        if code == "mock_code":
            return {
                "access_token": "mock_access_token",
                "email": "user@gmail.com",
                "name": "Google User",
                "picture": "https://example.com/profile.jpg"
            }
        return None
    
    @staticmethod
    def get_user_info(access_token: str) -> Optional[Dict]:
        """Get user information from Google"""
        # Mock implementation
        if access_token == "mock_access_token":
            return {
                "email": "user@gmail.com",
                "name": "Google User",
                "picture": "https://example.com/profile.jpg"
            }
        return None

# Global auth instances
simple_auth = SimpleAuth()
google_auth = GoogleAuth()
