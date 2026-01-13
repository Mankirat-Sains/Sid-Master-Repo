#!/usr/bin/env bash
set -euo pipefail

# Restart the frontend dev server, freeing the port if something is already running there.
PORT="${PORT:-3000}"
HOST="${HOST:-0.0.0.0}"

free_port() {
  local port="$1"
  local pids
  pids="$(lsof -ti tcp:"${port}" 2>/dev/null || true)"
  if [ -n "${pids}" ]; then
    echo "Port ${port} is in use by: ${pids} — terminating..."
    kill ${pids} 2>/dev/null || true
    sleep 1
    if lsof -ti tcp:"${port}" >/dev/null 2>&1; then
      echo "Port ${port} is still busy. Close the process manually and retry." >&2
      exit 1
    fi
  fi
}

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}/Frontend/Frontend"

free_port "${PORT}"

echo "Starting frontend on ${HOST}:${PORT}..."
exec npm run dev -- --hostname "${HOST}" --port "${PORT}"
