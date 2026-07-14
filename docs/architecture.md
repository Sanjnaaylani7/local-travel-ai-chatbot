# Local Travel AI Chatbot — Architecture

## 1. Overview
A self-hosted, retrieval-augmented (RAG) chatbot that answers travel questions
(visas, flights, tour packages, hotels, Umrah/Hajj, insurance) using **only** a
local knowledge base built from approved travel-website content. No user data or
queries leave the environment.

## 2. Components

```
Browser widget ──HTTP──▶ FastAPI backend ──HTTP──▶ Model server (flan-t5)
                              │
                              ├─▶ Embeddings (sentence-transformers, in-process)
                              ├─▶ FAISS vector index (cosine, loaded from disk)
                              └─▶ SQL database (sessions, messages, feedback)
```

### 2.1 Frontend — `web_widget/`
- **Vanilla JS widget** (`widget/`): embeddable floating chat button + panel.
- **React widget** (`react-widget/`): component version for React apps.
- Both call `POST /api/session/` and `POST /api/chat/` and render source links.

### 2.2 Backend — `backend/src/` (FastAPI)
- `api/chat.py` — RAG endpoint: retrieve context → build prompt → generate → persist.
- `api/session.py` — create/delete sessions (persisted).
- `api/feedback.py` — capture feedback; admin export guarded by API key.
- `api/health.py` — `/api/health/` (liveness) and `/api/health/ready` (deep checks).
- `services/embeddings.py` — lazy, thread-safe sentence-transformer encoder.
- `services/vector_store.py` — FAISS cosine index loaded from `VECTOR_STORE_DIR`.
- `services/retrieval.py` — embed query, search, filter by similarity threshold.
- `services/model_client.py` — calls the model server with retries; builds the
  grounded prompt; returns a safe fallback when there is no context.
- `core/` — env-driven config, logging, security (admin API key), middleware
  (request IDs, rate limiting).

### 2.3 Model server — `model_server/src/serve.py`
- Self-hosted seq2seq LLM (default `google/flan-t5-small`) behind `POST /infer`.
- Environment-driven (`MODEL_NAME`, `PORT`, token limits); `/health` for probes.

### 2.4 Data pipeline — `data_pipeline/`
- `crawler/` → `extractor/clean.py` → `chunker/chunk.py` → `ingest/ingest_to_vector.py`.
- `run_pipeline.py` orchestrates the stages and writes `index.faiss` + `metadata.json`.
- Uses the **same** embedding model as the backend so vectors are comparable.

### 2.5 Vector store
- FAISS `IndexFlatIP` over L2-normalised embeddings ⇒ inner product == cosine similarity.
- Loaded in-process by the backend (fast, no extra service) and shared with
  backend replicas via a read-only mounted directory.

## 3. Request flow
1. Widget creates/reuses a session and POSTs the user message.
2. Backend embeds the query and retrieves the top-k most similar chunks.
3. Chunks below `SIMILARITY_THRESHOLD` are discarded. If nothing remains, a safe
   fallback is returned (no hallucination).
4. A grounded prompt (context + recent history) is sent to the model server.
5. The answer plus source URLs is returned and the turn is persisted.

## 4. Security & privacy
- All inference and retrieval run locally; nothing is sent to third parties.
- CORS origins, rate limiting and an admin API key are configured via environment.
- Public endpoints (chat/session/health) are unauthenticated by design; privileged
  endpoints (feedback export) require `X-Admin-Api-Key`.

## 5. Scalability
- Backend is stateless (state in the DB) → scale horizontally behind Nginx.
- Swap SQLite for PostgreSQL via `DATABASE_URL`.
- The read-only FAISS index is shared across replicas; rebuild offline and reload.
- The model server scales independently; increase replicas or use a GPU image.
