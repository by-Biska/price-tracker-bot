# app/init_db.py
import asyncio
from database import engine
from models import Base

async def init_models():
    async with engine.begin() as conn:
        # Создаем все таблицы, описанные в моделях
        await conn.run_sync(Base.metadata.create_all)
    print("Таблицы успешно созданы в базе данных!")

if __name__ == "__main__":
    asyncio.run(init_models())