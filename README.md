# Local Travel AI Chatbot

A self-hosted, retrieval-augmented (RAG) chatbot for travel support (visas,
flights, tour packages, hotels, Umrah/Hajj, insurance). It answers using **only**
a local knowledge base built from approved travel-website content, and runs a
local language model — no data leaves your environment.

## Architecture
Browser widget → FastAPI backend (embeddings + FAISS retrieval + SQL) → local
model server (`flan-t5`). See [`docs/architecture.md`](docs/architecture.md).

```
web_widget/     Embeddable chat UI (vanilla JS + React)
backend/        FastAPI app: chat, session, feedback, health (RAG orchestration)
model_server/   Self-hosted seq2seq LLM behind /infer
data_pipeline/  crawl → clean → chunk → embed → FAISS index
embeddings/     Standalone embedding utility
vector_db/      FAISS index helper + config
infra/          docker-compose, nginx, prometheus
docs/           architecture / hosting / runbook
tests/          unit + integration tests
```

## Quick start (local)
```bash
bash scripts/setup_env.sh
source .venv/bin/activate
python data_pipeline/run_pipeline.py --crawl        # build the knowledge index

# start the model server and backend in separate terminals
cd model_server && PORT=8001 python src/serve.py
cd backend && uvicorn src.main:app --port 8000
```
Then open the widget at `web_widget/widget/index.html` (set
`window.CHATBOT_API_BASE = "http://localhost:8000"`), or serve everything with
Docker (see below).

## Quick start (Docker)
```bash
cp .env.example .env                                # edit CORS_ORIGINS, ADMIN_API_KEY
python data_pipeline/run_pipeline.py --crawl        # build index (mounted into backend)
docker compose -f infra/docker-compose.yml --env-file .env up -d --build
```
Widget: `http://localhost/`  •  API: `http://localhost/api`

## Tests
```bash
pip install -r backend/requirements-dev.txt
pytest
```

## Configuration
All settings are environment variables (see [`.env.example`](.env.example)):
key ones are `DATABASE_URL`, `MODEL_URL`, `EMBEDDING_MODEL`, `VECTOR_STORE_DIR`,
`TOP_K`, `SIMILARITY_THRESHOLD`, `CORS_ORIGINS`, `RATE_LIMIT_PER_MINUTE`,
`ADMIN_API_KEY`.

See [`docs/hosting.md`](docs/hosting.md) and [`docs/runbook.md`](docs/runbook.md)
for deployment and operations.
