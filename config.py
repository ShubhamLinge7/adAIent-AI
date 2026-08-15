"""
Configuration for the industrial troubleshooting assistant.
All settings for offline operation on Windows.
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MANUALS_DIR = DATA_DIR / "manuals"
INDEXES_DIR = DATA_DIR / "indexes"

# Ensure directories exist
MANUALS_DIR.mkdir(parents=True, exist_ok=True)
INDEXES_DIR.mkdir(parents=True, exist_ok=True)

# Embedding model (local, offline)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384  # Dimension for all-MiniLM-L6-v2

# Chunking parameters
CHUNK_SIZE = 1200  # Characters per chunk (increased for better context)
CHUNK_OVERLAP = 200  # Overlap between chunks

# Retrieval parameters
TOP_K_CHUNKS = 5  # Number of relevant chunks to retrieve

# Ollama LLM settings
LLM_PROVIDER = "ollama"  # Options: "ollama", "openai", "groq", "ollama-multi"
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:3b"  # Using llama3.2:3b as configured
OLLAMA_TIMEOUT = 300  # Timeout in seconds

# Intent validation keywords (troubleshooting indicators)
TROUBLESHOOTING_KEYWORDS = [
    # Not + action/state
    r"not\s+(working|start|run|moving|responding|operating|function)",
    r"won't\s+(start|run|move|respond|work)",
    r"doesn't\s+(start|run|move|respond|work)",
    r"fails?\s+to\s+(start|run|move|respond|work)",

    # Stopped/shutdown states
    "stopped", "shutdown", "shut down", "stopped working",

    # Error states
    "error", "fault", "alarm", "warning", "issue", "problem", "malfunction",
    "broken", "damaged", "failed", "failure",

    # Physical issues
    "leak", "leaking", "noise", "vibration", "overheating", "overheat",
    "too hot", "burning", "smoking", "sparking",

    # Operational issues
    "unresponsive", "frozen", "stuck", "jamb", "jam", "block",
    "slow", "jitter", "shake", "grinding",

    # Unexpected behavior
    "strange", "unusual", "abnormal", "weird", "unexpected",

    # Action requests
    "how to fix", "how do i fix", "troubleshoot", "diagnose", "repair",
    "what to do when", "what should i do", "fix", "repair", "check",

    # Error codes
    r"error\s+code", r"code\s+[a-z0-9]+", r"[a-z]\d+",  # E404, E001, etc
]

# Blocked keywords (informational/theoretical)
INFORMATIONAL_KEYWORDS = [
    "what is", "what are", "explain", "describe", "tell me about",
    "how does it work", "how it works", "theory", "principle",
    "specifications", "features", "capabilities", "benefits",
    "compare", "comparison", "difference between",
    "history", "why was", "who invented"
]
