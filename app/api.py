"""FastAPI application for book-mirror-plus."""

from dotenv import load_dotenv; load_dotenv()
import os
#print("GOOGLE_API_KEY:", os.getenv("GOOGLE_API_KEY"))

import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from .db import db_manager
from .ingest import ingester
from .enrich import enricher
from .embed import embedding_generator
from .cluster import clusterer
from .insights import insights_generator
from .recommend import recommender
from sqlmodel import SQLModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Book Mirror Plus API",
    description="A local Streamlit + FastAPI app for Goodreads analysis with deep insights",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API responses
class StatusResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None


class IngestionResponse(BaseModel):
    success: bool
    total_rows: int
    processed_books: int
    skipped_books: int
    errors: List[str]


class EnrichmentResponse(BaseModel):
    success: bool
    total_books: int
    enriched: int
    skipped: int
    errors: int


class EmbeddingResponse(BaseModel):
    success: bool
    total_books: int
    embedded: int
    skipped: int
    errors: int


class ClusteringResponse(BaseModel):
    success: bool
    optimal_k: Optional[int] = None
    total_books: int
    updated_books: int
    cluster_distribution: Optional[Dict[int, int]] = None
    error: Optional[str] = None


class InsightsResponse(BaseModel):
    success: bool
    insights: Optional[Dict[str, str]] = None
    data_summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    raw_response: Optional[str] = None


class RecommendationResponse(BaseModel):
    success: bool
    recommendations: List[Dict[str, Any]]
    query: str
    total_found: int


class BookResponse(BaseModel):
    book_id: str
    title: str
    author: str
    my_rating: Optional[int] = None
    average_rating: Optional[float] = None
    genres: Optional[str] = None
    description: Optional[str] = None
    cluster_id: Optional[int] = None
    umap_x: Optional[float] = None
    umap_y: Optional[float] = None
    date_read: Optional[str] = None  # Added for dashboard table


class InsightsRequest(BaseModel):
    prompt: str


# Health check endpoint
@app.get("/", response_model=StatusResponse)
async def root():
    """Health check endpoint."""
    return StatusResponse(
        status="healthy",
        message="Book Mirror Plus API is running",
        data={
            "version": "0.1.0",
            "endpoints": [
                "/docs",
                "/upload",
                "/enrich",
                "/embed",
                "/cluster",
                "/insights",
                "/recommend"
            ]
        }
    )


