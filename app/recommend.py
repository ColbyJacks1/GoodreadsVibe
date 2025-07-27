"""Personalized book recommendation system."""

import json
import logging
import os
import random
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from .db import db_manager
from .embed import embedding_generator

logger = logging.getLogger(__name__)


class BookRecommender:
    """Provides personalized book recommendations."""
    
    def __init__(self):
        self.db = db_manager
        self.embedding_generator = embedding_generator
        
        # Weights for recommendation scoring
        self.cosine_weight = float(os.getenv("COSINE_WEIGHT", 0.6))
        self.rating_weight = float(os.getenv("RATING_WEIGHT", 0.3))
        self.random_weight = float(os.getenv("RANDOM_WEIGHT", 0.1))
        
        # Ensure weights sum to 1
        total_weight = self.cosine_weight + self.rating_weight + self.random_weight
        self.cosine_weight /= total_weight
        self.rating_weight /= total_weight
        self.random_weight /= total_weight
    
    def get_query_embedding(self, query: str) -> Optional[List[float]]:
        """Generate embedding for the search query."""
        try:
            return self.embedding_generator.generate_embedding(query)
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            return None
    
    def calculate_cosine_similarity(self, query_embedding: List[float], 
                                  book_embedding: List[float]) -> float:
        """Calculate cosine similarity between query and book embedding."""
        try:
            # Convert to numpy arrays
            query_vec = np.array(query_embedding).reshape(1, -1)
            book_vec = np.array(book_embedding).reshape(1, -1)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(query_vec, book_vec)[0][0]
            return float(similarity)
        
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {str(e)}")
            return 0.0
    
    def normalize_rating(self, rating: Optional[int]) -> float:
        """Normalize rating to 0-1 scale."""
        if rating is None:
            return 0.5  # Neutral rating for books without ratings
        return (rating - 1) / 4.0  # Convert 1-5 scale to 0-1
    
    def calculate_recommendation_score(self, cosine_sim: float, rating: float, 
                                     random_factor: float) -> float:
        """Calculate final recommendation score using weighted combination."""
        score = (
            self.cosine_weight * cosine_sim +
            self.rating_weight * rating +
            self.random_weight * random_factor
        )
        return score
    
    def get_shared_keywords(self, query: str, book) -> List[str]:
        """Extract shared keywords between query and book."""
        query_words = set(query.lower().split())
        book_text = f"{book.title} {book.author}".lower()
        
        if book.description:
            book_text += f" {book.description.lower()}"
        
        if book.subjects:
            book_text += f" {book.subjects.lower()}"
        
        if book.genres:
            book_text += f" {book.genres.lower()}"
        
        book_words = set(book_text.split())
        
        # Find common words (excluding common stop words)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        shared = query_words.intersection(book_words) - stop_words
        
        return list(shared)[:5]  # Return top 5 shared keywords
    
    def recommend_books(self, query: str, limit: int = 10, 
                       exclude_read: bool = True) -> List[Dict[str, Any]]:
        """Generate personalized book recommendations."""
        try:
            # Get query embedding
            query_embedding = self.get_query_embedding(query)
            if not query_embedding:
                return []
            
            # Get all books with embeddings
            books_with_embeddings = self.embedding_generator.get_books_with_embeddings()
            
            if not books_with_embeddings:
                logger.warning("No books with embeddings available for recommendations")
                return []
            
            # Filter out read books if requested
            if exclude_read:
                # For now, we'll assume all books in the database are read
                # In a real system, you'd have a separate "to-read" list
                available_books = books_with_embeddings
            else:
                available_books = books_with_embeddings
            
            recommendations = []
            
            for book in available_books:
                try:
                    # Parse book embedding
                    book_embedding = json.loads(book.embedding)
                    
                    # Calculate cosine similarity
                    cosine_sim = self.calculate_cosine_similarity(query_embedding, book_embedding)
                    
                    # Normalize rating
                    normalized_rating = self.normalize_rating(book.my_rating)
                    
                    # Generate random factor
                    random_factor = random.random()
                    
                    # Calculate final score
                    score = self.calculate_recommendation_score(cosine_sim, normalized_rating, random_factor)
                    
                    # Get shared keywords
                    shared_keywords = self.get_shared_keywords(query, book)
                    
                    recommendations.append({
                        'book_id': book.book_id,
                        'title': book.title,
                        'author': book.author,
                        'score': round(score, 4),
                        'cosine_similarity': round(cosine_sim, 4),
                        'rating': book.my_rating,
                        'normalized_rating': round(normalized_rating, 4),
                        'random_factor': round(random_factor, 4),
                        'shared_keywords': shared_keywords,
                        'genres': book.genres,
                        'description': book.description,
                        'publisher': book.publisher,
                        'year_published': book.year_published
                    })
                
                except Exception as e:
                    logger.warning(f"Error processing book {book.title}: {str(e)}")
                    continue
            
            # Sort by score (highest first) and return top results
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            
            return recommendations[:limit]
        
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    def get_recommendation_explanation(self, recommendation: Dict[str, Any]) -> str:
        """Generate explanation for why a book was recommended."""
        explanation_parts = []
        
        # Add cosine similarity explanation
        cosine_sim = recommendation['cosine_similarity']
        if cosine_sim > 0.8:
            explanation_parts.append("Very similar to your query")
        elif cosine_sim > 0.6:
            explanation_parts.append("Similar to your query")
        elif cosine_sim > 0.4:
            explanation_parts.append("Somewhat similar to your query")
        else:
            explanation_parts.append("Different from your query but high-rated")
        
        # Add rating explanation
        rating = recommendation['rating']
        if rating and rating >= 4:
            explanation_parts.append("Highly rated")
        elif rating and rating >= 3:
            explanation_parts.append("Well-rated")
        
        # Add shared keywords
        shared_keywords = recommendation['shared_keywords']
        if shared_keywords:
            explanation_parts.append(f"Shares keywords: {', '.join(shared_keywords)}")
        
        # Add genre information
        genres = recommendation['genres']
        if genres:
            explanation_parts.append(f"Genre: {genres}")
        
        return " | ".join(explanation_parts)
    
    def get_recommendation_stats(self) -> Dict[str, Any]:
        """Get statistics about the recommendation system."""
        books = self.db.get_all_books()
        books_with_embeddings = self.embedding_generator.get_books_with_embeddings()
        
        return {
            'total_books': len(books),
            'books_with_embeddings': len(books_with_embeddings),
            'embedding_rate': round(len(books_with_embeddings) / len(books) * 100, 2) if books else 0,
            'weights': {
                'cosine_similarity': self.cosine_weight,
                'rating': self.rating_weight,
                'random': self.random_weight
            }
        }
    
    def get_similar_books(self, book_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find books similar to a specific book."""
        target_book = self.db.get_book(book_id)
        if not target_book or not target_book.embedding:
            return []
        
        try:
            target_embedding = json.loads(target_book.embedding)
            books_with_embeddings = self.embedding_generator.get_books_with_embeddings()
            
            similarities = []
            for book in books_with_embeddings:
                if book.book_id == book_id:
                    continue  # Skip the target book itself
                
                try:
                    book_embedding = json.loads(book.embedding)
                    similarity = self.calculate_cosine_similarity(target_embedding, book_embedding)
                    
                    similarities.append({
                        'book_id': book.book_id,
                        'title': book.title,
                        'author': book.author,
                        'similarity': round(similarity, 4),
                        'rating': book.my_rating,
                        'genres': book.genres
                    })
                
                except Exception as e:
                    logger.warning(f"Error processing similar book {book.title}: {str(e)}")
                    continue
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            return similarities[:limit]
        
        except Exception as e:
            logger.error(f"Error finding similar books: {str(e)}")
            return []


# Global recommender instance
recommender = BookRecommender() 