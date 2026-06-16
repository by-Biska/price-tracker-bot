import asyncio
import os
import httpx
import re
from bs4 import BeautifulSoup
from celery import Celery
from sqlalchemy import select, update

from aiogram import Bot

from database import async_session
from models import Product

celery = Celery('tasks', broker='redis://redis:6379/0')

# Настройка расписания Celery Beat (задача будет запускаться автоматически)
celery.conf.beat_schedule = {
    'check-prices-every-30-minutes': {
        'task': 'app.tasks.check_all_prices',
        'schedule': 1800.0,  # Время в секундах (30 минут). Для тестов можно поставить например 30.0
    },
}
celery.conf.timezone = 'UTC'

# Инициализируем бота. Токен автоматически подтянется из docker-compose
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=TELEGRAM_TOKEN)

def parse_price(html_content: str) -> float | None:
    """Синхронная функция для извлечения цены из HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    price_element = soup.find(id="productMainPrice")
    
    if price_element:
        price_text = price_element.get_text()
        
        cleaned_price = re.sub(r'[^\d]', '', price_text)
        if cleaned_price:
            return float(cleaned_price)
    return None

@celery.task(name="app.tasks.check_all_prices")
def check_all_prices():
    """Точка входа для Celery (синхронная обертка для асинхронного кода)"""
    return asyncio.run(run_price_checker())

async def run_price_checker():
    """Основная асинхронная логика обновления цен"""
    async with async_session() as session:
        # 1. Делаем JOIN, чтобы сразу вытащить товар вместе с telegram_id его владельца        query = select(Product, User.telegram_id).join(User, Product.user_id == User.id)
        query = select(Product, User.telegram_id).join(User, Product.user_id == User.id)
        result = await session.execute(query)

        rows = result.all()

        if not rows:
            print("В базе данных пока нет товаров для проверки.")
            return

        # Используем один клиент для всех запросов (эффективнее)
        async with httpx.AsyncClient(timeout=10.0) as client:
            for product in products:
                try:
                    # 2. Асинхронно скачиваем страницу
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                    response = await client.get(product.url, headers=headers)
                    
                    if response.status_code == 200:
                        # 3. Синхронно парсим цену
                        new_price = parse_price(response.text)
                        
                        if new_price and new_price != product.current_price:
                            old_price = product.current_price
                            
                            # Обновляем цену в БД
                            await session.execute(
                                update(Product)
                                .where(Product.id == product.id)
                                .values(current_price=new_price)
                            )
                            print(f"Цена для товара {product.id} изменилась: {old_price} -> {new_price}")
                            
                            # Проверяем, упала ли цена ниже целевой (target_price)
                            if new_price <= product.target_price:
                                message_text = (
                                    f"📉 **Цена снизилась до целевой!**\n\n"
                                    f"Товар: {product.title or product.url}\n"
                                    f"Старая цена: {old_price} руб.\n"
                                    f"Новая цена: **{new_price}** руб.\n"
                                    f"Твоя цель: {product.target_price} руб.\n\n"
                                    f"🔗 [Ссылка на товар]({product.url})"
                                )
                                
                                await bot.send_message(
                                    chat_id=telegram_id, 
                                    text=message_text, 
                                    parse_mode="Markdown",
                                    disable_web_page_preview=True
                                )
                
                except Exception as e:
                    print(f"Ошибка при парсинге {product.url}: {e}")
            
            await session.commit()

        # Закрываем сессию бота, чтобы не висели открытые коннекты
    await bot.session.close()