"""Tests for the insights module."""

import pytest
from unittest.mock import Mock, patch
import json

from app.insights import LiteraryInsightsGenerator


class TestLiteraryInsightsGenerator:
    """Test cases for LiteraryInsightsGenerator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock the Google Gemini API key
        with patch.dict('os.environ', {'GOOGLE_GEMINI_API_KEY': 'test_key'}):
            self.insights_generator = LiteraryInsightsGenerator()
    
    def test_create_aggregated_data(self):
        """Test aggregated data creation."""
        # Mock the database to return some books
        mock_book = Mock()
        mock_book.title = "Test Book"
        mock_book.author = "Test Author"
        mock_book.my_rating = 4
        mock_book.bookshelves = "fiction, sci-fi"
        mock_book.date_read = None
        mock_book.description = None
        mock_book.subjects = None
        
        with patch.object(self.insights_generator.db, 'get_all_books') as mock_get_books:
            mock_get_books.return_value = [mock_book]
            
            # Mock cluster stats
            with patch.object(self.insights_generator.clusterer, 'get_clustering_stats') as mock_cluster_stats:
                mock_cluster_stats.return_value = {
                    'num_clusters': 3,
                    'cluster_distribution': {0: 5, 1: 3, 2: 2}
                }
                
                # Mock cluster exemplars
                with patch.object(self.insights_generator.clusterer, 'get_all_cluster_exemplars') as mock_exemplars:
                    mock_exemplars.return_value = {
                        0: [{'title': 'Book 1', 'author': 'Author 1'}],
                        1: [{'title': 'Book 2', 'author': 'Author 2'}],
                        2: [{'title': 'Book 3', 'author': 'Author 3'}]
                    }
                    
                    aggregated_data = self.insights_generator.create_aggregated_data()
                    
                    # Check structure
                    assert 'total_books' in aggregated_data
                    assert 'average_rating' in aggregated_data
                    assert 'rating_distribution' in aggregated_data
                    assert 'top_genres' in aggregated_data
                    assert 'top_authors' in aggregated_data
                    assert 'cluster_analysis' in aggregated_data
    
    def test_parse_insights_response(self):
        """Test parsing of insights response."""
        response_text = """
        🎯 **Personality Type**
        This is the personality type section.
        
        🧠 **Intellectual Profile**
        This is the intellectual profile section.
        
        ❤️ **Emotional Preferences**
        This is the emotional preferences section.
        
        🎭 **Dominant Themes**
        This is the dominant themes section.
        
        📖 **Literary Portrait**
        This is the literary portrait section.
        """
        
        insights = self.insights_generator._parse_insights_response(response_text)
        
        # Check all sections are parsed
        assert 'personality_type' in insights
        assert 'intellectual_profile' in insights
        assert 'emotional_preferences' in insights
        assert 'dominant_themes' in insights
        assert 'literary_portrait' in insights
        
        # Check content
        assert 'personality type section' in insights['personality_type']
        assert 'intellectual profile section' in insights['intellectual_profile']
    
    def test_get_insights_stats(self):
        """Test insights statistics."""
        stats = self.insights_generator.get_insights_stats()
        
        # Should return valid stats structure
        assert 'total_books' in stats
        assert 'books_with_ratings' in stats
        assert 'books_with_clusters' in stats
        assert 'can_generate_insights' in stats
        assert 'reason' in stats
    
    @patch('google.generativeai.GenerativeModel')
    def test_generate_insights(self, mock_model):
        """Test insights generation."""
        # Mock the Gemini model
        mock_response = Mock()
        mock_response.text = """
        🎯 **Personality Type**
        Test personality type.
        
        🧠 **Intellectual Profile**
        Test intellectual profile.
        
        ❤️ **Emotional Preferences**
        Test emotional preferences.
        
        🎭 **Dominant Themes**
        Test dominant themes.
        
        📖 **Literary Portrait**
        Test literary portrait.
        """
        mock_model.return_value.generate_content.return_value = mock_response
        
        # Mock aggregated data
        with patch.object(self.insights_generator, 'create_aggregated_data') as mock_data:
            mock_data.return_value = {
                'total_books': 5,
                'average_rating': 4.0,
                'rating_distribution': {4: 3, 5: 2},
                'top_genres': {'fiction': 3},
                'top_authors': {'Author 1': 2},
                'cluster_analysis': {
                    'num_clusters': 2,
                    'cluster_distribution': {0: 3, 1: 2},
                    'exemplars': {0: [], 1: []}
                }
            }
            
            result = self.insights_generator.generate_insights()
            
            # Check result structure
            assert result.get('success') is True
            assert 'insights' in result
            assert 'data_summary' in result
            
            # Check insights sections
            insights = result['insights']
            assert 'personality_type' in insights
            assert 'intellectual_profile' in insights
            assert 'emotional_preferences' in insights
            assert 'dominant_themes' in insights
            assert 'literary_portrait' in insights


if __name__ == "__main__":
    pytest.main([__file__]) 