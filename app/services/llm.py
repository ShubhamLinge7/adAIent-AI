"""
LLM service - delegates to provider-specific implementations.
"""
from app.services.llm_providers import get_llm_service

__all__ = ['get_llm_service']
