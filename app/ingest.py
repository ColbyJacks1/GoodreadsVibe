"""CSV ingestion and data processing."""

import csv
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd
import re

from .db import db_manager, BookCreate


logger = logging.getLogger(__name__)


class GenreNormalizer:
    """Normalizes inconsistent Goodreads genres into standardized categories."""
    
    def __init__(self):
        # Define genre mapping rules
        self.genre_mappings = {
            # Fiction categories
            'fiction': ['fiction', 'general', 'literary-fiction', 'literary', 'contemporary-fiction'],
            'science_fiction': ['science-fiction', 'sci-fi', 'scifi', 'science fiction', 'sf'],
            'fantasy': ['fantasy', 'epic-fantasy', 'high-fantasy', 'urban-fantasy', 'dark-fantasy'],
            'mystery': ['mystery', 'detective', 'crime', 'thriller', 'suspense'],
            'romance': ['romance', 'romantic', 'love-story', 'chick-lit', 'women-fiction'],
            'historical_fiction': ['historical-fiction', 'historical', 'period-fiction'],
            'young_adult': ['young-adult', 'ya', 'teen', 'adolescent', 'juvenile-fiction'],
            'children': ['children', 'childrens', 'kids', 'middle-grade', 'juvenile'],
            'classics': ['classics', 'classic', 'literary-classics', 'canon'],
            
            # Non-fiction categories
            'non_fiction': ['non-fiction', 'nonfiction', 'general-non-fiction'],
            'biography': ['biography', 'biographies', 'memoir', 'autobiography'],
            'history': ['history', 'historical', 'world-war', '1939-1945', 'military-history'],
            'philosophy': ['philosophy', 'philosophical', 'ethics', 'metaphysics'],
            'science': ['science', 'scientific', 'physics', 'chemistry', 'biology'],
            'psychology': ['psychology', 'psychological', 'psych', 'mental-health'],
            'self_help': ['self-help', 'selfhelp', 'personal-development', 'motivation'],
            'business': ['business', 'economics', 'finance', 'management', 'leadership'],
            'politics': ['politics', 'political', 'government', 'current-events'],
            'religion': ['religion', 'religious', 'spirituality', 'theology'],
            'travel': ['travel', 'travelogue', 'adventure', 'exploration'],
            'cookbook': ['cookbook', 'cooking', 'food', 'recipes', 'culinary'],
            'art': ['art', 'artistic', 'design', 'photography', 'architecture'],
            'education': ['education', 'academic', 'textbook', 'reference'],
            
            # Special categories
            'poetry': ['poetry', 'poems', 'verse'],
            'drama': ['drama', 'plays', 'theater', 'theatre'],
            'comics': ['comics', 'graphic-novel', 'manga', 'superhero'],
            'horror': ['horror', 'scary', 'supernatural', 'paranormal'],
            'western': ['western', 'cowboy', 'wild-west'],
            'war': ['war', 'military', 'battle', 'conflict'],
            'adventure': ['adventure', 'action', 'exploration'],
            'satire': ['satire', 'humor', 'comedy', 'funny'],
            'dystopian': ['dystopian', 'dystopia', 'post-apocalyptic'],
            'steampunk': ['steampunk', 'cyberpunk', 'alternate-history'],
        }
        
        # Create reverse mapping for quick lookup
        self.reverse_mappings = {}
        for normalized_genre, variants in self.genre_mappings.items():
            for variant in variants:
                self.reverse_mappings[variant.lower()] = normalized_genre
    
    def normalize_genre(self, genre_text: str) -> Optional[str]:
        """Normalize a single genre text to a standard category."""
        if not genre_text:
            return None
        
        # Clean the genre text
        cleaned = re.sub(r'[^\w\s-]', '', genre_text.lower().strip())
        
        # Direct match
        if cleaned in self.reverse_mappings:
            return self.reverse_mappings[cleaned]
        
        # Partial match (check if any variant is contained in the text)
        for variant, normalized in self.reverse_mappings.items():
            if variant in cleaned or cleaned in variant:
                return normalized
        
        # Check for common patterns
        if any(word in cleaned for word in ['fiction', 'novel']):
            return 'fiction'
        elif any(word in cleaned for word in ['non-fiction', 'nonfiction']):
            return 'non_fiction'
        elif any(word in cleaned for word in ['classic', 'canon']):
            return 'classics'
        elif any(word in cleaned for word in ['young', 'teen', 'ya']):
            return 'young_adult'
        elif any(word in cleaned for word in ['child', 'kid']):
            return 'children'
        
        return None
    
    def normalize_bookshelves(self, bookshelves: str) -> List[str]:
        """Normalize bookshelves string to a list of standardized genres."""
        if not bookshelves:
            return []
        
        # Split by common delimiters
        genres = re.split(r'[,;|]', bookshelves)
        normalized_genres = []
        
        for genre in genres:
            normalized = self.normalize_genre(genre.strip())
            if normalized and normalized not in normalized_genres:
                normalized_genres.append(normalized)
        
        return normalized_genres


