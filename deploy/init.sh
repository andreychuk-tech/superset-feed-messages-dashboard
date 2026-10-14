#!/usr/bin/env bash
set -e
docker compose -f deploy/docker-compose.simple.yml up -d
echo "Жду запуска Superset..."
sleep 60
docker exec superset_simple mkdir -p /tmp/data
docker cp data/dau_segments.csv superset_simple:/tmp/data/dau_segments.csv
docker cp data/msg_activity.csv superset_simple:/tmp/data/msg_activity.csv
docker cp data/retention.csv superset_simple:/tmp/data/retention.csv
docker cp data/ads_profile.csv superset_simple:/tmp/data/ads_profile.csv
docker cp data/weekly_audience.csv superset_simple:/tmp/data/weekly_audience.csv

docker cp scripts/load_csv_to_sqlite.py superset_simple:/tmp/load_csv_to_sqlite.py
docker exec superset_simple /app/.venv/bin/python /tmp/load_csv_to_sqlite.py

echo "Готово! Данные загружены в SQLite."
echo "Следующий шаг: импортируй дашборды в Superset:"
echo "  1. dashboard/dashboard_feed_messages.zip — лента и сообщения."
echo "  2. dashboard/dashboard_retention.zip — Retention рекламных пользователей."
echo "Открой Superset в браузере и войди под настроенной учётной записью."

