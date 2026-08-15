"""
PDF indexing service.
Handles PDF extraction, chunking, and FAISS index creation per manual.
"""
import os
import pickle
from pathlib import Path
from typing import List, Dict, Tuple
import logging

import numpy as np
import faiss
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer

import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ManualIndexer:
    """Manages indexing of PDF manuals into per-manual FAISS indexes."""
    
    def __init__(self):
        """Initialize the indexer with embedding model."""
        logger.info(f"Loading embedding model: {config.EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL, local_files_only=True)
        logger.info("Embedding model loaded successfully")
    
    def get_manual_index_path(self, manual_id: str) -> Path:
        """Get the directory path for a manual's index."""
        return config.INDEXES_DIR / manual_id
    
    def is_indexed(self, manual_id: str) -> bool:
        """Check if a manual has been indexed."""
        index_dir = self.get_manual_index_path(manual_id)
        index_file = index_dir / "index.faiss"
        metadata_file = index_dir / "metadata.pkl"
        return index_file.exists() and metadata_file.exists()
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract all text from a PDF file."""
        try:
            logger.info(f"Extracting text from {pdf_path.name}")
            reader = PdfReader(str(pdf_path))
            text = ""
            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n[Page {page_num}]\n{page_text}"
            logger.info(f"Extracted {len(text)} characters from {len(reader.pages)} pages")
            return text
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path}: {e}")
            raise
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks, preserving page numbers."""
        chunks = []
        lines = text.split('\n')
        current_chunk = []
        current_page = "Page 1"
        chunk_size = 0
        
        for line in lines:
            # Track current page
            if line.strip().startswith('[Page '):
                current_page = line.strip()
                continue
            
            line_size = len(line)
            
            if chunk_size + line_size > config.CHUNK_SIZE:
                if current_chunk:
                    # Add page marker at start of chunk
                    chunk_text = f"[{current_page}]\n" + '\n'.join(current_chunk)
                    chunks.append(chunk_text)
                    
                    # Overlap: keep last few lines
                    overlap_lines = current_chunk[-5:] if len(current_chunk) > 5 else current_chunk
                    current_chunk = overlap_lines + [line]
                    chunk_size = sum(len(l) for l in current_chunk)
                else:
                    current_chunk = [line]
                    chunk_size = line_size
            else:
                current_chunk.append(line)
                chunk_size += line_size
        
        # Add final chunk
        if current_chunk:
            chunk_text = f"[{current_page}]\n" + '\n'.join(current_chunk)
            chunks.append(chunk_text)
        
        logger.info(f"Created {len(chunks)} chunks")
        return chunks
    
    def create_embeddings(self, chunks: List[str]) -> np.ndarray:
        """Create embeddings for text chunks."""
        logger.info(f"Creating embeddings for {len(chunks)} chunks")
        embeddings = self.embedding_model.encode(
            chunks,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        return embeddings
    
    def build_faiss_index(self, embeddings: np.ndarray) -> faiss.Index:
        """Build FAISS index from embeddings."""
        dimension = embeddings.shape[1]
        logger.info(f"Building FAISS index with dimension {dimension}")
        
        # Use IndexFlatL2 for exact search (simple and reliable)
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings.astype('float32'))
        
        logger.info(f"FAISS index built with {index.ntotal} vectors")
        return index
    
    def save_index(self, manual_id: str, index: faiss.Index, chunks: List[str]):
        """Save FAISS index and metadata to disk."""
        index_dir = self.get_manual_index_path(manual_id)
        index_dir.mkdir(parents=True, exist_ok=True)
        
        index_file = index_dir / "index.faiss"
        metadata_file = index_dir / "metadata.pkl"
        
        # Save FAISS index
        faiss.write_index(index, str(index_file))
        
        # Save metadata (chunks)
        metadata = {
            "chunks": chunks,
            "chunk_count": len(chunks),
            "embedding_model": config.EMBEDDING_MODEL
        }
        with open(metadata_file, "wb") as f:
            pickle.dump(metadata, f)
        
        logger.info(f"Index saved to {index_dir}")
    
    def index_manual(self, manual_id: str, pdf_path: Path) -> Dict:
        """
        Index a single manual: extract text → chunk → embed → save FAISS index.
        Returns metadata about the indexing operation.
        """
        try:
            logger.info(f"Starting indexing for manual: {manual_id}")
            
            # Extract text from PDF
            text = self.extract_text_from_pdf(pdf_path)
            
            if not text.strip():
                raise ValueError(f"No text extracted from {pdf_path.name}")
            
            # Chunk the text
            chunks = self.chunk_text(text)
            
            if not chunks:
                raise ValueError(f"No chunks created from {pdf_path.name}")
            
            # Create embeddings
            embeddings = self.create_embeddings(chunks)
            
            # Build FAISS index
            index = self.build_faiss_index(embeddings)
            
            # Save to disk
            self.save_index(manual_id, index, chunks)
            
            logger.info(f"Successfully indexed {manual_id}")
            return {
                "manual_id": manual_id,
                "chunk_count": len(chunks),
                "success": True
            }
        
        except Exception as e:
            logger.error(f"Failed to index {manual_id}: {e}")
            return {
                "manual_id": manual_id,
                "success": False,
                "error": str(e)
            }
    
    def index_all_manuals(self, force_reindex: bool = False) -> List[Dict]:
        """
        Index all PDFs in the manuals directory.
        Skip already-indexed manuals unless force_reindex is True.
        """
        results = []
        
        pdf_files = list(config.MANUALS_DIR.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files in {config.MANUALS_DIR}")
        
        for pdf_path in pdf_files:
            manual_id = pdf_path.stem  # Filename without extension
            
            # Skip if already indexed (unless forcing)
            if not force_reindex and self.is_indexed(manual_id):
                logger.info(f"Skipping {manual_id} (already indexed)")
                results.append({
                    "manual_id": manual_id,
                    "skipped": True,
                    "reason": "Already indexed"
                })
                continue
            
            # Index the manual
            result = self.index_manual(manual_id, pdf_path)
            results.append(result)
        
        return results
    
    def get_chunk_count(self, manual_id: str) -> int:
        """Get the number of chunks in a manual's index."""
        if not self.is_indexed(manual_id):
            return 0
        
        metadata_file = self.get_manual_index_path(manual_id) / "metadata.pkl"
        try:
            with open(metadata_file, "rb") as f:
                metadata = pickle.load(f)
                return metadata.get("chunk_count", 0)
        except Exception as e:
            logger.error(f"Failed to read metadata for {manual_id}: {e}")
            return 0


# Global indexer instance
_indexer = None


def get_indexer() -> ManualIndexer:
    """Get or create the global indexer instance."""
    global _indexer
    if _indexer is None:
        _indexer = ManualIndexer()
    return _indexer

