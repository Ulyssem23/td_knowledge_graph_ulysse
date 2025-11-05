#!/usr/bin/env bash
set -euo pipefail

GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
CYAN="\033[0;36m"
RESET="\033[0m"

echo -e "${CYAN}🛠 Starting System Health Check...${RESET}"

# -------- FastAPI Health --------
echo -e "\n${YELLOW}Checking FastAPI health...${RESET}"
if curl -sS http://127.0.0.1:8000/health | grep -q '"ok":true'; then
  echo -e "${GREEN}✔ FastAPI is healthy${RESET}"
else
  echo -e "${RED}✖ FastAPI health check failed${RESET}"
  exit 1
fi

# -------- Postgres Queries --------
echo -e "\n${YELLOW}Running Postgres sample queries...${RESET}"

echo -e "${CYAN}--- Query 1: Sample orders ---${RESET}"
docker compose exec -T postgres psql -U app -d shop -c "SELECT * FROM orders LIMIT 5;"

echo -e "${CYAN}--- Query 2: Total orders ---${RESET}"
docker compose exec -T postgres psql -U app -d shop -c "SELECT COUNT(*) AS total_orders FROM orders;"

echo -e "${CYAN}--- Query 3: Sample customers ---${RESET}"
docker compose exec -T postgres psql -U app -d shop -c "SELECT * FROM customers LIMIT 5;"

echo -e "${CYAN}--- Query 4: Orders per customer ---${RESET}"
docker compose exec -T postgres psql -U app -d shop -c "SELECT customer_id, COUNT(*) AS orders_count FROM orders GROUP BY customer_id LIMIT 5;"

echo -e "${CYAN}--- Query 5: Recent orders ---${RESET}"
docker compose exec -T postgres psql -U app -d shop -c "SELECT * FROM orders ORDER BY ts DESC LIMIT 5;"

echo -e "${GREEN}✔ Postgres queries completed successfully${RESET}"

# -------- Neo4j Queries --------
echo -e "\n${YELLOW}Running Neo4j sample queries...${RESET}"

echo -e "${CYAN}--- Query 1: DB info ---${RESET}"
docker compose exec -T neo4j cypher-shell -u neo4j -p password "CALL db.info();"

echo -e "${CYAN}--- Query 2: Sample nodes ---${RESET}"
docker compose exec -T neo4j cypher-shell -u neo4j -p password "MATCH (n) RETURN n LIMIT 5;"

echo -e "${CYAN}--- Query 3: Node count ---${RESET}"
docker compose exec -T neo4j cypher-shell -u neo4j -p password "MATCH (n) RETURN count(n) AS total_nodes;"

echo -e "${CYAN}--- Query 4: Sample relationships ---${RESET}"
docker compose exec -T neo4j cypher-shell -u neo4j -p password "MATCH (a)-[r]->(b) RETURN a,b,r LIMIT 5;"

echo -e "${CYAN}--- Query 5: Relationship count ---${RESET}"
docker compose exec -T neo4j cypher-shell -u neo4j -p password "MATCH ()-[r]->() RETURN count(r) AS total_relationships;"

echo -e "${GREEN}✔ Neo4j queries completed successfully${RESET}"

# -------- ETL --------
echo -e "\n${YELLOW}Running ETL inside app container...${RESET}"
docker compose exec -T app python /work/app/etl.py | tail -n 1

echo -e "${GREEN}✅ ETL process completed.${RESET}"
