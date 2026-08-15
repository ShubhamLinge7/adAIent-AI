"""
Semantic intent validator using embedding similarity.
Fast validation using cosine similarity instead of LLM calls.
"""
import logging
from typing import Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SemanticValidator:
    """Validates troubleshooting intent using embedding similarity (fast)."""
    
    def __init__(self):
        """Initialize semantic validator with embedding model."""
        logger.info("Loading embedding model for semantic validation...")
        self.model = SentenceTransformer(config.EMBEDDING_MODEL)
        
        # Sample troubleshooting questions (positive examples)
        self.troubleshooting_examples = [
            "motor not starting",
            "pump is leaking fluid",
            "conveyor belt stopped moving",
            "robot arm error code displayed",
            "machine making grinding noise",
            "equipment overheating",
            "belt is slipping",
            "unusual vibration detected",
            "system won't power on",
            "sensor not responding",
            "valve stuck closed",
            "pressure gauge showing error",
            "temperature too high",
            "motor keeps shutting down",
            "strange sound from pump",
            "equipment frozen and unresponsive",
            "bearing making noise",
            "drive shaft broken",
            "hydraulic system pressure drop",
            "electrical fault alarm"
        ]
        
        # Sample informational questions (negative examples)
        self.informational_examples = [
            "what is a motor",
            "explain how pumps work",
            "tell me about conveyor systems",
            "describe the components",
            "how does a robot arm operate",
            "what are the specifications",
            "theory behind operation",
            "working principle explained"
        ]
        
        # Pre-compute embeddings for sample questions
        logger.info("Computing embeddings for sample questions...")
        self.troubleshooting_embeddings = self.model.encode(self.troubleshooting_examples)
        self.informational_embeddings = self.model.encode(self.informational_examples)
        logger.info("Semantic validator ready")

    def validate(self, question: str) -> Tuple[bool, str]:
        """
        Validate if a question is troubleshooting-focused using semantic similarity.
        
        Args:
            question: User's question
        
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Quick pre-check for obvious informational questions
            obvious_informational = [
                "what is", "what are", "explain", "describe", 
                "tell me about", "how does", "how it works",
                "define", "definition", "meaning of", "theory"
            ]
            
            question_lower = question.lower().strip()
            for phrase in obvious_informational:
                if question_lower.startswith(phrase):
                    logger.warning(f"Query blocked (obviously informational): {question[:50]}...")
                    return False, (
                        "This assistant is designed for troubleshooting only. "
                        "Please ask about a specific fault, error, or malfunction you're experiencing. "
                        "Examples: 'Motor not starting', 'Unusual noise from pump', 'Error code E404 displayed'"
                    )
            
            # Compute embedding for user question
            question_embedding = self.model.encode([question])[0]
            
            # Calculate similarity with troubleshooting examples
            troubleshooting_similarities = self._cosine_similarity(
                question_embedding, 
                self.troubleshooting_embeddings
            )
            max_troubleshooting_sim = np.max(troubleshooting_similarities)
            
            # Calculate similarity with informational examples
            informational_similarities = self._cosine_similarity(
                question_embedding,
                self.informational_embeddings
            )
            max_informational_sim = np.max(informational_similarities)
            
            logger.info(f"Semantic similarity - Troubleshooting: {max_troubleshooting_sim:.3f}, Informational: {max_informational_sim:.3f}")
            
            # Decision logic: accept if more similar to troubleshooting OR if not clearly informational
            if max_troubleshooting_sim > 0.3 or max_informational_sim < 0.4:
                # Likely troubleshooting or neutral question
                logger.info(f"Query validated (semantic): {question[:50]}...")
                return True, ""
            else:
                # More similar to informational questions
                logger.warning(f"Query rejected (informational): {question[:50]}...")
                return False, (
                    "This assistant is designed for troubleshooting only. "
                    "Please describe a specific problem, fault, or error you're experiencing. "
                    "Examples: 'Motor not starting', 'Unusual noise from pump', 'Error code displayed'"
                )
        
        except Exception as e:
            logger.error(f"Error during semantic validation: {e}")
            # Fallback: accept the question
            logger.warning(f"Validation error, accepting question: {question[:50]}...")
            return True, ""
    
    def _cosine_similarity(self, vec1, vec2_matrix):
        """Calculate cosine similarity between a vector and matrix of vectors."""
        # Normalize vectors
        vec1_norm = vec1 / np.linalg.norm(vec1)
        vec2_norm = vec2_matrix / np.linalg.norm(vec2_matrix, axis=1, keepdims=True)
        
        # Compute dot product (cosine similarity)
        return np.dot(vec2_norm, vec1_norm)


# Global validator instance
_validator = None


def get_semantic_validator() -> SemanticValidator:
    """Get or create the global semantic validator instance."""
    global _validator
    if _validator is None:
        _validator = SemanticValidator()
    return _validator
