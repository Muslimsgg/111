# handlers/templates.py

import os
import logging
from aiogram import types
from aiogram.dispatcher import FSMContext, Dispatcher
from aiogram.dispatcher.filters.state import State, StatesGroup
from sqlalchemy.orm import Session
from database import SessionLocal
from models.models import Template
from config import ADMIN_ID

logger = logging.getLogger(__name__)

class TemplateStates(StatesGroup):
    """Состояния для процесса добавления шаблона."""
    waiting_for_name = State()
    waiting_for_text = State()
    waiting_for_image = State()
    waiting_for_button_text = State()
    waiting_for_button_url = State()

class EditTemplateStates(StatesGroup):
    """Состояния для процесса редактирования шаблона."""
    waiting_for_template_selection = State()
    waiting_for_field_selection = State()
    waiting_for_new_value = State()
    waiting_for_new_button_url = State()

class DeleteTemplateStates(StatesGroup):
    """Состояния для процесса удаления шаблона."""
    waiting_for_template_selection = State()

# Функции для добавления шаблона

async def add_template(message: types.Message):
    """Начало процесса добавления нового шаблона."""
    if message.from_user.id != ADMIN_ID:
        await message.reply("У вас нет доступа к этому боту.")
        logger.warning(f"Пользователь с ID {message.from_user.id} попытался использовать /add_template без доступа.")
        return
    await message.reply("Введите название шаблона:")
    await TemplateStates.waiting_for_name.set()
    logger.info("Начат процесс добавления нового шаблона.")

async def template_name_received(message: types.Message, state: FSMContext):
    """Получение названия шаблона."""
    name = message.text.strip()
    with SessionLocal() as session:
        if session.query(Template).filter(Template.name == name).first():
            await message.reply("Шаблон с таким названием уже существует. Пожалуйста, выберите другое название.")
            logger.warning(f"Попытка добавить шаблон с существующим названием: '{name}'.")
            return
        await state.update_data(name=name)
    await message.reply("Введите текст сообщения:")
    await TemplateStates.waiting_for_text.set()
    logger.info(f"Название шаблона получено: '{name}'.")

async def template_text_received(message: types.Message, state: FSMContext):
    """Получение текста сообщения."""
    await state.update_data(text=message.text)
    await message.reply("Отправьте изображение (или напишите 'нет'):")
    await TemplateStates.waiting_for_image.set()
    logger.info("Текст шаблона получен.")

async def template_image_received(message: types.Message, state: FSMContext):
    """Получение изображения для шаблона."""
    data = await state.get_data()
    if message.text and message.text.lower() == 'нет':
        image_path = None
    elif message.photo:
        # Создание папки images, если не существует
        os.makedirs('images', exist_ok=True)
        # Получение наибольшего размера фото
        photo = message.photo[-1]
        image_path = f"images/{photo.file_unique_id}.jpg"
        await photo.download(destination_file=image_path)
        logger.info(f"Изображение шаблона сохранено по пути: {image_path}.")
    else:
        await message.reply("Пожалуйста, отправьте изображение или напишите 'нет'.")
        logger.warning("Некорректный ввод при запросе изображения.")
        return
    await state.update_data(image_path=image_path)
    await message.reply("Введите текст на кнопке (или напишите 'нет'):")
    await TemplateStates.waiting_for_button_text.set()

async def template_button_text_received(message: types.Message, state: FSMContext):
    """Получение текста кнопки."""
    if message.text.lower() == 'нет':
        button_text = None
        button_url = None
    else:
        button_text = message.text.strip()
        await state.update_data(button_text=button_text)
        await message.reply("Введите URL для кнопки:")
        await TemplateStates.waiting_for_button_url.set()
        logger.info(f"Текст кнопки получен: '{button_text}'.")
        return
    
    # Сохранение шаблона без кнопки
    data = await state.get_data()
    new_template = Template(
        name=data['name'],
        text=data['text'],
        image_path=data['image_path'],
        button_text=button_text,
        button_url=button_url
    )
    with SessionLocal() as session:
        session.add(new_template)
        session.commit()
        logger.info(f"Новый шаблон '{new_template.name}' сохранён без кнопки.")
    await message.reply("Шаблон сохранён.")
    await state.finish()

async def template_button_url_received(message: types.Message, state: FSMContext):
    """Получение URL для кнопки."""
    button_url = message.text.strip()
    data = await state.get_data()
    new_template = Template(
        name=data['name'],
        text=data['text'],
        image_path=data['image_path'],
        button_text=data.get('button_text'),
        button_url=button_url
    )
    with SessionLocal() as session:
        session.add(new_template)
        session.commit()
        logger.info(f"Новый шаблон '{new_template.name}' сохранён с кнопкой.")
    await message.reply("Шаблон сохранён.")
    await state.finish()

# Функции для просмотра шаблонов

