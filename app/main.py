import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from dotenv import load_dotenv
from sqlalchemy import text

from app.database import engine


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set")


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "Привіт! Бот працює ✅\n\n"
        "Доступні команди:\n"
        "/help — допомога\n"
        "/add_income — додати дохід"
    )


@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "Для додавання доходу використай команду:\n\n"
        "/add_income СУМА КАТЕГОРІЯ ОПИС\n\n"
        "Наприклад:\n"
        "/add_income 1800 rental Оренда сукні"
    )


@dp.message(Command("add_income"))
async def add_income_handler(message: Message):
    parts = message.text.split(maxsplit=3)

    if len(parts) < 4:
        await message.answer(
            "Неправильний формат ❌\n\n"
            "Використай:\n"
            "/add_income СУМА КАТЕГОРІЯ ОПИС\n\n"
            "Наприклад:\n"
            "/add_income 1800 rental Оренда сукні"
        )
        return

    amount_text = parts[1]
    category = parts[2].strip()
    description = parts[3].strip()

    try:
        amount = float(amount_text.replace(",", "."))
    except ValueError:
        await message.answer(
            "Сума повинна бути числом.\n"
            "Наприклад:\n"
            "/add_income 1800 rental Оренда сукні"
        )
        return

    if amount <= 0:
        await message.answer("Сума повинна бути більшою за 0.")
        return

    if not category or not description:
        await message.answer(
            "Категорія та опис не можуть бути порожніми."
        )
        return

    client_name = (
        message.from_user.full_name
        if message.from_user
        else "Telegram client"
    )

    try:
        async with engine.begin() as connection:
            order_result = await connection.execute(
                text(
                    """
                    INSERT INTO orders (
                        client_name,
                        status,
                        total_amount
                    )
                    VALUES (
                        :client_name,
                        'paid',
                        :total_amount
                    )
                    RETURNING id
                    """
                ),
                {
                    "client_name": client_name,
                    "total_amount": amount,
                },
            )

            order_id = order_result.scalar_one()

            await connection.execute(
                text(
                    """
                    INSERT INTO transactions (
                        order_id,
                        type,
                        amount,
                        category,
                        description
                    )
                    VALUES (
                        :order_id,
                        'income',
                        :amount,
                        :category,
                        :description
                    )
                    """
                ),
                {
                    "order_id": order_id,
                    "amount": amount,
                    "category": category,
                    "description": description,
                },
            )

        await message.answer(
            "Дохід успішно додано ✅\n\n"
            f"Сума: {amount:.2f} грн\n"
            f"Категорія: {category}\n"
            f"Опис: {description}"
        )

        logging.info(
            "Income added: amount=%s category=%s order_id=%s",
            amount,
            category,
            order_id,
        )

    except Exception:
        logging.exception("Failed to add income")

        await message.answer(
            "Не вдалося додати операцію ❌"
        )


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    logging.info("Bot started")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())