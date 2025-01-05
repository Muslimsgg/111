# handlers/admin.py

from aiogram import types
from aiogram.dispatcher import Dispatcher
from config import ADMIN_ID
import logging

logger = logging.getLogger(__name__)

async def send_welcome(message: types.Message):
    """
    Обработчик команды /start.
    Приветствует администратора.
    """
    if message.from_user.id != ADMIN_ID:
        await message.reply("У вас нет доступа к этому боту.")
        logger.warning(f"Пользователь с ID {message.from_user.id} попытался использовать /start без доступа.")
        return
    await message.reply("Добро пожаловать! Я готов к работе.")
    logger.info(f"Администратор с ID {message.from_user.id} запустил бота.")

def register_handlers_admin(dp: Dispatcher):
    """
    Регистрация обработчиков административных команд.
    """
    dp.register_message_handler(send_welcome, commands=['start'], state="*")
