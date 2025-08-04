"""LLM-powered book recommendations using Google Gemini."""

import json
import logging
import os
import time
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .db import db_manager, LLMHistoryCreate
from .usage_logger import usage_logger

logger = logging.getLogger(__name__)


class LLMRecommender:
    """Provides personalized book recommendations using Gemini AI."""
    
    def __init__(self):
        self.db = db_manager
        
        # Initialize Google Gemini
        api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        if not api_key:
            logger.warning("No Google Gemini API key provided. Recommendations will be disabled.")
            self.model = None
        else:
            genai.configure(api_key=api_key)
            model_name = os.getenv("GEMINI_RECOMMENDATION_MODEL", "gemini-2.5-flash")
            self.model = genai.GenerativeModel(model_name)
        
        # Load recommendation prompt template
        prompt_path = Path(__file__).parent.parent / "prompts" / "recommendation_prompt.md"
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

    def generate_recommendations(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Generate personalized book recommendations using Gemini AI."""
        try:
            if not self.model:
                logger.warning("Gemini model not available, returning test data")
                # Return test data for development/testing
                test_response = """## RECOMMENDATIONS

### 1. The Midnight Library by Matt Haig
**Why this book:** Perfect for someone who enjoys thought-provoking fiction with philosophical themes. It explores the concept of parallel lives and what-ifs, which aligns with your interest in introspective narratives.
**Connection to your reading:** Similar to books you've enjoyed that explore life choices and personal growth, with a touch of magical realism.
**Themes:** Life choices, regret, parallel universes, self-discovery

### 2. Project Hail Mary by Andy Weir
**Why this book:** Combines your interest in science fiction with compelling character development and problem-solving narratives.
**Connection to your reading:** Builds on your appreciation for well-crafted sci-fi with strong character arcs.
**Themes:** Space exploration, friendship, problem-solving, survival

### 3. The Seven Husbands of Evelyn Hugo by Taylor Jenkins Reid
**Why this book:** Offers a compelling narrative structure with strong character development and historical fiction elements.
**Connection to your reading:** Fits your pattern of enjoying character-driven stories with rich historical contexts.
**Themes:** Fame, love, ambition, storytelling, Hollywood history

### 4. Klara and the Sun by Kazuo Ishiguro
**Why this book:** Combines your interest in speculative fiction with deep emotional resonance and philosophical questions.
**Connection to your reading:** Similar to books you've enjoyed that blend genre elements with literary quality.
**Themes:** Artificial intelligence, love, consciousness, human nature

### 5. The Invisible Life of Addie LaRue by V.E. Schwab
**Why this book:** Offers a unique blend of historical fiction and fantasy with a strong female protagonist.
**Connection to your reading:** Matches your appreciation for well-crafted stories with memorable characters.
**Themes:** Immortality, love, art, memory, identity"""
                
                # Log the test response
                usage_logger.log_ai_response(
                    analysis_type="llm_recommendations_test",
                    prompt=f"Test recommendation query: {query}",
                    response=test_response,
                    book_count=0,
                    processing_time=0.0
                )
                
                return {
                    "success": True,
                    "recommendations": test_response,
                    "query": query,
                    "limit": limit
                }
            
            books = self.db.get_all_books()
            if not books:
                return {"error": "No books found"}
            
            books_text = self._format_books(books)
            
            # Format prompt
            prompt = self.prompt_template.format(
                query=query,
                books=books_text,
                limit=limit
            )
            
            logger.info(f"Generating recommendations for query: {query}")
            
            # Capture start time for processing time
            start_time = time.time()
            
            response = self.model.generate_content(prompt)
            
            processing_time = time.time() - start_time
            
            if not response.text:
                error_msg = "No response from LLM"
                usage_logger.log_ai_response(
                    analysis_type="llm_recommendations",
                    prompt=prompt,
                    response="",
                    book_count=len(books),
                    processing_time=processing_time,
                    error=error_msg
                )
                return {"error": error_msg}
            
            # Log the AI response
            usage_logger.log_ai_response(
                analysis_type="llm_recommendations",
                prompt=prompt,
                response=response.text,
                book_count=len(books),
                processing_time=processing_time
            )
            
            return {
                "success": True,
                "recommendations": response.text,
                "query": query,
                "limit": limit
            }
        
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            usage_logger.log_error("llm_recommendations", str(e))
            return {"error": str(e)}


# Global LLM recommender instance
print("🔄 Creating llm_recommender instance...")
llm_recommender = LLMRecommender()
print(f"✅ Created llm_recommender with methods: {[m for m in dir(llm_recommender) if not m.startswith('_')]}") 