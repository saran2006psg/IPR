"""
PDF text extraction module for Legal Contract Risk Analyzer.

This module provides functionality to extract text content from PDF files
using PyMuPDF (fitz), with OCR fallback for scanned/image-only pages.
"""

import logging
import os
from typing import Optional

import numpy as np

try:
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError(
        "PyMuPDF is required for PDF extraction. "
        "Install it with: pip install PyMuPDF"
    )

try:
    import easyocr  # type: ignore
except ImportError:
    easyocr = None

from .config import (
    OCR_ENABLED,
    OCR_ENGINE,
    OCR_FORCE_ALL_PAGES,
    OCR_LANGUAGES,
    OCR_MIN_CHARS_PER_PAGE,
    OCR_RENDER_SCALE,
)

logger = logging.getLogger(__name__)

_ocr_reader = None
_ocr_init_error: Optional[str] = None


def _get_ocr_reader():
    """Initialize and cache OCR reader when OCR is enabled."""
    global _ocr_reader, _ocr_init_error

    if not OCR_ENABLED:
        return None
    if OCR_ENGINE != "easyocr":
        if _ocr_init_error is None:
            _ocr_init_error = f"Unsupported OCR_ENGINE '{OCR_ENGINE}'."
            logger.warning(_ocr_init_error)
        return None
    if _ocr_reader is not None:
        return _ocr_reader
    if easyocr is None:
        if _ocr_init_error is None:
            _ocr_init_error = "easyocr is not installed. Install dependencies from requirements.txt."
            logger.warning(_ocr_init_error)
        return None

    try:
        logger.info("Initializing OCR engine '%s' with languages=%s", OCR_ENGINE, OCR_LANGUAGES)
        _ocr_reader = easyocr.Reader(OCR_LANGUAGES, gpu=False)
        return _ocr_reader
    except Exception as exc:
        _ocr_init_error = str(exc)
        logger.warning("Failed to initialize OCR engine: %s", exc)
        return None


def _render_page_for_ocr(page: fitz.Page) -> np.ndarray:
    """Render a PDF page to an RGB image array for OCR."""
    matrix = fitz.Matrix(OCR_RENDER_SCALE, OCR_RENDER_SCALE)
    pix = page.get_pixmap(matrix=matrix, alpha=False)

    image = np.frombuffer(pix.samples, dtype=np.uint8)
    image = image.reshape(pix.height, pix.width, pix.n)

    if pix.n == 1:
        image = np.repeat(image, 3, axis=2)
    elif pix.n >= 4:
        image = image[:, :, :3]

    return image


def _extract_page_text_with_ocr(page: fitz.Page, page_num: int) -> str:
    """Run OCR on a single PDF page and return extracted text."""
    reader = _get_ocr_reader()
    if reader is None:
        return ""

    try:
        image = _render_page_for_ocr(page)
        chunks = reader.readtext(image, detail=0, paragraph=True)
        text = "\n".join(str(chunk).strip() for chunk in chunks if str(chunk).strip())
        logger.debug("OCR extracted %d characters from page %d", len(text), page_num)
        return text
    except Exception as exc:
        logger.warning("OCR failed on page %d: %s", page_num, exc)
        return ""


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
            native_text = page.get_text("text").strip()

            use_ocr = OCR_ENABLED and (
                OCR_FORCE_ALL_PAGES or len(native_text) < OCR_MIN_CHARS_PER_PAGE
            )

            page_text = native_text
            if use_ocr:
                ocr_text = _extract_page_text_with_ocr(page, page_num + 1).strip()
                if ocr_text and native_text and OCR_FORCE_ALL_PAGES:
                    page_text = f"{native_text}\n{ocr_text}".strip()
                elif ocr_text and not native_text:
                    page_text = ocr_text
                elif ocr_text and len(ocr_text) > len(native_text):
                    page_text = ocr_text

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
