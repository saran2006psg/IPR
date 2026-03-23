"""
Risk analysis compatibility layer for Legal Contract Risk Analyzer.

This module keeps the historical public API while delegating risk reasoning
to the local HuggingFace RAG reasoner in llm_reasoner.py.
"""

import logging
from typing import Dict, Any, List

from .llm_reasoner import analyze_clause_with_llm, analyze_clauses_with_llm_batch

logger = logging.getLogger(__name__)


def analyze_risk(contract_clause: str, query_results: Any) -> Dict[str, Any]:
    """
    Analyze a contract clause by delegating to the local RAG reasoner.
    
    Args:
        contract_clause: The original contract clause text
        query_results: Results from Pinecone query (from query_pinecone())
        
    Returns:
        Dictionary with structured risk analysis:
        {
            "clause_text": str,
            "similar_clauses": [
                {
                    "text": str,
                    "score": float,
                    "severity": str,
                    "clause_type": str
                },
                ...
            ],
            "risk_level": "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN",
            "explanation": str
        }
        
    Example:
        >>> from retrieval_pipeline.embedder import embed_clause
        >>> from retrieval_pipeline.retriever import query_pinecone
        >>> 
        >>> clause = "Either party may terminate with 30 days notice."
        >>> vector = embed_clause(clause)
        >>> results = query_pinecone(vector)
        >>> analysis = analyze_risk(clause, results)
        >>> print(analysis["risk_level"])
        'MEDIUM'
    """
    logger.debug("Analyzing clause with local reasoner (%d chars)", len(contract_clause))
    return analyze_clause_with_llm(clause_text=contract_clause, retrieved_clauses=query_results)


def analyze_risk_batch(
    contract_clauses: List[str],
    query_results_list: List[Any]
) -> List[Dict[str, Any]]:
    """
    Analyze risk for multiple contract clauses.
    
    Args:
        contract_clauses: List of contract clause texts
        query_results_list: List of Pinecone query results (one per clause)
        
    Returns:
        List of risk analysis results, one per clause
        
    Raises:
        ValueError: If lists have different lengths
        
    Example:
        >>> clauses = ["clause 1", "clause 2", "clause 3"]
        >>> vectors = embed_clauses(clauses)
        >>> results = query_pinecone_batch(vectors)
        >>> analyses = analyze_risk_batch(clauses, results)
        >>> len(analyses)
        3
    """
    if len(contract_clauses) != len(query_results_list):
        raise ValueError(
            f"Clauses and results lists must have same length: "
            f"{len(contract_clauses)} != {len(query_results_list)}"
        )
    
    logger.info("Batch risk analysis for %d clause(s)", len(contract_clauses))

    analyses = []
    try:
        analyses = analyze_clauses_with_llm_batch(contract_clauses, query_results_list)
    except Exception as e:
        logger.error("Batch reasoner failed, falling back to per-clause analysis: %s", e)
        for i, (clause, results) in enumerate(zip(contract_clauses, query_results_list), start=1):
            try:
                analysis = analyze_risk(clause, results)
                analyses.append(analysis)
                logger.debug("Analyzed clause %d/%d: %s", i, len(contract_clauses), analysis["risk_level"])
            except Exception as clause_error:
                logger.error("Risk analysis failed for clause %d: %s", i, clause_error)
                analyses.append(
                    {
                        "clause_text": clause,
                        "similar_clauses": [],
                        "risk_level": "UNKNOWN",
                        "explanation": f"Analysis failed: {str(clause_error)}",
                    }
                )
    
    # Log summary statistics
    risk_counts = {}
    for analysis in analyses:
        level = analysis["risk_level"]
        risk_counts[level] = risk_counts.get(level, 0) + 1
    
    logger.info(f"Batch analysis complete. Risk distribution: {risk_counts}")
    
    return analyses


def get_risk_summary(analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a summary of risk analysis results.
    
    Args:
        analyses: List of risk analysis results from analyze_risk() or analyze_risk_batch()
        
    Returns:
        Dictionary with summary statistics:
        {
            "total_clauses": int,
            "high_risk_count": int,
            "medium_risk_count": int,
            "low_risk_count": int,
            "high_risk_percentage": float,
            "medium_risk_percentage": float,
            "low_risk_percentage": float
        }
        
    Example:
        >>> summary = get_risk_summary(analyses)
        >>> print(f"High risk: {summary['high_risk_percentage']:.1f}%")
    """
    total = len(analyses)
    
    if total == 0:
        return {
            "total_clauses": 0,
            "high_risk_count": 0,
            "medium_risk_count": 0,
            "low_risk_count": 0,
            "high_risk_percentage": 0.0,
            "medium_risk_percentage": 0.0,
            "low_risk_percentage": 0.0
        }
    
    # Count each risk level
    high_count = sum(1 for a in analyses if a["risk_level"] == "HIGH")
    medium_count = sum(1 for a in analyses if a["risk_level"] == "MEDIUM")
    low_count = sum(1 for a in analyses if a["risk_level"] == "LOW")
    
    return {
        "total_clauses": total,
        "high_risk_count": high_count,
        "medium_risk_count": medium_count,
        "low_risk_count": low_count,
        "high_risk_percentage": round((high_count / total) * 100, 2),
        "medium_risk_percentage": round((medium_count / total) * 100, 2),
        "low_risk_percentage": round((low_count / total) * 100, 2)
    }
