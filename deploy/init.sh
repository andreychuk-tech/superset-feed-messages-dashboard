#!/usr/bin/env bash
set -e
docker compose -f deploy/docker-compose.simple.yml up -d
echo "Жду запуска Superset..."
sleep 60
docker exec superset_simple mkdir -p /tmp/data
docker cp data/dau_segments.csv superset_simple:/tmp/data/dau_segments.csv
docker cp data/msg_activity.csv superset_simple:/tmp/data/msg_activity.csv
docker cp scripts/load_csv_to_sqlite.py superset_simple:/tmp/load_csv_to_sqlite.py
docker exec superset_simple /app/.venv/bin/python /tmp/load_csv_to_sqlite.py
echo "Готово. Импортируй dashboard/dashboard_feed_messages.zip в Superset (admin / admin)."
