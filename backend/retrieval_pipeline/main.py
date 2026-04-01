"""
Main orchestrator for Legal Contract Risk Analyzer - Retrieval Pipeline.

This module provides the main entry point and CLI interface for analyzing
contract PDFs and generating risk reports.
"""

import argparse
import logging
import sys
from typing import List, Dict, Any

from .config import setup_logging
from .pdf_extractor import extract_pdf_text, validate_pdf
from .clause_segmenter import segment_clauses
from .embedder import embed_clauses
from .retriever import query_pinecone_batch
from .risk_analyzer import analyze_risk_batch, get_risk_summary

logger = logging.getLogger(__name__)


def print_separator(char="=", length=80):
    """Print a separator line."""
    print(char * length)


def print_clause_analysis(analysis: Dict[str, Any], clause_num: int):
    """
    Pretty-print the risk analysis for a single clause.
    
    Args:
        analysis: Risk analysis result dictionary
        clause_num: Clause number (for display)
    """
    print_separator("─")
    print(f"\n📄 CLAUSE #{clause_num}")
    print_separator("─")
    
    # Print the contract clause
    clause_text = analysis.get("clause_text", "")
    print(f"\n📝 Text:")
    if len(clause_text) > 300:
        print(f"   {clause_text[:300]}...")
    else:
        print(f"   {clause_text}")
    
    # Print risk level with color/emoji
    risk_level = analysis["risk_level"]
    risk_emoji = {
        "HIGH": "🔴",
        "MEDIUM": "🟡",
        "LOW": "🟢",
        "UNKNOWN": "⚪"
    }
    
    print(f"\n⚠️  Risk Level: {risk_emoji.get(risk_level, '⚪')} {risk_level}")
    print(f"💡 Explanation: {analysis['explanation']}")
    
    # Print similar clauses
    similar_clauses = analysis.get("similar_clauses", [])
    if similar_clauses:
        print(f"\n🔍 Similar Clauses Found ({len(similar_clauses)}):")
        for i, similar in enumerate(similar_clauses[:3], 1):  # Show top 3
            print(f"\n   {i}. Score: {similar['score']:.4f} | "
                  f"Severity: {similar['severity']} | "
                  f"Type: {similar['clause_type']}")
            print(f"      {similar['text']}")
    else:
        print("\n🔍 Similar Clauses: None found")


def print_summary(summary: Dict[str, Any]):
    """
    Pretty-print the risk analysis summary.
    
    Args:
        summary: Summary statistics from get_risk_summary()
    """
    print_separator("=")
    print("\n📊 RISK ANALYSIS SUMMARY")
    print_separator("=")
    
    total = summary["total_clauses"]
    high = summary["high_risk_count"]
    medium = summary["medium_risk_count"]
    low = summary["low_risk_count"]
    
    print(f"\nTotal Clauses Analyzed: {total}")
    print(f"\n  🔴 HIGH RISK:   {high:3d} ({summary['high_risk_percentage']:5.1f}%)")
    print(f"  🟡 MEDIUM RISK: {medium:3d} ({summary['medium_risk_percentage']:5.1f}%)")
    print(f"  🟢 LOW RISK:    {low:3d} ({summary['low_risk_percentage']:5.1f}%)")
    
    print_separator("=")


