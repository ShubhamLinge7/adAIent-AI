"""
Vector retrieval service.
Handles searching FAISS indexes for relevant context.
"""
import pickle
from pathlib import Path
from typing import List, Tuple
import logging

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContextRetriever:
    """Retrieves relevant context from manual-specific FAISS indexes."""
    
    def __init__(self):
        """Initialize retriever with embedding model."""
        logger.info(f"Loading embedding model for retrieval: {config.EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL, local_files_only=True)
        self._index_cache = {}  # Cache loaded indexes
        self._metadata_cache = {}  # Cache loaded metadata
    
    def _get_index_path(self, manual_id: str) -> Path:
        """Get the directory path for a manual's index."""
        return config.INDEXES_DIR / manual_id
    
    def _load_index(self, manual_id: str) -> Tuple[faiss.Index, dict]:
        """Load FAISS index and metadata for a manual."""
        # Check cache first
        if manual_id in self._index_cache:
            return self._index_cache[manual_id], self._metadata_cache[manual_id]
        
        index_dir = self._get_index_path(manual_id)
        index_file = index_dir / "index.faiss"
        metadata_file = index_dir / "metadata.pkl"
        
        if not index_file.exists() or not metadata_file.exists():
            raise FileNotFoundError(f"Index not found for manual: {manual_id}")
        
        # Load FAISS index
        logger.info(f"Loading FAISS index for {manual_id}")
        index = faiss.read_index(str(index_file))
        
        # Load metadata
        with open(metadata_file, "rb") as f:
            metadata = pickle.load(f)
        
        # Cache for future use
        self._index_cache[manual_id] = index
        self._metadata_cache[manual_id] = metadata
        
        logger.info(f"Loaded index with {index.ntotal} vectors for {manual_id}")
        return index, metadata
    
    def retrieve(self, manual_id: str, query: str, top_k: int = None) -> List[str]:
        """
        Retrieve top-K most relevant chunks from a manual's index.
        
        Args:
            manual_id: ID of the manual to search
            query: User's troubleshooting question
            top_k: Number of chunks to retrieve (default from config)
        
        Returns:
            List of relevant text chunks
        """
        if top_k is None:
            top_k = config.TOP_K_CHUNKS
        
        try:
            # Load index and metadata
            index, metadata = self._load_index(manual_id)
            chunks = metadata["chunks"]
            
            # Embed the query
            logger.info(f"Embedding query: {query[:50]}...")
            query_embedding = self.embedding_model.encode(
                [query],
                convert_to_numpy=True
            ).astype('float32')
            
            # Search FAISS index
            logger.info(f"Searching index for top-{top_k} results")
            distances, indices = index.search(query_embedding, top_k)
            
            # Retrieve corresponding chunks
            retrieved_chunks = []
            for idx in indices[0]:
                if 0 <= idx < len(chunks):
                    retrieved_chunks.append(chunks[idx])
            
            logger.info(f"Retrieved {len(retrieved_chunks)} chunks for query")
            return retrieved_chunks
        
        except FileNotFoundError as e:
            logger.error(f"Manual not indexed: {manual_id}")
            raise
        except Exception as e:
            logger.error(f"Retrieval failed for {manual_id}: {e}")
            raise
    
    def clear_cache(self):
        """Clear the index cache (useful if indexes are updated)."""
        self._index_cache.clear()
        self._metadata_cache.clear()
        logger.info("Index cache cleared")


# Global retriever instance
_retriever = None


def get_retriever() -> ContextRetriever:
    """Get or create the global retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = ContextRetriever()
    return _retriever