async def list_templates(message: types.Message):
    """Вывод списка всех сохранённых шаблонов."""
    if message.from_user.id != ADMIN_ID:
        await message.reply("У вас нет доступа к этому боту.")
        logger.warning(f"Пользователь с ID {message.from_user.id} попытался использовать /list_templates без доступа.")
        return
    with SessionLocal() as session:
        templates = session.query(Template).all()
        if not templates:
            await message.reply("Нет сохранённых шаблонов.")
            logger.info("Список шаблонов пуст.")
            return
        response = "Сохранённые шаблоны:\n" + "\n".join(f"- {template.name}" for template in templates)
    await message.reply(response)
    logger.info("Выведен список сохранённых шаблонов.")

# Функции для удаления шаблона

async def delete_template_start(message: types.Message, state: FSMContext):
    """Начало процесса удаления шаблона."""
    if message.from_user.id != ADMIN_ID:
        await message.reply("У вас нет доступа к этому боту.")
        logger.warning(f"Пользователь с ID {message.from_user.id} попытался использовать /delete_template без доступа.")
        return
    with SessionLocal() as session:
        templates = session.query(Template).all()
        if not templates:
            await message.reply("Нет шаблонов для удаления.")
            logger.info("Нет шаблонов для удаления.")
            return
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for template in templates:
            keyboard.add(template.name)
    await message.reply("Выберите шаблон для удаления:", reply_markup=keyboard)
    await state.set_state(DeleteTemplateStates.waiting_for_template_selection)
    logger.info("Запрошено удаление шаблона. Ожидание выбора шаблона.")

async def delete_template_confirm(message: types.Message, state: FSMContext):
    """Подтверждение удаления шаблона."""
    template_name = message.text.strip()
    with SessionLocal() as session:
        template = session.query(Template).filter(Template.name == template_name).first()
        if not template:
            await message.reply("Шаблон не найден.")
            logger.warning(f"Шаблон '{template_name}' не найден для удаления.")
            await state.finish()
            return
        session.delete(template)
        session.commit()
        # Удаление изображения, если оно есть
        if template.image_path and os.path.exists(template.image_path):
            os.remove(template.image_path)
            logger.info(f"Изображение шаблона '{template_name}' удалено.")
    await message.reply(f"Шаблон '{template_name}' удалён.", reply_markup=types.ReplyKeyboardRemove())
    logger.info(f"Шаблон '{template_name}' успешно удалён.")
    await state.finish()

# Функции для редактирования шаблона

async def edit_template_start(message: types.Message, state: FSMContext):
    """Начало процесса редактирования шаблона."""
    if message.from_user.id != ADMIN_ID:
        await message.reply("У вас нет доступа к этому боту.")
        logger.warning(f"Пользователь с ID {message.from_user.id} попытался использовать /edit_template без доступа.")
        return
    with SessionLocal() as session:
        templates = session.query(Template).all()
        if not templates:
            await message.reply("Нет шаблонов для редактирования.")
            logger.info("Нет шаблонов для редактирования.")
            return
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for template in templates:
            keyboard.add(template.name)
    await message.reply("Выберите шаблон для редактирования:", reply_markup=keyboard)
    await EditTemplateStates.waiting_for_template_selection.set()
    logger.info("Запрошено редактирование шаблона. Ожидание выбора шаблона.")

async def edit_template_field_selection(message: types.Message, state: FSMContext):
    """Обработка выбора шаблона для редактирования."""
    template_name = message.text.strip()
    with SessionLocal() as session:
        template = session.query(Template).filter(Template.name == template_name).first()
        if not template:
            await message.reply("Шаблон не найден.")
            logger.warning(f"Шаблон '{template_name}' не найден для редактирования.")
            await state.finish()
            return
        template_id = template.id
    await state.update_data(template_id=template_id)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add("Текст", "Изображение", "Кнопка", "Отмена")
    await message.reply("Выберите поле для редактирования:", reply_markup=keyboard)
    await EditTemplateStates.waiting_for_field_selection.set()
    logger.info(f"Выбран шаблон '{template_name}' для редактирования. Ожидание выбора поля.")

