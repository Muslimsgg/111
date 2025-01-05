# utils/helpers.py

def parse_predefined_schedule(selected_option: str):
    """
    Парсинг предустановленных вариантов расписания.
    Возвращает тип расписания и соответствующие параметры.

    Примеры:
    - "Ежедневно в 12:00" -> ('cron', {'hour': 12, 'minute': 0})
    - "Каждые 12 часов" -> ('interval', {'hours': 12})
    - "Каждую минуту" -> ('interval', {'minutes': 1})
    """
    selected_option = selected_option.lower()
    if "ежедневно в" in selected_option:
        try:
            time_part = selected_option.split("ежедневно в")[-1].strip()
            hour, minute = map(int, time_part.split(":"))
            return ('cron', {'hour': hour, 'minute': minute})
        except Exception:
            return (None, None)
    elif "каждые" in selected_option and "часов" in selected_option:
        try:
            hours = int(selected_option.split("каждые")[-1].split("часов")[0].strip())
            return ('interval', {'hours': hours})
        except Exception:
            return (None, None)
    elif "каждую минуту" in selected_option:
        return ('interval', {'minutes': 1})
    else:
        return (None, None)
