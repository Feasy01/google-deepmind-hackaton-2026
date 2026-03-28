#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
DB_DIR="$ROOT_DIR/db"
BACKEND_PORT=8000
FRONTEND_PORT=5173

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[start-dev]${NC} $1"; }
warn() { echo -e "${YELLOW}[start-dev]${NC} $1"; }
err()  { echo -e "${RED}[start-dev]${NC} $1"; }

PIDS=()
cleanup() {
    log "Shutting down..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    docker compose -f "$DB_DIR/docker-compose.yml" down 2>/dev/null || true
    wait 2>/dev/null
    log "Done."
}
trap cleanup EXIT INT TERM

# --- Pre-flight checks ---
for cmd in docker ngrok uv node; do
    if ! command -v "$cmd" &>/dev/null; then
        err "$cmd is not installed. Please install it first."
        exit 1
    fi
done

if [ ! -f "$BACKEND_DIR/.env" ]; then
    err "Backend .env not found. Copy backend/.env.example to backend/.env and fill in your keys."
    exit 1
fi

# --- 1. Qdrant ---
log "Starting Qdrant..."
docker compose -f "$DB_DIR/docker-compose.yml" up -d

# Wait for Qdrant to be ready
for i in $(seq 1 15); do
    if curl -sf http://localhost:6333/readyz &>/dev/null; then
        log "Qdrant is ready."
        break
    fi
    if [ "$i" -eq 15 ]; then
        err "Qdrant failed to start."
        exit 1
    fi
    sleep 1
done

# --- 2. ngrok ---
log "Starting ngrok tunnel on port $BACKEND_PORT..."
ngrok http "$BACKEND_PORT" --log=stdout --log-format=json > /tmp/ngrok.log 2>&1 &
PIDS+=($!)

# Wait for ngrok to establish the tunnel
NGROK_URL=""
for i in $(seq 1 15); do
    NGROK_URL=$(curl -sf http://127.0.0.1:4040/api/tunnels 2>/dev/null \
        | python3 -c "import sys,json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])" 2>/dev/null || true)
    if [ -n "$NGROK_URL" ]; then
        break
    fi
    sleep 1
done

if [ -z "$NGROK_URL" ]; then
    err "Failed to get ngrok URL. Check ngrok auth: ngrok config add-authtoken <token>"
    exit 1
fi

log "ngrok URL: $NGROK_URL"

# Write VAPI_WEBHOOK_URL into backend .env
if grep -q "^VAPI_WEBHOOK_URL=" "$BACKEND_DIR/.env" 2>/dev/null; then
    sed -i "s|^VAPI_WEBHOOK_URL=.*|VAPI_WEBHOOK_URL=$NGROK_URL|" "$BACKEND_DIR/.env"
else
    echo "VAPI_WEBHOOK_URL=$NGROK_URL" >> "$BACKEND_DIR/.env"
fi
log "Set VAPI_WEBHOOK_URL=$NGROK_URL in backend/.env"

# --- 3. Backend ---
log "Starting backend..."
cd "$BACKEND_DIR"
uv run uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload &
PIDS+=($!)
cd "$ROOT_DIR"

# Wait for backend
for i in $(seq 1 20); do
    if curl -sf "http://localhost:$BACKEND_PORT/api/docs" &>/dev/null; then
        log "Backend is ready at http://localhost:$BACKEND_PORT"
        break
    fi
    sleep 1
done

# --- 4. Frontend ---
log "Starting frontend..."
cd "$FRONTEND_DIR"
npm run dev &
PIDS+=($!)
cd "$ROOT_DIR"

echo ""
log "========================================="
log " All services running:"
log "   Qdrant:    http://localhost:6333"
log "   Backend:   http://localhost:$BACKEND_PORT"
log "   Frontend:  http://localhost:$FRONTEND_PORT"
log "   ngrok:     $NGROK_URL"
log "   ngrok UI:  http://127.0.0.1:4040"
log "========================================="
log " Press Ctrl+C to stop everything."
echo ""

wait
