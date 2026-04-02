# Operations

## Local Startup

Recommended startup:

1. Activate Python virtual environment.
2. Start backend API on port `8000`.
3. Start frontend development server on port `5173`.

You can use the helper script:

- `start_all.ps1`

This script opens separate terminals for backend and frontend and waits for backend health readiness.

## Runtime Services

1. Backend API service
   - Default: `http://localhost:8000`

2. Frontend application
   - Default: `http://localhost:5173`

3. Model service
   - Exposed through configured model service endpoint used by the reasoning layer

4. Chat persistence
   - SQLite file in backend data folder

## Key Environment Variables

Configuration is centralized in `backend/retrieval_pipeline/config.py`.

Important groups:

1. Retrieval and embedding
   - index name, top-k, similarity thresholds, embedding model, batch sizes

2. OCR
   - enable/disable OCR, OCR language list, OCR minimum text threshold, render scale

3. Agreement context
   - default agreement type and default user role

4. Chat controls
   - session TTL, history length, answer/question character limits

5. Model and reasoning
   - model path and model service communication parameters

## Health Monitoring

Use:

- `GET /health`

Minimum healthy conditions:

- `api=ready`
- chat DB reports ready
- model service is not in error state

## Data Lifecycle

1. Uploaded contracts
   - Stored as temporary files during processing
   - Deleted in cleanup blocks after request handling

2. Analysis outputs
   - Returned in HTTP response
   - Session context optionally persisted for chat

3. Chat sessions
   - Stored in SQLite
   - Expired sessions removed by TTL cleanup routine

## Troubleshooting

## Issue: Backend not reachable

Checks:

1. Confirm backend terminal is running without import/runtime exceptions.
2. Verify port `8000` is free and listening.
3. Call `/health` directly from browser or curl.

## Issue: Analysis fails for PDF

Checks:

1. Confirm file is a valid `.pdf`.
2. Verify extraction dependencies are installed.
3. Test with a smaller known-good PDF.

## Issue: Chat session not found

Checks:

1. Ensure `session_id` came from latest `/analyze` or `/chat/upload` response.
2. Verify session has not expired due to TTL.

## Issue: Poor clause extraction from scans

Checks:

1. Enable OCR mode.
2. Increase OCR render scale.
3. Lower minimum native text threshold to trigger OCR more often.

## Validation Checklist

After setup changes, verify:

1. `/health` returns ready API and DB status.
2. `/metadata/agreement-options` returns non-empty options.
3. `/analyze` returns clause list and session ID.
4. `/chat/ask` returns answer with history and citations.
