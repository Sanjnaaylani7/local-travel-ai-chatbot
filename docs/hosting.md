# Hosting the Local Travel AI Chatbot

This guide covers running the stack with Docker Compose. All services are
self-hosted; no external AI APIs are used.

## Prerequisites
- Docker and Docker Compose.
- ~4 GB RAM free (model + embeddings). More is better for concurrency.
- Outbound internet on first run to download the models (cached afterwards).

## 1. Configure environment
```bash
cp .env.example .env
# Edit .env — at minimum set CORS_ORIGINS to your website and a strong ADMIN_API_KEY.
```

## 2. Build the knowledge index
The backend needs a FAISS index before it can answer grounded questions.
Run the pipeline on the host (or in a one-off container):
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r data_pipeline/requirements.txt
python data_pipeline/run_pipeline.py --crawl   # crawl live site, then build
# or, to rebuild from existing raw_content.json:
python data_pipeline/run_pipeline.py
```
This writes `data_pipeline/output/vector_store/{index.faiss,metadata.json}`,
which Compose mounts read-only into the backend at `/vector_store`.

## 3. Start the stack
```bash
docker compose -f infra/docker-compose.yml --env-file .env up -d --build
```
Services:
- **nginx** — serves the widget and proxies the API on port **80**.
- **backend** — FastAPI (internal 8000).
- **model_server** — flan-t5 inference (internal 8001).
- **prometheus** — metrics on port **9090** (scrapes backend `/metrics`).

## 4. Verify
```bash
curl http://localhost/api/health/        # liveness
curl http://localhost/api/health/ready   # DB + vector store + model server
```
Open `http://localhost/` for the chat widget.

## 5. Endpoints
| Method | Path | Purpose |
|-------|------|---------|
| POST | `/api/session/` | Create a session |
| DELETE | `/api/session/{id}` | Delete a session |
| POST | `/api/chat/` | Ask a question (RAG) |
| POST | `/api/feedback/` | Submit feedback |
| GET | `/api/feedback/` | Export feedback (needs `X-Admin-Api-Key`) |
| GET | `/api/health/` , `/api/health/ready` | Health probes |

## 6. Production notes
- Put TLS in front of Nginx (e.g. a load balancer or certbot).
- Use PostgreSQL: set `DATABASE_URL=postgresql+psycopg://user:pass@host:5432/db`.
- Scale the backend with more `UVICORN_WORKERS` and/or replicas; it is stateless.
- Rebuild the index on a schedule and restart/rolling-reload the backend.
