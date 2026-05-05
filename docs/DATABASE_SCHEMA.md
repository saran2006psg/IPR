# Database Schema

## Purpose

This document defines the full data schema for the Contract Risk Analyzer project, including:

1. Current persisted schema in production code
2. Logical schemas stored as JSON objects inside persisted records
3. Vector index schema used by retrieval
4. Seed dataset schema used for ingestion
5. A normalized SQL schema proposal for future scale

## Current Storage Topology

The system currently uses a hybrid data model:

1. SQLite for chat sessions and chat messages
2. Pinecone for vector similarity search over legal clauses
3. CSV as the source dataset for Pinecone ingestion
4. In-code catalogs for agreement types and role guidance

## 1. SQLite Schema (Current)

### 1.1 Database location

- Config key: `CHAT_DB_PATH`
- Default path: `backend/data/chat_sessions.db`
- Source: `backend/retrieval_pipeline/config.py`

### 1.2 Table: `chat_sessions`

Created in `backend/chat_session_store.py`.

```sql
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id TEXT PRIMARY KEY,
    file_name TEXT,
    analyses_json TEXT NOT NULL,
    summary_text TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
```

Column definitions:

| Column          | Type | Null | Description                                     |
| --------------- | ---- | ---- | ----------------------------------------------- |
| `session_id`    | TEXT | NO   | UUID string primary key                         |
| `file_name`     | TEXT | YES  | Uploaded file name                              |
| `analyses_json` | TEXT | NO   | JSON-serialized list of clause analysis objects |
| `summary_text`  | TEXT | YES  | Contract-level summary string                   |
| `created_at`    | REAL | NO   | Unix timestamp in seconds                       |
| `updated_at`    | REAL | NO   | Unix timestamp in seconds                       |

### 1.3 Table: `chat_messages`

Created in `backend/chat_session_store.py`.

```sql
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    confidence REAL,
    fallback_used INTEGER DEFAULT 0,
    citations_json TEXT,
    created_at REAL NOT NULL,
    FOREIGN KEY(session_id) REFERENCES chat_sessions(session_id)
);
```

Column definitions:

| Column           | Type    | Null | Description                               |
| ---------------- | ------- | ---- | ----------------------------------------- |
| `id`             | INTEGER | NO   | Auto-increment message primary key        |
| `session_id`     | TEXT    | NO   | FK to `chat_sessions.session_id`          |
| `role`           | TEXT    | NO   | Chat role, expected `user` or `assistant` |
| `content`        | TEXT    | NO   | Message text                              |
| `confidence`     | REAL    | YES  | Answer confidence score                   |
| `fallback_used`  | INTEGER | YES  | Boolean encoded as `0` or `1`             |
| `citations_json` | TEXT    | YES  | JSON-serialized citation list             |
| `created_at`     | REAL    | NO   | Unix timestamp in seconds                 |

### 1.4 Indexes

```sql
CREATE INDEX IF NOT EXISTS idx_chat_messages_session
ON chat_messages(session_id);
```

### 1.5 Session retention and cleanup

- Config key: `CHAT_SESSION_TTL_SEC`
- Default: `86400` seconds (24 hours)
- Cleanup function: `cleanup_expired_sessions()` in `backend/chat_session_store.py`
- Behavior: deletes expired rows in `chat_sessions`, then deletes corresponding `chat_messages`

## 2. JSON Schemas Stored in SQLite Columns

### 2.1 `chat_sessions.analyses_json`

`analyses_json` stores an array of clause analysis objects produced by the retrieval pipeline.

JSON shape:

```json
[
  {
    "clause_text": "string",
    "risk_level": "HIGH|MEDIUM|LOW|UNKNOWN",
    "explanation": "string",
    "model_used": true,
    "fallback_used": false,
    "agreement_type": "string",
    "user_type": "string",
    "similar_clauses": [
      {
        "text": "string",
        "severity": "HIGH|MEDIUM|LOW|UNKNOWN",
        "clause_type": "string",
        "score": 0.0,
        "match_id": "string",
        "rule_id": "string",
        "rule_name": "string"
      }
    ]
  }
]
```

Primary sources:

- `backend/retrieval_pipeline/llm_reasoner.py`
- `backend/retrieval_pipeline/risk_analyzer.py`
- `backend/retrieval_pipeline/main.py`

