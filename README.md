# Telegram Price Tracker Bot

Асинхронный Telegram-бот для отслеживания цен на товары. Вы отправляете боту ссылку на товар и целевую цену, а фоновый воркер проверяет её каждые 30 минут и уведомляет вас в случае падения.

## Технологический стек
- Backend: Python 3.12, Aiogram 3.x
- Database: PostgreSQL + SQLAlchemy 2.0 (Asyncpg)
- Task Queue: Celery + Redis
- Parsing: BeautifulSoup4 + HTTPX
- DevOps: Docker + Docker Compose

## Локальный запуск

1. Подготовка окружения
Создайте файл .env в корневой директории проекта и добавьте ваш токен:
TELEGRAM_TOKEN=your_bot_token_here

2. Запуск контейнеров
Запустите всю архитектуру одной командой через Docker Compose:
docker compose up --build -d

3. Инициализация базы данных
При первом запуске необходимо создать таблицы в PostgreSQL:
docker compose exec bot python app/init_db.py

## Команды бота
- /start — Регистрация пользователя и приветствие.
- /list — Просмотр всех отслеживаемых товаров, текущих и целевых цен.
- /delete_[ID] — Удаление товара из отслеживания.