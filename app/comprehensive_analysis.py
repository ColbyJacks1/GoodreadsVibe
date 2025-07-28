"""Comprehensive book analysis using Google Gemini."""

import json
import logging
import os
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .session_db import session_db_manager

logger = logging.getLogger(__name__)


class ComprehensiveAnalyzer:
    """Generates comprehensive analysis including insights, profile, and recommendations."""
    
    def __init__(self):
        self.db = session_db_manager
        
        # Initialize Google Gemini
        api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        if not api_key:
            logger.warning("No Google Gemini API key provided. Analysis will be disabled.")
            self.model = None
        else:
            genai.configure(api_key=api_key)
            model_name = os.getenv("GEMINI_INSIGHTS_MODEL", "gemini-2.5-flash")
            self.model = genai.GenerativeModel(model_name)
        
        # Load comprehensive prompt template
        prompt_path = Path(__file__).parent.parent / "prompts" / "comprehensive_analysis_prompt.md"
        with open(prompt_path, 'r') as f:
            self.prompt_template = f.read()
    
    def _format_books(self, books: List[Any]) -> str:
        """Format user's books for LLM context."""
        if not books:
            return "No books available."
        
        # Sort by rating (highest first) and date read (most recent first)
        sorted_books = sorted(books, 
                             key=lambda x: (x.get('my_rating') or 0, x.get('date_read') or x.get('date_added')), 
                             reverse=True)
        
        book_lines = []
        for book in sorted_books:
            rating = book.get('my_rating') or "No rating"
            date_read = book.get('date_read')
            date_added = book.get('date_added')
            date = date_read or date_added
            date_str = date if isinstance(date, str) else "Unknown date"
            
            line = f"- {book.get('title', 'Unknown')} by {book.get('author', 'Unknown')} (Rating: {rating}, Read: {date_str})"
            
            if book.get('genres'):
                line += f" [Genres: {book['genres']}]"
            
            if book.get('my_review'):
                line += f" - Review: {book['my_review'][:100]}..."
            
            book_lines.append(line)
        
        return "\n".join(book_lines)

    def generate_comprehensive_analysis(self) -> Dict[str, Any]:
        """Generate comprehensive analysis including insights, profile, and recommendations."""
        try:
            if not self.model:
                return {"error": "Google Gemini model not available. Please set GOOGLE_GEMINI_API_KEY environment variable.", "raw_response": "Google Gemini model not available. Please set GOOGLE_GEMINI_API_KEY environment variable."}
            
            # Get user's books
            books = self.db.get_user_books()
            if not books:
                return {"error": "No books found"}
            
            # Format books for context
            books_text = self._format_books(books)
            
            # Create the comprehensive prompt
            full_prompt = self.prompt_template.format(books=books_text)
            
            logger.info("Generating comprehensive analysis...")
            response = self.model.generate_content(full_prompt)
            logger.info(f"LLM raw response: {response.text}")
            
            if not response.text:
                return {"error": "No response from LLM", "raw_response": ""}
            
            # Log the interaction (session-based)
            self.db.add_llm_history(
                prompt="Comprehensive analysis request",
                response=response.text,
                extra=json.dumps({"status": "success", "analysis_type": "comprehensive"})
            )
            
            # Parse the response into sections
            parsed_sections = self._parse_comprehensive_response(response.text)
            
            # Debug: Log what sections were found
            logger.info(f"Parsed sections: {list(parsed_sections.keys())}")
            for section, content in parsed_sections.items():
                logger.info(f"Section '{section}' length: {len(content)} chars")
            
            return {
                "success": True,
                "comprehensive_analysis": response.text,
                "parsed_sections": parsed_sections,
                "raw_response": response.text,
                "data_summary": {
                    "total_books": len(books),
                    "avg_rating": sum(b.get('my_rating', 0) for b in books if b.get('my_rating')) / len([b for b in books if b.get('my_rating')]) if any(b.get('my_rating') for b in books) else 0
                }
            }
        
        except Exception as e:
            logger.error(f"Error generating comprehensive analysis: {str(e)}")
            self.db.add_llm_history(
                prompt="EXCEPTION",
                response=str(e),
                extra="{\"status\": \"error\"}"
            )
            return {"error": str(e), "raw_response": str(e)}
    
    def _parse_comprehensive_response(self, response_text: str) -> Dict[str, str]:
        """Parse the comprehensive response into separate sections."""
        sections = {
            "insights": "",
            "profile": "",
            "recommendations": "",
            "humorous": ""
        }
        
        # More robust parsing - look for section headers
        lines = response_text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            # Check for section headers (case insensitive and flexible)
            line_upper = line.upper().strip()
            
            if "LITERARY PSYCHOLOGY INSIGHTS" in line_upper:
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "insights"
                current_content = [line]
            elif "PERSONAL PROFILE ANALYSIS" in line_upper:
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "profile"
                current_content = [line]
            elif "PERSONALIZED" in line_upper and "RECOMMENDATION" in line_upper:
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "recommendations"
                current_content = [line]
            elif "HUMOROUS" in line_upper and "ROAST" in line_upper:
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "humorous"
                current_content = [line]
            elif "ANALYSIS SUMMARY" in line_upper or line_upper.startswith("---"):
                # End of sections, add final section
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content)
                break
            elif current_section:
                current_content.append(line)
        
        # Add the last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content)
        
        # Fallback: If recommendations section is empty but profile section is very long,
        # try to split the profile section on "PERSONALIZED" or "RECOMMENDATION" keywords
        if not sections.get("recommendations") and sections.get("profile"):
            profile_content = sections["profile"]
            if "PERSONALIZED" in profile_content.upper() or "RECOMMENDATION" in profile_content.upper():
                # Try to split the profile section
                profile_lines = profile_content.split('\n')
                recommendations_start = -1
                
                for i, line in enumerate(profile_lines):
                    line_upper = line.upper()
                    if ("PERSONALIZED" in line_upper and "RECOMMENDATION" in line_upper) or \
                       ("BOOK" in line_upper and "RECOMMENDATION" in line_upper):
                        recommendations_start = i
                        break
                
                if recommendations_start > 0:
                    # Split the content
                    sections["profile"] = '\n'.join(profile_lines[:recommendations_start])
                    sections["recommendations"] = '\n'.join(profile_lines[recommendations_start:])
        

        
        return sections
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """Get statistics about the comprehensive analysis capability."""
        books = self.db.get_all_books()
        
        if not books:
            return {
                "total_books": 0,
                "can_generate_analysis": False,
                "reason": "No books in database"
            }
        
        # Check if we have enough data for meaningful analysis
        books_with_ratings = [book for book in books if book.get('my_rating')]
        
        can_generate = (
            len(books) >= 5 and
            len(books_with_ratings) >= 3
        )
        
        return {
            "total_books": len(books),
            "books_with_ratings": len(books_with_ratings),
            "can_generate_analysis": can_generate,
            "reason": "Insufficient data" if not can_generate else "Ready"
        }


# Global comprehensive analyzer instance
comprehensive_analyzer = ComprehensiveAnalyzer() 