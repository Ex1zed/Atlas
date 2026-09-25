"""
Модуль для работы с базой данных MySQL.
Здесь собраны все функции, которые читают и пишут данные в базу —
интерфейс (main.py) ничего не знает про SQL, только вызывает эти функции.
"""

import mysql.connector
from datetime import date, timedelta

# ===== Настройки подключения к базе данных =====
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Alek20089583",
    "database": "atlas_db"  # если у тебя другое имя базы — поменяй здесь
}


def get_connection():
    """Создаёт новое подключение к базе данных."""
    return mysql.connector.connect(**DB_CONFIG)


def load_tasks_from_db():
    """Забирает все задачи из базы данных.

    Возвращает список кортежей вида (id, text, is_done, category, due_date).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, text, is_done, category, due_date FROM tasks")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def add_task_to_db(text, category, due_date):
    """Добавляет новую задачу в базу и возвращает её id.

    due_date передавай как строку "YYYY-MM-DD" или None, если без срока.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (text, is_done, category, due_date) VALUES (%s, %s, %s, %s)",
        (text, False, category, due_date)
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return new_id


def update_task_status(task_id, is_done):
    """Обновляет статус выполнения задачи в базе.

    Заодно фиксирует дату выполнения (для подсчёта стрика) —
    при отметке ставится сегодняшняя дата, при снятии галочки — очищается.
    """
    conn = get_connection()
    cursor = conn.cursor()
    completed_at = date.today() if is_done else None
    cursor.execute(
        "UPDATE tasks SET is_done = %s, completed_at = %s WHERE id = %s",
        (is_done, completed_at, task_id)
    )
    conn.commit()
    cursor.close()
    conn.close()


def delete_task_from_db(task_id):
    """Удаляет задачу из базы по id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    conn.commit()
    cursor.close()
    conn.close()


# ===== Очки =====

POINTS_PER_TASK = 10  # сколько очков даёт одна выполненная задача


def get_total_points():
    """Возвращает текущее количество очков."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT total_points FROM points WHERE id = 1")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else 0


def add_points(amount):
    """Прибавляет (или отнимает, если amount отрицательный) очки к общему счёту."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE points SET total_points = total_points + %s WHERE id = 1", (amount,))
    conn.commit()
    cursor.close()
    conn.close()


# ===== Сон =====

SLEEP_BONUS_POINTS = 15  # бонус за хороший сон
SLEEP_BONUS_THRESHOLD_HOURS = 8  # от скольки часов начинается бонус


def add_sleep_log(log_date, bedtime, wake_time, duration_hours):
    """Сохраняет запись о сне в базу."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sleep_logs (log_date, bedtime, wake_time, duration_hours) VALUES (%s, %s, %s, %s)",
        (log_date, bedtime, wake_time, duration_hours)
    )
    conn.commit()
    cursor.close()
    conn.close()


def load_sleep_logs(limit=10):
    """Возвращает последние записи о сне, самые новые сверху."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT log_date, bedtime, wake_time, duration_hours FROM sleep_logs "
        "ORDER BY log_date DESC LIMIT %s",
        (limit,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


# ===== Финансы =====

FINANCE_CATEGORIES = ["Еда", "Транспорт", "Развлечения", "Учёба", "Другое"]


def add_finance_entry(log_date, entry_type, category, amount, note=""):
    """Сохраняет запись о доходе или расходе."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO finance_logs (log_date, type, category, amount, note) VALUES (%s, %s, %s, %s, %s)",
        (log_date, entry_type, category, amount, note)
    )
    conn.commit()
    cursor.close()
    conn.close()


def load_finance_entries(limit=20):
    """Возвращает последние записи о финансах, самые новые сверху."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, log_date, type, category, amount, note FROM finance_logs "
        "ORDER BY log_date DESC, id DESC LIMIT %s",
        (limit,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_finance_balance():
    """Считает текущий баланс: сумма доходов минус сумма расходов."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT "
        "COALESCE(SUM(CASE WHEN type = 'Доход' THEN amount ELSE 0 END), 0), "
        "COALESCE(SUM(CASE WHEN type = 'Расход' THEN amount ELSE 0 END), 0) "
        "FROM finance_logs"
    )
    income_total, expense_total = cursor.fetchone()
    cursor.close()
    conn.close()
    return float(income_total), float(expense_total)


def delete_finance_entry(entry_id):
    """Удаляет запись о доходе/расходе по id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM finance_logs WHERE id = %s", (entry_id,))
    conn.commit()
    cursor.close()
    conn.close()


# ===== Статистика для графиков =====

def get_expenses_by_category():
    """Возвращает список (категория, сумма) только по расходам, для круговой диаграммы."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT category, SUM(amount) FROM finance_logs "
        "WHERE type = 'Расход' GROUP BY category ORDER BY SUM(amount) DESC"
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [(cat, float(total)) for cat, total in rows]


