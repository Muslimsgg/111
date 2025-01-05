# bot.py

import logging
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.executor import start_polling
from config import BOT_TOKEN
from database import engine
from models.models import Base
from handlers.admin import register_handlers_admin
from handlers.templates import register_handlers_templates
from handlers.timers import register_handlers_timers, scheduler
import asyncio

# Инициализация логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Инициализация хранилища для FSM
storage = MemoryStorage()

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=storage)

# Инициализация базы данных
Base.metadata.create_all(bind=engine)
logger.info("База данных инициализирована.")

# Регистрация обработчиков
register_handlers_admin(dp)
register_handlers_templates(dp)
register_handlers_timers(dp, bot, scheduler)

async def on_startup(dispatcher: Dispatcher):
    """
    Действия при запуске бота.
    """
    # Отправка тестового сообщения
    from utils.send_message import send_test_message
    await send_test_message(bot)
    logger.info("Тестовое сообщение отправлено при запуске.")

async def on_shutdown(dispatcher: Dispatcher):
    """
    Действия при остановке бота.
    """
    await bot.close()
    scheduler.shutdown(wait=False)
    logger.info("Бот успешно остановлен.")

if __name__ == '__main__':
    # Запуск бота
    start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