def analyze_contract(
    pdf_path: str,
    verbose: bool = False,
    agreement_type: str = "Company Sales Agreement",
    user_type: str = "Buyer",
) -> List[Dict[str, Any]]:
    """
    Analyze a contract PDF and return risk analysis results.
    
    This is the main pipeline function that orchestrates:
    1. PDF text extraction
    2. Clause segmentation
    3. Embedding generation
    4. Pinecone querying
    5. Risk analysis
    
    Args:
        pdf_path: Path to the contract PDF file
        verbose: Whether to print detailed progress information
        agreement_type: Agreement template used for role-aware review
        user_type: Reviewing user role within the agreement type
        
    Returns:
        List of risk analysis results, one per clause
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If PDF is invalid or contains no text
        Exception: If any pipeline stage fails
        
    Example:
        >>> analyses = analyze_contract("contract.pdf")
        >>> print(f"Analyzed {len(analyses)} clauses")
    """
    logger.info(f"Starting contract analysis: {pdf_path}")
    
    # Stage 1: Extract PDF text
    if verbose:
        print("\n[1/5] 📄 Extracting text from PDF...")
    
    try:
        text = extract_pdf_text(pdf_path)
        logger.info(f"Extracted {len(text)} characters from PDF")
        if verbose:
            print(f"      ✓ Extracted {len(text)} characters")
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        raise
    
    # Stage 2: Segment into clauses
    if verbose:
        print("\n[2/5] ✂️  Segmenting text into clauses...")
    
    try:
        clauses = segment_clauses(text)
        logger.info(f"Segmented into {len(clauses)} clauses")
        if verbose:
            print(f"      ✓ Segmented into {len(clauses)} clauses")
        
        if not clauses:
            raise ValueError("No valid clauses extracted from PDF")
            
    except Exception as e:
        logger.error(f"Clause segmentation failed: {e}")
        raise
    
    # Stage 3: Generate embeddings
    if verbose:
        print(f"\n[3/5] 🧮 Generating embeddings for {len(clauses)} clauses...")
    
    try:
        vectors = embed_clauses(clauses, show_progress=verbose)
        logger.info(f"Generated {len(vectors)} embedding vectors")
        if verbose:
            print(f"      ✓ Generated {len(vectors)} embedding vectors")
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise
    
    # Stage 4: Query Pinecone
    if verbose:
        print(f"\n[4/5] 🔍 Querying Pinecone for similar clauses...")
    
    try:
        query_results = query_pinecone_batch(vectors)
        logger.info(f"Completed {len(query_results)} Pinecone queries")
        if verbose:
            print(f"      ✓ Completed {len(query_results)} queries")
    except Exception as e:
        logger.error(f"Pinecone querying failed: {e}")
        raise
    
    # Stage 5: Analyze risk
    if verbose:
        print(f"\n[5/5] 🎯 Analyzing risk levels...")
    
    try:
        analyses = analyze_risk_batch(
            clauses,
            query_results,
            agreement_type=agreement_type,
            user_type=user_type,
        )
        logger.info(f"Completed risk analysis for {len(analyses)} clauses")
        if verbose:
            print(f"      ✓ Analyzed {len(analyses)} clauses")
    except Exception as e:
        logger.error(f"Risk analysis failed: {e}")
        raise
    
    logger.info("Contract analysis complete")
    
    return analyses


def main(pdf_path: str = None):
    """
    Main entry point for the retrieval pipeline.
    
    Args:
        pdf_path: Optional path to PDF file (if not provided, uses argparse)
    """
    # Set up logging
    setup_logging()
    
    # Parse command-line arguments if pdf_path not provided
    if pdf_path is None:
        parser = argparse.ArgumentParser(
            description="Legal Contract Risk Analyzer - Analyze contract PDFs for risk",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python -m retrieval_pipeline.main contract.pdf
  python -m retrieval_pipeline.main --verbose contract.pdf
  python -m retrieval_pipeline.main --quiet contract.pdf

The tool will:
  1. Extract text from the PDF
  2. Segment into individual clauses
  3. Generate embeddings for each clause
  4. Query Pinecone for similar clauses
    5. Analyze risk using local model reasoning over retrieved context
  6. Print a detailed risk report
            """
        )
        
        parser.add_argument(
            "pdf_path",
            help="Path to the contract PDF file to analyze"
        )
        
        parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Print detailed progress information"
        )
        
        parser.add_argument(
            "-q", "--quiet",
            action="store_true",
            help="Suppress clause-by-clause output (show only summary)"
        )
        
        args = parser.parse_args()
        pdf_path = args.pdf_path
        verbose = args.verbose
        quiet = args.quiet
    else:
        verbose = False
        quiet = False
    
    print_separator("=")
    print("🏛️  LEGAL CONTRACT RISK ANALYZER")
    print_separator("=")
    print(f"\nAnalyzing: {pdf_path}")
    
    # Validate PDF
    if not validate_pdf(pdf_path):
        print(f"\n❌ Error: Invalid or missing PDF file: {pdf_path}")
        sys.exit(1)
    
    try:
        # Run the analysis pipeline
        analyses = analyze_contract(pdf_path, verbose=verbose)
        
        # Print individual clause analyses (unless quiet mode)
        if not quiet:
            print("\n")
            print_separator("=")
            print("📋 CLAUSE-BY-CLAUSE ANALYSIS")
            print_separator("=")
            
            for i, analysis in enumerate(analyses, 1):
                print_clause_analysis(analysis, i)
        
        # Print summary
        print("\n")
        summary = get_risk_summary(analyses)
        print_summary(summary)
        
        print("\n✅ Analysis complete!")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
