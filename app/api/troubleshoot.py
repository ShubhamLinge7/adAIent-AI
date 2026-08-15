"""
API endpoint for troubleshooting queries.
"""
from fastapi import APIRouter, HTTPException
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models.schemas import TroubleshootRequest, TroubleshootResponse, ErrorResponse
from app.services.semantic_validator import get_semantic_validator
from app.services.indexer import get_indexer
from app.services.retriever import get_retriever
from app.services.llm import get_llm_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/ask", response_model=TroubleshootResponse)
async def troubleshoot(request: TroubleshootRequest):
    """
    Answer a troubleshooting question using the selected manual.
    
    Workflow:
    1. Validate intent (troubleshooting vs informational)
    2. Check if manual is indexed
    3. Retrieve relevant context from manual
    4. Generate response using LLM
    
    Args:
        request: Troubleshooting request with manual_id and question
    
    Returns:
        Troubleshooting response with answer and context
    """
    try:
        # Step 1: Validate intent using semantic validation (LLM-based)
        logger.info(f"Processing question for manual: {request.manual_id}")
        validator = get_semantic_validator()
        is_valid, error_message = validator.validate(request.question)
        
        if not is_valid:
            logger.warning(f"Intent validation failed: {error_message}")
            raise HTTPException(status_code=400, detail=error_message)
        
        # Step 2: Check if manual is indexed
        indexer = get_indexer()
        if not indexer.is_indexed(request.manual_id):
            logger.error(f"Manual not indexed: {request.manual_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Manual '{request.manual_id}' is not indexed. Please ensure the PDF exists and has been indexed."
            )
        
        # Step 3: Retrieve relevant context
        retriever = get_retriever()
        try:
            context_chunks = retriever.retrieve(request.manual_id, request.question)
        except FileNotFoundError:
            logger.error(f"Index not found for manual: {request.manual_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Index not found for manual '{request.manual_id}'"
            )
        
        if not context_chunks:
            logger.warning(f"No context retrieved for question: {request.question[:50]}...")
            raise HTTPException(
                status_code=404,
                detail="No relevant information found in the selected manual for this query."
            )
        
        logger.info(f"Retrieved {len(context_chunks)} context chunks")
        
        # Step 4: Generate response using LLM (async)
        llm_service = get_llm_service()
        answer = await llm_service.generate_response(
            question=request.question,
            context_chunks=context_chunks,
            manual_id=request.manual_id
        )
        
        # Step 5: Prepare response
        response = TroubleshootResponse(
            manual_id=request.manual_id,
            question=request.question,
            answer=answer,
            context_used=context_chunks
        )
        
        # Add warning if LLM service had issues
        if "unavailable" in answer.lower() or "timed out" in answer.lower():
            response.warning = "LLM service issue detected. Response may be incomplete."
        
        logger.info("Troubleshooting response generated successfully")
        return response
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error during troubleshooting: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )
