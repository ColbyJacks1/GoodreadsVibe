"""Tests for the clustering module."""

import pytest
import numpy as np
from unittest.mock import Mock, patch

from app.cluster import BookClusterer


class TestBookClusterer:
    """Test cases for BookClusterer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.clusterer = BookClusterer()
    
    def test_find_optimal_k(self):
        """Test optimal k finding."""
        # Create mock embeddings
        embeddings = np.random.rand(20, 10)  # 20 books, 10 dimensions
        
        # Mock the silhouette score calculation
        with patch('sklearn.metrics.silhouette_score') as mock_silhouette:
            mock_silhouette.return_value = 0.5
            optimal_k = self.clusterer.find_optimal_k(embeddings)
            
            # Should return a value within the expected range
            assert self.clusterer.min_k <= optimal_k <= self.clusterer.max_k
    
    def test_perform_clustering(self):
        """Test clustering performance."""
        # Create mock embeddings
        embeddings = np.random.rand(10, 5)  # 10 books, 5 dimensions
        k = 3
        
        cluster_labels, centroid_distances = self.clusterer.perform_clustering(embeddings, k)
        
        # Check output shapes
        assert len(cluster_labels) == 10
        assert len(centroid_distances) == 10
        
        # Check cluster labels are within range
        assert all(0 <= label < k for label in cluster_labels)
        
        # Check distances are non-negative
        assert all(distance >= 0 for distance in centroid_distances)
    
    def test_perform_umap_reduction(self):
        """Test UMAP dimensionality reduction."""
        # Create mock embeddings
        embeddings = np.random.rand(10, 10)  # 10 books, 10 dimensions
        
        umap_coords = self.clusterer.perform_umap_reduction(embeddings)
        
        # Check output shape
        assert umap_coords.shape == (10, 2)  # Should reduce to 2D
    
    def test_get_clustering_stats(self):
        """Test clustering statistics."""
        stats = self.clusterer.get_clustering_stats()
        
        # Should return valid stats structure
        assert 'total_books' in stats
        assert 'clustered_books' in stats
        assert 'clustering_rate' in stats
        assert 'num_clusters' in stats
        assert 'cluster_distribution' in stats
    
    def test_get_cluster_exemplars(self):
        """Test getting cluster exemplars."""
        # This would require a database with clustered books
        # For now, just test the method exists and doesn't crash
        exemplars = self.clusterer.get_cluster_exemplars(0)
        assert isinstance(exemplars, list)


if __name__ == "__main__":
    pytest.main([__file__]) 