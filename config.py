# config.py

import os
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()

# Инициализация переменных
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID")) if os.getenv("GROUP_ID") else None
ADMIN_ID = int(os.getenv("ADMIN_ID")) if os.getenv("ADMIN_ID") else None

# Проверка переменных
if not BOT_TOKEN or not GROUP_ID or not ADMIN_ID:
    raise ValueError("Ошибка: Проверь файл .env — переменные BOT_TOKEN, GROUP_ID или ADMIN_ID отсутствуют.")
