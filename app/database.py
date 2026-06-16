# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import os

# Берем URL из docker-compose.yml
DATABASE_URL = os.getenv("DATABASE_URL")

# Создаем асинхронный движок
engine = create_async_engine(DATABASE_URL, echo=True)

# Фабрика асинхронных сессий
async_session = async_sessionmaker(engine, expire_on_commit=False)