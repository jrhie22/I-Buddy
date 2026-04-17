#!/bin/bash
set -e
# Run from this script's directory so `app:app` resolves (Azure cwd is not always wwwroot).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
exec gunicorn --bind=0.0.0.0:"${PORT:-8000}" app:app
