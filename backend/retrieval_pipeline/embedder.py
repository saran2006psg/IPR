"""
Embedding generation module for Legal Contract Risk Analyzer.

This module provides functionality to generate embeddings for contract clauses
using SentenceTransformer models, with singleton model loading for efficiency.
"""

import logging
from typing import List, Union

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError(
        "sentence-transformers is required for embedding generation. "
        "Install it with: pip install sentence-transformers"
    )

from .config import (
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    NORMALIZE_EMBEDDINGS,
    BATCH_SIZE
)

logger = logging.getLogger(__name__)

# Module-level variable for singleton model instance
_model_instance = None


def _load_model() -> SentenceTransformer:
    """
    Load the SentenceTransformer model (singleton pattern).
    
    This function ensures the model is loaded only once and cached for
    subsequent calls, improving performance when embedding multiple clauses.
    
    Returns:
        Loaded SentenceTransformer model instance
    """
    global _model_instance
    
    if _model_instance is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _model_instance = SentenceTransformer(EMBEDDING_MODEL)
        logger.info(f"Model loaded successfully (dimension: {EMBEDDING_DIMENSION})")
    
    return _model_instance


def embed_clause(clause: str) -> List[float]:
    """
    Generate an embedding vector for a single contract clause.
    
    Args:
        clause: Text of the contract clause
        
    Returns:
        Embedding vector as a list of floats (length = 768)
        
    Raises:
        ValueError: If the clause is empty or None
        
    Example:
        >>> clause = "The term of this agreement shall be 12 months."
        >>> vector = embed_clause(clause)
        >>> len(vector)
        768
    """
    if not clause or not clause.strip():
        raise ValueError("Clause text cannot be empty")
    
    # Load model (will use cached instance if already loaded)
    model = _load_model()
    
    # Generate embedding
    # normalize_embeddings=True ensures unit vectors for cosine similarity
    embedding = model.encode(
        clause,
        normalize_embeddings=NORMALIZE_EMBEDDINGS,
        show_progress_bar=False
    )
    
    # Convert numpy array to list
    embedding_list = embedding.tolist()
    
    logger.debug(f"Generated embedding for clause ({len(clause)} chars): dimension={len(embedding_list)}")
    
    return embedding_list


def embed_clauses(clauses: List[str], show_progress: bool = True) -> List[List[float]]:
    """
    Generate embedding vectors for multiple contract clauses (batch processing).
    
    This function is more efficient than calling embed_clause() multiple times
    as it processes clauses in batches.
    
    Args:
        clauses: List of contract clause texts
        show_progress: Whether to display a progress bar during encoding
        
    Returns:
        List of embedding vectors, each as a list of floats
        
    Raises:
        ValueError: If clauses list is empty or contains only empty strings
        
    Example:
        >>> clauses = [
        ...     "The term shall be 12 months.",
        ...     "Either party may terminate with 30 days notice.",
        ...     "This agreement is governed by New York law."
        ... ]
        >>> vectors = embed_clauses(clauses)
        >>> len(vectors)
        3
        >>> len(vectors[0])
        768
    """
    if not clauses:
        raise ValueError("Clauses list cannot be empty")
    
    # Filter out empty clauses
    valid_clauses = [c for c in clauses if c and c.strip()]
    
    if not valid_clauses:
        raise ValueError("All clauses are empty")
    
    if len(valid_clauses) < len(clauses):
        logger.warning(
            f"Filtered out {len(clauses) - len(valid_clauses)} empty clause(s)"
        )
    
    logger.info(f"Generating embeddings for {len(valid_clauses)} clause(s)")
    
    # Load model (will use cached instance if already loaded)
    model = _load_model()
    
    # Generate embeddings in batches
    embeddings = model.encode(
        valid_clauses,
        batch_size=BATCH_SIZE,
        normalize_embeddings=NORMALIZE_EMBEDDINGS,
        show_progress_bar=show_progress
    )
    
    # Convert numpy array to list of lists
    embeddings_list = embeddings.tolist()
    
    logger.info(
        f"Successfully generated {len(embeddings_list)} embeddings "
        f"(dimension: {EMBEDDING_DIMENSION})"
    )
    
    return embeddings_list


def get_embedding_dimension() -> int:
    """
    Get the dimension of embeddings produced by the model.
    
    Returns:
        Embedding dimension (768 for all-mpnet-base-v2)
        
    Example:
        >>> get_embedding_dimension()
        768
    """
    return EMBEDDING_DIMENSION


def reset_model_cache():
    """
    Reset the cached model instance (useful for testing or memory management).
    
    This forces the model to be reloaded on the next embedding operation.
    """
    global _model_instance
    _model_instance = None
    logger.info("Model cache cleared")
