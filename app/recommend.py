"""Book recommendations using Google Gemini."""

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


class BookRecommender:
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
            model_name = os.getenv("GEMINI_RECOMMENDATION_MODEL", "gemini-2.0-flash-exp")
            self.model = genai.GenerativeModel(model_name)
        
        # Load recommendation prompt template
        prompt_path = Path(__file__).parent.parent / "prompts" / "recommendation_prompt.md"
        if prompt_path.exists():
            with open(prompt_path, 'r') as f:
                self.prompt_template = f.read()
        else:
            # Fallback prompt template
            self.prompt_template = self._get_default_prompt_template()
    
    def _get_default_prompt_template(self) -> str:
        """Get default recommendation prompt template."""
        return """You are a personalized book recommendation system. Based on the user's query and their reading history, suggest relevant books.

## User's Query
{query}

## User's Reading History
{reading_history}

## Available Books
{available_books}

## Instructions
1. Analyze the user's query and reading preferences
2. Consider their ratings, genres, and reading patterns
3. Suggest {limit} books that would be most relevant to their query
4. For each recommendation, provide:
   - Title and author
   - Brief explanation of why it's recommended
   - How it relates to their query and reading history
   - Any relevant themes or connections

## Response Format
Return a JSON object with this structure:
{{
    "recommendations": [
        {{
            "book_id": "string",
            "title": "string", 
            "author": "string",
            "explanation": "string",
            "relevance_score": 0.0-1.0,
            "themes": ["string"],
            "connections": "string"
        }}
    ],
    "analysis": {{
        "query_understanding": "string",
        "reading_patterns": "string",
        "recommendation_strategy": "string"
    }}
}}

Focus on providing thoughtful, personalized recommendations based on the user's specific interests and reading history."""

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

    def _create_recommendation_context(self, query: str, limit: int = 10) -> str:
        """Create context for recommendation generation."""
        # Get user's books
        user_books = self.db.get_all_books()
        
        # Format the context
        books_text = self._format_books(user_books)
        
        # Create the prompt
        prompt = self.prompt_template.format(
            query=query,
            books=books_text,
            limit=limit
        )
        
        return prompt

    def recommend_books(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Generate personalized book recommendations using Gemini AI."""
        try:
            if not self.model:
                logger.error("Gemini model not available. Cannot generate recommendations.")
                return {"error": "Gemini model not available", "recommendations": []}
            
            # Create recommendation context
            prompt = self._create_recommendation_context(query, limit)
            
            # Generate recommendations using Gemini
            response = self.model.generate_content(prompt)
            
            if not response.text:
                logger.error("No response from Gemini model")
                return {"error": "No response from model", "recommendations": []}
            
            # Log the interaction
            self.db.add_llm_history(LLMHistoryCreate(
                prompt=f"Recommendation query: {query}",
                response=response.text,
                extra=json.dumps({"limit": limit, "query": query})
            ))
            
            return {
                "success": True,
                "recommendations": response.text,
                "query": query,
                "total_found": "Generated by LLM"
            }
        
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return {"error": str(e), "recommendations": []}

    def _validate_recommendation(self, rec: Dict[str, Any]) -> bool:
        """Validate a recommendation has required fields."""
        required_fields = ["book_id", "title", "author", "explanation"]
        return all(field in rec and rec[field] for field in required_fields)

    def _extract_recommendations_from_text(self, text: str, limit: int) -> List[Dict[str, Any]]:
        """Extract recommendations from unstructured text response."""
        # Simple fallback parsing
        recommendations = []
        lines = text.split('\n')
        
        for line in lines:
            if 'by' in line and ('title' in line.lower() or 'author' in line.lower()):
                # Try to extract book information
                parts = line.split('by')
                if len(parts) == 2:
                    title = parts[0].strip()
                    author = parts[1].strip()
                    
                    recommendations.append({
                        "book_id": f"extracted_{len(recommendations)}",
                        "title": title,
                        "author": author,
                        "explanation": f"Recommended based on query analysis",
                        "relevance_score": 0.8,
                        "themes": [],
                        "connections": "Extracted from LLM response"
                    })
                    
                    if len(recommendations) >= limit:
                        break
        
        return recommendations

    def get_similar_books(self, book_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find books similar to a specific book using Gemini AI."""
        target_book = self.db.get_book(book_id)
        if not target_book:
            return []
        
        try:
            if not self.model:
                logger.error("Gemini model not available. Cannot find similar books.")
                return []
            
            # Create context for finding similar books
            prompt = f"""Find books similar to "{target_book.title}" by {target_book.author}.

Book details:
- Title: {target_book.title}
- Author: {target_book.author}
- Genres: {target_book.genres or 'Unknown'}
- Description: {target_book.description or 'No description available'}
- Rating: {target_book.my_rating or 'No rating'}

User's books:
{self._format_books(self.db.get_all_books())}

Find {limit} books that are most similar in terms of:
1. Genre and themes
2. Writing style and tone
3. Target audience
4. Subject matter

Return as JSON:
{{
    "similar_books": [
        {{
            "book_id": "string",
            "title": "string",
            "author": "string",
            "similarity_reason": "string",
            "similarity_score": 0.0-1.0
        }}
    ]
}}"""

            response = self.model.generate_content(prompt)
            
            if not response.text:
                return []
            
            try:
                result = json.loads(response.text)
                similar_books = result.get("similar_books", [])
                
                # Validate and enhance
                validated_books = []
                for book in similar_books:
                    if self._validate_recommendation(book):
                        db_book = self.db.get_book(book.get("book_id", ""))
                        if db_book:
                            book.update({
                                "publisher": db_book.publisher,
                                "year_published": db_book.year_published,
                                "genres": db_book.genres,
                                "description": db_book.description
                            })
                        validated_books.append(book)
                
                return validated_books
                
            except json.JSONDecodeError:
                logger.error("Failed to parse similar books response")
                return []
        
        except Exception as e:
            logger.error(f"Error finding similar books: {str(e)}")
            return []

    def get_recommendation_explanation(self, recommendation: Dict[str, Any]) -> str:
        """Get explanation for a recommendation."""
        return recommendation.get("explanation", "No explanation available")

    def get_recommendation_stats(self) -> Dict[str, Any]:
        """Get statistics about the recommendation system."""
        books = self.db.get_all_books()
        total_books = len(books)
        rated_books = len([b for b in books if b.my_rating])
        avg_rating = sum(b.my_rating for b in books if b.my_rating) / rated_books if rated_books else 0
        
        return {
            'total_books': total_books,
            'rated_books': rated_books,
            'average_rating': round(avg_rating, 2),
            'model_available': self.model is not None,
            'model_name': os.getenv("GEMINI_RECOMMENDATION_MODEL", "gemini-2.0-flash-exp")
        }

    def analyze_reading_preferences(self) -> Dict[str, Any]:
        """Analyze user's reading preferences using Gemini AI."""
        try:
            if not self.model:
                return {"error": "Gemini model not available"}
            
            books = self.db.get_all_books()
            if not books:
                return {"error": "No books found"}
            
            # Create analysis prompt
            prompt = f"""Analyze this reading history and provide insights about the reader's preferences:

{self._format_books(books)}

Provide a detailed analysis including:
1. Genre preferences and patterns
2. Author preferences
3. Rating patterns
4. Reading timeline analysis
5. Potential recommendations for future reading

Return as JSON:
{{
    "genre_analysis": {{
        "favorite_genres": ["string"],
        "genre_patterns": "string"
    }},
    "author_analysis": {{
        "favorite_authors": ["string"],
        "author_patterns": "string"
    }},
    "rating_analysis": {{
        "average_rating": 0.0,
        "rating_patterns": "string"
    }},
    "timeline_analysis": {{
        "reading_pace": "string",
        "reading_patterns": "string"
    }},
    "recommendations": {{
        "suggested_genres": ["string"],
        "suggested_authors": ["string"],
        "reading_goals": "string"
    }}
}}"""

            response = self.model.generate_content(prompt)
            
            if not response.text:
                return {"error": "No response from model"}
            
            try:
                result = json.loads(response.text)
                
                # Log the analysis
                self.db.add_llm_history(LLMHistoryCreate(
                    prompt="Reading preferences analysis",
                    response=response.text,
                    extra=json.dumps({"analysis_type": "preferences"})
                ))
                
                return result
                
            except json.JSONDecodeError:
                return {"error": "Failed to parse analysis response"}
        
        except Exception as e:
            logger.error(f"Error analyzing reading preferences: {str(e)}")
            return {"error": f"Analysis failed: {str(e)}"}


# Global recommender instance
recommender = BookRecommender() 