class GoodreadsIngester:
    """Handles ingestion of Goodreads CSV data."""
    
    def __init__(self):
        self.db = db_manager
        self.genre_normalizer = GenreNormalizer()
    
    def parse_date(self, date_str) -> Optional[datetime]:
        """Parse date string from Goodreads format."""
        if not date_str or (isinstance(date_str, str) and date_str.strip() == ''):
            return None
        try:
            value = date_str.strip() if isinstance(date_str, str) else str(date_str)
            for fmt in ['%Y/%m/%d', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            return None
        except Exception:
            return None

    def parse_rating(self, rating_str) -> Optional[int]:
        """Parse rating string to integer."""
        if not rating_str or (isinstance(rating_str, str) and rating_str.strip() == ''):
            return None
        try:
            value = rating_str.strip() if isinstance(rating_str, str) else rating_str
            rating = float(value)
            return int(rating) if rating > 0 else None
        except (ValueError, TypeError):
            return None

    def parse_year(self, year_str) -> Optional[int]:
        """Parse year string to integer."""
        if not year_str or (isinstance(year_str, str) and year_str.strip() == ''):
            return None
        try:
            value = year_str.strip() if isinstance(year_str, str) else year_str
            year = int(value)
            return year if 1500 <= year <= 2030 else None
        except (ValueError, TypeError):
            return None

    def parse_pages(self, pages_str) -> Optional[int]:
        """Parse pages string to integer."""
        if not pages_str or (isinstance(pages_str, str) and pages_str.strip() == ''):
            return None
        try:
            value = pages_str.strip() if isinstance(pages_str, str) else pages_str
            pages = int(value)
            return pages if pages > 0 else None
        except (ValueError, TypeError):
            return None
    
    def clean_text(self, text) -> Optional[str]:
        """Clean and normalize text fields."""
        if not text or not isinstance(text, str):
            return None
        
        # Remove extra whitespace and normalize
        cleaned = ' '.join(text.strip().split())
        return cleaned if cleaned else None
    
    def process_csv_row(self, row: Dict[str, Any]) -> BookCreate:
        """Process a single CSV row into a BookCreate object."""
        # Normalize genres from bookshelves
        bookshelves = self.clean_text(row.get('Bookshelves', ''))
        normalized_genres = self.genre_normalizer.normalize_bookshelves(bookshelves or '')
        genres_str = ', '.join(normalized_genres) if normalized_genres else None
        
        return BookCreate(
            book_id=str(row.get('Book Id', '')),
            title=self.clean_text(row.get('Title', '')),
            author=self.clean_text(row.get('Author', '')),
            isbn=self.clean_text(row.get('ISBN', '')),
            isbn13=self.clean_text(row.get('ISBN13', '')),
            my_rating=self.parse_rating(row.get('My Rating', '')),
            average_rating=self.parse_rating(row.get('Average Rating', '')),
            publisher=self.clean_text(row.get('Publisher', '')),
            pages=self.parse_pages(row.get('Number of Pages', '')),
            year_published=self.parse_year(row.get('Year Published', '')),
            original_publication_year=self.parse_year(row.get('Original Publication Year', '')),
            date_read=self.parse_date(row.get('Date Read', '')),
            date_added=self.parse_date(row.get('Date Added', '')),
            bookshelves=bookshelves,  # Keep original for reference
            my_review=self.clean_text(row.get('My Review', '')),
            genres=genres_str  # Add normalized genres
        )
    
    def ingest_csv(self, file_path: str) -> Dict[str, Any]:
        """Ingest a Goodreads CSV file and return statistics."""
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        logger.info(f"Starting ingestion of {file_path}")
        
        stats = {
            'total_rows': 0,
            'processed_books': 0,
            'skipped_books': 0,
            'errors': []
        }
        
        try:
            # Use pandas for better CSV handling
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} rows from CSV")
            
            for index, row in df.iterrows():
                stats['total_rows'] += 1
                
                try:
                    # Convert row to dict for processing
                    row_dict = row.to_dict()
                    
                    # Skip rows without essential data
                    if not row_dict.get('Title') or not row_dict.get('Author'):
                        stats['skipped_books'] += 1
                        continue
                    
                    # Process the row
                    book_data = self.process_csv_row(row_dict)
                    
                    # Check if book already exists
                    existing_book = self.db.get_book(book_data.book_id)
                    if existing_book:
                        logger.debug(f"Book already exists: {book_data.title}")
                        stats['skipped_books'] += 1
                        continue
                    
                    # Add to database
                    self.db.add_book(book_data)
                    stats['processed_books'] += 1
                    
                    if stats['processed_books'] % 100 == 0:
                        logger.info(f"Processed {stats['processed_books']} books...")
                
                except Exception as e:
                    error_msg = f"Error processing row {index + 1}: {str(e)}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)
                    stats['skipped_books'] += 1
            
            logger.info(f"Ingestion complete. Processed: {stats['processed_books']}, "
                       f"Skipped: {stats['skipped_books']}, Errors: {len(stats['errors'])}")
            
            return stats
        
        except Exception as e:
            error_msg = f"Failed to ingest CSV: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def get_ingestion_stats(self) -> Dict[str, Any]:
        """Get statistics about the ingested data."""
        books = self.db.get_all_books()
        
        if not books:
            return {
                'total_books': 0,
                'avg_rating': 0.0,
                'rating_distribution': {},
                'genre_distribution': {},
                'author_distribution': {},
                'year_distribution': {}
            }
        
        # Calculate statistics
        ratings = [book.my_rating for book in books if book.my_rating]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
        
        # Rating distribution
        rating_dist = {}
        for rating in ratings:
            rating_dist[rating] = rating_dist.get(rating, 0) + 1
        
        # Genre distribution (using normalized genres)
        genre_dist = {}
        for book in books:
            if book.genres:  # Use the normalized genres field
                genres = [g.strip() for g in book.genres.split(',')]
                for genre in genres:
                    if genre:
                        genre_dist[genre] = genre_dist.get(genre, 0) + 1
            elif book.bookshelves:  # Fallback to bookshelves if genres not set
                normalized_genres = self.genre_normalizer.normalize_bookshelves(book.bookshelves)
                for genre in normalized_genres:
                    genre_dist[genre] = genre_dist.get(genre, 0) + 1
        
        # Author distribution
        author_dist = {}
        for book in books:
            if book.author:
                author_dist[book.author] = author_dist.get(book.author, 0) + 1
        
        # Year distribution
        year_dist = {}
        for book in books:
            if book.year_published:
                year_dist[book.year_published] = year_dist.get(book.year_published, 0) + 1
        
        return {
            'total_books': len(books),
            'avg_rating': round(avg_rating, 2),
            'rating_distribution': rating_dist,
            'genre_distribution': dict(sorted(genre_dist.items(), key=lambda x: x[1], reverse=True)[:10]),
            'author_distribution': dict(sorted(author_dist.items(), key=lambda x: x[1], reverse=True)[:10]),
            'year_distribution': dict(sorted(year_dist.items()))
        }


# Global ingester instance
ingester = GoodreadsIngester() 