# API Reference

Base URL (local): `http://localhost:8000`

All endpoints are served by FastAPI in `backend/api.py`.

## 1. Health

`GET /health`

Purpose:

- Service readiness probe for API, model service, and chat DB.

Response fields:

- `status`: overall (`ok` or `degraded`)
- `api`: API readiness
- `model_server`: model service readiness state
- `chatbot_db`: chat DB readiness
- `model_server_url`: configured model service URL
- `llm_provider`: provider label
- `llm_model`: model label
- `timestamp`: UTC timestamp

## 2. Agreement Metadata

`GET /metadata/agreement-options`

Purpose:

- Returns allowed agreement types and valid user roles for each.

Response shape:

- `options`: list of objects
  - `agreement_type`
  - `user_types` (string array)

## 3. Analyze Contract

`POST /analyze`

Content type:

- `multipart/form-data`

Form fields:

- `file`: PDF file (required)
- `agreement_type`: string (optional; defaults from config)
- `user_type`: string (optional; defaults from config)

Response:

- `results`: array of clause analysis objects
- `session_id`: generated chat session ID
- `agreement_type`: resolved value
- `user_type`: resolved value

Clause analysis object:

- `clause`
- `risk_level`
- `explanation`
- `similar_clauses` (array)

Similar clause object:

- `text`
- `score`
- `severity`
- `clause_type`
- optional: `match_id`, `rule_id`, `rule_name`

## 4. Summarize Contract

`POST /summarize`

Content type:

- `multipart/form-data`

Form fields:

- `file`: PDF file (required)
- `agreement_type`: string (optional)
- `user_type`: string (optional)

Response:

- `summary`: synthesized contract summary text

## 5. Chat Upload

`POST /chat/upload`

Purpose:

- Analyze uploaded contract and create a dedicated chat session.

Form fields:

- `file`: PDF file (required)
- `agreement_type`: string (optional)
- `user_type`: string (optional)

Response:

- `session_id`
- `clause_count`
- `high_risk_count`
- `summary`
- `agreement_type`
- `user_type`

## 6. Chat Ask

`POST /chat/ask`

Content type:

- `application/json`

Request body:

- `session_id`: string (required)
- `question`: string (required)
- `selected_clause_index`: integer (optional)
- `agreement_type`: string (optional)
- `user_type`: string (optional)

Response:

- `session_id`
- `answer`
- `confidence`
- `fallback_used`
- `citations`: array
- `history`: array of chat messages
- `agreement_type`
- `user_type`

Citation object:

- `clause_index`
- `risk_level`
- `relevance_score`
- `snippet`

Message object:

- `role`
- `content`
- `confidence` (optional)
- `fallback_used`
- `citations`

## Error Codes

Common statuses:

- `200`: success
- `400`: validation error (bad file type, invalid role context, oversized question)
- `404`: missing/expired chat session
- `500`: internal processing failure
