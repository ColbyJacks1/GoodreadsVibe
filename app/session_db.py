"""Session-based database management for multi-user support."""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import streamlit as st

logger = logging.getLogger(__name__)


class SessionDatabaseManager:
    """Session-based database manager for multi-user isolation."""
    
    def __init__(self):
        self.session_key_prefix = "goodreads_analyzer_"
    
    def _get_session_key(self, key: str) -> str:
        """Get session key with prefix."""
        return f"{self.session_key_prefix}{key}"
    
    def get_user_books(self) -> List[Dict[str, Any]]:
        """Get books for current user session."""
        books_key = self._get_session_key("books")
        return st.session_state.get(books_key, [])
    
    def add_user_book(self, book_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a book to current user's session."""
        books_key = self._get_session_key("books")
        if books_key not in st.session_state:
            st.session_state[books_key] = []
        
        # Add unique ID and timestamp
        book_data['id'] = len(st.session_state[books_key]) + 1
        book_data['created_at'] = datetime.utcnow().isoformat()
        book_data['updated_at'] = datetime.utcnow().isoformat()
        
        st.session_state[books_key].append(book_data)
        return book_data
    
    def clear_user_books(self) -> None:
        """Clear all books for current user."""
        books_key = self._get_session_key("books")
        if books_key in st.session_state:
            del st.session_state[books_key]
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Get statistics for current user."""
        stats_key = self._get_session_key("stats")
        default_stats = {
            'total_books': 0,
            'processed_books': 0,
            'enriched_books': 0,
            'books_with_ratings': 0,
            'average_rating': 0.0
        }
        return st.session_state.get(stats_key, default_stats)
    
    def update_user_stats(self, stats: Dict[str, Any]) -> None:
        """Update statistics for current user."""
        stats_key = self._get_session_key("stats")
        st.session_state[stats_key] = stats
    
    def get_llm_history(self) -> List[Dict[str, Any]]:
        """Get LLM history for current user."""
        history_key = self._get_session_key("llm_history")
        return st.session_state.get(history_key, [])
    
    def add_llm_history(self, prompt: str, response: str, extra: Optional[str] = None) -> Dict[str, Any]:
        """Add LLM interaction to current user's history."""
        history_key = self._get_session_key("llm_history")
        if history_key not in st.session_state:
            st.session_state[history_key] = []
        
        history_entry = {
            'id': len(st.session_state[history_key]) + 1,
            'timestamp': datetime.utcnow().isoformat(),
            'prompt': prompt,
            'response': response,
            'extra': extra
        }
        
        st.session_state[history_key].append(history_entry)
        return history_entry
    
    def get_all_books(self) -> List[Dict[str, Any]]:
        """Get all books for current user (compatibility method)."""
        return self.get_user_books()
    
    def create_tables(self) -> None:
        """Initialize session state (compatibility method)."""
        # Session state is automatically initialized
        pass


# Global session database manager instance
session_db_manager = SessionDatabaseManager() 