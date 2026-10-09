import os

# Демо-ключ по умолчанию; для любого реального развёртывания задай свой через окружение
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "demo-only-secret-key-change-me")

# Нужно, чтобы подключить SQLite для загрузки CSV
PREVENT_UNSAFE_DB_CONNECTIONS = False

# Прокси Codespaces (убирает редирект на localhost)
ENABLE_PROXY_FIX = True
PROXY_FIX_CONFIG = {"x_for": 1, "x_proto": 1, "x_host": 1, "x_port": 0, "x_prefix": 0}

# Только для локальной демонстрации, не для публичного сервера
WTF_CSRF_ENABLED = False
TALISMAN_ENABLED = False