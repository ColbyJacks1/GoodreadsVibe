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

from .db import db_manager, LLMHistoryCreate

logger = logging.getLogger(__name__)


class ComprehensiveAnalyzer:
    """Generates comprehensive analysis including insights, profile, and recommendations."""
    
    def __init__(self):
        self.db = db_manager
        
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
                             key=lambda x: (x.my_rating or 0, x.date_read or x.date_added), 
                             reverse=True)
        
        book_lines = []
        for book in sorted_books:
            rating = book.my_rating or "No rating"
            date = book.date_read or book.date_added
            date_str = date.strftime("%Y-%m-%d") if date else "Unknown date"
            
            line = f"- {book.title} by {book.author} (Rating: {rating}, Read: {date_str})"
            
            if book.genres:
                line += f" [Genres: {book.genres}]"
            
            if book.my_review:
                line += f" - Review: {book.my_review[:100]}..."
            
            book_lines.append(line)
        
        return "\n".join(book_lines)

    def generate_comprehensive_analysis(self) -> Dict[str, Any]:
        """Generate comprehensive analysis including insights, profile, and recommendations."""
        try:
            if not self.model:
                db_manager.add_llm_history(LLMHistoryCreate(
                    prompt="MODEL NOT AVAILABLE",
                    response="Google Gemini model not available. Please set GOOGLE_GEMINI_API_KEY environment variable.",
                    extra="{\"status\": \"error\"}"
                ))
                return {"error": "Google Gemini model not available. Please set GOOGLE_GEMINI_API_KEY environment variable.", "raw_response": "Google Gemini model not available. Please set GOOGLE_GEMINI_API_KEY environment variable."}
            
            # Get user's books
            books = self.db.get_all_books()
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
            
            # Log the interaction
            db_manager.add_llm_history(LLMHistoryCreate(
                prompt="Comprehensive analysis request",
                response=response.text,
                extra=json.dumps({"status": "success", "analysis_type": "comprehensive"})
            ))
            
            # Parse the response into sections
            parsed_sections = self._parse_comprehensive_response(response.text)
            
            return {
                "success": True,
                "comprehensive_analysis": response.text,
                "parsed_sections": parsed_sections,
                "raw_response": response.text,
                "data_summary": {
                    "total_books": len(books),
                    "avg_rating": sum(b.my_rating for b in books if b.my_rating) / len([b for b in books if b.my_rating]) if any(b.my_rating for b in books) else 0
                }
            }
        
        except Exception as e:
            logger.error(f"Error generating comprehensive analysis: {str(e)}")
            db_manager.add_llm_history(LLMHistoryCreate(
                prompt="EXCEPTION",
                response=str(e),
                extra="{\"status\": \"error\"}"
            ))
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
            # Check for section headers
            if "## LITERARY PSYCHOLOGY INSIGHTS" in line:
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "insights"
                current_content = [line]
            elif "## PERSONAL PROFILE ANALYSIS" in line:
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "profile"
                current_content = [line]
            elif "## PERSONALIZED RECOMMENDATIONS" in line:
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "recommendations"
                current_content = [line]
            elif "## HUMOROUS ROAST ANALYSIS" in line:
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "humorous"
                current_content = [line]
            elif "## ANALYSIS SUMMARY" in line:
                # End of sections, add final section
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content)
                break
            elif current_section:
                current_content.append(line)
        
        # Add the last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content)
        

        
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
        books_with_ratings = [book for book in books if book.my_rating]
        
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