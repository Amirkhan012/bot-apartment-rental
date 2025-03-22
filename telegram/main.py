from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from telegram.config import TELEGRAM_TOKEN
from telegram.handlers import (
    basic, photos, address, start, publications, rentals_search_custom)


bot = Bot(token=TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


dp.include_router(start.router)
dp.include_router(basic.router)
dp.include_router(photos.router)
dp.include_router(address.router)
dp.include_router(publications.router)
dp.include_router(rentals_search_custom.router)


async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    print("Bot is running...")
    await dp.start_polling(bot, skip_updates=True)
