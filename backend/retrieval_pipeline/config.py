"""
Configuration constants for the Legal Contract Risk Analyzer retrieval pipeline.

This module centralizes all configuration parameters used across the pipeline,
including Pinecone settings, embedding model configuration, and logging setup.
"""

import logging
import os

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

HF_MODEL_PATH = os.getenv("HF_MODEL_PATH", "../../models/roberta-base")
"""Path to the local fine-tuned question-answering model directory."""

HF_LABELS = ["LOW", "MEDIUM", "HIGH", "UNKNOWN"]
"""Fallback label order when model config does not define id2label mapping."""

HF_MAX_LENGTH = 512
"""Maximum token length for local model inference."""

HF_BATCH_SIZE = 8
"""Batch size used for local model inference."""


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
