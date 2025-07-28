"""Tests for the Gemini-based recommendation system."""

import pytest
from unittest.mock import patch, MagicMock
import json
import os

from app.recommend import BookRecommender


class TestBookRecommender:
    """Test the BookRecommender class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch.dict('os.environ', {'GOOGLE_GEMINI_API_KEY': 'test_key'}):
            self.recommender = BookRecommender()
    
    def test_init_without_api_key(self):
        """Test initialization without API key."""
        with patch.dict('os.environ', {}, clear=True):
            recommender = BookRecommender()
            assert recommender.model is None
    
    def test_init_with_api_key(self):
        """Test initialization with API key."""
        with patch.dict('os.environ', {'GOOGLE_GEMINI_API_KEY': 'test_key'}):
            with patch('google.generativeai.configure') as mock_configure:
                with patch('google.generativeai.GenerativeModel') as mock_model:
                    recommender = BookRecommender()
                    mock_configure.assert_called_once_with(api_key='test_key')
                    mock_model.assert_called_once()
    
    def test_format_reading_history(self):
        """Test formatting reading history."""
        # Mock books
        mock_books = [
            MagicMock(
                title="Test Book 1",
                author="Author 1",
                my_rating=5,
                date_read=None,
                date_added=None,
                genres="Fiction",
                my_review="Great book!"
            ),
            MagicMock(
                title="Test Book 2",
                author="Author 2",
                my_rating=4,
                date_read=None,
                date_added=None,
                genres="Non-fiction",
                my_review=None
            )
        ]
        
        history = self.recommender._format_reading_history(mock_books)
        assert "Test Book 1 by Author 1" in history
        assert "Test Book 2 by Author 2" in history
        assert "Rating: 5" in history
        assert "Rating: 4" in history
        assert "[Genres: Fiction]" in history
        assert "[Genres: Non-fiction]" in history
    
    def test_format_available_books(self):
        """Test formatting available books."""
        # Mock books
        mock_books = [
            MagicMock(
                title="Available Book 1",
                author="Author 1",
                average_rating=4.5,
                year_published=2020,
                genres="Fiction",
                description="A great book about..."
            ),
            MagicMock(
                title="Available Book 2",
                author="Author 2",
                average_rating=None,
                year_published=None,
                genres=None,
                description=None
            )
        ]
        
        books_text = self.recommender._format_available_books(mock_books)
        assert "Available Book 1 by Author 1" in books_text
        assert "Available Book 2 by Author 2" in books_text
        assert "(Rating: 4.5)" in books_text
        assert "(2020)" in books_text
        assert "[Genres: Fiction]" in books_text
    
    def test_validate_recommendation(self):
        """Test recommendation validation."""
        # Valid recommendation
        valid_rec = {
            "book_id": "123",
            "title": "Test Book",
            "author": "Test Author",
            "explanation": "Great book!"
        }
        assert self.recommender._validate_recommendation(valid_rec) is True
        
        # Invalid recommendation (missing fields)
        invalid_rec = {
            "book_id": "123",
            "title": "Test Book"
            # Missing author and explanation
        }
        assert self.recommender._validate_recommendation(invalid_rec) is False
    
    def test_extract_recommendations_from_text(self):
        """Test extracting recommendations from text."""
        text = """
        Here are some recommendations:
        1. The Great Gatsby by F. Scott Fitzgerald
        2. 1984 by George Orwell
        3. To Kill a Mockingbird by Harper Lee
        """
        
        recommendations = self.recommender._extract_recommendations_from_text(text, 2)
        
        assert len(recommendations) == 2
        assert recommendations[0]["title"] == "The Great Gatsby"
        assert recommendations[0]["author"] == "F. Scott Fitzgerald"
        assert recommendations[1]["title"] == "1984"
        assert recommendations[1]["author"] == "George Orwell"
    
    @patch('app.recommend.BookRecommender._create_recommendation_context')
    def test_recommend_books_success(self, mock_create_context):
        """Test successful book recommendations."""
        # Mock the context creation
        mock_create_context.return_value = "Test prompt"
        
        # Mock the Gemini model response
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "recommendations": [
                {
                    "book_id": "123",
                    "title": "Test Book",
                    "author": "Test Author",
                    "explanation": "Great recommendation!",
                    "relevance_score": 0.9,
                    "themes": ["fiction", "adventure"],
                    "connections": "Matches your interests"
                }
            ]
        })
        
        self.recommender.model = MagicMock()
        self.recommender.model.generate_content.return_value = mock_response
        
        # Mock database
        with patch.object(self.recommender.db, 'get_book') as mock_get_book:
            mock_book = MagicMock()
            mock_book.publisher = "Test Publisher"
            mock_book.year_published = 2020
            mock_get_book.return_value = mock_book
            
            with patch.object(self.recommender.db, 'add_llm_history') as mock_add_history:
                recommendations = self.recommender.recommend_books("test query", 5)
                
                assert len(recommendations) == 1
                assert recommendations[0]["title"] == "Test Book"
                assert recommendations[0]["author"] == "Test Author"
                assert recommendations[0]["explanation"] == "Great recommendation!"
                assert recommendations[0]["relevance_score"] == 0.9
                assert recommendations[0]["publisher"] == "Test Publisher"
                assert recommendations[0]["year_published"] == 2020
                
                # Verify LLM history was logged
                mock_add_history.assert_called_once()
    
    def test_recommend_books_no_model(self):
        """Test recommendations when model is not available."""
        self.recommender.model = None
        recommendations = self.recommender.recommend_books("test query")
        assert recommendations == []
    
    def test_get_recommendation_explanation(self):
        """Test getting recommendation explanation."""
        recommendation = {
            "explanation": "This book matches your interests in science fiction",
            "connections": "Similar to books you've enjoyed"
        }
        
        explanation = self.recommender.get_recommendation_explanation(recommendation)
        assert explanation == "This book matches your interests in science fiction"
        
        # Test fallback
        recommendation_no_explanation = {"title": "Test Book"}
        explanation = self.recommender.get_recommendation_explanation(recommendation_no_explanation)
        assert explanation == "No explanation available"
    
    def test_get_recommendation_stats(self):
        """Test getting recommendation statistics."""
        with patch.object(self.recommender.db, 'get_all_books') as mock_get_books:
            mock_books = [
                MagicMock(my_rating=5),
                MagicMock(my_rating=4),
                MagicMock(my_rating=None),
                MagicMock(my_rating=3)
            ]
            mock_get_books.return_value = mock_books
            
            stats = self.recommender.get_recommendation_stats()
            
            assert stats['total_books'] == 4
            assert stats['rated_books'] == 3
            assert stats['average_rating'] == 4.0
            assert 'model_available' in stats
            assert 'model_name' in stats
    
    def test_analyze_reading_preferences_no_model(self):
        """Test reading preferences analysis when model is not available."""
        self.recommender.model = None
        result = self.recommender.analyze_reading_preferences()
        assert result == {"error": "Gemini model not available"}
    
    def test_analyze_reading_preferences_no_books(self):
        """Test reading preferences analysis with no books."""
        with patch.object(self.recommender.db, 'get_all_books') as mock_get_books:
            mock_get_books.return_value = []
            
            result = self.recommender.analyze_reading_preferences()
            assert result == {"error": "No books found"} 