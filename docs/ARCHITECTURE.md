# Architecture

## Architecture Style

The project follows a layered service architecture:

- Presentation layer (React frontend)
- API orchestration layer (FastAPI)
- Domain pipeline layer (retrieval and risk modules)
- Data and model layer (vector index, local model files, SQLite session storage)

## Logical Subsystems

## 1. Frontend Application

Location: `frontend/src`

Responsibilities:

- Collect user input (PDF + agreement context)
- Trigger analysis and render results
- Provide clause-focused chat interface
- Maintain client-side view state and selected clause

## 2. Backend API Service

Location: `backend/api.py`

Responsibilities:

- Expose REST endpoints
- Validate uploads and request payloads
- Invoke retrieval pipeline
- Transform pipeline outputs into UI-friendly schemas
- Manage chat sessions and message history integration

## 3. Retrieval Pipeline

Location: `backend/retrieval_pipeline`

Responsibilities:

- PDF extraction and OCR fallback
- Clause segmentation and normalization
- Embedding generation
- Vector retrieval from legal knowledge base
- Risk analysis orchestration and summarization

## 4. Reasoning and QA Layer

Locations:

- `backend/retrieval_pipeline/llm_reasoner.py`
- `backend/model_server.py`
- `models/roberta-base`

Responsibilities:

- Context-grounded clause reasoning
- Confidence-aware answer quality handling
- Contract summary generation
- Batch and single-request QA support through a dedicated model service

## 5. Persistence Layer

Location: `backend/chat_session_store.py`

Responsibilities:

- Create and store chat sessions
- Save conversational turns and citations
- Enforce TTL-based cleanup
- Provide history retrieval for contextual answers

## Data Stores and Assets

1. Vector knowledge base
   Stores embedded legal reference clauses used for similarity matching.

2. SQLite chat store
   Stores session context and messages in `backend/data/chat_sessions.db`.

3. Local model directory
   Fine-tuned RoBERTa model files under `models/roberta-base`.

4. Clause dataset
   Seed data in `data/legal_contract_clauses.csv` used by ingestion scripts.

## End-to-End Interaction Sequence

1. Frontend uploads PDF to API (`/analyze`).
2. API saves temp file and validates PDF.
3. Pipeline extracts text and segments clauses.
4. Pipeline embeds each clause.
5. Retriever queries vector index for top similar clauses.
6. Reasoner assigns risk label and explanation per clause.
7. API returns results and creates a chat session.
8. Frontend renders clause list and enables chat follow-ups.

## Design Characteristics

- Modularity: Pipeline stages are implemented as composable modules.
- Traceability: Explanations include similarity-backed references.
- Role-awareness: Agreement and user role shape review context.
- Resilience: Error handling and fallback behavior across stages.
- Scalability path: Batch embedding/retrieval and isolated model serving.
