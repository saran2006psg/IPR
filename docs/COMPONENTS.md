# Components

This document lists the primary runtime components and their responsibilities.

## Backend Components

## API Layer

1. `backend/api.py`
   - Defines all REST endpoints
   - Handles upload validation and request parsing
   - Coordinates analysis, summarization, and chat operations
   - Returns typed responses through Pydantic models

2. `backend/chat_orchestrator.py`
   - Builds grounded answers from analyzed clauses
   - Selects relevant clauses and creates citations
   - Produces readable responses for clause-specific or contract-level questions

3. `backend/chat_session_store.py`
   - SQLite schema creation and connection handling
   - Session creation, touch/update, and TTL cleanup
   - Message persistence and history retrieval

4. `backend/model_server.py`
   - Dedicated QA inference service for RoBERTa
   - Loads tokenizer/model once at startup
   - Supports single and batched QA requests

## Retrieval Pipeline Package

1. `backend/retrieval_pipeline/main.py`
   - Orchestrates full clause analysis pipeline
   - Provides CLI and callable `analyze_contract` entry point

2. `backend/retrieval_pipeline/config.py`
   - Central configuration and defaults
   - OCR, embedding, retrieval, chat, and model service parameters

3. `backend/retrieval_pipeline/pdf_extractor.py`
   - PDF validation and text extraction
   - OCR fallback path for low-text pages

4. `backend/retrieval_pipeline/clause_segmenter.py`
   - Text cleaning and segmentation into clauses
   - Rule-based splitting for section formats and paragraph breaks

5. `backend/retrieval_pipeline/embedder.py`
   - Converts clauses into dense embeddings
   - Uses sentence-transformers model compatible with index vectors

6. `backend/retrieval_pipeline/retriever.py`
   - Pinecone connection management
   - Top-k similarity retrieval per clause

7. `backend/retrieval_pipeline/risk_analyzer.py`
   - Compatibility wrapper for risk reasoning
   - Batch and fallback single-clause analysis execution

8. `backend/retrieval_pipeline/llm_reasoner.py`
   - Context-grounded reasoning logic
   - Confidence and quality scoring
   - Contract summary synthesis and answer normalization

9. `backend/retrieval_pipeline/agreement_profiles.py`
   - Agreement and role mapping definitions
   - Validation for allowed combinations

## Backend Utility Scripts

1. `backend/scripts/ingest_pipeline.py`
   - Loads legal clause dataset into vector index

2. `backend/scripts/test_system.py`
   - End-to-end checks of key services and pipeline components

3. `backend/scripts/check_model_integration.py`
   - Model integration validation

4. `backend/scripts/check_model_server.py`
   - Model server readiness and endpoint validation

## Frontend Components

## App Shell

1. `frontend/src/App.jsx`
   - Main state container
   - View routing between upload, analysis, and history screens
   - Coordinates API calls and chat interactions

2. `frontend/src/main.jsx`
   - React bootstrap and root rendering

## Upload and Analysis UI

1. `frontend/src/components/UploadView.jsx`
   - PDF drop/upload interaction
   - Agreement-role selection
   - Progress step visualization while analyzing

2. `frontend/src/components/AnalysisView.jsx`
   - Split-pane analysis experience
   - Clause list, selected clause explanation, and reference matches
   - Embedded chat panel for follow-up questions

3. `frontend/src/components/ChatPanel.jsx`
   - Displays conversation history
   - Sends user prompts and handles loading states

## Data Contracts Between Layers

Key contract fields:

- Clause output: `clause`, `risk_level`, `explanation`, `similar_clauses`
- Similar match: `text`, `score`, `severity`, `clause_type`, optional IDs
- Chat response: `answer`, `confidence`, `fallback_used`, `citations`, `history`
- Context metadata: `agreement_type`, `user_type`
