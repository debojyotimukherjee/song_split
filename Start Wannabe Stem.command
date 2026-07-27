#!/bin/bash
set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

echo "Starting Wannabe Stem..."
echo

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker Desktop is not installed."
  echo "Install it from https://www.docker.com/products/docker-desktop/ and run this again."
  read -r -p "Press Return to close."
  exit 1
fi

open -a "Docker" >/dev/null 2>&1 || true

echo "Waiting for Docker Desktop..."
for attempt in $(seq 1 90); do
  if docker info >/dev/null 2>&1; then
    break
  fi
  sleep 2
  if [ "$attempt" -eq 90 ]; then
    echo "Docker Desktop did not become ready. Open Docker Desktop and try again."
    read -r -p "Press Return to close."
    exit 1
  fi
done

mkdir -p data/inbox data/jobs data/models

export INSTALL_DEMUCS=true
docker compose up -d --build api

echo
echo "Wannabe Stem is running."
echo "Opening http://localhost:8000 ..."
open "http://localhost:8000"
echo
echo "You can close this window. Use Stop Wannabe Stem.command when finished."
read -r -p "Press Return to close."
