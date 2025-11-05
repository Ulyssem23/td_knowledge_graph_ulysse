#!/bin/bash
set -euo pipefail
echo "Starting app container: installing requirements (this may take a few seconds)..."
pip install --no-cache-dir -r requirements.txt
echo "Running ETL once at startup..."
python /work/app/etl.py || true
echo "Starting Uvicorn..."
uvicorn main:app --host 0.0.0.0 --port 8000
