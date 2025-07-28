#!/usr/bin/env python3
"""Create a sample database with dummy books for testing."""

import json
import sqlite3
from datetime import datetime

def create_sample_database():
    """Create a sample SQLite database with 5 dummy books."""
    
    # Sample books data
    sample_books = [
        {
            'book_id': '1',
            'title': 'The Great Gatsby',
            'author': 'F. Scott Fitzgerald',
            'isbn': '9780743273565',
            'isbn13': '9780743273565',
            'my_rating': 4,
            'average_rating': 3.93,
            'publisher': 'Simon & Schuster',
            'pages': 180,
            'year_published': 2004,
            'original_publication_year': 1925,
            'date_read': '2023-01-15',
            'date_added': '2022-12-01',
            'bookshelves': 'classics, fiction',
            'my_review': 'Beautiful prose and tragic story of the American Dream',
            'description': 'A story of the fabulously wealthy Jay Gatsby and his love for the beautiful Daisy Buchanan.',
            'subjects': 'American literature, Jazz Age, Social classes',
            'genres': 'Fiction, Classics, Romance',
            'language': 'en',
    
            'cluster_id': 0,
            'centroid_distance': 0.15,
            'umap_x': -0.5,
            'umap_y': 0.3
        },
        {
            'book_id': '2',
            'title': 'Dune',
            'author': 'Frank Herbert',
            'isbn': '9780441172719',
            'isbn13': '9780441172719',
            'my_rating': 5,
            'average_rating': 4.25,
            'publisher': 'ACE',
            'pages': 688,
            'year_published': 1990,
            'original_publication_year': 1965,
            'date_read': '2023-03-20',
            'date_added': '2023-01-10',
            'bookshelves': 'science-fiction',
            'my_review': 'Epic science fiction masterpiece with complex world-building',
            'description': 'Set on the desert planet Arrakis, Dune is the story of the boy Paul Atreides.',
            'subjects': 'Science fiction, Desert planets, Political intrigue',
            'genres': 'Science Fiction, Fantasy, Adventure',
            'language': 'en',
    
            'cluster_id': 1,
            'centroid_distance': 0.12,
            'umap_x': 0.8,
            'umap_y': -0.2
        },
        {
            'book_id': '3',
            'title': 'The Hobbit',
            'author': 'J.R.R. Tolkien',
            'isbn': '9780547928247',
            'isbn13': '9780547928247',
            'my_rating': 4,
            'average_rating': 4.28,
            'publisher': 'Houghton Mifflin Harcourt',
            'pages': 366,
            'year_published': 2012,
            'original_publication_year': 1937,
            'date_read': '2022-11-10',
            'date_added': '2022-10-15',
            'bookshelves': 'fantasy',
            'my_review': 'Classic fantasy adventure that started it all',
            'description': 'Bilbo Baggins is a hobbit who enjoys a comfortable, unambitious life.',
            'subjects': 'Fantasy, Middle-earth, Adventure',
            'genres': 'Fantasy, Adventure, Classics',
            'language': 'en',
    
            'cluster_id': 0,
            'centroid_distance': 0.18,
            'umap_x': -0.3,
            'umap_y': 0.6
        },
        {
            'book_id': '4',
            'title': 'Sapiens: A Brief History of Humankind',
            'author': 'Yuval Noah Harari',
            'isbn': '9780062316097',
            'isbn13': '9780062316097',
            'my_rating': 4,
            'average_rating': 4.37,
            'publisher': 'Harper',
            'pages': 443,
            'year_published': 2015,
            'original_publication_year': 2011,
            'date_read': '2023-05-12',
            'date_added': '2023-04-01',
            'bookshelves': 'non-fiction, history',
            'my_review': 'Fascinating overview of human history and development',
            'description': 'A groundbreaking narrative of humanity\'s creation and evolution.',
            'subjects': 'Human evolution, History, Anthropology',
            'genres': 'Non-fiction, History, Science',
            'language': 'en',
    
            'cluster_id': 2,
            'centroid_distance': 0.22,
            'umap_x': 0.2,
            'umap_y': 0.8
        },
        {
            'book_id': '5',
            'title': 'The Martian',
            'author': 'Andy Weir',
            'isbn': '9780553418026',
            'isbn13': '9780553418026',
            'my_rating': 5,
            'average_rating': 4.41,
            'publisher': 'Crown',
            'pages': 369,
            'year_published': 2014,
            'original_publication_year': 2011,
            'date_read': '2023-02-28',
            'date_added': '2023-01-20',
            'bookshelves': 'science-fiction',
            'my_review': 'Incredible survival story with great science and humor',
            'description': 'A mission to Mars goes terribly wrong, and astronaut Mark Watney is left behind.',
            'subjects': 'Space exploration, Survival, Science',
            'genres': 'Science Fiction, Adventure, Thriller',
            'language': 'en',
    
            'cluster_id': 1,
            'centroid_distance': 0.14,
            'umap_x': 0.6,
            'umap_y': -0.4
        }
    ]
    
    # Create database connection
    conn = sqlite3.connect('embed_data.sqlite')
    cursor = conn.cursor()
    
    # Create books table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS book (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT,
            isbn13 TEXT,
            my_rating INTEGER,
            average_rating REAL,
            publisher TEXT,
            pages INTEGER,
            year_published INTEGER,
            original_publication_year INTEGER,
            date_read TEXT,
            date_added TEXT,
            bookshelves TEXT,
            my_review TEXT,
            description TEXT,
            subjects TEXT,
            genres TEXT,
            language TEXT,
        
            cluster_id INTEGER,
            centroid_distance REAL,
            umap_x REAL,
            umap_y REAL,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # Insert sample books
    for book in sample_books:
        cursor.execute('''
            INSERT OR REPLACE INTO book (
                book_id, title, author, isbn, isbn13, my_rating, average_rating,
                publisher, pages, year_published, original_publication_year,
                date_read, date_added, bookshelves, my_review, description,
                subjects, genres, language, cluster_id, centroid_distance,
                umap_x, umap_y, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            book['book_id'], book['title'], book['author'], book['isbn'],
            book['isbn13'], book['my_rating'], book['average_rating'],
            book['publisher'], book['pages'], book['year_published'],
            book['original_publication_year'], book['date_read'], book['date_added'],
            book['bookshelves'], book['my_review'], book['description'],
            book['subjects'], book['genres'], book['language'],
            book['cluster_id'], book['centroid_distance'], book['umap_x'],
            book['umap_y'], datetime.now().isoformat(), datetime.now().isoformat()
        ))
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print("✅ Sample database created successfully!")
    print("📊 Added 5 sample books with clustering data")
    print("🗄️  Database file: embed_data.sqlite")
    print("\nSample books:")
    for book in sample_books:
        print(f"  • {book['title']} by {book['author']} (Rating: {book['my_rating']}⭐)")

if __name__ == "__main__":
    create_sample_database() 