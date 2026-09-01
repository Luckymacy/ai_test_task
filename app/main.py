import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: Message):
    logger.info("User %s used /start", message.from_user.id)
    await message.answer("Привіт! Бот працює ✅")


@dp.message(Command("help"))
async def help_handler(message: Message):
    logger.info("User %s used /help", message.from_user.id)
    await message.answer("Доступні команди: /start, /help")


async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set")

    logger.info("Bot is starting")

    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())