def get_sleep_last_n_days(n=7):
    """Возвращает средний сон по дням за последние n дней, отсортированные по возрастанию даты.

    Если за один день несколько записей — берётся их среднее, чтобы график
    показывал один столбец на день, а не накладывающиеся друг на друга бруски.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT log_date, AVG(duration_hours) FROM sleep_logs "
        "GROUP BY log_date ORDER BY log_date DESC LIMIT %s",
        (n,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return list(reversed(rows))  # разворачиваем, чтобы старые даты были слева на графике


def get_completed_tasks_by_category():
    """Возвращает список (категория, количество выполненных задач)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT category, COUNT(*) FROM tasks "
        "WHERE is_done = TRUE GROUP BY category ORDER BY COUNT(*) DESC"
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def bulk_add_finance_entries(entries):
    """Добавляет сразу много записей о финансах (используется при импорте из банка).

    entries — список кортежей (log_date, entry_type, category, amount, note).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO finance_logs (log_date, type, category, amount, note) VALUES (%s, %s, %s, %s, %s)",
        entries
    )
    conn.commit()
    cursor.close()
    conn.close()


# ===== Статистика для достижений =====

def get_completed_tasks_count():
    """Считает общее количество когда-либо выполненных задач."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE is_done = TRUE")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0]


def get_task_streak():
    """Считает текущий стрик — сколько дней подряд выполнялась хотя бы одна задача.

    Если сегодня ещё ничего не выполнено, стрик не сбрасывается сразу —
    считается от вчерашнего дня, чтобы не наказывать за то, что день ещё не закончился.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT completed_at FROM tasks WHERE completed_at IS NOT NULL")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    completed_dates = {row[0] for row in rows}
    if not completed_dates:
        return 0

    current = date.today()
    if current not in completed_dates:
        current -= timedelta(days=1)

    streak = 0
    while current in completed_dates:
        streak += 1
        current -= timedelta(days=1)

    return streak


def get_good_sleep_nights_count():
    """Считает количество ночей сна с длительностью 8+ часов."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM sleep_logs WHERE duration_hours >= %s",
        (SLEEP_BONUS_THRESHOLD_HOURS,)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0]


def get_finance_entries_count():
    """Считает общее количество финансовых записей."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM finance_logs")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0]


def get_all_stats():
    """Собирает всю статистику разом — используется для проверки достижений."""
    return {
        "completed_tasks": get_completed_tasks_count(),
        "good_sleep_nights": get_good_sleep_nights_count(),
        "finance_entries": get_finance_entries_count(),
        "total_points": get_total_points(),
        "task_streak": get_task_streak(),
    }


# ===== Достижения =====

def get_unlocked_achievement_codes():
    """Возвращает множество кодов уже разблокированных достижений."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT code FROM achievements_unlocked")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {row[0] for row in rows}


def unlock_achievement(code, unlocked_date):
    """Отмечает достижение как разблокированное. Игнорирует, если уже разблокировано."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT IGNORE INTO achievements_unlocked (code, unlocked_date) VALUES (%s, %s)",
        (code, unlocked_date)
    )
    conn.commit()
    cursor.close()
    conn.close()


# ===== Награды =====

def add_reward(title, cost):
    """Создаёт новую награду, которую можно будет обменять на очки."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO rewards (title, cost) VALUES (%s, %s)", (title, cost))
    conn.commit()
    cursor.close()
    conn.close()


def load_rewards():
    """Возвращает список всех наград: (id, title, cost)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, cost FROM rewards ORDER BY cost ASC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def delete_reward(reward_id):
    """Удаляет награду из списка (саму возможность её получить, не историю обменов)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rewards WHERE id = %s", (reward_id,))
    conn.commit()
    cursor.close()
    conn.close()


def redeem_reward(reward_id, title, cost, redeemed_date):
    """Списывает очки и записывает обмен награды в историю."""
    add_points(-cost)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO redeemed_rewards (reward_title, cost, redeemed_date) VALUES (%s, %s, %s)",
        (title, cost, redeemed_date)
    )
    conn.commit()
    cursor.close()
    conn.close()


def load_redeemed_rewards(limit=15):
    """Возвращает историю полученных наград, самые новые сверху."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT reward_title, cost, redeemed_date FROM redeemed_rewards "
        "ORDER BY redeemed_date DESC, id DESC LIMIT %s",
        (limit,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows