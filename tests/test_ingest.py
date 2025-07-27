"""Tests for the ingestion module."""

import pytest
import pandas as pd
from datetime import datetime
from pathlib import Path
import tempfile
import os

from app.ingest import GoodreadsIngester


class TestGoodreadsIngester:
    """Test cases for GoodreadsIngester."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.ingester = GoodreadsIngester()
        
        # Create sample CSV data
        self.sample_data = [
            {
                'Book Id': '1',
                'Title': 'The Great Gatsby',
                'Author': 'F. Scott Fitzgerald',
                'ISBN': '9780743273565',
                'My Rating': '4',
                'Average Rating': '3.93',
                'Publisher': 'Simon & Schuster',
                'Pages': '180',
                'Year Published': '2004',
                'Original Publication Year': '1925',
                'Date Read (yyyy/mm/dd)': '2023/01/15',
                'Date Added (yyyy/mm/dd)': '2022/12/01',
                'Bookshelves': 'classics, fiction',
                'My Review': 'Beautiful prose and tragic story'
            },
            {
                'Book Id': '2',
                'Title': 'Dune',
                'Author': 'Frank Herbert',
                'ISBN': '9780441172719',
                'My Rating': '5',
                'Average Rating': '4.25',
                'Publisher': 'ACE',
                'Pages': '688',
                'Year Published': '1990',
                'Original Publication Year': '1965',
                'Date Read (yyyy/mm/dd)': '2023/03/20',
                'Date Added (yyyy/mm/dd)': '2023/01/10',
                'Bookshelves': 'science-fiction',
                'My Review': 'Epic science fiction masterpiece'
            }
        ]
    
    def test_parse_date(self):
        """Test date parsing functionality."""
        # Test valid dates
        assert self.ingester.parse_date('2023/01/15') == datetime(2023, 1, 15)
        assert self.ingester.parse_date('2023-01-15') == datetime(2023, 1, 15)
        
        # Test invalid dates
        assert self.ingester.parse_date('') is None
        assert self.ingester.parse_date('invalid') is None
        assert self.ingester.parse_date(None) is None
    
    def test_parse_rating(self):
        """Test rating parsing functionality."""
        # Test valid ratings
        assert self.ingester.parse_rating('4') == 4
        assert self.ingester.parse_rating('5') == 5
        
        # Test invalid ratings
        assert self.ingester.parse_rating('') is None
        assert self.ingester.parse_rating('0') is None
        assert self.ingester.parse_rating('invalid') is None
    
    def test_parse_year(self):
        """Test year parsing functionality."""
        # Test valid years
        assert self.ingester.parse_year('2004') == 2004
        assert self.ingester.parse_year('1965') == 1965
        
        # Test invalid years
        assert self.ingester.parse_year('') is None
        assert self.ingester.parse_year('1800') is None  # Too old
        assert self.ingester.parse_year('2030') is None  # Too new
        assert self.ingester.parse_year('invalid') is None
    
    def test_clean_text(self):
        """Test text cleaning functionality."""
        # Test normal text
        assert self.ingester.clean_text('  hello  world  ') == 'hello world'
        
        # Test empty/None text
        assert self.ingester.clean_text('') is None
        assert self.ingester.clean_text(None) is None
        assert self.ingester.clean_text('   ') is None
    
    def test_process_csv_row(self):
        """Test CSV row processing."""
        row = self.sample_data[0]
        book_data = self.ingester.process_csv_row(row)
        
        assert book_data.book_id == '1'
        assert book_data.title == 'The Great Gatsby'
        assert book_data.author == 'F. Scott Fitzgerald'
        assert book_data.my_rating == 4
        assert book_data.average_rating == 3.93
        assert book_data.publisher == 'Simon & Schuster'
        assert book_data.pages == 180
        assert book_data.year_published == 2004
        assert book_data.original_publication_year == 1925
        assert book_data.date_read == datetime(2023, 1, 15)
        assert book_data.date_added == datetime(2022, 12, 1)
        assert book_data.bookshelves == 'classics, fiction'
        assert book_data.my_review == 'Beautiful prose and tragic story'
    
    def test_ingest_csv(self):
        """Test CSV ingestion."""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame(self.sample_data)
            df.to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            # Test ingestion
            stats = self.ingester.ingest_csv(temp_path)
            
            assert stats['total_rows'] == 2
            assert stats['processed_books'] == 2
            assert stats['skipped_books'] == 0
            assert len(stats['errors']) == 0
        
        finally:
            # Clean up
            os.unlink(temp_path)
    
    def test_get_ingestion_stats(self):
        """Test ingestion statistics."""
        stats = self.ingester.get_ingestion_stats()
        
        # Should return valid stats structure
        assert 'total_books' in stats
        assert 'avg_rating' in stats
        assert 'rating_distribution' in stats
        assert 'genre_distribution' in stats
        assert 'author_distribution' in stats
        assert 'year_distribution' in stats


if __name__ == "__main__":
    pytest.main([__file__]) 