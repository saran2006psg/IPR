"""
FastAPI Backend for AI Contract Risk Analyzer.

This module provides a RESTful API wrapper around the retrieval pipeline's
analyze_contract() function, enabling web-based contract risk analysis.
"""

import logging
import os
import tempfile
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from chat_orchestrator import answer_contract_question, build_summary
from chat_session_store import (
    add_message,
    cleanup_expired_sessions,
    create_session,
    get_messages,
    get_session,
    init_db,
    is_db_ready,
    touch_session,
)
from retrieval_pipeline import analyze_contract
from retrieval_pipeline.pdf_extractor import validate_pdf
from retrieval_pipeline.config import CHAT_MAX_QUESTION_CHARS, CHAT_SESSION_TTL_SEC, setup_logging
from retrieval_pipeline.llm_reasoner import get_model_service_status, summarize_contract_analysis

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)
init_db()

# Initialize FastAPI app
app = FastAPI(
    title="AI Contract Risk Analyzer API",
    description="Analyze contract PDFs for risky clauses using AI-powered similarity search",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("ALLOW_ALL_ORIGINS", "true").lower() in ["1", "true", "yes"] else ["http://localhost:5173"],
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
    session_id: Optional[str] = None


class SummaryResponse(BaseModel):
    """Contract summary response."""
    summary: str


class HealthResponse(BaseModel):
    """Service health response including model-server status."""
    status: str
    api: str
    model_server: str
    chatbot_db: str
    model_server_url: str
    timestamp: str


class ChatUploadResponse(BaseModel):
    """Response returned when creating a chat session from a contract."""
    session_id: str
    clause_count: int
    high_risk_count: int
    summary: str


class ChatAskRequest(BaseModel):
    """Chat question payload."""
    session_id: str
    question: str


class Citation(BaseModel):
    """Source citation for chatbot responses."""
    clause_index: int
    risk_level: str
    relevance_score: float
    snippet: str


class ChatMessage(BaseModel):
    """Single message in chat history."""
    role: str
    content: str
    confidence: Optional[float] = None
    fallback_used: bool = False
    citations: List[Citation] = []


class ChatAskResponse(BaseModel):
    """Assistant response for a user question."""
    session_id: str
    answer: str
    confidence: float
    fallback_used: bool
    citations: List[Citation]
    history: List[ChatMessage]


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Status message indicating the API is operational
    """
    model_info = get_model_service_status()
    model_status = model_info.get("status", "unknown")
    db_ready = is_db_ready()
    overall = "ok" if model_status in ["ready", "disabled", "loading"] and db_ready else "degraded"

    # Opportunistic cleanup of old sessions.
    cleanup_expired_sessions(CHAT_SESSION_TTL_SEC)

    return HealthResponse(
        status=overall,
        api="ready",
        model_server=model_status,
        chatbot_db="ready" if db_ready else "error",
        model_server_url=str(model_info.get("url", "")),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


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

        session_summary = build_summary(analyses)
        session_id = create_session(file.filename or "uploaded_contract.pdf", analyses, session_summary)
        
        return AnalysisResponse(results=results, session_id=session_id)
        
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


# Summary endpoint
@app.post("/summarize", response_model=SummaryResponse)
async def summarize_contract_endpoint(file: UploadFile = File(...)):
    """
    Generate a summary of contract analysis results.
    
    This endpoint:
    1. Validates the uploaded file is a PDF
    2. Saves it to a temporary location
    3. Runs the analysis pipeline
    4. Generates a comprehensive summary
    5. Cleans up the temporary file
    
    Args:
        file: Uploaded PDF file (multipart/form-data with field name "file")
        
    Returns:
        JSON response with contract summary:
        {
            "summary": "Comprehensive summary text..."
        }
        
    Raises:
        HTTPException 400: If file is not a PDF or is invalid
        HTTPException 500: If analysis or summarization fails
        
    Example:
        curl -X POST http://localhost:8000/summarize \\
             -F "file=@contract.pdf"
    """
    logger.info(f"Received upload for summarization: {file.filename}")
    
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
        logger.info("Starting contract analysis pipeline for summarization...")
        analyses = analyze_contract(temp_path, verbose=False)
        logger.info(f"Analysis complete: {len(analyses)} clauses analyzed")
        
        # Generate summary
        logger.info("Generating contract summary...")
        summary = summarize_contract_analysis(analyses)
        logger.info("Summary generation complete")
        
        return SummaryResponse(summary=summary)
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
        
    except Exception as e:
        # Log and return 500 for pipeline errors
        logger.error(f"Summarization pipeline failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Contract summarization failed: {str(e)}"
        )
        
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                logger.info(f"Cleaned up temporary file: {temp_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {e}")


@app.post("/chat/upload", response_model=ChatUploadResponse)
async def upload_for_chat_endpoint(file: UploadFile = File(...)):
    """Upload a PDF, analyze it, and create a persistent chatbot session."""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    temp_path = None
    try:
        tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        temp_path = tmp.name
        content = await file.read()
        tmp.write(content)
        tmp.close()

        validate_pdf(temp_path)
        analyses = analyze_contract(temp_path, verbose=False)
        summary = build_summary(analyses)
        session_id = create_session(file.filename or "uploaded_contract.pdf", analyses, summary)

        high_risk_count = len([a for a in analyses if a.get("risk_level") == "HIGH"])
        return ChatUploadResponse(
            session_id=session_id,
            clause_count=len(analyses),
            high_risk_count=high_risk_count,
            summary=summary,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Chat upload bootstrap failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat bootstrap failed: {str(e)}")
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception:
                pass


@app.post("/chat/ask", response_model=ChatAskResponse)
async def ask_chat_question(payload: ChatAskRequest):
    """Answer a user question from a previously analyzed contract session."""
    question = (payload.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if len(question) > CHAT_MAX_QUESTION_CHARS:
        raise HTTPException(status_code=400, detail=f"Question is too long (max {CHAT_MAX_QUESTION_CHARS} chars).")

    cleanup_expired_sessions(CHAT_SESSION_TTL_SEC)
    session = get_session(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found or expired.")

    history = get_messages(payload.session_id, limit=30)

    add_message(payload.session_id, "user", question)
    answer_payload = answer_contract_question(
        question=question,
        analyses=session["analyses"],
        summary=session["summary"],
        chat_history=history,
    )

    add_message(
        payload.session_id,
        "assistant",
        answer_payload["answer"],
        confidence=float(answer_payload.get("confidence", 0.0)),
        fallback_used=bool(answer_payload.get("fallback_used", False)),
        citations=answer_payload.get("citations", []),
    )
    touch_session(payload.session_id)

    fresh_history = get_messages(payload.session_id, limit=30)
    return ChatAskResponse(
        session_id=payload.session_id,
        answer=answer_payload["answer"],
        confidence=float(answer_payload.get("confidence", 0.0)),
        fallback_used=bool(answer_payload.get("fallback_used", False)),
        citations=[Citation(**c) for c in answer_payload.get("citations", [])],
        history=[
            ChatMessage(
                role=m["role"],
                content=m["content"],
                confidence=m.get("confidence"),
                fallback_used=bool(m.get("fallback_used", False)),
                citations=[Citation(**c) for c in m.get("citations", [])],
            )
            for m in fresh_history
        ],
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
