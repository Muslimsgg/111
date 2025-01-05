# Telegram Message Scheduler Bot

## Описание

Телеграм-бот для отправки сообщений в группу в различных форматах, сохранения шаблонов сообщений и автоматической отправки по расписанию.

## Возможности

- Отправка текстовых сообщений, сообщений с изображением и кнопками.
- Создание, просмотр, редактирование и удаление шаблонов сообщений.
- Настройка автоматической отправки сообщений по расписанию (ежедневно или каждые 12 часов).
- Административный доступ только для указанного пользователя.

## Установка



1. **Установите зависимости:**

    ```bash
    pip install -r requirements.txt
    ```

2. **Создайте файл `.env` в корне проекта и добавьте следующие переменные:**

    ```env
    BOT_TOKEN=ваш_токен_бота
    GROUP_ID=-123456789
    ADMIN_ID=ваш_user_id
    ```

    - **BOT_TOKEN:** Токен вашего Telegram-бота, полученный от [BotFather](https://t.me/BotFather).
    - **GROUP_ID:** ID группы, куда бот будет отправлять сообщения. Убедитесь, что бот добавлен в эту группу.
    - **ADMIN_ID:** Ваш Telegram ID для администрирования бота.



3. **Инициализируйте базу данных:**

    Выполните следующую команду для создания базы данных и необходимых таблиц:

    ```bash
    python
    ```

    В интерактивном режиме Python выполните:

    ```python
    from database import Base, engine
    Base.metadata.create_all(bind=engine)
    exit()
    ```

4. **Запустите бота:**

    ```bash
    python bot.py
    ```

## Использование

### Команды администратора

- `/start` — приветствие.
- `/add_template` — добавить новый шаблон.
- `/list_templates` — просмотреть все шаблоны.
- `/delete_template` — удалить шаблон.
- `/edit_template` — редактировать шаблон.
- `/schedule` — настроить расписание отправки сообщения.
- `/cancel_schedule шаблон` — отключить расписание для указанного шаблона.

### Примеры сценариев работы

#### Добавление нового шаблона

1. **Команда:** Администратор отправляет команду `/add_template`.
2. **Бот:** Запрашивает название шаблона.
3. **Администратор:** Вводит название шаблона, например, `Доброе утро`.
4. **Бот:** Запрашивает текст сообщения.
5. **Администратор:** Вводит текст, например, `Доброе утро! Желаю всем отличного дня!`.
6. **Бот:** Запрашивает изображение или вводит `нет` для пропуска.
7. **Администратор:** Отправляет изображение или пишет `нет`.
8. **Бот:** Запрашивает текст кнопки или вводит `нет` для пропуска.
9. **Администратор:** Вводит текст кнопки, например, `Подробнее` или пишет `нет`.
10. **Бот:** Если введён текст кнопки, запрашивает URL для кнопки.
11. **Администратор:** Вводит URL, например, `https://example.com`, или пишет `нет`.
12. **Бот:** Подтверждает сохранение шаблона: `Шаблон сохранён.`

#### Просмотр списка шаблонов

1. **Команда:** Администратор отправляет команду `/list_templates`.
2. **Бот:** Отображает список всех сохранённых шаблонов:
    ```
    Сохранённые шаблоны:
    - Доброе утро
    - Вечернее напоминание
    ```

#### Редактирование шаблона

1. **Команда:** Администратор отправляет команду `/edit_template`.
2. **Бот:** Запрашивает выбор шаблона для редактирования.
3. **Администратор:** Выбирает шаблон, например, `Доброе утро`.
4. **Бот:** Запрашивает выбор поля для редактирования:
    - Текст
    - Изображение
    - Кнопка
    - Отмена
5. **Администратор:** Выбирает, например, `Текст`.
6. **Бот:** Запрашивает новый текст сообщения.
7. **Администратор:** Вводит новый текст, например, `Доброе утро! Пусть ваш день будет продуктивным!`.
8. **Бот:** Подтверждает обновление: `Текст шаблона успешно обновлён.`

#### Удаление шаблона

1. **Команда:** Администратор отправляет команду `/delete_template`.
2. **Бот:** Запрашивает выбор шаблона для удаления.
3. **Администратор:** Выбирает шаблон, например, `Вечернее напоминание`.
4. **Бот:** Подтверждает удаление: `Шаблон 'Вечернее напоминание' удалён.`

#### Настройка расписания отправки сообщений

1. **Команда:** Администратор отправляет команду `/schedule`.
2. **Бот:** Запрашивает выбор шаблона для отправки.
3. **Администратор:** Выбирает шаблон, например, `Доброе утро`.
4. **Бот:** Предлагает выбрать расписание:
    - Ежедневно в 12:00
    - Каждые 12 часов
    - Отмена
    - Удалить таймер
    - Отправлять каждую минуту
5. **Администратор:** Выбирает, например, `Ежедневно в 12:00`.
6. **Бот:** Подтверждает настройку расписания: `Сообщение будет отправляться ежедневно в 12:00.`

#### Отмена расписания

1. **Команда:** Администратор отправляет команду `/cancel_schedule шаблон1`.
2. **Бот:** Подтверждает отключение расписания: `Расписание для шаблона 'шаблон1' отключено.`

## Структура проекта