# Upload and ingestion endpoint
@app.post("/upload", response_model=IngestionResponse)
async def upload_csv(file: UploadFile = File(...)):
    """Upload and ingest Goodreads CSV file."""
    try:
        # Save uploaded file temporarily
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Ingest the CSV
        stats = ingester.ingest_csv(temp_path)
        
        # Clean up temp file
        os.remove(temp_path)
        
        return IngestionResponse(
            success=True,
            total_rows=stats['total_rows'],
            processed_books=stats['processed_books'],
            skipped_books=stats['skipped_books'],
            errors=stats['errors']
        )
    
    except Exception as e:
        logger.error(f"Error uploading CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Enrichment endpoint
@app.post("/enrich", response_model=EnrichmentResponse)
async def enrich_books(limit: Optional[int] = None):
    """Enrich books with Open Library metadata."""
    try:
        stats = enricher.enrich_all_books(limit=limit)
        
        return EnrichmentResponse(
            success=True,
            total_books=stats['total_books'],
            enriched=stats['enriched'],
            skipped=stats['skipped'],
            errors=stats['errors']
        )
    
    except Exception as e:
        logger.error(f"Error enriching books: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Embedding generation endpoint
@app.post("/embed", response_model=EmbeddingResponse)
async def generate_embeddings(limit: Optional[int] = None):
    """Generate embeddings for all books."""
    try:
        stats = embedding_generator.embed_all_books(limit=limit)
        
        return EmbeddingResponse(
            success=True,
            total_books=stats['total_books'],
            embedded=stats['embedded'],
            skipped=stats['skipped'],
            errors=stats['errors']
        )
    
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Clustering endpoint
@app.post("/cluster", response_model=ClusteringResponse)
async def cluster_books():
    """Perform clustering on all books with embeddings."""
    try:
        result = clusterer.cluster_all_books()
        
        if result['success']:
            return ClusteringResponse(
                success=True,
                optimal_k=result['optimal_k'],
                total_books=result['total_books'],
                updated_books=result['updated_books'],
                cluster_distribution=result['cluster_distribution']
            )
        else:
            return ClusteringResponse(
                success=False,
                total_books=0,
                updated_books=0,
                error=result['error']
            )
    
    except Exception as e:
        logger.error(f"Error clustering books: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Insights endpoint
@app.post("/insights", response_model=InsightsResponse)
async def get_insights(request: InsightsRequest = Body(...)):
    """Generate deep literary psychology insights with a custom prompt."""
    try:
        result = insights_generator.generate_insights(prompt=request.prompt)
        if result.get('success'):
            return InsightsResponse(
                success=True,
                insights=result['insights'],
                data_summary=result['data_summary'],
                raw_response=result.get('raw_response', None)
            )
        else:
            return InsightsResponse(
                success=False,
                error=result.get('error', 'Unknown error'),
                raw_response=result.get('raw_response', None)
            )
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Recommendation endpoint
@app.get("/recommend", response_model=RecommendationResponse)
async def get_recommendations(q: str, limit: int = 10):
    """Get personalized book recommendations."""
    try:
        recommendations = recommender.recommend_books(q, limit=limit)
        
        return RecommendationResponse(
            success=True,
            recommendations=recommendations,
            query=q,
            total_found=len(recommendations)
        )
    
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Statistics endpoints
@app.get("/stats/ingestion")
async def get_ingestion_stats():
    """Get ingestion statistics."""
    try:
        stats = ingester.get_ingestion_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error(f"Error getting ingestion stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats/enrichment")
async def get_enrichment_stats():
    """Get enrichment statistics."""
    try:
        stats = enricher.get_enrichment_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error(f"Error getting enrichment stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats/embedding")
async def get_embedding_stats():
    """Get embedding statistics."""
    try:
        stats = embedding_generator.get_embedding_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error(f"Error getting embedding stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats/clustering")
async def get_clustering_stats():
    """Get clustering statistics."""
    try:
        stats = clusterer.get_clustering_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error(f"Error getting clustering stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats/insights")
async def get_insights_stats():
    """Get insights generation statistics."""
    try:
        stats = insights_generator.get_insights_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error(f"Error getting insights stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats/recommendations")
async def get_recommendation_stats():
    """Get recommendation system statistics."""
    try:
        stats = recommender.get_recommendation_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error(f"Error getting recommendation stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Book data endpoints
@app.get("/books", response_model=List[BookResponse])
async def get_all_books():
    """Get all books in the database."""
    try:
        books = db_manager.get_all_books()
        return [
            BookResponse(
                book_id=book.book_id,
                title=book.title,
                author=book.author,
                my_rating=book.my_rating,
                average_rating=book.average_rating,
                genres=book.genres,
                description=book.description,
                cluster_id=book.cluster_id,
                umap_x=book.umap_x,
                umap_y=book.umap_y,
                date_read=book.date_read.strftime('%Y-%m-%d') if book.date_read else None  # Added
            )
            for book in books
        ]
    except Exception as e:
        logger.error(f"Error getting books: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/books/cluster/{cluster_id}")
async def get_books_by_cluster(cluster_id: int):
    """Get all books in a specific cluster."""
    try:
        books = db_manager.get_books_by_cluster(cluster_id)
        return {
            "success": True,
            "cluster_id": cluster_id,
            "books": [
                {
                    "book_id": book.book_id,
                    "title": book.title,
                    "author": book.author,
                    "rating": book.my_rating,
                    "genres": book.genres,
                    "umap_x": book.umap_x,
                    "umap_y": book.umap_y
                }
                for book in books
            ]
        }
    except Exception as e:
        logger.error(f"Error getting books by cluster: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/clusters/exemplars")
async def get_cluster_exemplars():
    """Get exemplar books for all clusters."""
    try:
        exemplars = clusterer.get_all_cluster_exemplars()
        return {"success": True, "exemplars": exemplars}
    except Exception as e:
        logger.error(f"Error getting cluster exemplars: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Similar books endpoint
@app.get("/books/{book_id}/similar")
async def get_similar_books(book_id: str, limit: int = 5):
    """Get books similar to a specific book."""
    try:
        similar_books = recommender.get_similar_books(book_id, limit=limit)
        return {
            "success": True,
            "target_book_id": book_id,
            "similar_books": similar_books
        }
    except Exception as e:
        logger.error(f"Error getting similar books: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reset", response_model=StatusResponse)
async def reset_database():
    """Reset the database by dropping all tables and recreating them."""
    try:
        # Drop all tables
        SQLModel.metadata.drop_all(db_manager.engine)
        # Recreate tables
        db_manager.create_tables()
        
        return StatusResponse(
            status="success",
            message="Database reset successfully",
            data={"tables_dropped": True}
        )
    
    except Exception as e:
        logger.error(f"Error resetting database: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "app.api:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True
    ) 