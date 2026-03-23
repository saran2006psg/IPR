"""
FastAPI Backend for AI Contract Risk Analyzer.

This module provides a RESTful API wrapper around the retrieval pipeline's
analyze_contract() function, enabling web-based contract risk analysis.
"""

import logging
import os
import tempfile
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from retrieval_pipeline import analyze_contract
from retrieval_pipeline.pdf_extractor import validate_pdf
from retrieval_pipeline.config import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Contract Risk Analyzer API",
    description="Analyze contract PDFs for risky clauses using AI-powered similarity search",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Response models
class SimilarClause(BaseModel):
    """A similar clause retrieved from the Pinecone knowledge base."""
    text: str
    score: float
    severity: str
    clause_type: str


class ClauseResult(BaseModel):
    """Individual clause risk analysis result."""
    clause: str
    risk_level: str
    explanation: str
    similar_clauses: List[SimilarClause] = []


class AnalysisResponse(BaseModel):
    """Complete contract analysis response."""
    results: List[ClauseResult]


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Status message indicating the API is operational
    """
    return {"status": "ok"}


# Main analysis endpoint
@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_contract_endpoint(file: UploadFile = File(...)):
    """
    Analyze a contract PDF for risky clauses.
    
    This endpoint:
    1. Validates the uploaded file is a PDF
    2. Saves it to a temporary location
    3. Runs the analysis pipeline
    4. Returns structured risk results
    5. Cleans up the temporary file
    
    Args:
        file: Uploaded PDF file (multipart/form-data with field name "file")
        
    Returns:
        JSON response with analysis results:
        {
            "results": [
                {
                    "clause": "Contract clause text",
                    "risk_level": "HIGH" | "MEDIUM" | "LOW",
                    "explanation": "Risk explanation"
                },
                ...
            ]
        }
        
    Raises:
        HTTPException 400: If file is not a PDF or is invalid
        HTTPException 500: If analysis pipeline fails
        
    Example:
        curl -X POST http://localhost:8000/analyze \\
             -F "file=@contract.pdf"
    """
    logger.info(f"Received upload: {file.filename}")
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        logger.warning(f"Invalid file type: {file.filename}")
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted. Please upload a .pdf file."
        )
    
    # Create a temporary file to store the upload
    temp_file = None
    temp_path = None
    
    try:
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(
            suffix='.pdf',
            delete=False
        )
        temp_path = temp_file.name
        
        # Write uploaded file to temp location
        content = await file.read()
        temp_file.write(content)
        temp_file.close()
        
        logger.info(f"Saved upload to temporary file: {temp_path}")
        
        # Validate PDF structure
        try:
            validate_pdf(temp_path)
        except ValueError as e:
            logger.warning(f"PDF validation failed: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid PDF file: {str(e)}"
            )
        
        # Run analysis pipeline
        logger.info("Starting contract analysis pipeline...")
        analyses = analyze_contract(temp_path, verbose=False)
        logger.info(f"Analysis complete: {len(analyses)} clauses analyzed")
        
        # Transform results to match frontend spec
        results = [
            ClauseResult(
                clause=analysis["clause_text"],
                risk_level=analysis["risk_level"],
                explanation=analysis["explanation"],
                similar_clauses=[
                    SimilarClause(
                        text=sc.get("text", ""),
                        score=sc.get("score", 0.0),
                        severity=sc.get("severity", "unknown"),
                        clause_type=sc.get("clause_type", "unknown"),
                    )
                    for sc in analysis.get("similar_clauses", [])
                ],
            )
            for analysis in analyses
        ]
        
        return AnalysisResponse(results=results)
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
        
    except Exception as e:
        # Log and return 500 for pipeline errors
        logger.error(f"Analysis pipeline failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Contract analysis failed: {str(e)}"
        )
        
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                logger.info(f"Cleaned up temporary file: {temp_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
