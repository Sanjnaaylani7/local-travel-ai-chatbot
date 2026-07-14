#!/usr/bin/env bash
# Set up a local development environment for the Local Travel AI Chatbot.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "==> Creating virtual environment (.venv)"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Upgrading pip"
pip install --upgrade pip

echo "==> Installing backend dependencies"
pip install -r backend/requirements-dev.txt

echo "==> Installing data pipeline dependencies"
pip install -r data_pipeline/requirements.txt

echo "==> Installing model server dependencies"
pip install -r model_server/requirements.txt

if [ ! -f .env ]; then
  echo "==> Creating .env from .env.example"
  cp .env.example .env
fi

echo "Done. Activate with 'source .venv/bin/activate'."
echo "Next: build the knowledge index with 'python data_pipeline/run_pipeline.py --crawl'"
