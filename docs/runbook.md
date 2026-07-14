# Runbook — Local Travel AI Chatbot

Operational procedures for running and maintaining the chatbot.

## Local development
```bash
bash scripts/setup_env.sh          # venv + install deps + create .env
source .venv/bin/activate
python data_pipeline/run_pipeline.py --crawl   # build the knowledge index

# Terminal 1 — model server
cd model_server && PORT=8001 python src/serve.py

# Terminal 2 — backend
cd backend && uvicorn src.main:app --reload --port 8000
```
Run the tests:
```bash
pip install -r backend/requirements-dev.txt
pytest
```

## Deployment
See `docs/hosting.md`. In short:
```bash
cp .env.example .env               # edit values
python data_pipeline/run_pipeline.py --crawl
docker compose -f infra/docker-compose.yml --env-file .env up -d --build
```

## Monitoring
- **Liveness:** `GET /api/health/` — process is up.
- **Readiness:** `GET /api/health/ready` — database, vector store and model
  server are all reachable. Returns 503 if the database is down.
- **Metrics:** `GET /metrics` (Prometheus format) when the instrumentator is
  installed; scraped by the bundled Prometheus at `:9090`.
- **Logs:** structured JSON in production (`docker compose logs backend`), each
  request tagged with an `X-Request-ID`.

## Troubleshooting
| Symptom | Likely cause | Action |
|--------|--------------|--------|
| Answers are always the fallback message | Vector store not loaded | Confirm `index.faiss` exists in `VECTOR_STORE_DIR`; rebuild pipeline; check `/api/health/ready` |
| `model_server: unavailable` in readiness | Model still loading or crashed | Check `docker compose logs model_server`; first load downloads the model |
| 429 Too Many Requests | Rate limit hit | Increase `RATE_LIMIT_PER_MINUTE` or front with a gateway limiter |
| 401 on feedback export | Missing/invalid admin key | Send `X-Admin-Api-Key`; ensure `ADMIN_API_KEY` is set |
| Import errors on start | Running from wrong dir | Backend runs as `uvicorn src.main:app` from the `backend/` directory |

## Maintenance
- **Refresh knowledge:** re-run `data_pipeline/run_pipeline.py --crawl`, then
  restart the backend (or POST-reload) to pick up the new index.
- **Database backups:** back up the SQL database regularly (SQLite file or
  managed Postgres snapshots).
- **Model updates:** change `MODEL_NAME` / `EMBEDDING_MODEL` in `.env`. If you
  change the embedding model you MUST rebuild the index.
