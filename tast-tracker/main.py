"""
Главный файл приложения "Атлас" — трекер задач.
Отвечает только за интерфейс: вся работа с базой данных вынесена в database.py
"""

import customtkinter as ctk
from database import (
    load_tasks_from_db,
    add_task_to_db,
    update_task_status,
    delete_task_from_db,
)

# ===== Настройка интерфейса =====
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Мой трекер задач")
app.geometry("450x500")

# tasks хранит виджеты на экране, привязанные к id задачи в базе: {task_id: (checkbox, var)}
tasks = {}


def render_task(task_id, text, is_done):
    """Создаёт на экране один чекбокс задачи, полученной из базы."""
    task_var = ctk.BooleanVar(value=bool(is_done))
    task_checkbox = ctk.CTkCheckBox(
        tasks_frame,
        text=text,
        variable=task_var,
        font=("Arial", 14),
        command=lambda: update_task_status(task_id, task_var.get())
    )
    task_checkbox.pack(anchor="w", pady=5, padx=10)
    tasks[task_id] = (task_checkbox, task_var)


def load_and_display_tasks():
    """Загружает задачи из базы и отображает их в окне."""
    for task_id, (checkbox, _) in tasks.items():
        checkbox.destroy()
    tasks.clear()

    for task_id, text, is_done in load_tasks_from_db():
        render_task(task_id, text, is_done)


def add_task():
    """Добавляет новую задачу: сохраняет в базу и сразу показывает на экране."""
    text = task_entry.get().strip()
    if text == "":
        return

    new_id = add_task_to_db(text)
    render_task(new_id, text, False)
    task_entry.delete(0, "end")


def delete_completed():
    """Удаляет все отмеченные задачи из базы и с экрана."""
    completed_ids = [task_id for task_id, (_, var) in tasks.items() if var.get()]
    for task_id in completed_ids:
        delete_task_from_db(task_id)
        checkbox, _ = tasks.pop(task_id)
        checkbox.destroy()


# Заголовок
title_label = ctk.CTkLabel(app, text="Мои задачи", font=("Arial", 22, "bold"))
title_label.pack(pady=(20, 10))

# Поле ввода новой задачи
input_frame = ctk.CTkFrame(app, fg_color="transparent")
input_frame.pack(pady=10, padx=20, fill="x")

task_entry = ctk.CTkEntry(input_frame, placeholder_text="Введи новую задачу...")
task_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

add_button = ctk.CTkButton(input_frame, text="Добавить", command=add_task, width=100)
add_button.pack(side="left")

task_entry.bind("<Return>", lambda event: add_task())

# Прокручиваемая область для списка задач
tasks_frame = ctk.CTkScrollableFrame(app, label_text="Список задач")
tasks_frame.pack(pady=10, padx=20, fill="both", expand=True)

# Кнопка удаления выполненных задач
clear_button = ctk.CTkButton(
    app,
    text="Удалить выполненные",
    command=delete_completed,
    fg_color="#8B3A3A",
    hover_color="#6B2A2A"
)
clear_button.pack(pady=(0, 20))

# При запуске сразу подгружаем задачи из базы (если есть с прошлого раза)
load_and_display_tasks()

app.mainloop()