"""OpenAI embedding generation and storage."""

import json
import logging
import os
from typing import List, Dict, Any, Optional
import numpy as np  # type: ignore
import google.generativeai as genai
import time

from .db import db_manager, BookUpdate

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generates and manages Gemini embeddings for books."""
    
    def __init__(self):
        self.db = db_manager
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model = "text-embedding-004"
        self.batch_size = 50  # Process books in batches
        if not self.api_key:
            logger.warning("No Google API key provided. Embedding generation will be disabled.")
            self.client_available = False
        else:
            genai.configure(api_key=self.api_key)
            self.client_available = True
    
    def create_book_text(self, book) -> str:
        """Create a text representation of a book for embedding."""
        text_parts = []
        # Basic book information
        text_parts.append(f"Title: {book.title}")
        text_parts.append(f"Author: {book.author}")
        # Add description if available
        if book.description:
            text_parts.append(f"Description: {book.description}")
        # Add subjects/genres if available
        if book.subjects:
            text_parts.append(f"Subjects: {book.subjects}")
        if book.genres:
            text_parts.append(f"Genres: {book.genres}")
        # Add review if available
        if book.my_review:
            text_parts.append(f"Review: {book.my_review}")
        # Add bookshelves
        if book.bookshelves:
            text_parts.append(f"Bookshelves: {book.bookshelves}")
        # Add publisher and year
        if book.publisher:
            text_parts.append(f"Publisher: {book.publisher}")
        if book.year_published:
            text_parts.append(f"Year: {book.year_published}")
        return " | ".join(text_parts)

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a text string using Gemini."""
        if not self.client_available:
            logger.warning("Gemini client not available. Cannot generate embeddings.")
            return None
        try:
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type="SEMANTIC_SIMILARITY"
            )
            return result["embedding"]
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None

    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for a batch of texts using Gemini batch embedding."""
        if not self.client_available:
            logger.warning("Gemini client not available. Cannot generate embeddings.")
            return [None] * len(texts)
        try:
            result = genai.embed_content(
                model=self.model,
                content=texts,  # Batch embedding
                task_type="SEMANTIC_SIMILARITY"
            )
            # result["embedding"] is a list of embeddings
            return result["embedding"]
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            return [None] * len(texts)
    
    def embed_book(self, book_id: str) -> bool:
        """Generate and store embedding for a single book."""
        book = self.db.get_book(book_id)
        if not book:
            logger.error(f"Book not found: {book_id}")
            return False
        # Skip if already has embedding
        if book.embedding:
            logger.debug(f"Book already has embedding: {book.title}")
            return True
        try:
            # Create text representation
            text = self.create_book_text(book)
            # Generate embedding
            embedding = self.generate_embedding(text)
            if not embedding:
                logger.error(f"Failed to generate embedding for: {book.title}")
                return False
            # Store embedding as JSON string
            embedding_json = json.dumps(embedding)
            # Update book
            update_data = BookUpdate(embedding=embedding_json)
            self.db.update_book(book_id, update_data)
            logger.info(f"Generated embedding for: {book.title}")
            return True
        except Exception as e:
            logger.error(f"Error embedding book {book.title}: {str(e)}")
            return False
    
    def embed_all_books(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Generate embeddings for all books in the database using Gemini."""
        books = self.db.get_all_books()
        # Filter books without embeddings
        books_to_embed = [book for book in books if not book.embedding]
        if limit:
            books_to_embed = books_to_embed[:limit]
        stats = {
            'total_books': len(books_to_embed),
            'embedded': 0,
            'skipped': 0,
            'errors': 0
        }
        logger.info(f"Starting embedding generation for {len(books_to_embed)} books")
        # Process in batches
        batch_size = 50
        for i in range(0, len(books_to_embed), batch_size):
            batch = books_to_embed[i:i + batch_size]
            try:
                # Create texts for batch
                texts = [self.create_book_text(book) for book in batch]
                # Generate embeddings for batch
                embeddings = self.generate_embeddings_batch(texts)
                # Store embeddings
                for book, embedding in zip(batch, embeddings):
                    if embedding:
                        embedding_json = json.dumps(embedding)
                        update_data = BookUpdate(embedding=embedding_json)
                        self.db.update_book(book.book_id, update_data)
                        stats['embedded'] += 1
                    else:
                        stats['errors'] += 1
                # Throttle to 5 requests per minute (12 seconds between batches)
                if (i + batch_size) < len(books_to_embed):
                    logger.info("Sleeping 12 seconds to respect Gemini API rate limits...")
                    time.sleep(12)
                if (i + batch_size) % 50 == 0:
                    logger.info(f"Processed {i + batch_size}/{len(books_to_embed)} books...")
            except Exception as e:
                logger.error(f"Error processing batch: {str(e)}")
                stats['errors'] += len(batch)
        logger.info(f"Embedding generation complete. Embedded: {stats['embedded']}, "
                   f"Errors: {stats['errors']}")
        return stats
    
    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about embedding status."""
        books = self.db.get_all_books()
        if not books:
            return {
                'total_books': 0,
                'embedded_books': 0,
                'embedding_rate': 0.0
            }
        embedded_count = sum(1 for book in books if book.embedding)
        return {
            'total_books': len(books),
            'embedded_books': embedded_count,
            'embedding_rate': round(embedded_count / len(books) * 100, 2)
        }
    
    def get_embeddings_matrix(self) -> Optional[np.ndarray]:
        """Get all embeddings as a numpy matrix."""
        books = self.db.get_all_books()
        books_with_embeddings = [book for book in books if book.embedding]
        if not books_with_embeddings:
            return None
        embeddings = []
        for book in books_with_embeddings:
            if book.embedding is None:
                continue
            try:
                embedding = json.loads(book.embedding)
                embeddings.append(embedding)
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Invalid embedding for book: {book.title}")
                continue
        if not embeddings:
            return None
        return np.array(embeddings)
    
    def get_books_with_embeddings(self) -> List[Any]:
        """Get all books that have embeddings."""
        books = self.db.get_all_books()
        return [book for book in books if book.embedding]


# Global embedding generator instance
embedding_generator = EmbeddingGenerator() 