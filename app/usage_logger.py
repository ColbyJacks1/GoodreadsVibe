"""Enhanced console logging for comprehensive usage tracking."""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
import streamlit as st

class UsageLogger:
    """Logs usage patterns and AI outputs to console with detailed tracking."""
    
    def __init__(self):
        # Configure logging to write to console (visible in Streamlit Cloud)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()  # Console only
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log_page_view(self, page_name: str, user_session_id: str = None):
        """Log when a user views a page."""
        session_id = user_session_id or self._get_session_id()
        self.logger.info(f"PAGE_VIEW: {page_name} | Session: {session_id}")
    
    def log_file_upload(self, file_size: int, book_count: int, user_session_id: str = None):
        """Log when a user uploads a file."""
        session_id = user_session_id or self._get_session_id()
        self.logger.info(f"FILE_UPLOAD: Size: {file_size} bytes, Books: {book_count} | Session: {session_id}")
    
    def log_analysis_request(self, analysis_type: str, book_count: int, user_session_id: str = None):
        """Log when a user requests analysis."""
        session_id = user_session_id or self._get_session_id()
        self.logger.info(f"ANALYSIS_REQUEST: Type: {analysis_type}, Books: {book_count} | Session: {session_id}")
    
    def log_ai_response(self, analysis_type: str, prompt: str, response: str, 
                       book_count: int, user_session_id: str = None, 
                       processing_time: float = None, error: str = None):
        """Log AI prompts and responses for analysis."""
        session_id = user_session_id or self._get_session_id()
        
        # Create detailed log entry
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "analysis_type": analysis_type,
            "book_count": book_count,
            "prompt_length": len(prompt),
            "response_length": len(response),
            "processing_time_seconds": processing_time,
            "error": error,
            "success": error is None
        }
        
        # Log summary
        self.logger.info(f"AI_RESPONSE_SUMMARY: {json.dumps(log_data)}")
        
        # Log full prompt and response for analysis
        self.logger.info(f"=== AI PROMPT ({analysis_type}) ===")
        self.logger.info(prompt)
        self.logger.info(f"=== AI RESPONSE ({analysis_type}) ===")
        self.logger.info(response)
        self.logger.info(f"=== END AI RESPONSE ({analysis_type}) ===")
        
        if error:
            self.logger.error(f"AI_ERROR: {error}")
    
    def log_user_stats(self, stats: Dict[str, Any], user_session_id: str = None):
        """Log user statistics for analysis."""
        session_id = user_session_id or self._get_session_id()
        self.logger.info(f"USER_STATS: {json.dumps(stats)} | Session: {session_id}")
    
    def log_error(self, error_type: str, error_message: str, user_session_id: str = None):
        """Log errors."""
        session_id = user_session_id or self._get_session_id()
        self.logger.error(f"ERROR: {error_type} - {error_message} | Session: {session_id}")
    
    def _get_session_id(self) -> str:
        """Get a unique session ID for the current user."""
        if 'session_id' not in st.session_state:
            import uuid
            st.session_state.session_id = str(uuid.uuid4())
        return st.session_state.session_id

# Global logger instance
usage_logger = UsageLogger() 