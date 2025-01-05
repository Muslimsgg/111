# handlers/timers.py

import logging
from aiogram import types, Bot
from aiogram.dispatcher import FSMContext, Dispatcher
from aiogram.dispatcher.filters.state import State, StatesGroup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.base import JobLookupError
from database import SessionLocal
from models.models import Template
from config import ADMIN_ID
from utils.helpers import parse_predefined_schedule
from utils.send_message import send_template, send_test_message

logger = logging.getLogger(__name__)

class ScheduleStates(StatesGroup):
    waiting_for_template = State()
    waiting_for_schedule_selection = State()

scheduler = AsyncIOScheduler()
bot_instance: Bot = None

SCHEDULE_OPTIONS = [
    "Ежедневно в 12:00",
    "Каждые 12 часов",
    "Каждую минуту",
    "Удалить таймер",  
    "Отмена"
]

async def schedule_message(message: types.Message):
    """
    Начало процесса настройки расписания отправки сообщения.
    """
    logger.info("Вызвана команда /schedule")
    try:
        if message.from_user.id != ADMIN_ID:
            logger.warning(f"Пользователь с ID {message.from_user.id} попытался использовать /schedule без доступа.")
            await message.reply("У вас нет доступа к этому боту.")
            return

        with SessionLocal() as session:
            templates = session.query(Template).all()
            if not templates:
                await message.reply("Нет доступных шаблонов. Сначала добавьте шаблон.")
                logger.info("Нет доступных шаблонов для настройки расписания.")
                return

            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            for template in templates:
                keyboard.add(template.name)

        await message.reply("Выберите шаблон для отправки:", reply_markup=keyboard)
        await ScheduleStates.waiting_for_template.set()
        logger.info("Отправлен запрос на выбор шаблона для расписания.")
    except Exception as e:
        logger.error(f"Ошибка в обработчике /schedule: {e}")
        await message.reply("Произошла ошибка при обработке команды.")

async def schedule_template_selected(message: types.Message, state: FSMContext):
    """
    Обработка выбора шаблона для настройки расписания.
    """
    template_name = message.text.strip()
    logger.info(f"Выбран шаблон для расписания: '{template_name}'")
    try:
        with SessionLocal() as session:
            template = session.query(Template).filter(Template.name == template_name).first()
            if not template:
                await message.reply("Шаблон не найден.")
                logger.warning(f"Шаблон '{template_name}' не найден.")
                await state.finish()
                return
            template_id = template.id

        await state.update_data(template_id=template_id)

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for option in SCHEDULE_OPTIONS:
            keyboard.add(option)

        await message.reply(
            "Выберите расписание отправки сообщения:",
            reply_markup=keyboard
        )
        await ScheduleStates.waiting_for_schedule_selection.set()
        logger.info(f"Начат процесс настройки расписания для шаблона ID {template_id}.")
    except Exception as e:
        logger.error(f"Ошибка в обработчике выбора шаблона: {e}")
        await message.reply("Произошла ошибка при обработке выбора шаблона.")
        await state.finish()

