"""Database models and connection setup."""

import os
from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Session, create_engine, select
from pydantic import BaseModel


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
    genres: Optional[str] = None


class BookUpdate(BaseModel):
    """Schema for updating a book."""
    title: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    subjects: Optional[str] = None
    genres: Optional[str] = None
    language: Optional[str] = None


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