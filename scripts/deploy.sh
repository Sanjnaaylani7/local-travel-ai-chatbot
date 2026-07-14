#!/usr/bin/env bash
# Build and deploy the Local Travel AI Chatbot with Docker Compose.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f .env ]; then
  echo "==> Creating .env from .env.example (edit it before production!)"
  cp .env.example .env
fi

COMPOSE="docker compose -f infra/docker-compose.yml --env-file .env"

echo "==> Building images"
$COMPOSE build

echo "==> Starting services"
$COMPOSE up -d

echo "==> Waiting for backend health"
for i in $(seq 1 30); do
  if curl -fsS http://localhost/api/health/ >/dev/null 2>&1; then
    echo "Backend healthy."
    break
  fi
  sleep 2
done

echo "==> Service status"
$COMPOSE ps

echo "Deployment complete. Chat widget: http://localhost/  |  API: http://localhost/api"
