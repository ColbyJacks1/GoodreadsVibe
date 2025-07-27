"""K-means clustering and UMAP dimensionality reduction."""

import json
import logging
import os
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
import umap
from sklearn.manifold import TSNE

from .db import db_manager, BookUpdate
from .embed import embedding_generator

logger = logging.getLogger(__name__)


class BookClusterer:
    """Performs clustering and dimensionality reduction on book embeddings."""
    
    def __init__(self):
        self.db = db_manager
        self.embedding_generator = embedding_generator
        self.min_k = int(os.getenv("CLUSTERING_MIN_K", 3))
        self.max_k = int(os.getenv("CLUSTERING_MAX_K", 12))
        self.umap_n_neighbors = int(os.getenv("UMAP_N_NEIGHBORS", 15))
        self.umap_min_dist = float(os.getenv("UMAP_MIN_DIST", 0.1))
        self.umap_n_components = int(os.getenv("UMAP_N_COMPONENTS", 2))
    
    def get_embeddings_data(self) -> Tuple[Optional[np.ndarray], List[Any]]:
        """Get embeddings matrix and corresponding books."""
        embeddings_matrix = self.embedding_generator.get_embeddings_matrix()
        books_with_embeddings = self.embedding_generator.get_books_with_embeddings()
        
        if embeddings_matrix is None or len(books_with_embeddings) == 0:
            logger.warning("No embeddings available for clustering")
            return None, []
        
        return embeddings_matrix, books_with_embeddings
    
    def find_optimal_k(self, embeddings: np.ndarray) -> int:
        """Find optimal number of clusters using silhouette score."""
        logger.info(f"Finding optimal k between {self.min_k} and {self.max_k}")
        
        best_score = -1
        best_k = self.min_k
        
        for k in range(self.min_k, min(self.max_k + 1, len(embeddings) // 2)):
            try:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                cluster_labels = kmeans.fit_predict(embeddings)
                
                # Calculate silhouette score
                if len(np.unique(cluster_labels)) > 1:
                    score = silhouette_score(embeddings, cluster_labels)
                    logger.debug(f"K={k}, Silhouette score: {score:.3f}")
                    
                    if score > best_score:
                        best_score = score
                        best_k = k
                
            except Exception as e:
                logger.warning(f"Error calculating silhouette score for k={k}: {str(e)}")
                continue
        
        logger.info(f"Optimal k found: {best_k} (silhouette score: {best_score:.3f})")
        return best_k
    
    def perform_clustering(self, embeddings: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
        """Perform K-means clustering."""
        logger.info(f"Performing K-means clustering with k={k}")
        
        # Standardize embeddings
        scaler = StandardScaler()
        embeddings_scaled = scaler.fit_transform(embeddings)
        
        # Perform clustering
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embeddings_scaled)
        
        # Calculate distances to centroids
        centroid_distances = kmeans.transform(embeddings_scaled)
        min_distances = np.min(centroid_distances, axis=1)
        
        return cluster_labels, min_distances
    
    def perform_umap_reduction(self, embeddings: np.ndarray) -> np.ndarray:
        """Perform UMAP dimensionality reduction."""
        logger.info("Performing UMAP dimensionality reduction")
        
        # Standardize embeddings
        scaler = StandardScaler()
        embeddings_scaled = scaler.fit_transform(embeddings)
        
        # Perform UMAP reduction
        reducer = umap.UMAP(
            n_neighbors=self.umap_n_neighbors,
            min_dist=self.umap_min_dist,
            n_components=self.umap_n_components,
            random_state=42,
            metric='cosine'
        )
        
        umap_coords = reducer.fit_transform(embeddings_scaled)
        logger.info(f"UMAP reduction complete. Shape: {umap_coords.shape}")
        
        return umap_coords
    
    def update_book_clustering(self, book_id: str, cluster_id: int, 
                             centroid_distance: float, umap_x: float, umap_y: float) -> bool:
        """Update book with clustering results."""
        try:
            update_data = BookUpdate(
                cluster_id=cluster_id,
                centroid_distance=float(centroid_distance),
                umap_x=float(umap_x),
                umap_y=float(umap_y)
            )
            
            self.db.update_book(book_id, update_data)
            return True
        
        except Exception as e:
            logger.error(f"Error updating book clustering: {str(e)}")
            return False
    
    def cluster_all_books(self) -> Dict[str, Any]:
        """Perform clustering on all books with embeddings."""
        embeddings, books = self.get_embeddings_data()
        
        if embeddings is None:
            return {
                'success': False,
                'error': 'No embeddings available'
            }
        
        try:
            # Find optimal k
            optimal_k = self.find_optimal_k(embeddings)
            
            # Perform clustering
            cluster_labels, centroid_distances = self.perform_clustering(embeddings, optimal_k)
            
            # Perform UMAP reduction
            umap_coords = self.perform_umap_reduction(embeddings)
            
            # Update books with clustering results
            updated_count = 0
            for i, book in enumerate(books):
                if self.update_book_clustering(
                    book.book_id,
                    int(cluster_labels[i]),
                    float(centroid_distances[i]),
                    float(umap_coords[i, 0]),
                    float(umap_coords[i, 1])
                ):
                    updated_count += 1
            
            logger.info(f"Clustering complete. Updated {updated_count}/{len(books)} books")
            
            return {
                'success': True,
                'optimal_k': optimal_k,
                'total_books': len(books),
                'updated_books': updated_count,
                'cluster_distribution': self._get_cluster_distribution(cluster_labels)
            }
        
        except Exception as e:
            logger.error(f"Error during clustering: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_cluster_distribution(self, cluster_labels: np.ndarray) -> Dict[int, int]:
        """Get distribution of books across clusters."""
        unique, counts = np.unique(cluster_labels, return_counts=True)
        return dict(zip(unique, counts))
    
    def get_clustering_stats(self) -> Dict[str, Any]:
        """Get statistics about clustering status."""
        books = self.db.get_all_books()
        books_with_clustering = [book for book in books if book.cluster_id is not None]
        
        if not books_with_clustering:
            return {
                'total_books': len(books),
                'clustered_books': 0,
                'clustering_rate': 0.0,
                'num_clusters': 0,
                'cluster_distribution': {}
            }
        
        # Get cluster distribution
        cluster_counts = {}
        for book in books_with_clustering:
            cluster_counts[book.cluster_id] = cluster_counts.get(book.cluster_id, 0) + 1
        
        return {
            'total_books': len(books),
            'clustered_books': len(books_with_clustering),
            'clustering_rate': round(len(books_with_clustering) / len(books) * 100, 2),
            'num_clusters': len(cluster_counts),
            'cluster_distribution': cluster_counts
        }
    
    def get_cluster_exemplars(self, cluster_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get exemplar books for a cluster (closest to centroid)."""
        books = self.db.get_books_by_cluster(cluster_id)
        
        # Sort by centroid distance (closest first)
        books_sorted = sorted(books, key=lambda x: x.centroid_distance or float('inf'))
        
        exemplars = []
        for book in books_sorted[:limit]:
            exemplars.append({
                'book_id': book.book_id,
                'title': book.title,
                'author': book.author,
                'rating': book.my_rating,
                'centroid_distance': book.centroid_distance,
                'genres': book.genres
            })
        
        return exemplars
    
    def get_all_cluster_exemplars(self) -> Dict[int, List[Dict[str, Any]]]:
        """Get exemplars for all clusters."""
        stats = self.get_clustering_stats()
        num_clusters = stats['num_clusters']
        
        exemplars = {}
        for cluster_id in range(num_clusters):
            exemplars[cluster_id] = self.get_cluster_exemplars(cluster_id)
        
        return exemplars


# Global clusterer instance
clusterer = BookClusterer() 