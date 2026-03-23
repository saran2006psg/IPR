"""
PDF text extraction module for Legal Contract Risk Analyzer.

This module provides functionality to extract text content from PDF files
using PyMuPDF (fitz), with validation and progress logging.
"""

import logging
import os
from typing import Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError(
        "PyMuPDF is required for PDF extraction. "
        "Install it with: pip install PyMuPDF"
    )

logger = logging.getLogger(__name__)


def extract_pdf_text(file_path: str) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        file_path: Path to the PDF file to extract text from.
        
    Returns:
        Extracted text as a single string with page breaks preserved.
        
    Raises:
        FileNotFoundError: If the PDF file does not exist.
        ValueError: If the file is not a valid PDF.
        Exception: If PDF extraction fails for any other reason.
        
    Example:
        >>> text = extract_pdf_text("contract.pdf")
        >>> print(f"Extracted {len(text)} characters")
    """
    # Validate file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    
    # Validate file extension
    if not file_path.lower().endswith('.pdf'):
        raise ValueError(f"File must be a PDF: {file_path}")
    
    logger.info(f"Starting PDF text extraction: {file_path}")
    
    try:
        # Open the PDF document
        doc = fitz.open(file_path)
        
        page_count = len(doc)
        logger.info(f"PDF contains {page_count} page(s)")
        
        # Extract text from all pages
        extracted_text = []
        for page_num in range(page_count):
            page = doc[page_num]
            page_text = page.get_text()
            
            if page_text.strip():  # Only add non-empty pages
                extracted_text.append(page_text)
                logger.debug(f"Extracted {len(page_text)} characters from page {page_num + 1}")
            else:
                logger.warning(f"Page {page_num + 1} appears to be empty")
        
        # Close the document
        doc.close()
        
        # Combine all page texts with page breaks
        full_text = "\n\n".join(extracted_text)
        
        logger.info(
            f"Successfully extracted {len(full_text)} characters "
            f"from {page_count} page(s)"
        )
        
        if not full_text.strip():
            logger.warning("Extracted text is empty - PDF may contain only images or be corrupted")
        
        return full_text
        
    except fitz.FileDataError as e:
        raise ValueError(f"Invalid or corrupted PDF file: {e}")
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        raise


def validate_pdf(file_path: str) -> bool:
    """
    Check if a file is a valid PDF without extracting text.
    
    Args:
        file_path: Path to the file to validate.
        
    Returns:
        True if the file is a valid PDF, False otherwise.
        
    Example:
        >>> if validate_pdf("document.pdf"):
        ...     text = extract_pdf_text("document.pdf")
    """
    if not os.path.exists(file_path):
        return False
    
    if not file_path.lower().endswith('.pdf'):
        return False
    
    try:
        doc = fitz.open(file_path)
        doc.close()
        return True
    except:
        return False
