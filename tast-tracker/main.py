import customtkinter as ctk

# Настройка внешнего вида
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Мой трекер задач")
app.geometry("450x500")

# Список для хранения задач в памяти (пока без сохранения в файл — это позже)
tasks = []


def add_task():
    """Добавляет новую задачу из поля ввода в список на экране."""
    text = task_entry.get().strip()  # получаем текст и убираем лишние пробелы
    if text == "":
        return  # если поле пустое — ничего не делаем

    # Создаём строку с задачей: чекбокс + текст
    task_var = ctk.BooleanVar(value=False)
    task_checkbox = ctk.CTkCheckBox(
        tasks_frame,
        text=text,
        variable=task_var,
        font=("Arial", 14)
    )
    task_checkbox.pack(anchor="w", pady=5, padx=10)

    tasks.append((task_checkbox, task_var))
    task_entry.delete(0, "end")  # очищаем поле ввода после добавления


def delete_completed():
    """Удаляет все отмеченные (выполненные) задачи из списка."""
    global tasks
    remaining = []
    for checkbox, var in tasks:
        if var.get():  # если задача отмечена — удаляем виджет
            checkbox.destroy()
        else:
            remaining.append((checkbox, var))
    tasks = remaining


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

# Нажатие Enter в поле ввода тоже добавляет задачу
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

app.mainloop()