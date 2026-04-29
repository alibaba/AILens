#!/usr/bin/env bash
# Local development startup — runs backend + frontend directly (no Docker)
# Gateway must be started separately (requires ClickHouse connection).
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Backend — must run from monorepo root (uses relative imports)
echo "Starting backend on :8000 ..."
cd "$ROOT"
pip3 install -r backend/requirements.txt -q 2>/dev/null || true
TRACEQL_BASE_URL="${TRACEQL_BASE_URL:-http://localhost:8080}" \
  python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Frontend
echo "Starting frontend on :3000 ..."
cd "$ROOT/frontend"
npm install --silent
npm run dev &
FRONTEND_PID=$!

echo ""
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Frontend: http://localhost:3000"
echo ""
echo "  Gateway must be started separately — see README for instructions."
echo ""
echo "Press Ctrl+C to stop all services."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT INT TERM
wait
