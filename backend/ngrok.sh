#!/usr/bin/env bash
set -euo pipefail

# Starts an ngrok HTTP tunnel to the local backend.
# Use NGROK_PORT to override the default local port (8000).
# Example: NGROK_PORT=8000 ./ngrok.sh

LOCAL_PORT="${NGROK_PORT:-8000}"
NGROK_HOSTNAME="neomi-unprorogued-allegra.ngrok-free.dev"

cd "$(dirname "$0")"

echo "Starting ngrok tunnel to http://localhost:${LOCAL_PORT}"
echo "Public URL: https://${NGROK_HOSTNAME}"

ngrok http "http://localhost:${LOCAL_PORT}" --hostname="${NGROK_HOSTNAME}"
