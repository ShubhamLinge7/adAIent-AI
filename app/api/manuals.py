"""
API endpoint for listing available manuals.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import List
import logging
import sys
from pathlib import Path
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import config
from app.models.schemas import ManualInfo
from app.services.indexer import get_indexer
from app.auth.dependencies import require_role
from app.auth.models import UserRole, Session

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/manuals", response_model=List[ManualInfo])
async def list_manuals():
    """
    List all available manuals in the system.
    
    Returns:
        List of manual information including indexing status.
    """
    try:
        indexer = get_indexer()
        manuals = []
        
        # Scan PDF files in manuals directory
        pdf_files = list(config.MANUALS_DIR.glob("*.pdf"))
        
        for pdf_path in pdf_files:
            manual_id = pdf_path.stem
            is_indexed = indexer.is_indexed(manual_id)
            chunk_count = indexer.get_chunk_count(manual_id) if is_indexed else None
            
            manuals.append(ManualInfo(
                manual_id=manual_id,
                filename=pdf_path.name,
                indexed=is_indexed,
                chunk_count=chunk_count
            ))
        
        logger.info(f"Listed {len(manuals)} manuals")
        return manuals
    
    except Exception as e:
        logger.error(f"Failed to list manuals: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list manuals: {str(e)}")


@router.post("/manuals/upload", response_model=ManualInfo)
async def upload_manual(
    file: UploadFile = File(...),
    current_user: Session = Depends(require_role(UserRole.ADMIN, UserRole.SUPERADMIN))
):
    """
    Upload a new manual PDF and automatically index it.
    
    Args:
        file: PDF file to upload (configurable limit in config.py)
        current_user: Authenticated admin or superadmin user
    
    Returns:
        ManualInfo with indexing status
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Validate file size (configurable limit)
        MAX_SIZE = config.MAX_UPLOAD_SIZE_MB * 1024 * 1024  # Convert MB to bytes
        
        # Read file content
        content = await file.read()
        if len(content) > MAX_SIZE:
            raise HTTPException(status_code=400, detail=f"File size exceeds {config.MAX_UPLOAD_SIZE_MB}MB limit")
        
        # Generate manual_id from filename (remove .pdf extension)
        manual_id = Path(file.filename).stem
        
        # Check if manual already exists
        pdf_path = config.MANUALS_DIR / file.filename
        if pdf_path.exists():
            raise HTTPException(status_code=409, detail=f"Manual '{file.filename}' already exists")
        
        # Save file to manuals directory
        config.MANUALS_DIR.mkdir(parents=True, exist_ok=True)
        with open(pdf_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Saved manual: {file.filename} ({len(content)} bytes)")
        
        # Index the manual automatically
        indexer = get_indexer()
        result = indexer.index_manual(manual_id, pdf_path)
        
        logger.info(f"Indexed manual {manual_id}: {result['chunk_count']} chunks")
        
        return ManualInfo(
            manual_id=manual_id,
            filename=file.filename,
            indexed=True,
            chunk_count=result['chunk_count']
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Failed to upload manual: {e}")
        # Clean up file if it was saved but indexing failed
        if pdf_path.exists():
            pdf_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to upload manual: {str(e)}")


@router.delete("/manuals/{manual_id}")
async def delete_manual(
    manual_id: str,
    current_user: Session = Depends(require_role(UserRole.ADMIN, UserRole.SUPERADMIN))
):
    """
    Delete a manual and its FAISS index.
    
    Args:
        manual_id: ID of the manual to delete (filename without .pdf)
        current_user: Authenticated admin or superadmin user
    
    Returns:
        Success message
    """
    try:
        # Find the PDF file
        pdf_path = None
        for pdf_file in config.MANUALS_DIR.glob("*.pdf"):
            if pdf_file.stem == manual_id:
                pdf_path = pdf_file
                break
        
        if not pdf_path:
            raise HTTPException(status_code=404, detail=f"Manual '{manual_id}' not found")
        
        # Delete the FAISS index and related files
        indexer = get_indexer()
        deleted_files = []
        
        # Delete index file
        index_path = config.INDEXES_DIR / f"{manual_id}.index"
        if index_path.exists():
            index_path.unlink()
            logger.info(f"Deleted index: {index_path}")
            deleted_files.append(index_path.name)
        
        # Delete metadata JSON
        metadata_path = config.INDEXES_DIR / f"{manual_id}_metadata.json"
        if metadata_path.exists():
            metadata_path.unlink()
            logger.info(f"Deleted metadata: {metadata_path}")
            deleted_files.append(metadata_path.name)
        
        # Delete any pkl files
        pkl_path = config.INDEXES_DIR / f"{manual_id}.pkl"
        if pkl_path.exists():
            pkl_path.unlink()
            logger.info(f"Deleted pkl: {pkl_path}")
            deleted_files.append(pkl_path.name)
        
        # Delete the PDF file
        pdf_path.unlink()
        logger.info(f"Deleted manual: {pdf_path.name}")
        deleted_files.append(pdf_path.name)
        
        return {
            "success": True,
            "message": f"Manual '{manual_id}' and all related files deleted successfully",
            "deleted_files": deleted_files
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete manual: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete manual: {str(e)}")

@router.get("/manuals/{manual_id}/preview")
async def preview_manual(manual_id: str):
    """
    Get a preview of a manual including metadata and sample chunks.
    
    Args:
        manual_id: ID of the manual to preview
        
    Returns:
        Manual metadata and first 5 chunks
    """
    try:
        indexer = get_indexer()
        
        # Check if manual exists and is indexed
        if not indexer.is_indexed(manual_id):
            raise HTTPException(status_code=404, detail=f"Manual '{manual_id}' not found or not indexed")
        
        # Get PDF filename
        pdf_path = None
        for pdf_file in config.MANUALS_DIR.glob("*.pdf"):
            if pdf_file.stem == manual_id:
                pdf_path = pdf_file
                break
        
        if not pdf_path:
            raise HTTPException(status_code=404, detail=f"Manual '{manual_id}' PDF not found")
        
        # Load metadata and chunks
        import pickle
        index_dir = indexer.get_manual_index_path(manual_id)
        metadata_file = index_dir / "metadata.pkl"
        
        with open(metadata_file, 'rb') as f:
            metadata = pickle.load(f)
        
        # Get first 5 chunks as preview
        chunks = metadata.get('chunks', [])
        sample_chunks = chunks[:5] if len(chunks) >= 5 else chunks
        
        return {
            "manual_id": manual_id,
            "filename": pdf_path.name,
            "chunk_count": len(chunks),
            "sample_chunks": sample_chunks
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to preview manual: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to preview manual: {str(e)}")


@router.get("/pdf/{manual_id}")
async def get_manual_pdf(manual_id: str):
    """
    Get PDF file for viewing in browser.
    
    Args:
        manual_id: ID of the manual (filename without .pdf extension)
        
    Returns:
        PDF file for browser viewing
    """
    from fastapi.responses import FileResponse
    
    try:
        # Find PDF file
        pdf_path = None
        for pdf_file in config.MANUALS_DIR.glob("*.pdf"):
            if pdf_file.stem == manual_id:
                pdf_path = pdf_file
                break
        
        if not pdf_path or not pdf_path.exists():
            raise HTTPException(status_code=404, detail=f"Manual '{manual_id}' PDF not found")
        
        # Return PDF file with proper content type for inline viewing
        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename=pdf_path.name,
            headers={"Content-Disposition": f"inline; filename={pdf_path.name}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to serve PDF: {str(e)}")