async def schedule_selection_received(message: types.Message, state: FSMContext):
    """Получение и обработка выбора расписания, включая удаление таймера."""
    user_id = message.from_user.id
    selected_option = message.text
    logger.info(f"Пользователь {user_id} выбрал опцию: '{selected_option}'")
    try:
        data = await state.get_data()
        template_id = data.get('template_id')
        if template_id is None:
            await message.reply("Ошибка: ID шаблона не найден. Пожалуйста, начните процесс заново.", reply_markup=types.ReplyKeyboardRemove())
            logger.error(f"У пользователя {user_id} отсутствует template_id в state.")
            await state.finish()
            return

        if selected_option == "Отмена":
            await message.reply("Настройка отменена.", reply_markup=types.ReplyKeyboardRemove())
            await state.finish()
            logger.info(f"Пользователь {user_id} отменил настройку.")
            return

        if selected_option == "Удалить таймер":
            job_id = f"template_{template_id}"
            try:
                scheduler.remove_job(job_id)
                await message.reply(f"Таймер для шаблона ID {template_id} удален.", reply_markup=types.ReplyKeyboardRemove())
                logger.info(f"Пользователь {user_id} удалил таймер для шаблона ID {template_id}.")
            except JobLookupError:
                await message.reply(f"Таймер для шаблона ID {template_id} не установлен.", reply_markup=types.ReplyKeyboardRemove())
                logger.info(f"Пользователь {user_id} попытался удалить несуществующий таймер для шаблона ID {template_id}.")
            except Exception as e: # Перехватываем ошибки при удалении таймера
                logger.exception(f"Ошибка при удалении таймера у пользователя {user_id}: {e}")
                await message.reply("Произошла ошибка при удалении таймера.", reply_markup=types.ReplyKeyboardRemove())
            await state.finish()
            return

        schedule_type, schedule_params = parse_predefined_schedule(selected_option)
        if not schedule_type:
            logger.warning(f"Пользователь {user_id}: Неверный выбранный вариант расписания: '{selected_option}'")
            await message.reply("Неверный выбор расписания. Попробуйте снова.", reply_markup=types.ReplyKeyboardRemove())
            return

        job_id = f"template_{template_id}"
        try:
            scheduler.remove_job(job_id)
            logger.info(f"Удалена существующая задача с ID {job_id} перед созданием новой.")
        except JobLookupError:
            logger.info(f"Задача с ID {job_id} не найдена. Создаётся новая.")
        except Exception as e: # Перехватываем ошибки при удалении существующей задачи
            logger.exception(f"Ошибка при удалении существующей задачи у пользователя {user_id}: {e}")
            await message.reply("Произошла ошибка при обработке расписания.", reply_markup=types.ReplyKeyboardRemove())
            await state.finish()
            return

        if schedule_type == 'cron':
            try: # Перехватываем ошибки при создании cron задачи
                trigger = CronTrigger(**schedule_params)
                scheduler.add_job(send_template, trigger, args=[bot_instance, template_id], id=job_id, replace_existing=True)
                time_str = f"{schedule_params['hour']:02d}:{schedule_params['minute']:02d}"
                await message.reply(f"Сообщение будет отправляться ежедневно в {time_str}.", reply_markup=types.ReplyKeyboardRemove())
                logger.info(f"Пользователь {user_id}: Добавлена задача cron для шаблона ID {template_id} с расписанием ежедневно в {time_str}.")
            except Exception as e:
                logger.exception(f"Ошибка при создании cron задачи у пользователя {user_id}: {e}")
                await message.reply("Произошла ошибка при настройке расписания.", reply_markup=types.ReplyKeyboardRemove())
                await state.finish()
                return

        elif schedule_type == 'interval':
            try: # Перехватываем ошибки при создании interval задачи
                trigger = IntervalTrigger(**schedule_params)
                scheduler.add_job(send_template, trigger, args=[bot_instance, template_id], id=job_id, replace_existing=True)
                if 'hours' in schedule_params:
                    await message.reply(f"Сообщение будет отправляться каждые {schedule_params['hours']} часов.", reply_markup=types.ReplyKeyboardRemove())
                    logger.info(f"Пользователь {user_id}: Добавлена задача interval для шаблона ID {template_id} с расписанием каждые {schedule_params['hours']} часов.")
                elif 'minutes' in schedule_params:
                    await message.reply(f"Сообщение будет отправляться каждые {schedule_params['minutes']} минут.", reply_markup=types.ReplyKeyboardRemove())
                    logger.info(f"Пользователь {user_id}: Добавлена задача interval для шаблона ID {template_id} с расписанием каждые {schedule_params['minutes']} минут.")
            except Exception as e:
                logger.exception(f"Ошибка при создании interval задачи у пользователя {user_id}: {e}")
                await message.reply("Произошла ошибка при настройке расписания.", reply_markup=types.ReplyKeyboardRemove())
                await state.finish()
                return

        else:
            logger.error(f"Пользователь {user_id}: Неизвестный тип расписания.")
            await message.reply("Произошла ошибка при настройке расписания.", reply_markup=types.ReplyKeyboardRemove())
            return

        await state.finish()
    except Exception as e: # Самый внешний except, перехватывает все остальные ошибки
        logger.exception(f"Общая ошибка в обработчике выбора расписания у пользователя {user_id}: {e}")
        await message.reply("Произошла общая ошибка при обработке расписания.", reply_markup=types.ReplyKeyboardRemove())
        await state.finish()

