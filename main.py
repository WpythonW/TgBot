import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN
from handlers_start import register_handlers_start
from handlers_user_input import register_handlers_user_input
from database import init_db, close_db

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

async def main():
    await init_db()  # Инициализируем соединение с базой данных
    register_handlers_start(dp)
    register_handlers_user_input(dp)
    logging.info("Handlers registered successfully")
    try:
        await dp.start_polling(bot)
    finally:
        await close_db()  # Закрываем соединение с базой данных

if __name__ == '__main__':
    asyncio.run(main())