async def edit_template_new_value(message: types.Message, state: FSMContext):
    """Обработка выбора поля для редактирования."""
    field = message.text.strip().lower()
    if field == "отмена":
        await message.reply("Редактирование шаблона отменено.", reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
        logger.info("Редактирование шаблона отменено пользователем.")
        return
    if field not in ["текст", "изображение", "кнопка"]:
        await message.reply("Пожалуйста, выберите корректное поле для редактирования.", reply_markup=types.ReplyKeyboardRemove())
        logger.warning(f"Некорректный выбор поля для редактирования: '{field}'.")
        await state.finish()
        return
    await state.update_data(field=field)
    if field == "кнопка":
        await message.reply("Введите новый текст для кнопки (или напишите 'нет'):", reply_markup=types.ReplyKeyboardRemove())
    elif field == "изображение":
        await message.reply("Отправьте новое изображение (или напишите 'нет'):", reply_markup=types.ReplyKeyboardRemove())
    else:  # текст
        await message.reply("Введите новый текст сообщения:", reply_markup=types.ReplyKeyboardRemove())
    await EditTemplateStates.waiting_for_new_value.set()
    logger.info(f"Поле для редактирования выбрано: '{field}'.")

async def edit_template_save_new_value(message: types.Message, state: FSMContext):
    """Сохранение нового значения для выбранного поля."""
    data = await state.get_data()
    template_id = data['template_id']
    field = data['field']
    with SessionLocal() as session:
        template = session.query(Template).filter(Template.id == template_id).first()
        if not template:
            await message.reply("Шаблон не найден.")
            logger.error(f"Шаблон с ID {template_id} не найден при попытке редактирования.")
            await state.finish()
            return
        if field == "текст":
            template.text = message.text.strip()
            await message.reply("Текст шаблона успешно обновлён.")
            logger.info(f"Текст шаблона ID {template_id} обновлён.")
        elif field == "изображение":
            if message.text and message.text.lower() == 'нет':
                # Удаление старого изображения, если оно есть
                if template.image_path and os.path.exists(template.image_path):
                    os.remove(template.image_path)
                    logger.info(f"Старое изображение шаблона ID {template_id} удалено.")
                template.image_path = None
                await message.reply("Изображение шаблона удалено.")
            elif message.photo:
                # Удаление старого изображения, если оно есть
                if template.image_path and os.path.exists(template.image_path):
                    os.remove(template.image_path)
                    logger.info(f"Старое изображение шаблона ID {template_id} удалено.")
                # Сохранение нового изображения
                os.makedirs('images', exist_ok=True)
                photo = message.photo[-1]
                image_path = f"images/{photo.file_unique_id}.jpg"
                await photo.download(destination_file=image_path)
                template.image_path = image_path
                await message.reply("Изображение шаблона успешно обновлено.")
                logger.info(f"Новое изображение шаблона ID {template_id} сохранено по пути: {image_path}.")
            else:
                await message.reply("Пожалуйста, отправьте изображение или напишите 'нет'.")
                logger.warning("Некорректный ввод при обновлении изображения.")
                return
        elif field == "кнопка":
            if message.text and message.text.lower() == 'нет':
                template.button_text = None
                template.button_url = None
                await message.reply("Кнопка шаблона удалена.")
                logger.info(f"Кнопка шаблона ID {template_id} удалена.")
            else:
                template.button_text = message.text.strip()
                await state.update_data(button_text=template.button_text)
                await message.reply("Введите новый URL для кнопки:")
                await EditTemplateStates.waiting_for_new_button_url.set()
                logger.info(f"Текст кнопки шаблона ID {template_id} обновлён: '{template.button_text}'.")
                return
        session.commit()
        logger.info(f"Шаблон ID {template_id} обновлён.")
    await state.finish()

async def edit_template_save_button_url(message: types.Message, state: FSMContext):
    """Сохранение нового URL для кнопки."""
    new_button_url = message.text.strip()
    data = await state.get_data()
    template_id = data['template_id']
    with SessionLocal() as session:
        template = session.query(Template).filter(Template.id == template_id).first()
        if not template:
            await message.reply("Шаблон не найден.")
            logger.error(f"Шаблон с ID {template_id} не найден при попытке обновления URL кнопки.")
            await state.finish()
            return
        template.button_url = new_button_url
        session.commit()
        logger.info(f"URL кнопки шаблона ID {template_id} обновлён: '{new_button_url}'.")
    await message.reply("URL кнопки шаблона успешно обновлён.")
    await state.finish()

def register_handlers_templates(dp: Dispatcher):
    """Регистрация обработчиков для управления шаблонами."""
    # Обработчики добавления шаблонов
    dp.register_message_handler(add_template, commands=['add_template'], state="*")
    dp.register_message_handler(template_name_received, state=TemplateStates.waiting_for_name)
    dp.register_message_handler(template_text_received, state=TemplateStates.waiting_for_text)
    dp.register_message_handler(template_image_received, content_types=['photo', 'text'], state=TemplateStates.waiting_for_image)
    dp.register_message_handler(template_button_text_received, state=TemplateStates.waiting_for_button_text)
    dp.register_message_handler(template_button_url_received, state=TemplateStates.waiting_for_button_url)
    
    # Обработчики просмотра шаблонов
    dp.register_message_handler(list_templates, commands=['list_templates'], state="*")
    
    # Обработчики удаления шаблонов
    dp.register_message_handler(delete_template_start, commands=['delete_template'], state="*")
    dp.register_message_handler(delete_template_confirm, state=DeleteTemplateStates.waiting_for_template_selection)
    
    # Обработчики редактирования шаблонов
    dp.register_message_handler(edit_template_start, commands=['edit_template'], state="*")
    dp.register_message_handler(edit_template_field_selection, state=EditTemplateStates.waiting_for_template_selection)
    dp.register_message_handler(edit_template_new_value, state=EditTemplateStates.waiting_for_field_selection)
    dp.register_message_handler(edit_template_save_new_value, state=EditTemplateStates.waiting_for_new_value)
    dp.register_message_handler(edit_template_save_button_url, state=EditTemplateStates.waiting_for_new_button_url)
