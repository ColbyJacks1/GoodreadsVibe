"""Comprehensive book analysis using Google Gemini."""

# Version: 2024-12-19 - Fixed for Streamlit Cloud deployment
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
        
        # Load comprehensive prompt template (for parallel analysis)
        prompt_path = Path(__file__).parent.parent / "prompts" / "comprehensive_analysis_prompt_parallel.md"
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



    def generate_quick_analysis(self) -> Dict[str, Any]:
        """Generate quick analysis (roast + recommendations) for immediate display."""
        try:
            if not self.model:
                logger.warning("Gemini model not available, returning test data")
                # Return test data for development/testing
                test_response = """## ROAST ME

### 🎭 Reader Summary
You're a fascinating reader with eclectic tastes! Your bookshelf is like a literary buffet - a little bit of everything, which suggests you're either incredibly curious or just can't commit to one genre.

### 🔥 Literary Roast
• You've read so much fiction that your friends probably think you're preparing for a career in daydreaming. Your reality-avoidance skills are truly impressive!
• Your rating pattern suggests you're either very generous with your stars or very easily pleased. Either way, you're the kind of person who gives 5 stars to a restaurant just because they remembered your name.
• For someone who claims to love literature, you sure spend a lot of time reading about [insert genre here]. Make up your mind! Are you a serious reader or just someone who likes pretty book covers?

### 📊 Reading Habits Exposed
- **Most Read Genre:** Fiction - You're clearly avoiding reality like it's your job!
- **Reading Speed:** Moderate - Not too fast, not too slow, just right for procrastination!
- **Rating Pattern:** Generous - You're either very kind or very easily pleased!

### 🔮 Brutally Honest Predictions
Based on your reading patterns, I predict you'll continue to buy more books than you can read, and your "to-read" list will grow faster than your "read" list. You're also likely to have at least one book that's been "currently reading" for over a year.

## PERSONALIZED RECOMMENDATIONS

### 📚 Curated Book Recommendations
Based on your reading patterns, here are some recommendations:

### 1. The Great Gatsby by F. Scott Fitzgerald
- **Why this book:** Classic literature that matches your sophisticated tastes
- **Connection to your reading:** Fits your preference for well-crafted prose
- **Themes:** American Dream, love, and the Jazz Age

### 2. 1984 by George Orwell
- **Why this book:** Dystopian fiction that will challenge your thinking
- **Connection to your reading:** Expands your genre horizons
- **Themes:** Totalitarianism, surveillance, and truth

### 3. Sapiens by Yuval Noah Harari
- **Why this book:** Non-fiction that will balance your reading diet
- **Connection to your reading:** Provides intellectual stimulation
- **Themes:** Human history, evolution, and society

### 🎯 Genre Expansion
You should explore more non-fiction and historical fiction to balance your reading diet. Consider branching out into science writing and philosophy to challenge your perspectives."""
                
                # Parse the test response
                parsed_sections = self._parse_quick_response(test_response)
                
                return {
                    "success": True,
                    "quick_analysis": test_response,
                    "parsed_sections": parsed_sections,
                    "raw_response": test_response
                }
            
            books = self.db.get_all_books()
            if not books:
                return {"error": "No books found"}
            
            books_text = self._format_books(books)
            
            # Load quick analysis prompt
            prompt_path = Path(__file__).parent.parent / "prompts" / "quick_analysis_prompt.md"
            with open(prompt_path, 'r') as f:
                quick_prompt_template = f.read()
            
            quick_prompt = quick_prompt_template.format(books=books_text)
            
            logger.info("Generating quick analysis...")
            response = self.model.generate_content(quick_prompt)
            
            if not response.text:
                return {"error": "No response from LLM"}
            
            # Parse quick response
            parsed_sections = self._parse_quick_response(response.text)
            
            return {
                "success": True,
                "quick_analysis": response.text,
                "parsed_sections": parsed_sections,
                "raw_response": response.text
            }
        
        except Exception as e:
            logger.error(f"Error generating quick analysis: {str(e)}")
            return {"error": str(e)}

    def generate_comprehensive_analysis_parallel(self) -> Dict[str, Any]:
        """Generate comprehensive analysis (insights + profile) for secondary display."""
        try:
            if not self.model:
                logger.warning("Gemini model not available, returning test data")
                # Return test data for development/testing
                test_response = """## LITERARY PSYCHOLOGY INSIGHTS

### 📖 Literary Portrait
You are a thoughtful reader with diverse interests who enjoys both intellectual challenge and emotional depth. Your reading choices reveal someone who values both cognitive stimulation and psychological insight.

### 🎭 Dominant Themes
Your reading shows a balance between fiction and non-fiction, with recurring themes of human psychology, social commentary, and personal growth. You're drawn to stories that explore the complexities of human nature.

### ❤️ Reading Journey Timeline
Your reading has evolved over time, showing growth and exploration. You've moved from simple entertainment to more complex narratives that challenge your thinking and expand your worldview.

### 🎯 Personality Type
You are an analytical reader who enjoys depth and complexity. You prefer books that challenge your thinking and offer new perspectives on familiar topics.

### 🧠 Intellectual Profile
You prefer books that challenge your thinking and expand your worldview. You're comfortable with uncertainty and appreciate authors who trust their readers to navigate complexity.

## PERSONAL PROFILE ANALYSIS

### Core Demographics
- **Age & Life Stage:** Adult with established reading habits
- **Education Level:** Well-educated with intellectual curiosity
- **Professional Field:** Likely in a knowledge-based profession
- **Geographic Location:** English-speaking region
- **Family Status:** Independent adult

### Mindset & Preferences
- **Politics & Values:** Open-minded and curious
- **Risk Tolerance:** Moderate, with intellectual exploration
- **Learning Style:** Analytical and reflective
- **Information Diet:** Diverse and balanced
- **Life Arc:** Growth-oriented and curious

### DETAILED ANALYSIS

**Age and Life Stage**
- **Conclusion:** Adult reader with established patterns
- **Evidence:** Consistent reading habits over time
- **Confidence:** High
- **Notes:** Reading patterns suggest mature perspective

**Education Level**
- **Conclusion:** Well-educated with intellectual interests
- **Evidence:** Preference for complex narratives and non-fiction
- **Confidence:** Medium
- **Notes:** Reading choices indicate sophisticated tastes

**Professional Field**
- **Conclusion:** Knowledge-based profession
- **Evidence:** Interest in intellectual and analytical content
- **Confidence:** Medium
- **Notes:** Reading patterns suggest professional development interests

**Learning Style**
- **Conclusion:** Analytical and reflective learner
- **Evidence:** Preference for complex narratives and thought-provoking content
- **Confidence:** High
- **Notes:** Clear preference for intellectually challenging material

**Information Diet**
- **Conclusion:** Diverse and balanced approach
- **Evidence:** Mix of fiction and non-fiction across multiple genres
- **Confidence:** High
- **Notes:** Healthy balance between entertainment and education"""
                
                # Parse the test response
                parsed_sections = self._parse_comprehensive_response_parallel(test_response)
                
                return {
                    "success": True,
                    "comprehensive_analysis_parallel": test_response,
                    "parsed_sections": parsed_sections,
                    "raw_response": test_response
                }
            
            books = self.db.get_all_books()
            if not books:
                return {"error": "No books found"}
            
            books_text = self._format_books(books)
            
            # Load comprehensive analysis prompt
            prompt_path = Path(__file__).parent.parent / "prompts" / "comprehensive_analysis_prompt_parallel.md"
            with open(prompt_path, 'r') as f:
                comprehensive_prompt_template = f.read()
            
            comprehensive_prompt = comprehensive_prompt_template.format(books=books_text)
            
            logger.info("Generating comprehensive analysis parallel...")
            response = self.model.generate_content(comprehensive_prompt)
            
            if not response.text:
                return {"error": "No response from LLM"}
            
            # Parse comprehensive response
            parsed_sections = self._parse_comprehensive_response_parallel(response.text)
            
            return {
                "success": True,
                "comprehensive_analysis_parallel": response.text,
                "parsed_sections": parsed_sections,
                "raw_response": response.text
            }
        
        except Exception as e:
            logger.error(f"Error generating comprehensive analysis parallel: {str(e)}")
            return {"error": str(e)}
    


    def _parse_quick_response(self, response_text: str) -> Dict[str, str]:
        """Parse the quick response into separate sections."""
        sections = {
            "humorous": "",
            "recommendations": ""
        }
        
        # Debug: Log the raw response to see what we're working with
        logger.info(f"Raw quick response: {response_text[:500]}...")
        
        # Parse quick response (roast + recommendations)
        lines = response_text.split('\n')
        current_section = None
        current_content = []
        
        # Multiple header patterns to try
        roast_headers = [
            "## ROAST ME",
            "## HUMOROUS ROAST ANALYSIS", 
            "## ROAST",
            "ROAST ME",
            "HUMOROUS ROAST"
        ]
        
        recommendations_headers = [
            "## PERSONALIZED RECOMMENDATIONS",
            "## RECOMMENDATIONS",
            "## BOOK RECOMMENDATIONS",
            "PERSONALIZED RECOMMENDATIONS"
        ]
        
        for line in lines:
            # Check for roast section with multiple header patterns
            if any(header in line for header in roast_headers):
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "humorous"
                current_content = [line]
                logger.info(f"Found roast section with header: {line}")
            elif any(header in line for header in recommendations_headers):
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "recommendations"
                current_content = [line]
                logger.info(f"Found recommendations section with header: {line}")
            elif current_section:
                current_content.append(line)
        
        # Add the last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content)
        
        # Fallback: If no sections found, try to split by common patterns
        if not sections["humorous"] and not sections["recommendations"]:
            logger.warning("No sections found with headers, trying fallback parsing...")
            sections = self._fallback_parse_quick_response(response_text)
        
        # Debug: Log what we found
        logger.info(f"Parsed sections - humorous: {len(sections['humorous'])} chars, recommendations: {len(sections['recommendations'])} chars")
        
        return sections
    
    def _fallback_parse_quick_response(self, response_text: str) -> Dict[str, str]:
        """Fallback parsing when headers aren't found."""
        sections = {
            "humorous": "",
            "recommendations": ""
        }
        
        # Try to find content by looking for key phrases
        text_lower = response_text.lower()
        
        # Look for roast indicators
        roast_indicators = ["roast", "humorous", "witty", "sarcastic", "reader summary", "literary roast"]
        recommendations_indicators = ["recommendations", "suggestions", "books to read", "curated"]
        
        # Split the text roughly in half and assign based on content
        lines = response_text.split('\n')
        mid_point = len(lines) // 2
        
        first_half = '\n'.join(lines[:mid_point])
        second_half = '\n'.join(lines[mid_point:])
        
        # Check which half has more roast indicators
        first_roast_score = sum(1 for indicator in roast_indicators if indicator in first_half.lower())
        second_roast_score = sum(1 for indicator in roast_indicators if indicator in second_half.lower())
        
        if first_roast_score > second_roast_score:
            sections["humorous"] = first_half
            sections["recommendations"] = second_half
        else:
            sections["humorous"] = second_half
            sections["recommendations"] = first_half
        
        logger.info(f"Fallback parsing - assigned {len(sections['humorous'])} chars to humorous, {len(sections['recommendations'])} chars to recommendations")
        
        return sections

    def _parse_comprehensive_response_parallel(self, response_text: str) -> Dict[str, str]:
        """Parse the comprehensive response parallel into separate sections."""
        sections = {
            "insights": "",
            "profile": ""
        }
        
        # Parse comprehensive response (insights + profile)
        lines = response_text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
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
print("🔄 Creating comprehensive_analyzer instance...")
comprehensive_analyzer = ComprehensiveAnalyzer()
print(f"✅ Created comprehensive_analyzer with methods: {[m for m in dir(comprehensive_analyzer) if not m.startswith('_')]}")
