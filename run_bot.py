import asyncio

from telegram.main import main
from telegram_db.db import init_db


async def runner():
    await init_db()
    await main()

if __name__ == "__main__":
    asyncio.run(runner())
