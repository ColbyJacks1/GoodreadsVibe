"""Open Library metadata enrichment."""

import logging
import time
from typing import Dict, Any, Optional, List
import requests
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from .db import db_manager, BookUpdate

logger = logging.getLogger(__name__)


class OpenLibraryEnricher:
    """Enriches books with metadata from Open Library API."""
    
    def __init__(self):
        self.db = db_manager
        self.base_url = "https://openlibrary.org"
        self.session = requests.Session()
        # Add connection pooling for better performance
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.headers.update({
            'User-Agent': 'BookMirrorPlus/1.0 (https://github.com/your-repo)'
        })
        self.rate_limit_delay = 0.02  # 20ms instead of 100ms
        # Thread-local storage for sessions
        self._thread_local = threading.local()
    
    def _get_session(self):
        """Get thread-local session for concurrent requests."""
        if not hasattr(self._thread_local, 'session'):
            self._thread_local.session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(
                pool_connections=5,
                pool_maxsize=10
            )
            self._thread_local.session.mount('http://', adapter)
            self._thread_local.session.mount('https://', adapter)
            self._thread_local.session.headers.update({
                'User-Agent': 'BookMirrorPlus/1.0 (https://github.com/your-repo)'
            })
        return self._thread_local.session
    
    def search_book(self, title: str, author: str = None) -> Optional[Dict[str, Any]]:
        """Search for a book in Open Library."""
        try:
            # Build search query
            query_parts = [title]
            if author:
                query_parts.append(author)
            
            query = " ".join(query_parts)
            encoded_query = quote(query)
            
            url = f"{self.base_url}/search.json"
            params = {
                'q': query,
                'limit': 5,
                'fields': 'key,title,author_name,first_sentence,subject,language,number_of_pages_median'
            }
            
            session = self._get_session()
            response = session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get('docs'):
                return data['docs'][0]  # Return first match
            
            return None
        
        except Exception as e:
            logger.error(f"Error searching for book '{title}': {str(e)}")
            return None
    
    def get_book_details(self, book_key: str) -> Optional[Dict[str, Any]]:
        """Get detailed book information from Open Library."""
        try:
            url = f"{self.base_url}{book_key}.json"
            session = self._get_session()
            response = session.get(url)
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error getting book details for {book_key}: {str(e)}")
            return None
    
    def extract_subjects(self, subjects: List[str]) -> List[str]:
        """Extract and clean subject categories."""
        if not subjects:
            return []
        
        # Filter out very specific or technical subjects
        filtered_subjects = []
        for subject in subjects:
            subject_lower = subject.lower()
            # Skip very specific technical subjects
            if any(skip in subject_lower for skip in ['fiction', 'juvenile', 'access', 'protected']):
                continue
            filtered_subjects.append(subject)
        
        return filtered_subjects[:10]  # Limit to top 10
    
    def extract_genres(self, subjects: List[str]) -> List[str]:
        """Extract genre-like subjects."""
        if not subjects:
            return []
        
        # Common genre keywords
        genre_keywords = [
            'fiction', 'romance', 'mystery', 'thriller', 'fantasy', 'science fiction',
            'horror', 'historical', 'biography', 'autobiography', 'memoir', 'poetry',
            'drama', 'comedy', 'adventure', 'western', 'war', 'crime', 'detective',
            'supernatural', 'paranormal', 'dystopian', 'utopian', 'satire', 'humor'
        ]
        
        genres = []
        for subject in subjects:
            subject_lower = subject.lower()
            for keyword in genre_keywords:
                if keyword in subject_lower:
                    genres.append(subject)
                    break
        
        return genres[:5]  # Limit to top 5
    
    def clean_description(self, description: Optional[str]) -> str:
        """Clean and truncate book description."""
        if not description:
            description = ""
        
        # Remove HTML tags and extra whitespace
        import re
        cleaned = re.sub(r'<[^>]+>', '', description)
        cleaned = ' '.join(cleaned.split())
        
        # Truncate if too long
        if len(cleaned) > 1000:
            cleaned = cleaned[:997] + "..."
        
        return cleaned
    
    def enrich_book(self, book_id: str) -> bool:
        """Enrich a single book with Open Library metadata."""
        book = self.db.get_book(book_id)
        if not book:
            logger.error(f"Book not found: {book_id}")
            return False
        
        # Skip if already enriched
        if book.description or book.subjects or book.genres:
            logger.debug(f"Book already enriched: {book.title}")
            return True
        
        try:
            # Search for the book
            search_result = self.search_book(book.title, book.author)
            if not search_result:
                logger.debug(f"No Open Library match found for: {book.title}")
                return False
            
            # Get detailed information
            book_key = search_result.get('key')
            if not book_key:
                return False
            
            details = self.get_book_details(book_key)
            if not details:
                return False
            
            # Extract and process data
            desc_field = details.get('description')
            if isinstance(desc_field, dict):
                desc_value = desc_field.get('value', '') or ''
            elif isinstance(desc_field, str):
                desc_value = desc_field
            else:
                desc_value = ''
            if desc_value is None:
                desc_value = ''
            description = self.clean_description(desc_value)
            
            subjects = details.get('subjects', [])
            clean_subjects = self.extract_subjects(subjects)
            subjects_str = ', '.join(clean_subjects) if clean_subjects else None
            
            genres = self.extract_genres(subjects)
            genres_str = ', '.join(genres) if genres else None
            
            language = details.get('languages', [{}])[0].get('key', '').split('/')[-1] if details.get('languages') else None
            
            # Update book with enriched data
            update_data = BookUpdate(
                description=description,
                subjects=subjects_str,
                genres=genres_str,
                language=language
            )
            
            self.db.update_book(book_id, update_data)
            logger.info(f"Enriched book: {book.title}")
            
            # Rate limiting
            time.sleep(self.rate_limit_delay)
            
            return True
        
        except Exception as e:
            logger.error(f"Error enriching book {book.title}: {str(e)}")
            return False
    
    def enrich_book_concurrent(self, book) -> Dict[str, Any]:
        """Enrich a single book for concurrent processing."""
        result = {
            'book_id': book.book_id,
            'title': book.title,
            'status': 'error',
            'message': ''
        }
        
        try:
            if self.enrich_book(book.book_id):
                result['status'] = 'enriched'
                result['message'] = f"Successfully enriched: {book.title}"
            else:
                result['status'] = 'skipped'
                result['message'] = f"Skipped enrichment for: {book.title}"
        except Exception as e:
            result['message'] = f"Error enriching {book.title}: {str(e)}"
            logger.error(f"Error processing book {book.title}: {str(e)}")
        
        return result
    
    def enrich_books_concurrent(self, books: List, max_workers: int = 10) -> Dict[str, Any]:
        """Enrich books concurrently for better performance."""
        stats = {
            'total_books': len(books),
            'enriched': 0,
            'skipped': 0,
            'errors': 0,
            'results': []
        }
        
        logger.info(f"Starting concurrent enrichment of {len(books)} books with {max_workers} workers")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_book = {executor.submit(self.enrich_book_concurrent, book): book for book in books}
            
            # Process completed tasks
            for i, future in enumerate(as_completed(future_to_book)):
                try:
                    result = future.result()
                    stats['results'].append(result)
                    
                    if result['status'] == 'enriched':
                        stats['enriched'] += 1
                    elif result['status'] == 'skipped':
                        stats['skipped'] += 1
                    else:
                        stats['errors'] += 1
                    
                    # Log progress every 10 books
                    if (i + 1) % 10 == 0:
                        logger.info(f"Processed {i + 1}/{len(books)} books... "
                                  f"(Enriched: {stats['enriched']}, Skipped: {stats['skipped']}, Errors: {stats['errors']})")
                
                except Exception as e:
                    book = future_to_book[future]
                    logger.error(f"Unexpected error processing book {book.title}: {str(e)}")
                    stats['errors'] += 1
        
        logger.info(f"Concurrent enrichment complete. Enriched: {stats['enriched']}, "
                   f"Skipped: {stats['skipped']}, Errors: {stats['errors']}")
        
        return stats
    
    def enrich_all_books(self, limit: Optional[int] = None, max_workers: int = 10) -> Dict[str, Any]:
        """Enrich all books in the database with concurrent processing."""
        books = self.db.get_all_books()
        
        if limit:
            books = books[:limit]
        
        # Use concurrent processing for better performance
        return self.enrich_books_concurrent(books, max_workers)
    
    def get_enrichment_stats(self) -> Dict[str, Any]:
        """Get statistics about enrichment status."""
        books = self.db.get_all_books()
        
        if not books:
            return {
                'total_books': 0,
                'enriched_books': 0,
                'enrichment_rate': 0.0
            }
        
        enriched_count = sum(1 for book in books if book.description or book.subjects or book.genres)
        
        return {
            'total_books': len(books),
            'enriched_books': enriched_count,
            'enrichment_rate': round(enriched_count / len(books) * 100, 2)
        }


# Global enricher instance
enricher = OpenLibraryEnricher() 