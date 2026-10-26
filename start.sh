#!/usr/bin/env bash
# One-command start: sets up Python + Node deps if needed, builds the frontend,
# and serves app + API together at http://127.0.0.1:8000
set -euo pipefail
cd "$(dirname "$0")"

PY=${PYTHON:-python3}
if [ ! -x .venv/bin/python ]; then
  echo "Creating Python virtualenv…"
  "$PY" -m venv .venv
fi
.venv/bin/python -m pip install -q -r requirements.txt

if [ ! -d node_modules ]; then
  echo "Installing frontend packages…"
  npm install --no-audit --no-fund
fi
echo "Building frontend…"
npm run build --silent

echo "Starting SERVE on http://127.0.0.1:${PORT:-8000}  (Ctrl+C to stop)"
exec .venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port "${PORT:-8000}"
