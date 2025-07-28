"""Clustering functionality (no longer used)."""

import logging
from typing import Dict, Any, List

from .db import db_manager

logger = logging.getLogger(__name__)


class BookClusterer:
    """Clustering functionality is no longer used."""
    
    def __init__(self):
        self.db = db_manager
    
    def cluster_all_books(self) -> Dict[str, Any]:
        """Clustering is no longer supported."""
        logger.warning("Clustering is no longer supported")
        return {
            'success': False,
            'error': 'Clustering is no longer supported'
        }
    
    def get_clustering_stats(self) -> Dict[str, Any]:
        """Get statistics about clustering status."""
        books = self.db.get_all_books()
        
        return {
            'total_books': len(books),
            'clustered_books': 0,
            'clustering_rate': 0.0,
            'num_clusters': 0,
            'cluster_distribution': {}
        }
    
    def get_cluster_exemplars(self, cluster_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get exemplar books for a cluster (no longer supported)."""
        logger.warning("Clustering is no longer supported")
        return []
    
    def get_all_cluster_exemplars(self) -> Dict[int, List[Dict[str, Any]]]:
        """Get exemplars for all clusters (no longer supported)."""
        logger.warning("Clustering is no longer supported")
        return {}


# Global clusterer instance
clusterer = BookClusterer() 