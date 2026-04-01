"""
Configuration constants for the Legal Contract Risk Analyzer retrieval pipeline.

This module centralizes all configuration parameters used across the pipeline,
including Pinecone settings, embedding model configuration, and logging setup.
"""

import logging
import os

from dotenv import load_dotenv

from .agreement_profiles import AGREEMENT_USER_TYPE_MAP, DEFAULT_AGREEMENT_TYPE


# Load .env once so all processes share the same runtime settings.
load_dotenv()

# ============================================================================
# Pinecone Configuration
# ============================================================================

INDEX_NAME = "contract-risk-db"
"""Name of the Pinecone index containing legal clause embeddings."""

PINECONE_CLOUD = "aws"
"""Cloud provider for Pinecone serverless index."""

PINECONE_REGION = "us-east-1"
"""AWS region for Pinecone index."""


# ============================================================================
# Embedding Model Configuration
# ============================================================================

EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
"""SentenceTransformer model used for generating clause embeddings.
Must match the model used during ingestion to ensure compatibility."""

EMBEDDING_DIMENSION = 768
"""Dimension of the embedding vectors."""

NORMALIZE_EMBEDDINGS = True
"""Whether to normalize embeddings to unit vectors for cosine similarity."""

BATCH_SIZE = 32
"""Batch size for embedding generation."""


# ============================================================================
# Retrieval Configuration
# ============================================================================

TOP_K = 5
"""Number of similar clauses to retrieve from Pinecone for each query."""

SIMILARITY_THRESHOLD = 0.7
"""Minimum similarity score (0-1) for a match to be considered relevant for risk analysis."""

REASONER_SIMILARITY_THRESHOLD = 0.7
"""Minimum similarity score (0-1) for including retrieved matches in local RAG reasoning."""


# ============================================================================
# Clause Segmentation Configuration
# ============================================================================

MIN_CLAUSE_LENGTH = 20
"""Minimum character length for a text segment to be considered a valid clause."""


# ============================================================================
# OCR Configuration
# ============================================================================

OCR_ENABLED = os.getenv("OCR_ENABLED", "true").lower() in ["1", "true", "yes"]
"""Whether OCR fallback is enabled for scanned/image-only PDF pages."""

OCR_ENGINE = os.getenv("OCR_ENGINE", "easyocr").strip().lower()
"""OCR engine to use for rasterized pages. Supported: easyocr."""

OCR_LANGUAGES = [
    lang.strip() for lang in os.getenv("OCR_LANGUAGES", "en").split(",") if lang.strip()
]
"""Language list passed to OCR engine."""

OCR_RENDER_SCALE = float(os.getenv("OCR_RENDER_SCALE", "2.0"))
"""PDF page rasterization scale before OCR. Higher values improve quality at cost of speed."""

OCR_MIN_CHARS_PER_PAGE = int(os.getenv("OCR_MIN_CHARS_PER_PAGE", "30"))
"""Trigger OCR when native text extraction yields fewer characters than this threshold."""

OCR_FORCE_ALL_PAGES = os.getenv("OCR_FORCE_ALL_PAGES", "false").lower() in ["1", "true", "yes"]
"""Force OCR for every page even when text extraction produced content."""


# ============================================================================
# Risk Analysis Configuration
# ============================================================================

RISK_LEVELS = {
    "high": "HIGH",
    "medium": "MEDIUM",
    "low": "LOW"
}
"""Mapping from Pinecone metadata severity values to output risk levels."""


# ============================================================================
# Local HuggingFace Reasoner Configuration
# ============================================================================

# Standard project model location(s)
_DEFAULT_HF_MODEL_PATHS = [
    os.getenv("HF_MODEL_PATH"),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models", "roberta-base")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "roberta-base")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend", "models", "roberta-base")),
]

def _find_hf_model_path():
    for candidate in _DEFAULT_HF_MODEL_PATHS:
        if not candidate:
            continue
        if os.path.exists(candidate):
            return candidate
    return _DEFAULT_HF_MODEL_PATHS[1]  # fallback path for clear error message

HF_MODEL_PATH = _find_hf_model_path()
"""Path to the local fine-tuned question-answering model directory."""

HF_LABELS = ["LOW", "MEDIUM", "HIGH", "UNKNOWN"]
"""Fallback label order when model config does not define id2label mapping."""

HF_MAX_LENGTH = 512
"""Maximum token length for local model inference."""

HF_BATCH_SIZE = 8
"""Batch size used for local model inference."""


# ============================================================================
# Groq LLM Configuration
# ============================================================================

