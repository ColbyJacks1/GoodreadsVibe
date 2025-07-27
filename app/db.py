"""Database models and connection setup."""

import os
from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Session, create_engine, select
from pydantic import BaseModel
import numpy as np


class Book(SQLModel, table=True):
    """Book model with Goodreads and enriched data."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    book_id: str = Field(unique=True, index=True)
    title: str = Field(index=True)
    author: str = Field(index=True)
    isbn: Optional[str] = Field(default=None)
    isbn13: Optional[str] = Field(default=None)
    my_rating: Optional[int] = Field(default=None)
    average_rating: Optional[float] = Field(default=None)
    publisher: Optional[str] = Field(default=None)
    pages: Optional[int] = Field(default=None)
    year_published: Optional[int] = Field(default=None)
    original_publication_year: Optional[int] = Field(default=None)
    date_read: Optional[datetime] = Field(default=None)
    date_added: Optional[datetime] = Field(default=None)
    bookshelves: Optional[str] = Field(default=None)
    my_review: Optional[str] = Field(default=None)
    
    # Enriched data from Open Library
    description: Optional[str] = Field(default=None)
    subjects: Optional[str] = Field(default=None)
    genres: Optional[str] = Field(default=None)
    language: Optional[str] = Field(default=None)
    
    # Embedding and clustering data
    # embedding: Optional[str] = Field(default=None)  # JSON string of embedding
    # cluster_id: Optional[int] = Field(default=None, index=True)
    # centroid_distance: Optional[float] = Field(default=None)
    # umap_x: Optional[float] = Field(default=None)
    # umap_y: Optional[float] = Field(default=None)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BookCreate(BaseModel):
    """Schema for creating a new book."""
    book_id: str
    title: str
    author: str
    isbn: Optional[str] = None
    isbn13: Optional[str] = None
    my_rating: Optional[int] = None
    average_rating: Optional[float] = None
    publisher: Optional[str] = None
    pages: Optional[int] = None
    year_published: Optional[int] = None
    original_publication_year: Optional[int] = None
    date_read: Optional[datetime] = None
    date_added: Optional[datetime] = None
    bookshelves: Optional[str] = None
    my_review: Optional[str] = None


class BookUpdate(BaseModel):
    """Schema for updating a book."""
    title: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    subjects: Optional[str] = None
    genres: Optional[str] = None
    language: Optional[str] = None
    embedding: Optional[str] = None
    cluster_id: Optional[int] = None
    centroid_distance: Optional[float] = None
    umap_x: Optional[float] = None
    umap_y: Optional[float] = None


class ClusterStats(BaseModel):
    """Statistics for a cluster."""
    cluster_id: int
    size: int
    avg_rating: float
    top_genres: List[str]
    top_authors: List[str]
    exemplar_books: List[str]
    centroid_embedding: List[float]


class LLMHistory(SQLModel, table=True):
    """History of LLM prompt/response interactions."""
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    prompt: str
    response: str
    extra: Optional[str] = None  # JSON string for any extra info

class LLMHistoryCreate(BaseModel):
    prompt: str
    response: str
    extra: Optional[str] = None


class DatabaseManager:
    """Database connection and management."""
    
    def __init__(self):
        database_url = os.getenv("DATABASE_URL", "sqlite:///./embed_data.sqlite")
        self.engine = create_engine(database_url, echo=False)
        self.create_tables()
    
    def create_tables(self):
        """Create all tables."""
        SQLModel.metadata.create_all(self.engine)
    
    def get_session(self):
        """Get database session."""
        return Session(self.engine)
    
    def add_book(self, book_data: BookCreate) -> Book:
        """Add a new book to the database."""
        with self.get_session() as session:
            book = Book(**book_data.dict())
            session.add(book)
            session.commit()
            session.refresh(book)
            return book
    
    def get_book(self, book_id: str) -> Optional[Book]:
        """Get a book by its Goodreads ID."""
        with self.get_session() as session:
            statement = select(Book).where(Book.book_id == book_id)
            return session.exec(statement).first()
    
    def get_all_books(self) -> List[Book]:
        """Get all books."""
        with self.get_session() as session:
            statement = select(Book)
            return list(session.exec(statement))
    
    def get_books_by_cluster(self, cluster_id: int) -> List[Book]:
        """Get all books in a cluster."""
        with self.get_session() as session:
            statement = select(Book).where(Book.cluster_id == cluster_id)
            return list(session.exec(statement))
    
    def update_book(self, book_id: str, update_data: BookUpdate) -> Optional[Book]:
        """Update a book."""
        with self.get_session() as session:
            book = self.get_book(book_id)
            if book:
                for field, value in update_data.dict(exclude_unset=True).items():
                    setattr(book, field, value)
                book.updated_at = datetime.utcnow()
                session.add(book)
                session.commit()
                session.refresh(book)
            return book
    
    def get_cluster_stats(self) -> List[ClusterStats]:
        """Get statistics for all clusters."""
        with self.get_session() as session:
            books = self.get_all_books()
            clusters = {}
            
            for book in books:
                if book.cluster_id is not None:
                    if book.cluster_id not in clusters:
                        clusters[book.cluster_id] = {
                            'books': [],
                            'ratings': [],
                            'genres': [],
                            'authors': []
                        }
                    
                    clusters[book.cluster_id]['books'].append(book)
                    if book.my_rating:
                        clusters[book.cluster_id]['ratings'].append(book.my_rating)
                    if book.genres:
                        clusters[book.cluster_id]['genres'].extend(book.genres.split(', '))
                    if book.author:
                        clusters[book.cluster_id]['authors'].append(book.author)
            
            stats = []
            for cluster_id, data in clusters.items():
                # Get top genres
                genre_counts = {}
                for genre in data['genres']:
                    genre_counts[genre] = genre_counts.get(genre, 0) + 1
                top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                top_genres = [genre for genre, _ in top_genres]
                
                # Get top authors
                author_counts = {}
                for author in data['authors']:
                    author_counts[author] = author_counts.get(author, 0) + 1
                top_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                top_authors = [author for author, _ in top_authors]
                
                # Get exemplar books (highest rated)
                exemplar_books = sorted(data['books'], key=lambda x: x.my_rating or 0, reverse=True)[:3]
                exemplar_titles = [book.title for book in exemplar_books]
                
                # Calculate average rating
                avg_rating = np.mean(data['ratings']) if data['ratings'] else 0.0
                
                stats.append(ClusterStats(
                    cluster_id=cluster_id,
                    size=len(data['books']),
                    avg_rating=avg_rating,
                    top_genres=top_genres,
                    top_authors=top_authors,
                    exemplar_books=exemplar_titles,
                    centroid_embedding=[]  # Will be filled by clustering module
                ))
            
            return stats

    def add_llm_history(self, history_data: LLMHistoryCreate) -> LLMHistory:
        """Add a new LLM prompt/response record to the database."""
        with self.get_session() as session:
            record = LLMHistory(**history_data.dict())
            session.add(record)
            session.commit()
            session.refresh(record)
            return record


# Global database manager instance
db_manager = DatabaseManager() 