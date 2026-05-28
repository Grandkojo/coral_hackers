#!/usr/bin/env bash
set -euo pipefail

cd /app

wait_for_postgres() {
  local url="${DATABASE_URL:-}"
  if [[ "$url" != postgres* ]]; then
    return 0
  fi

  python <<'PY'
import os
import socket
import sys
import time
from urllib.parse import urlparse

raw = os.environ.get("DATABASE_URL", "")
for prefix in ("postgresql+psycopg://", "postgresql://"):
    if raw.startswith(prefix):
        raw = "postgresql://" + raw[len(prefix):]
        break

parsed = urlparse(raw)
host = parsed.hostname or "postgres"
port = parsed.port or 5432

for attempt in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            break
    except OSError:
        time.sleep(1)
else:
    sys.exit("postgres not ready after 60s")

print(f"postgres ready at {host}:{port}")
PY
}

init_database() {
  python - <<'PY'
from app.db.session import init_db

init_db()
print("database initialized")
PY
}

setup_coral_sources() {
  if [[ "${CORAL_MODE:-mock}" != "cli" ]]; then
    echo "CORAL_MODE=${CORAL_MODE:-mock}; skipping coral source setup"
    return 0
  fi

  if [[ "${CORAL_SETUP_ON_START:-true}" != "true" ]]; then
    echo "CORAL_SETUP_ON_START=false; skipping coral source setup"
    return 0
  fi

  mkdir -p "${CORAL_CONFIG_DIR:-/data/coral}"
  export CORAL_CONFIG_DIR="${CORAL_CONFIG_DIR:-/data/coral}"
  export CORAL_SETUP_SMOKE="${CORAL_SETUP_SMOKE:-false}"

  echo "configuring coral sources in ${CORAL_CONFIG_DIR}"
  /app/scripts/setup_coral_sources.sh
}

wait_for_postgres
init_database
setup_coral_sources

exec "$@"