### 2.2 `chat_messages.citations_json`

`citations_json` stores an array of citation objects.

JSON shape:

```json
[
  {
    "clause_index": 0,
    "risk_level": "HIGH|MEDIUM|LOW|UNKNOWN",
    "relevance_score": 1.0,
    "snippet": "string"
  }
]
```

Primary sources:

- `backend/chat_orchestrator.py`
- `backend/api.py` (`Citation` model)

## 3. Pinecone Vector Schema (Current)

### 3.1 Index definition

- Index name: `contract-risk-db`
- Dimension: `768`
- Similarity metric: `cosine`
- Cloud/region defaults: `aws` / `us-east-1`
- Sources:
  - `backend/retrieval_pipeline/config.py`
  - `backend/scripts/ingest_pipeline.py`

### 3.2 Stored vector record shape

Ingestion upserts records in this format:

```json
{
  "id": "string",
  "values": [0.0, 0.0, 0.0],
  "metadata": {
    "clause_text": "string",
    "severity": "low|medium|high",
    "clause_type": "string"
  }
}
```

Retrieval normalizes metadata into the app-level similar clause schema:

- `text`
- `severity` (uppercased)
- `clause_type`
- `score`
- optional IDs (`match_id`, `rule_id`, `rule_name`)

## 4. Seed CSV Schema (Current)

Source file: `data/legal_contract_clauses.csv`

Columns:

| Column        | Type   | Description                                 |
| ------------- | ------ | ------------------------------------------- |
| `clause_text` | string | Raw legal clause text                       |
| `clause_type` | string | Clause category label                       |
| `risk_level`  | string | Source risk label (`low`, `medium`, `high`) |

Validation is enforced in `backend/scripts/ingest_pipeline.py` before embedding and upsert.

## 5. Agreement and Role Catalog Schema (Current App-Level)

Agreement type to role mapping is currently defined in code, not in DB:

- Source: `backend/retrieval_pipeline/agreement_profiles.py`
- Structure: `AGREEMENT_USER_TYPE_MAP` + `ROLE_REVIEW_GUIDANCE`

Canonical agreement-role pairs:

| Agreement Type          | Allowed Roles                                             |
| ----------------------- | --------------------------------------------------------- |
| Company Sales Agreement | Buyer, Seller                                             |
| Merger Agreement        | Acquirer, Target Company, Shareholder                     |
| Stakeholder Agreement   | Majority Shareholder, Minority Shareholder, Company Board |
| Rent Agreement          | Landlord, Tenant                                          |

## 6. Relationship Model (Current)

Current durable relationship graph:

1. One `chat_sessions` row has many `chat_messages` rows
2. `chat_sessions.analyses_json` embeds many clause analyses
3. Each clause analysis embeds many similar clauses from Pinecone
4. Each assistant message can embed many citations in `citations_json`

Logical ER (current):

```text
chat_sessions (1) ------ (N) chat_messages
      |
      +-- analyses_json[]
            |
            +-- similar_clauses[] (from Pinecone)

chat_messages
      +-- citations_json[]
```

## 7. API Data Contract Fields That Depend on Schema

Important response/request models in `backend/api.py`:

1. `SimilarClause`
   - `text`, `score`, `severity`, `clause_type`, optional ids
2. `ClauseResult`
   - `clause`, `risk_level`, `explanation`, `similar_clauses`
3. `ChatUploadResponse`
   - `session_id`, `clause_count`, `high_risk_count`, `summary`, `agreement_type`, `user_type`
4. `ChatAskRequest`
   - `session_id`, `question`, optional `selected_clause_index`, optional context
5. `ChatAskResponse`
   - `answer`, `confidence`, `fallback_used`, `citations`, `history`
6. `Citation`
   - `clause_index`, `risk_level`, `relevance_score`, `snippet`

These contracts rely on the SQLite + JSON structures above.

## 8. Proposed Normalized SQL Schema (Future)

The current schema is functional for session chat persistence, but analytics and long-term governance are limited by JSON blobs and in-code catalogs. A normalized relational schema can be added without changing core product behavior.

Target: PostgreSQL + pgvector

