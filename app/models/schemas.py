"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class ManualInfo(BaseModel):
    """Information about an available manual."""
    manual_id: str = Field(..., description="Unique identifier (filename without extension)")
    filename: str = Field(..., description="Original PDF filename")
    indexed: bool = Field(..., description="Whether the manual has been indexed")
    chunk_count: Optional[int] = Field(None, description="Number of chunks in index")


class TroubleshootRequest(BaseModel):
    """Request to troubleshoot an issue."""
    manual_id: str = Field(..., description="ID of the manual to search")
    question: str = Field(..., min_length=10, max_length=500, description="Troubleshooting question")


class TroubleshootResponse(BaseModel):
    """Response from troubleshooting query."""
    manual_id: str
    question: str
    answer: str
    context_used: List[str] = Field(default_factory=list, description="Chunks retrieved from manual")
    warning: Optional[str] = Field(None, description="Warning if answer quality is uncertain")


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    details: Optional[str] = None
