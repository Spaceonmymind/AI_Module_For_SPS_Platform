# ===============================
#   SPS AI Service — Dockerfile
# ===============================

# 1. Базовый образ
FROM python:3.12-slim

# 2. Настройки окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 3. Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    poppler-utils \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# 4. Создаём рабочую директорию
WORKDIR /app

# 5. Копируем зависимости и устанавливаем
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# 6. Копируем весь код проекта
COPY . /app

# 7. Открываем порт для FastAPI
EXPOSE 5005

# 8. Настраиваем Healthcheck
# Проверяет /health раз в 30 сек, ждёт 5 сек, допускает 3 неудачные попытки
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fs http://localhost:5005/health || exit 1

# 9. Точка входа — запуск сервиса с логами
CMD ["uvicorn", "ai_service:app", "--host", "0.0.0.0", "--port", "5005", "--log-level", "info"]
