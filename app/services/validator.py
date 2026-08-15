"""
Intent validation service.
Ensures queries are troubleshooting-focused, not informational.
"""
import re
import logging
from typing import Tuple

import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntentValidator:
    """Validates that user queries are troubleshooting-related."""
    
    def __init__(self):
        """Initialize validator with keyword lists."""
        # Compile troubleshooting patterns - handle both raw strings and regex patterns
        self.troubleshooting_patterns = []
        for pattern in config.TROUBLESHOOTING_KEYWORDS:
            try:
                # Try to compile as regex first (for patterns like r"not\s+...")
                self.troubleshooting_patterns.append(re.compile(pattern, re.IGNORECASE))
            except:
                # Fall back to simple string matching
                self.troubleshooting_patterns.append(re.compile(re.escape(pattern), re.IGNORECASE))
        
        self.informational_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in config.INFORMATIONAL_KEYWORDS
        ]
    
    def validate(self, question: str) -> Tuple[bool, str]:
        """
        Validate if a question is troubleshooting-focused.
        
        Args:
            question: User's question
        
        Returns:
            Tuple of (is_valid, message)
            - is_valid: True if troubleshooting question, False if informational
            - message: Error message if invalid, empty string if valid
        """
        question_lower = question.lower().strip()
        
        # Check for informational keywords (blocklist)
        for pattern in self.informational_patterns:
            if pattern.search(question_lower):
                logger.warning(f"Query blocked (informational): {question[:50]}...")
                return False, (
                    "This assistant is designed for troubleshooting only. "
                    "Please ask about a specific fault, error, or malfunction you're experiencing. "
                    "Informational questions (e.g., 'what is...', 'explain...', 'how does it work') "
                    "are not supported."
                )
        
        # Check for troubleshooting keywords (allowlist)
        has_troubleshooting_intent = any(
            pattern.search(question_lower)
            for pattern in self.troubleshooting_patterns
        )
        
        if not has_troubleshooting_intent:
            logger.warning(f"Query blocked (no troubleshooting intent): {question[:50]}...")
            return False, (
                "This assistant is designed for troubleshooting only. "
                "Please describe a specific problem or fault you're experiencing "
                "(e.g., 'motor not starting', 'error code displayed', 'unusual noise')."
            )
        
        # Valid troubleshooting question
        logger.info(f"Query validated: {question[:50]}...")
        return True, ""


# Global validator instance
_validator = None


def get_validator() -> IntentValidator:
    """Get or create the global validator instance."""
    global _validator
    if _validator is None:
        _validator = IntentValidator()
    return _validator
