import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, delete

from database import async_session
import models
from parser import get_product_info

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# 1. Определяем состояния
class TrackProduct(StatesGroup):
    waiting_for_price = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    async with async_session() as session:
        query = select(models.User).where(models.User.telegram_id == message.from_user.id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            new_user = models.User(
                telegram_id=message.from_user.id,
                username=message.from_user.username
            )
            session.add(new_user)
            await session.commit()
    
    await message.answer(f"Привет, {message.from_user.first_name}! Пришли ссылку на товар.")

# 2. Обработчик ссылок (переводит бота в состояние ожидания цены)
@dp.message(lambda message: message.text and message.text.startswith("http"))
async def handle_link(message: types.Message, state: FSMContext):
    await message.answer("🔍 Ищу товар, подожди секунду...")
    
    product_data = await get_product_info(message.text)
    
    if product_data:
        # Сохраняем данные во временное хранилище FSM
        await state.update_data(
            url=message.text,
            title=product_data['title'],
            current_price=product_data['price']
        )
        # Устанавливаем состояние ожидания цены
        await state.set_state(TrackProduct.waiting_for_price)
        
        await message.answer(
            f"✅ **Нашел товар:**\n{product_data['title']}\n\n"
            f"💰 **Текущая цена:** {product_data['price']} руб.\n\n"
            "Напиши целевую цену (просто число), при которой мне тебя оповестить:",
            parse_mode="Markdown"
        )
    else:
        await message.answer("❌ Не удалось получить данные о товаре.")

# 3. Обработчик цены (сработает только после ссылки)
@dp.message(TrackProduct.waiting_for_price)
async def handle_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи только число (например, 9500).")
        return

    target_price = float(message.text)
    user_data = await state.get_data()
    
    async with async_session() as session:
        # 1. Сначала найдем внутреннего ID пользователя в нашей БД
        user_query = select(models.User).where(models.User.telegram_id == message.from_user.id)
        user_result = await session.execute(user_query)
        db_user = user_result.scalar_one()

        # 2. Создаем запись о товаре
        new_product = models.Product(
            url=user_data['url'],
            title=user_data['title'],
            current_price=user_data['current_price'],
            target_price=target_price,
            user_id=db_user.id  # Привязываем товар к пользователю
        )
        
        session.add(new_product)
        await session.commit()
    
    await message.answer(
        f"🚀 Принято! Я сообщу, когда цена на **{user_data['title']}** "
        f"упадет до {target_price} руб.\n\n"
        f"Текущая цена: {user_data['current_price']} руб.",
        parse_mode="Markdown"
    )
    # Сбрасываем состояние, чтобы бот снова мог принимать ссылки
    await state.clear()

@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    async with async_session() as session:
        # Ищем пользователя и его товары через JOIN
        query = (
            select(models.Product)
            .join(models.User)
            .where(models.User.telegram_id == message.from_user.id)
        )
        result = await session.execute(query)
        products = result.scalars().all()

        if not products:
            await message.answer("Ты пока не отслеживаешь ни одного товара. Пришли мне ссылку!")
            return

        response_text = "📋 **Твои отслеживаемые товары:**\n\n"
        for index, product in enumerate(products, 1):
            # Обрезаем длинный тайтл, чтобы сообщение не ломалось
            title = product.title[:40] + "..." if product.title and len(product.title) > 40 else product.title or "Товар"
            response_text += (
                f"{index}. **{title}**\n"
                f"💰 Текущая: {product.current_price} руб. | 🎯 Цель: {product.target_price} руб.\n"
                f"🔗 Ссылка: [Перейти]({product.url})\n"
                f"❌ Удалить: `/delete_{product.id}`\n\n"
            )
        
        await message.answer(response_text, parse_mode="Markdown", disable_web_page_preview=True)

# 3.6. Удаление товара из базы по ID
@dp.message(lambda message: message.text and message.text.startswith("/delete_"))
async def handle_delete_product(message: types.Message):
    try:
        product_id = int(message.text.split("_")[1])
    except (IndexError, ValueError):
        await message.answer("Неверный формат команды удаления.")
        return

    async with async_session() as session:
        # Проверяем, принадлежит ли товар этому пользователю (защита)
        query = (
            select(models.Product)
            .join(models.User)
            .where(models.Product.id == product_id, models.User.telegram_id == message.from_user.id)
        )
        result = await session.execute(query)
        product = result.scalar_one_or_none()

        if not product:
            await message.answer("Товар не найден или у тебя нет прав на его удаление.")
            return

        # Удаляем
        await session.execute(delete(models.Product).where(models.Product.id == product_id))
        await session.commit()
    
    await message.answer("✅ Товар успешно удален из отслеживания!")

# 4. Обработчик для любого другого текста (мусор)
@dp.message()
async def handle_garbage(message: types.Message):
    await message.answer("Я тебя не совсем понял. Пришли ссылку на товар (начинается с http).")

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())