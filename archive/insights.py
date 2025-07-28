"""Literary psychology insights using Google Gemini."""

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
from .cluster import clusterer

logger = logging.getLogger(__name__)


class LiteraryInsightsGenerator:
    """Generates deep, non-deterministic literary psychology insights."""
    
    def __init__(self):
        self.db = db_manager
        self.clusterer = clusterer
        
        # Initialize Google Gemini
        api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        if not api_key:
            logger.warning("No Google Gemini API key provided. Insights generation will be disabled.")
            self.model = None
        else:
            genai.configure(api_key=api_key)
            model_name = os.getenv("GEMINI_INSIGHTS_MODEL", "gemini-2.5-flash")
            self.model = genai.GenerativeModel(model_name)
        
        # Load prompt template
        prompt_path = Path(__file__).parent.parent / "prompts" / "insight_prompt.md"
        with open(prompt_path, 'r') as f:
            self.prompt_template = f.read()
    
    # def create_aggregated_data(self, use_clustering: bool = True) -> Dict[str, Any]:
    def create_aggregated_data(self) -> Dict[str, Any]:
        """Create aggregated data for insight generation."""
        books = self.db.get_all_books()
        
        if not books:
            return {"error": "No books found"}
        
        # Basic statistics
        total_books = len(books)
        ratings = [book.my_rating for book in books if book.my_rating]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # Genre analysis
        genre_counts = {}
        for book in books:
            if book.bookshelves:
                genres = [g.strip() for g in book.bookshelves.split(',')]
                for genre in genres:
                    if genre:
                        genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # Author analysis
        author_counts = {}
        for book in books:
            if book.author:
                author_counts[book.author] = author_counts.get(book.author, 0) + 1
        
        # Rating distribution
        rating_dist = {}
        for rating in ratings:
            rating_dist[rating] = rating_dist.get(rating, 0) + 1
        
        # Temporal analysis
        books_with_dates = [book for book in books if book.date_read is not None]
        if books_with_dates:
            books_with_dates.sort(key=lambda x: x.date_read)  # type: ignore
            start_date = books_with_dates[0].date_read
            end_date = books_with_dates[-1].date_read
            total_days = (end_date - start_date).days if start_date and end_date else 0
            books_per_month = len(books_with_dates) / max(1, total_days / 30) if total_days else len(books_with_dates)
            reading_timeline = {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None,
                'total_days': total_days,
                'books_per_month': books_per_month
            }
        else:
            reading_timeline = {}
        
        # Enrichment analysis
        enriched_books = [book for book in books if book.description or book.subjects or book.genres]
        enrichment_rate = len(enriched_books) / len(books) if books else 0
        
        # Create aggregated data
        aggregated_data = {
            "total_books": total_books,
            "average_rating": round(avg_rating, 2),
            "rating_distribution": rating_dist,
            "top_genres": dict(sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "top_authors": dict(sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "reading_timeline": reading_timeline,
            "enrichment_rate": round(enrichment_rate * 100, 2),
            "all_books": [
                {
                    "title": book.title,
                    "author": book.author,
                    "rating": book.my_rating,
                    "genres": book.bookshelves,
                    "date_read": book.date_read.isoformat() if book.date_read else None,
                    "review": book.my_review,
                    "description": book.description,
                    "subjects": book.subjects
                }
                for book in books  # Include all books with full details
            ]
        }
        
        # # Add clustering data if requested and available
        # if use_clustering:
        #     try:
        #         cluster_stats = self.clusterer.get_clustering_stats()
        #         cluster_exemplars = self.clusterer.get_all_cluster_exemplars()
        #         
        #         aggregated_data["cluster_analysis"] = {
        #             "num_clusters": cluster_stats.get('num_clusters', 0),
        #             "cluster_distribution": cluster_stats.get('cluster_distribution', {}),
        #             "exemplars": cluster_exemplars
        #         }
        #     except Exception as e:
        #         logger.warning(f"Clustering data not available: {str(e)}")
        #         aggregated_data["cluster_analysis"] = {
        #             "num_clusters": 0,
        #             "cluster_distribution": {},
        #             "exemplars": []
        #         }
        
        return aggregated_data

    # def generate_insights(self, use_clustering: bool = False) -> Dict[str, Any]:
    def generate_insights(self) -> Dict[str, Any]:
        """Generate deep literary psychology insights."""
        try:
            if not self.model:
                db_manager.add_llm_history(LLMHistoryCreate(
                    prompt="MODEL NOT AVAILABLE",
                    response="Google Gemini model not available. Please set GOOGLE_GEMINI_API_KEY environment variable.",
                    extra="{\"status\": \"error\"}"
                ))
                return {"error": "Google Gemini model not available. Please set GOOGLE_GEMINI_API_KEY environment variable.", "raw_response": "Google Gemini model not available. Please set GOOGLE_GEMINI_API_KEY environment variable."}
            aggregated_data = self.create_aggregated_data()
            if "error" in aggregated_data:
                db_manager.add_llm_history(LLMHistoryCreate(
                    prompt="AGGREGATION ERROR",
                    response=aggregated_data["error"],
                    extra="{\"status\": \"error\"}"
                ))
                return {"error": aggregated_data["error"], "raw_response": aggregated_data["error"]}
            data_json = json.dumps(aggregated_data, indent=2)
            full_prompt = self.prompt_template.strip() + "\n\nBOOKS DATA:\n" + data_json
            logger.info("Generating literary psychology insights...")
            response = self.model.generate_content(full_prompt)
            logger.info(f"LLM raw response: {response.text}")
            db_manager.add_llm_history(LLMHistoryCreate(
                prompt=full_prompt,
                response=response.text or "",
                extra=json.dumps({"status": "success" if response.text else "error"})
            ))
            if not response.text:
                return {"error": "No response from LLM", "raw_response": ""}
            insights = self._parse_insights_response(response.text)
            return {
                "success": True,
                "insights": insights,
                "raw_response": response.text,
                "data_summary": {
                    "total_books": aggregated_data["total_books"],
                    "avg_rating": aggregated_data["average_rating"]
                }
            }
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            db_manager.add_llm_history(LLMHistoryCreate(
                prompt="EXCEPTION",
                response=str(e),
                extra="{\"status\": \"error\"}"
            ))
            return {"error": str(e), "raw_response": str(e)}
    
    def _parse_insights_response(self, response_text: str) -> Dict[str, str]:
        """Parse the LLM response to extract the five insight sections."""
        sections = {}
        
        # Define section markers
        section_markers = [
            ("🎯 **Personality Type**", "🧠 **Intellectual Profile**"),
            ("🧠 **Intellectual Profile**", "❤️ **Emotional Preferences**"),
            ("❤️ **Emotional Preferences**", "🎭 **Dominant Themes**"),
            ("🎭 **Dominant Themes**", "📖 **Literary Portrait**"),
            ("📖 **Literary Portrait**", None)
        ]
        
        for i, (start_marker, end_marker) in enumerate(section_markers):
            try:
                # Find start of section
                start_idx = response_text.find(start_marker)
                if start_idx == -1:
                    continue
                
                # Find end of section
                if end_marker:
                    end_idx = response_text.find(end_marker, start_idx)
                else:
                    end_idx = len(response_text)
                
                if end_idx == -1:
                    end_idx = len(response_text)
                
                # Extract section content
                section_start = start_idx + len(start_marker)
                section_content = response_text[section_start:end_idx].strip()
                
                # Clean up the content
                section_content = section_content.strip()
                if section_content.startswith("**"):
                    section_content = section_content[2:]
                if section_content.endswith("**"):
                    section_content = section_content[:-2]
                
                # Map to section names
                section_names = [
                    "personality_type",
                    "intellectual_profile", 
                    "emotional_preferences",
                    "dominant_themes",
                    "literary_portrait"
                ]
                
                sections[section_names[i]] = section_content
                
            except Exception as e:
                logger.warning(f"Error parsing section {i}: {str(e)}")
                continue
        
        return sections
    
    def get_insights_stats(self) -> Dict[str, Any]:
        """Get statistics about the insights generation capability."""
        books = self.db.get_all_books()
        
        if not books:
            return {
                "total_books": 0,
                "can_generate_insights": False,
                "reason": "No books in database"
            }
        
        # Check if we have enough data for meaningful insights
        books_with_ratings = [book for book in books if book.my_rating]
        
        # Simplified requirements - no longer need clustering
        can_generate = (
            len(books) >= 5 and
            len(books_with_ratings) >= 3
        )
        
        return {
            "total_books": len(books),
            "books_with_ratings": len(books_with_ratings),
            "can_generate_insights": can_generate,
            "reason": "Insufficient data" if not can_generate else "Ready"
        }


# Global insights generator instance
insights_generator = LiteraryInsightsGenerator() 