```sql
-- Agreements and roles
CREATE TABLE agreement_types (
    agreement_type_id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE agreement_roles (
    agreement_role_id UUID PRIMARY KEY,
    agreement_type_id UUID NOT NULL REFERENCES agreement_types(agreement_type_id),
    role_name TEXT NOT NULL,
    review_guidance TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (agreement_type_id, role_name)
);

-- Knowledge base
CREATE TABLE reference_clauses (
    reference_clause_id UUID PRIMARY KEY,
    clause_text TEXT NOT NULL,
    clause_type TEXT NOT NULL,
    source_risk_level TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE reference_clause_embeddings (
    reference_clause_id UUID PRIMARY KEY REFERENCES reference_clauses(reference_clause_id),
    embedding VECTOR(768) NOT NULL,
    embedding_model TEXT NOT NULL,
    normalized BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Contract uploads and clause analysis
CREATE TABLE contracts (
    contract_id UUID PRIMARY KEY,
    file_name TEXT,
    file_sha256 TEXT,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE contract_analyses (
    analysis_id UUID PRIMARY KEY,
    contract_id UUID NOT NULL REFERENCES contracts(contract_id),
    agreement_type_id UUID NOT NULL REFERENCES agreement_types(agreement_type_id),
    agreement_role_id UUID NOT NULL REFERENCES agreement_roles(agreement_role_id),
    summary_text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE contract_clauses (
    contract_clause_id UUID PRIMARY KEY,
    analysis_id UUID NOT NULL REFERENCES contract_analyses(analysis_id),
    clause_index INTEGER NOT NULL,
    clause_text TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    explanation TEXT NOT NULL,
    model_used BOOLEAN NOT NULL DEFAULT FALSE,
    fallback_used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (analysis_id, clause_index)
);

CREATE TABLE clause_similar_matches (
    clause_match_id UUID PRIMARY KEY,
    contract_clause_id UUID NOT NULL REFERENCES contract_clauses(contract_clause_id),
    reference_clause_id UUID REFERENCES reference_clauses(reference_clause_id),
    match_id TEXT,
    rule_id TEXT,
    rule_name TEXT,
    clause_type TEXT,
    severity TEXT,
    similarity_score DOUBLE PRECISION NOT NULL,
    matched_text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Chat
CREATE TABLE chat_sessions (
    session_id UUID PRIMARY KEY,
    analysis_id UUID NOT NULL REFERENCES contract_analyses(analysis_id),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE chat_messages (
    chat_message_id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES chat_sessions(session_id),
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    confidence DOUBLE PRECISION,
    fallback_used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE message_citations (
    message_citation_id UUID PRIMARY KEY,
    chat_message_id UUID NOT NULL REFERENCES chat_messages(chat_message_id),
    contract_clause_id UUID REFERENCES contract_clauses(contract_clause_id),
    relevance_score DOUBLE PRECISION NOT NULL,
    snippet TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_contract_clauses_analysis ON contract_clauses(analysis_id);
CREATE INDEX idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX idx_clause_similar_matches_clause ON clause_similar_matches(contract_clause_id);
```

## 9. Mapping: Current -> Future Tables

| Current Source                                               | Future Target                                       |
| ------------------------------------------------------------ | --------------------------------------------------- |
| `chat_sessions.session_id`                                   | `chat_sessions.session_id`                          |
| `chat_sessions.file_name`                                    | `contracts.file_name`                               |
| `chat_sessions.summary_text`                                 | `contract_analyses.summary_text`                    |
| `chat_sessions.analyses_json[*]`                             | `contract_clauses` + `clause_similar_matches`       |
| `chat_messages`                                              | `chat_messages`                                     |
| `chat_messages.citations_json[*]`                            | `message_citations`                                 |
| Pinecone metadata (`clause_text`, `severity`, `clause_type`) | `reference_clauses` + `reference_clause_embeddings` |
| `AGREEMENT_USER_TYPE_MAP` + `ROLE_REVIEW_GUIDANCE`           | `agreement_types` + `agreement_roles`               |

## 10. Notes and Constraints

1. Current schema intentionally optimizes for rapid session bootstrap and chat continuity.
2. Current SQLite tables do not enforce enum constraints for risk labels or roles.
3. Current design stores analysis detail as JSON for simplicity, not relational queryability.
4. Pinecone remains the retrieval source of truth for semantic similarity until a vector-capable relational setup is added.
5. Any migration should preserve endpoint response contracts defined in `backend/api.py`.
