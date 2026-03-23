"""
Clause segmentation module for Legal Contract Risk Analyzer.

This module provides functionality to segment contract text into individual clauses
using regex patterns for numbered sections, articles, and paragraph breaks.
"""

import logging
import re
from typing import List, Any

import pandas as pd

from .config import MIN_CLAUSE_LENGTH

logger = logging.getLogger(__name__)


def preprocess_text(text: Any) -> str:
    """
    Clean and preprocess clause text for embedding generation.
    
    This function handles text extracted from PDFs which often contains excessive 
    whitespace, multiple newlines, and inconsistent formatting.
    
    Adapted from the ingestion pipeline to ensure consistency.
    
    Args:
        text: Raw clause text (can be str, float/NaN, or None)
        
    Returns:
        Cleaned text string with normalized whitespace
        
    Example:
        >>> preprocess_text("  Multiple   spaces\\n\\nand newlines  ")
        'Multiple spaces and newlines'
    """
    # Handle NaN, None, or non-string values
    if pd.isna(text) or text is None:
        return ""
    
    text = str(text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    # Replace multiple whitespace characters (spaces, tabs, newlines) with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove any remaining control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    return text


def segment_clauses(text: str) -> List[str]:
    """
    Segment contract text into individual clauses.
    
    This function uses regex patterns to identify clause boundaries based on:
    - Numbered sections (1., 1.1, 1.1.1, etc.)
    - Article/Section headers (ARTICLE 1, Section 2, etc.)
    - Double newline breaks (paragraph boundaries)
    
    Args:
        text: Full contract text extracted from PDF
        
    Returns:
        List of clause strings, preprocessed and filtered by minimum length
        
    Example:
        >>> contract_text = '''
        ... 1. Parties
        ... This agreement is between Company A and Company B.
        ... 
        ... 2. Term
        ... The term shall be 12 months.
        ... '''
        >>> clauses = segment_clauses(contract_text)
        >>> len(clauses)
        2
    """
    logger.info("Starting clause segmentation")
    
    # Pattern to split on:
    # 1. Numbered clauses: "1.", "1.1", "1.1.1", etc. (at start of line)
    # 2. Section/Article headers: "Section 1", "ARTICLE II", etc.
    # 3. Double newlines (paragraph breaks)
    
    # First, try to split by numbered sections and articles
    # Pattern explanation:
    # (?=...) is a lookahead assertion (splits before the pattern)
    # \n\s* matches newline followed by optional whitespace
    # \d+\.[\d.]* matches numbers like "1.", "1.1.", "1.1.1."
    # (?:Section|SECTION|Article|ARTICLE)\s+[\dIVXivx]+ matches section/article headers
    
    pattern = r'(?=\n\s*(?:\d+\.[\d.]*\s|(?:Section|SECTION|Article|ARTICLE)\s+[\dIVXivx]+))'
    
    # Split the text
    segments = re.split(pattern, text)
    
    # If splitting by numbered sections didn't work well, try paragraph-based segmentation
    if len(segments) < 2:
        logger.debug("Numbered section splitting yielded few segments, trying paragraph breaks")
        # Split by double newlines (paragraph breaks)
        segments = re.split(r'\n\s*\n', text)
    
    logger.info(f"Initial split produced {len(segments)} segments")
    
    # Process and filter clauses
    clauses = []
    for i, segment in enumerate(segments):
        # Preprocess the clause text
        cleaned = preprocess_text(segment)
        
        # Filter out empty or very short segments
        if len(cleaned) >= MIN_CLAUSE_LENGTH:
            clauses.append(cleaned)
            logger.debug(f"Clause {i+1}: {len(cleaned)} characters")
        else:
            logger.debug(f"Skipping short segment ({len(cleaned)} chars)")
    
    logger.info(f"Segmentation complete: {len(clauses)} valid clauses extracted")
    
    if not clauses:
        logger.warning("No valid clauses extracted - text may be too short or improperly formatted")
    
    return clauses


def segment_clauses_advanced(text: str, custom_patterns: List[str] = None) -> List[str]:
    """
    Advanced clause segmentation with custom regex patterns.
    
    This function allows users to provide custom regex patterns for clause boundaries
    in addition to the default patterns.
    
    Args:
        text: Full contract text extracted from PDF
        custom_patterns: Optional list of additional regex patterns to use for splitting
        
    Returns:
        List of clause strings, preprocessed and filtered by minimum length
        
    Example:
        >>> # Split by numbered sections and custom "WHEREAS" clauses
        >>> clauses = segment_clauses_advanced(
        ...     contract_text,
        ...     custom_patterns=[r'(?=WHEREAS)']
        ... )
    """
    # Default patterns
    patterns = [
        r'(?=\n\s*(?:\d+\.[\d.]*\s))',  # Numbered sections
        r'(?=\n\s*(?:Section|SECTION|Article|ARTICLE)\s+[\dIVXivx]+)',  # Section/Article headers
    ]
    
    # Add custom patterns if provided
    if custom_patterns:
        patterns.extend(custom_patterns)
    
    # Combine all patterns with OR
    combined_pattern = '|'.join(patterns)
    
    # Split the text
    segments = re.split(combined_pattern, text)
    
    # If splitting didn't work well, fall back to paragraph breaks
    if len(segments) < 2:
        segments = re.split(r'\n\s*\n', text)
    
    # Process and filter
    clauses = []
    for segment in segments:
        cleaned = preprocess_text(segment)
        if len(cleaned) >= MIN_CLAUSE_LENGTH:
            clauses.append(cleaned)
    
    logger.info(f"Advanced segmentation complete: {len(clauses)} clauses extracted")
    
    return clauses
