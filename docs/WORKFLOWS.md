# Workflows

## 1. Contract Analysis Workflow

Entry point: `POST /analyze`

1. User selects agreement type and user role in UI.
2. User uploads a PDF contract.
3. Backend validates file type and saves to temporary storage.
4. PDF extractor reads document text.
5. OCR is applied for pages with weak or missing text.
6. Clause segmenter splits and cleans extracted content.
7. Embedder converts clauses into vectors.
8. Retriever gets top similar legal clauses from vector index.
9. Risk analyzer assigns risk label and explanation per clause.
10. Backend creates chat session and returns analysis payload.
11. Frontend opens analysis view with clause navigation and insights.

## 2. Contract Summarization Workflow

Entry point: `POST /summarize`

1. User uploads PDF for summary.
2. Backend executes the same analysis pipeline stages.
3. Summary generator composes contract-level findings from clause outputs.
4. Backend returns summary text.

## 3. Chat Bootstrap Workflow

Entry point: `POST /chat/upload`

1. User uploads contract intended for interactive Q&A.
2. Backend runs analysis pipeline and builds summary context.
3. Session store creates persistent session with analyses and summary.
4. Backend returns `session_id`, counts, and summary for chat UI.

## 4. Clause-Aware Chat Workflow

Entry point: `POST /chat/ask`

1. Frontend sends question, session ID, selected clause index, and context.
2. Backend validates session and question length.
3. Session history is loaded from SQLite.
4. Chat orchestrator selects relevant clauses and constructs grounded context.
5. Reasoning layer generates answer and confidence.
6. Backend stores assistant message with citations and fallback flags.
7. Updated chat history is returned to frontend.

## 5. Health and Metadata Workflow

Endpoints:

- `GET /health`
- `GET /metadata/agreement-options`

Behavior:

- Health checks API status, model service readiness, and chat DB readiness.
- Metadata endpoint returns allowed agreement-role combinations for frontend controls.

## Error Workflow

Common error paths:

- Non-PDF upload -> `400`
- Invalid agreement/user type combination -> `400`
- Missing or expired chat session -> `404`
- Unexpected pipeline failure -> `500`

Recovery strategy:

- User-correctable validation errors are returned as clear messages.
- Temporary files are cleaned in `finally` blocks to avoid residue.
- Session TTL cleanup prevents stale conversation growth.