async def cancel_schedule(message: types.Message):
    """
    Отключение расписания для шаблона.
    """
    logger.info("Вызвана команда /cancel_schedule")
    try:
        if message.from_user.id != ADMIN_ID:
            logger.warning(f"Пользователь с ID {message.from_user.id} попытался использовать /cancel_schedule без доступа.")
            await message.reply("У вас нет доступа к этому боту.")
            return

        args = message.get_args()
        if not args:
            logger.warning("Команда /cancel_schedule вызвана без аргументов.")
            await message.reply("Пожалуйста, укажите название шаблона. Пример: /cancel_schedule шаблон1")
            return

        template_name = args.strip()
        with SessionLocal() as session:
            template = session.query(Template).filter(Template.name == template_name).first()
            if not template:
                logger.warning(f"Шаблон '{template_name}' не найден для отключения расписания.")
                await message.reply("Шаблон не найден.")
                return
            job_id = f"template_{template.id}"
            try:
                scheduler.remove_job(job_id)
                logger.info(f"Расписание для шаблона ID {template.id} отключено.")
                await message.reply(f"Расписание для шаблона '{template_name}' отключено.")
            except JobLookupError:
                logger.warning(f"Расписание для шаблона ID {template.id} не найдено.")
                await message.reply(f"Расписание для шаблона '{template_name}' не найдено.")
    except Exception as e:
        logger.error(f"Ошибка в обработчике /cancel_schedule: {e}")
        await message.reply("Произошла ошибка при обработке команды.")

def register_handlers_timers(dp: Dispatcher, bot: Bot, scheduler_instance: AsyncIOScheduler):
    """
    Регистрация обработчиков для управления расписанием.
    """
    global bot_instance
    bot_instance = bot  # Сохранение экземпляра бота в глобальной переменной
    logger.info("Экземпляр бота сохранён в bot_instance.")

    dp.register_message_handler(schedule_message, commands=['schedule'], state="*")
    dp.register_message_handler(schedule_template_selected, state=ScheduleStates.waiting_for_template)
    dp.register_message_handler(schedule_selection_received, state=ScheduleStates.waiting_for_schedule_selection)
    dp.register_message_handler(cancel_schedule, commands=['cancel_schedule'], state="*")
    logger.info("Обработчики команд /schedule и /cancel_schedule зарегистрированы.")

    # Добавление тестовой команды для отправки тестового сообщения
    async def test_schedule(message: types.Message):
        """
        Команда /test_schedule для проверки работы расписания.
        """
        if message.from_user.id != ADMIN_ID:
            await message.reply("У вас нет доступа к этому боту.")
            logger.warning(f"Пользователь с ID {message.from_user.id} попытался использовать /test_schedule без доступа.")
            return
        await send_test_message(bot)
        await message.reply("Тестовое сообщение отправлено.")
        logger.info("Тестовое сообщение отправлено по команде /test_schedule.")

    dp.register_message_handler(test_schedule, commands=['test_schedule'], state="*")
    logger.info("Обработчик команды /test_schedule зарегистрирован.")

    # Запуск планировщика
    scheduler_instance.start()
    logger.info("Планировщик APScheduler запущен.")
