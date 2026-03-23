"""
Pinecone retrieval module for Legal Contract Risk Analyzer.

This module provides functionality to connect to the Pinecone vector database
and query for similar contract clauses based on embedding vectors.
"""

import logging
import os
from typing import List, Dict, Any, Optional

try:
    from pinecone import Pinecone
except ImportError:
    raise ImportError(
        "pinecone is required for vector retrieval. "
        "Install it with: pip install pinecone"
    )

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, will use environment variables directly
    pass

from .config import INDEX_NAME, TOP_K

logger = logging.getLogger(__name__)

# Module-level variable for singleton Pinecone client and index
_pinecone_client = None
_pinecone_index = None


def _init_pinecone() -> Any:
    """
    Initialize Pinecone client and connect to the index (singleton pattern).
    
    This function loads the API key from environment variables and establishes
    a connection to the existing Pinecone index. The connection is cached for
    subsequent queries.
    
    Returns:
        Pinecone index instance
        
    Raises:
        ValueError: If PINECONE_API_KEY is not set
        Exception: If connection to index fails
    """
    global _pinecone_client, _pinecone_index
    
    if _pinecone_index is not None:
        return _pinecone_index
    
    # Get API key from environment
    api_key = os.getenv("PINECONE_API_KEY")
    
    if not api_key:
        raise ValueError(
            "PINECONE_API_KEY not found in environment variables. "
            "Please set it in your .env file or environment."
        )
    
    logger.info("Initializing Pinecone client")
    
    try:
        # Initialize Pinecone client
        _pinecone_client = Pinecone(api_key=api_key)
        
        # Connect to the existing index
        logger.info(f"Connecting to Pinecone index: {INDEX_NAME}")
        _pinecone_index = _pinecone_client.Index(INDEX_NAME)
        
        # Verify connection by getting index stats
        stats = _pinecone_index.describe_index_stats()
        logger.info(
            f"Successfully connected to index '{INDEX_NAME}' "
            f"(vectors: {stats.get('total_vector_count', 'unknown')})"
        )
        
        return _pinecone_index
        
    except Exception as e:
        logger.error(f"Failed to connect to Pinecone: {e}")
        raise


def query_pinecone(
    vector: List[float],
    top_k: int = TOP_K,
    include_metadata: bool = True,
    filter_dict: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Query Pinecone for similar clauses based on an embedding vector.
    
    Args:
        vector: Embedding vector (list of floats, length 768)
        top_k: Number of most similar results to return (default: 5)
        include_metadata: Whether to include metadata in results (default: True)
        filter_dict: Optional metadata filter (e.g., {"severity": "high"})
        
    Returns:
        Dictionary containing query results with matches and scores.
        Format:
        {
            "matches": [
                {
                    "id": "123",
                    "score": 0.92,
                    "metadata": {
                        "clause_text": "...",
                        "severity": "high",
                        "clause_type": "termination"
                    }
                },
                ...
            ],
            "namespace": ""
        }
        
    Raises:
        ValueError: If vector is empty or has incorrect dimension
        
    Example:
        >>> from retrieval_pipeline.embedder import embed_clause
        >>> clause = "Either party may terminate with 30 days notice."
        >>> vector = embed_clause(clause)
        >>> results = query_pinecone(vector)
        >>> print(f"Found {len(results['matches'])} similar clauses")
    """
    if not vector:
        raise ValueError("Vector cannot be empty")
    
    if len(vector) != 768:
        raise ValueError(f"Vector dimension must be 768, got {len(vector)}")
    
    # Initialize Pinecone (will use cached connection if already initialized)
    index = _init_pinecone()
    
    logger.debug(f"Querying Pinecone with top_k={top_k}, include_metadata={include_metadata}")
    
    try:
        # Query the index
        query_params = {
            "vector": vector,
            "top_k": top_k,
            "include_metadata": include_metadata
        }
        
        # Add filter if provided
        if filter_dict:
            query_params["filter"] = filter_dict
            logger.debug(f"Applying filter: {filter_dict}")
        
        results = index.query(**query_params)
        
        # Log results summary
        if hasattr(results, 'matches'):
            num_matches = len(results.matches)
            logger.debug(f"Query returned {num_matches} match(es)")
            
            if num_matches > 0 and hasattr(results.matches[0], 'score'):
                best_score = results.matches[0].score
                logger.debug(f"Best match score: {best_score:.4f}")
        
        return results
        
    except Exception as e:
        logger.error(f"Pinecone query failed: {e}")
        raise


def query_pinecone_batch(
    vectors: List[List[float]],
    top_k: int = TOP_K,
    include_metadata: bool = True
) -> List[Dict[str, Any]]:
    """
    Query Pinecone for multiple vectors in batch.
    
    This function queries Pinecone for each vector individually but provides
    a convenient interface for batch processing.
    
    Args:
        vectors: List of embedding vectors
        top_k: Number of most similar results to return per query
        include_metadata: Whether to include metadata in results
        
    Returns:
        List of query results, one per input vector
        
    Example:
        >>> vectors = embed_clauses(["clause 1", "clause 2", "clause 3"])
        >>> results = query_pinecone_batch(vectors)
        >>> len(results)
        3
    """
    if not vectors:
        raise ValueError("Vectors list cannot be empty")
    
    logger.info(f"Batch querying Pinecone for {len(vectors)} vector(s)")
    
    results = []
    for i, vector in enumerate(vectors):
        try:
            result = query_pinecone(vector, top_k, include_metadata)
            results.append(result)
            logger.debug(f"Completed query {i+1}/{len(vectors)}")
        except Exception as e:
            logger.error(f"Query {i+1} failed: {e}")
            # Append empty result to maintain list alignment
            results.append({"matches": []})
    
    logger.info(f"Batch query complete: {len(results)} result(s)")
    
    return results


def get_index_stats() -> Dict[str, Any]:
    """
    Get statistics about the Pinecone index.
    
    Returns:
        Dictionary containing index statistics (total vectors, dimensions, etc.)
        
    Example:
        >>> stats = get_index_stats()
        >>> print(f"Total vectors: {stats['total_vector_count']}")
    """
    index = _init_pinecone()
    
    try:
        stats = index.describe_index_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get index stats: {e}")
        raise


def reset_pinecone_connection():
    """
    Reset the cached Pinecone connection (useful for testing or reconnection).
    
    This forces a new connection to be established on the next query.
    """
    global _pinecone_client, _pinecone_index
    _pinecone_client = None
    _pinecone_index = None
    logger.info("Pinecone connection cache cleared")
