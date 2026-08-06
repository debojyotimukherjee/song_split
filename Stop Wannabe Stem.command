#!/bin/bash
set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

echo "Stopping Wannabe Stem..."

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed or not on PATH."
  read -r -p "Press Return to close."
  exit 1
fi

docker compose down

echo
echo "Wannabe Stem stopped."
read -r -p "Press Return to close."
