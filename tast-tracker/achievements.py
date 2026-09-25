"""
Определения всех достижений в приложении.
Каждое достижение — это код, название, описание и условие разблокировки,
проверяемое по текущей статистике (переданной как словарь stats).
"""

ACHIEVEMENTS = [
    {
        "code": "first_task",
        "icon": "🎯",
        "title": "Первый шаг",
        "description": "Выполни свою первую задачу",
        "check": lambda stats: stats["completed_tasks"] >= 1,
    },
    {
        "code": "ten_tasks",
        "icon": "🔥",
        "title": "Продуктивность",
        "description": "Выполни 10 задач",
        "check": lambda stats: stats["completed_tasks"] >= 10,
    },
    {
        "code": "fifty_tasks",
        "icon": "💪",
        "title": "Мастер задач",
        "description": "Выполни 50 задач",
        "check": lambda stats: stats["completed_tasks"] >= 50,
    },
    {
        "code": "first_good_sleep",
        "icon": "🌙",
        "title": "Здоровый сон",
        "description": "Запиши ночь сна 8+ часов",
        "check": lambda stats: stats["good_sleep_nights"] >= 1,
    },
    {
        "code": "week_good_sleep",
        "icon": "😴",
        "title": "Режим дня",
        "description": "Запиши 7 ночей сна по 8+ часов",
        "check": lambda stats: stats["good_sleep_nights"] >= 7,
    },
    {
        "code": "first_finance",
        "icon": "💰",
        "title": "Финансист",
        "description": "Добавь первую запись о доходе/расходе",
        "check": lambda stats: stats["finance_entries"] >= 1,
    },
    {
        "code": "hundred_points",
        "icon": "⭐",
        "title": "Сотня",
        "description": "Набери 100 очков",
        "check": lambda stats: stats["total_points"] >= 100,
    },
    {
        "code": "five_hundred_points",
        "icon": "🏆",
        "title": "Атлас в деле",
        "description": "Набери 500 очков",
        "check": lambda stats: stats["total_points"] >= 500,
    },
    {
        "code": "streak_3",
        "icon": "🔥",
        "title": "Разгон",
        "description": "Выполняй задачи 3 дня подряд",
        "check": lambda stats: stats["task_streak"] >= 3,
    },
    {
        "code": "streak_7",
        "icon": "⚡",
        "title": "Неделя без пропусков",
        "description": "Выполняй задачи 7 дней подряд",
        "check": lambda stats: stats["task_streak"] >= 7,
    },
    {
        "code": "streak_30",
        "icon": "🌟",
        "title": "Привычка сформирована",
        "description": "Выполняй задачи 30 дней подряд",
        "check": lambda stats: stats["task_streak"] >= 30,
    },
]