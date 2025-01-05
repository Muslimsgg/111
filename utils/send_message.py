# utils/send_message.py

import logging
from aiogram import Bot
from aiogram.types import InputFile, InlineKeyboardMarkup, InlineKeyboardButton
from database import SessionLocal
from models.models import Template
from config import GROUP_ID

logger = logging.getLogger(__name__)

async def send_template(bot: Bot, template_id: int):
    """
    Отправка сообщения в группу на основе шаблона.
    """
    with SessionLocal() as session:
        template = session.query(Template).filter(Template.id == template_id).first()
        if not template:
            logger.error(f"Шаблон с ID {template_id} не найден.")
            return

    try:
        if template.image_path:
            photo = InputFile(template.image_path)
            if template.button_text and template.button_url:
                keyboard = InlineKeyboardMarkup()
                button = InlineKeyboardButton(text=template.button_text, url=template.button_url)
                keyboard.add(button)
                await bot.send_photo(chat_id=GROUP_ID, photo=photo, caption=template.text, reply_markup=keyboard)
            else:
                await bot.send_photo(chat_id=GROUP_ID, photo=photo, caption=template.text)
        else:
            if template.button_text and template.button_url:
                keyboard = InlineKeyboardMarkup()
                button = InlineKeyboardButton(text=template.button_text, url=template.button_url)
                keyboard.add(button)
                await bot.send_message(chat_id=GROUP_ID, text=template.text, reply_markup=keyboard)
            else:
                await bot.send_message(chat_id=GROUP_ID, text=template.text)
        logger.info(f"Сообщение по шаблону '{template.name}' успешно отправлено в группу.")
    except Exception as e:
        logger.error(f"Ошибка при отправке шаблона: {e}")

async def send_test_message(bot: Bot):
    """Отправка тестового сообщения для проверки работоспособности."""
    try:
        await bot.send_message(chat_id=GROUP_ID, text="Тестовое сообщение: Бот работает корректно!")
        logger.info("Тестовое сообщение успешно отправлено.")
    except Exception as e:
        logger.error(f"Ошибка при отправке тестового сообщения: {e}")
