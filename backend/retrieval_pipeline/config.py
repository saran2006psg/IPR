"""
Configuration constants for the Legal Contract Risk Analyzer retrieval pipeline.

This module centralizes all configuration parameters used across the pipeline,
including Pinecone settings, embedding model configuration, and logging setup.
"""

import logging
import os

from dotenv import load_dotenv


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
# External Model Service Configuration
# ============================================================================

MODEL_SERVER_ENABLED = os.getenv("MODEL_SERVER_ENABLED", "true").lower() in ["1", "true", "yes"]
"""Whether to call an external QA model service for inference."""

MODEL_SERVER_URL = os.getenv("MODEL_SERVER_URL", "http://localhost:9000/qa")
"""External model service endpoint for QA inference."""

MODEL_SERVER_TIMEOUT_SEC = float(os.getenv("MODEL_SERVER_TIMEOUT_SEC", "8"))
"""Timeout in seconds for model service requests."""

MODEL_SERVER_MAX_RETRIES = int(os.getenv("MODEL_SERVER_MAX_RETRIES", "2"))
"""Maximum retries for model service requests on transient failures."""

MODEL_SERVER_RETRY_BACKOFF_SEC = float(os.getenv("MODEL_SERVER_RETRY_BACKOFF_SEC", "0.4"))
"""Base backoff in seconds between model service retries."""

MODEL_SERVER_DOWN_COOLDOWN_SEC = float(os.getenv("MODEL_SERVER_DOWN_COOLDOWN_SEC", "20"))
"""Cooldown window after model-server failure before retrying network calls."""

QA_BATCH_MODE_ENABLED = os.getenv("QA_BATCH_MODE_ENABLED", "true").lower() in ["1", "true", "yes"]
"""Whether to use batched QA calls against the model server."""

MODEL_SERVER_BATCH_SIZE = int(os.getenv("MODEL_SERVER_BATCH_SIZE", "24"))
"""Number of QA pairs to send in each model-server batch request."""


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

CHAT_MAX_ANSWER_CHARS = int(os.getenv("CHAT_MAX_ANSWER_CHARS", "500"))
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
