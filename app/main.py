import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
from dotenv import load_dotenv
from sqlalchemy import text

from app.database import engine


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

dp = Dispatcher()

keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Help")]
    ],
    resize_keyboard=True
)


@dp.message(CommandStart())
async def start_handler(message: Message):
    logger.info("User %s used /start", message.from_user.id)

    await message.answer(
        "Привіт! Бот працює ✅\n\n"
        "Доступні команди:\n"
        "/start — запустити бота\n"
        "/help — допомога\n"
        "/add_income — додати тестове замовлення",
        reply_markup=keyboard
    )


@dp.message(Command("help"))
async def help_handler(message: Message):
    logger.info("User %s used /help", message.from_user.id)

    await message.answer(
        "Доступні команди:\n"
        "/start — запустити бота\n"
        "/help — допомога\n"
        "/add_income — додати тестове замовлення"
    )


@dp.message(lambda message: message.text == "Help")
async def help_button_handler(message: Message):
    logger.info("User %s pressed Help button", message.from_user.id)

    await message.answer(
        "Доступні команди:\n"
        "/start — запустити бота\n"
        "/help — допомога\n"
        "/add_income — додати тестове замовлення"
    )


@dp.message(Command("add_income"))
async def add_income_handler(message: Message):
    logger.info("User %s used /add_income", message.from_user.id)

    async with engine.begin() as connection:
        order_result = await connection.execute(
            text(
                """
                INSERT INTO orders (
                    client_name,
                    rental_date,
                    return_date,
                    status,
                    total_amount
                )
                VALUES (
                    :client_name,
                    CURRENT_DATE,
                    CURRENT_DATE + INTERVAL '2 days',
                    'paid',
                    1600
                )
                RETURNING id
                """
            ),
            {
                "client_name": message.from_user.full_name or "Telegram client"
            }
        )

        order_id = order_result.scalar_one()

        await connection.execute(
            text(
                """
                INSERT INTO order_items (order_id, item_name, price)
                VALUES
                    (:order_id, 'Dress', 1000),
                    (:order_id, 'Shoes', 400),
                    (:order_id, 'Accessories', 200)
                """
            ),
            {"order_id": order_id}
        )

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
                    1600,
                    'rental',
                    'Dress 1000 UAH, Shoes 400 UAH, Accessories 200 UAH'
                )
                """
            ),
            {"order_id": order_id}
        )

    await message.answer(
        f"Замовлення #{order_id} додано ✅\n"
        "Сукня — 1000 грн\n"
        "Взуття — 400 грн\n"
        "Аксесуари — 200 грн\n"
        "Загальна сума — 1600 грн"
    )


async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set")

    logger.info("Bot is starting")

    bot = Bot(token=BOT_TOKEN)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())