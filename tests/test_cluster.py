"""Tests for the clustering module."""

import pytest
from unittest.mock import Mock, patch

from app.cluster import BookClusterer


class TestBookClusterer:
    """Test cases for BookClusterer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.clusterer = BookClusterer()
    
    def test_cluster_all_books_disabled(self):
        """Test that clustering is no longer supported."""
        result = self.clusterer.cluster_all_books()
        
        # Should return failure since clustering is disabled
        assert not result['success']
        assert 'no longer supported' in result['error']
    
    def test_get_clustering_stats(self):
        """Test clustering statistics."""
        stats = self.clusterer.get_clustering_stats()
        
        # Should return valid stats structure with zero values
        assert 'total_books' in stats
        assert 'clustered_books' in stats
        assert 'clustering_rate' in stats
        assert 'num_clusters' in stats
        assert 'cluster_distribution' in stats
        
        # Should all be zero since clustering is disabled
        assert stats['clustered_books'] == 0
        assert stats['clustering_rate'] == 0.0
        assert stats['num_clusters'] == 0
    
    def test_get_cluster_exemplars_disabled(self):
        """Test getting cluster exemplars (no longer supported)."""
        exemplars = self.clusterer.get_cluster_exemplars(0)
        assert isinstance(exemplars, list)
        assert len(exemplars) == 0  # Should be empty since clustering is disabled
    
    def test_get_all_cluster_exemplars_disabled(self):
        """Test getting all cluster exemplars (no longer supported)."""
        exemplars = self.clusterer.get_all_cluster_exemplars()
        assert isinstance(exemplars, dict)
        assert len(exemplars) == 0  # Should be empty since clustering is disabled


if __name__ == "__main__":
    pytest.main([__file__]) 