GROQ_ENABLED = os.getenv("GROQ_ENABLED", "true").lower() in ["1", "true", "yes"]
"""Whether Groq-backed inference is enabled."""

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
"""Groq API key used for chat completions."""

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
"""Groq model used for clause risk reasoning and chat responses."""

GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
"""Groq OpenAI-compatible chat completion endpoint."""

GROQ_TIMEOUT_SEC = float(os.getenv("GROQ_TIMEOUT_SEC", "15"))
"""Timeout in seconds for Groq API requests."""

GROQ_MAX_RETRIES = int(os.getenv("GROQ_MAX_RETRIES", "2"))
"""Maximum retries for Groq requests on transient failures."""

GROQ_RETRY_BACKOFF_SEC = float(os.getenv("GROQ_RETRY_BACKOFF_SEC", "0.6"))
"""Base backoff in seconds between Groq retries."""

GROQ_DOWN_COOLDOWN_SEC = float(os.getenv("GROQ_DOWN_COOLDOWN_SEC", "15"))
"""Cooldown window after Groq call failure before retrying."""

# Backward-compatible aliases for scripts that still reference MODEL_SERVER_*
MODEL_SERVER_ENABLED = GROQ_ENABLED
MODEL_SERVER_URL = GROQ_API_URL
MODEL_SERVER_TIMEOUT_SEC = GROQ_TIMEOUT_SEC
MODEL_SERVER_MAX_RETRIES = GROQ_MAX_RETRIES
MODEL_SERVER_RETRY_BACKOFF_SEC = GROQ_RETRY_BACKOFF_SEC
MODEL_SERVER_DOWN_COOLDOWN_SEC = GROQ_DOWN_COOLDOWN_SEC

# Batch endpoint no longer applies for Groq chat completions.
QA_BATCH_MODE_ENABLED = False
MODEL_SERVER_BATCH_SIZE = 1


# ============================================================================
# Agreement Context Configuration
# ============================================================================

DEFAULT_CONTEXT_AGREEMENT_TYPE = os.getenv("DEFAULT_AGREEMENT_TYPE", DEFAULT_AGREEMENT_TYPE)
"""Default agreement type used when caller omits context."""

DEFAULT_CONTEXT_USER_TYPE = os.getenv(
    "DEFAULT_USER_TYPE",
    AGREEMENT_USER_TYPE_MAP.get(DEFAULT_CONTEXT_AGREEMENT_TYPE, ["Buyer"])[0],
)
"""Default user type used when caller omits context."""


# ============================================================================
# Chatbot Configuration
# ============================================================================

CHAT_DB_PATH = os.getenv(
    "CHAT_DB_PATH",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "chat_sessions.db")),
)
"""Path to SQLite DB storing chatbot sessions and message history."""

CHAT_SESSION_TTL_SEC = int(os.getenv("CHAT_SESSION_TTL_SEC", "86400"))
"""Time-to-live for chat sessions in seconds."""

CHAT_HISTORY_TURNS = int(os.getenv("CHAT_HISTORY_TURNS", "8"))
"""How many recent turns are included in chat context."""

CHAT_CONTEXT_CLAUSES = int(os.getenv("CHAT_CONTEXT_CLAUSES", "3"))
"""How many relevant clauses to include for each user question."""

CHAT_MIN_CONFIDENCE = float(os.getenv("CHAT_MIN_CONFIDENCE", "-0.5"))
"""Minimum QA confidence required before using model answer directly. IMPROVED: -2.5 → -0.5"""

SUMMARY_MIN_CONFIDENCE = float(os.getenv("SUMMARY_MIN_CONFIDENCE", "0.5"))
"""Minimum QA confidence required for summarization answers."""

MIN_ANSWER_LENGTH = int(os.getenv("MIN_ANSWER_LENGTH", "8"))
"""Minimum answer length (chars) to accept. IMPROVED: 2 → 8. Rejects garbage like 'No' or 'X'."""

MIN_ANSWER_FOR_FALLBACK = int(os.getenv("MIN_ANSWER_FOR_FALLBACK", "10"))
"""If model answer < this length, prefer alternative strategy (multi-answer fallback)."""

CHAT_MAX_QUESTION_CHARS = int(os.getenv("CHAT_MAX_QUESTION_CHARS", "1000"))
"""Maximum accepted user question length."""

CHAT_MAX_ANSWER_CHARS = int(os.getenv("CHAT_MAX_ANSWER_CHARS", "2000"))
"""Maximum assistant answer length."""


# ============================================================================
# Logging Configuration
# ============================================================================

LOG_LEVEL = logging.INFO
"""Default logging level for the pipeline."""

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
"""Format string for log messages."""

LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
"""Date format for log timestamps."""


def setup_logging():
    """Configure logging for the retrieval pipeline."""
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT
    )
