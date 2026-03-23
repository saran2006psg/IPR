"""
Legal Contract Risk Analyzer - Retrieval Pipeline

A modular Python package for analyzing legal contracts by extracting text from PDFs,
segmenting into clauses, generating embeddings, querying a Pinecone vector database,
and analyzing risk based on similar clauses.

Example usage:
    >>> from retrieval_pipeline import analyze_contract
    >>> analyses = analyze_contract("contract.pdf")
    >>> print(f"Analyzed {len(analyses)} clauses")

Command-line usage:
    python -m retrieval_pipeline.main contract.pdf
"""

__version__ = "1.0.0"
__author__ = "Legal Contract Risk Analyzer Team"

# Import configuration
from .config import (
    INDEX_NAME,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    TOP_K,
    SIMILARITY_THRESHOLD,
    setup_logging
)

# Import PDF extraction functions
from .pdf_extractor import (
    extract_pdf_text,
    validate_pdf
)

# Import clause segmentation functions
from .clause_segmenter import (
    segment_clauses,
    segment_clauses_advanced,
    preprocess_text
)

# Import embedding functions
from .embedder import (
    embed_clause,
    embed_clauses,
    get_embedding_dimension,
    reset_model_cache
)

# Import retrieval functions
from .retriever import (
    query_pinecone,
    query_pinecone_batch,
    get_index_stats,
    reset_pinecone_connection
)

# Import risk analysis functions
from .risk_analyzer import (
    analyze_risk,
    analyze_risk_batch,
    get_risk_summary
)

# Import local reasoner functions
from .llm_reasoner import (
    analyze_clause_with_llm,
    analyze_clauses_with_llm_batch,
)

# Import main pipeline function
from .main import (
    analyze_contract,
    main
)

# Define public API
__all__ = [
    # Configuration
    "INDEX_NAME",
    "EMBEDDING_MODEL",
    "EMBEDDING_DIMENSION",
    "TOP_K",
    "SIMILARITY_THRESHOLD",
    "setup_logging",
    
    # PDF Extraction
    "extract_pdf_text",
    "validate_pdf",
    
    # Clause Segmentation
    "segment_clauses",
    "segment_clauses_advanced",
    "preprocess_text",
    
    # Embedding Generation
    "embed_clause",
    "embed_clauses",
    "get_embedding_dimension",
    "reset_model_cache",
    
    # Pinecone Retrieval
    "query_pinecone",
    "query_pinecone_batch",
    "get_index_stats",
    "reset_pinecone_connection",
    
    # Risk Analysis
    "analyze_risk",
    "analyze_risk_batch",
    "get_risk_summary",

    # Local LLM Reasoner
    "analyze_clause_with_llm",
    "analyze_clauses_with_llm_batch",
    
    # Main Pipeline
    "analyze_contract",
    "main",
]
