"""
Модуль для работы с базой данных MySQL.
Здесь собраны все функции, которые читают и пишут данные в базу —
интерфейс (main.py) ничего не знает про SQL, только вызывает эти функции.
"""

import mysql.connector

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

    Возвращает список кортежей вида (id, text, is_done).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, text, is_done FROM tasks")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def add_task_to_db(text):
    """Добавляет новую задачу в базу и возвращает её id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (text, is_done) VALUES (%s, %s)", (text, False))
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return new_id


def update_task_status(task_id, is_done):
    """Обновляет статус выполнения задачи в базе."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET is_done = %s WHERE id = %s", (is_done, task_id))
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