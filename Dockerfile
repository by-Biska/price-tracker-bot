# Используем актуальный Python 3.12
FROM python:3.12-slim

# Устанавливаем системные зависимости для работы с БД и сетью
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код проекта
COPY . .

# По умолчанию ничего не запускаем, команды будут в docker-compose