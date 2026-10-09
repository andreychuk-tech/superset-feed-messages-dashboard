# Дашборд «Связь ленты и сообщений»

Аналитический дашборд в Apache Superset по данным симулятора (лента новостей и мессенджер).

## Запуск (GitHub Codespaces или локально)
docker compose -f deploy/docker-compose.simple.yml up -d
Вход: admin / admin (только для демо). В Codespaces открывай Superset по адресу из вкладки Ports, а не по localhost.

## Данные
Скрипт scripts/feed_messages.py выгружает агрегаты из ClickHouse в data/*.csv (в репозиторий не входят).
