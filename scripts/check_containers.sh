#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-host}"  # host | container

if [ "$MODE" = "container" ]; then
  # Running *inside* the app container
  APP_URL="http://app:8000/health"
  export PGPASSWORD=secret
  PSQL='psql -h postgres -U app -d shop -c'
  ETL='python /work/app/etl.py'
else
  # Running on the host (needs docker CLI)
  APP_URL="http://127.0.0.1:8000/health"
  PSQL='docker compose exec -T postgres psql -U app -d shop -c'
  ETL='docker compose exec -T app python /work/app/etl.py'
fi

echo "Checking FastAPI health..."
curl -fsS "$APP_URL"
echo -e "\n✔ FastAPI is healthy\n"

echo "Running Postgres sample queries..."
echo "--- Query 1: Sample orders ---"
eval "$PSQL \"SELECT id, customer_id, ts FROM orders ORDER BY ts LIMIT 5;\""

echo -e "\n--- Query 2: now() ---"
eval "$PSQL \"SELECT now();\""
echo "✔ Postgres OK"

echo -e "\nRunning ETL once..."
eval "$ETL" | sed -n '1,120p'
echo "✔ ETL OK"