"""
Главный файл приложения "Атлас" — единый дашборд с вкладками:
Задачи, Сон, Финансы, Достижения. Вся работа с базой данных вынесена
в database.py, парсинг банковской выписки — в bank_import.py,
список достижений — в achievements.py.
"""

import customtkinter as ctk
from datetime import datetime, date, timedelta
from tkinter import messagebox, filedialog
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from database import (
    load_tasks_from_db,
    add_task_to_db,
    update_task_status,
    delete_task_from_db,
    get_total_points,
    add_points,
    POINTS_PER_TASK,
    add_sleep_log,
    load_sleep_logs,
    SLEEP_BONUS_POINTS,
    SLEEP_BONUS_THRESHOLD_HOURS,
    add_finance_entry,
    load_finance_entries,
    get_finance_balance,
    delete_finance_entry,
    FINANCE_CATEGORIES,
    get_expenses_by_category,
    get_sleep_last_n_days,
    get_completed_tasks_by_category,
    bulk_add_finance_entries,
    get_all_stats,
    get_unlocked_achievement_codes,
    unlock_achievement,
    add_reward,
    load_rewards,
    delete_reward,
    redeem_reward,
    load_redeemed_rewards,
    get_task_streak,
)
from bank_import import parse_bank_csv
from achievements import ACHIEVEMENTS

CATEGORIES = ["Работа", "Учёба", "Спорт", "Питание"]

# ===== Настройка интерфейса =====
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Атлас")
app.geometry("950x720")

tasks = {}  # {task_id: (checkbox, var)}


def create_dark_figure(figsize=(4, 3)):
    """Создаёт matplotlib-фигуру, оформленную под тёмную тему приложения."""
    fig = Figure(figsize=figsize, dpi=100)
    fig.patch.set_facecolor("#2b2b2b")
    ax = fig.add_subplot(111)
    ax.set_facecolor("#2b2b2b")
    ax.tick_params(colors="white", labelsize=8)
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.title.set_color("white")
    for spine in ax.spines.values():
        spine.set_color("#555555")
    return fig, ax


def parse_time(time_text):
    """Превращает строку 'ЧЧ:ММ' во время. Возвращает None, если формат неверный."""
    try:
        return datetime.strptime(time_text.strip(), "%H:%M").time()
    except ValueError:
        return None


# ===== Верхняя панель: заголовок и очки (видны всегда, вне вкладок) =====
header_frame = ctk.CTkFrame(app, fg_color="transparent")
header_frame.pack(pady=(15, 5), padx=20, fill="x")

app_title_label = ctk.CTkLabel(header_frame, text="🗿 Атлас", font=("Arial", 24, "bold"))
app_title_label.pack(side="left")

points_label = ctk.CTkLabel(header_frame, text="⭐ Очки: 0", font=("Arial", 16), text_color="#FFD700")
points_label.pack(side="right", padx=(15, 0))

streak_label = ctk.CTkLabel(header_frame, text="🔥 Стрик: 0 дней", font=("Arial", 16), text_color="#FF8C42")
streak_label.pack(side="right")


def refresh_streak_label():
    """Обновляет надпись со стриком выполнения задач в шапке приложения."""
    streak = get_task_streak()
    streak_label.configure(text=f"🔥 Стрик: {streak} {'день' if streak == 1 else 'дней'}")


def refresh_points_label():
    """Обновляет надпись с текущим количеством очков в шапке приложения,
    а заодно список наград — доступность кнопки 'Обменять' зависит от очков."""
    points_label.configure(text=f"⭐ Очки: {get_total_points()}")
    try:
        refresh_rewards_list()
    except NameError:
        pass  # вкладка наград ещё не создана (первый вызов при старте файла)


# ===== Достижения: проверка условий (используется во всех вкладках) =====

def check_achievements():
    """Проверяет условия всех достижений, разблокирует новые и обновляет их вкладку."""
    stats = get_all_stats()
    unlocked_codes = get_unlocked_achievement_codes()
    newly_unlocked = []

    for achievement in ACHIEVEMENTS:
        if achievement["code"] in unlocked_codes:
            continue
        if achievement["check"](stats):
            unlock_achievement(achievement["code"], date.today())
            newly_unlocked.append(achievement)

    for achievement in newly_unlocked:
        messagebox.showinfo(
            "🏆 Новое достижение!",
            f"{achievement['icon']} {achievement['title']}\n{achievement['description']}"
        )

    if newly_unlocked:
        refresh_achievements_list()


# ===== Вкладки =====
tabview = ctk.CTkTabview(app, width=900, height=630)
tabview.pack(padx=20, pady=(5, 15), fill="both", expand=True)

tab_tasks = tabview.add("📋 Задачи")
tab_sleep = tabview.add("🌙 Сон")
tab_finance = tabview.add("💰 Финансы")
tab_rewards = tabview.add("🎁 Награды")
tab_achievements = tabview.add("🏆 Достижения")


# =====================================================================
# ВКЛАДКА: ЗАДАЧИ
# =====================================================================

def render_task(task_id, text, is_done, category, due_date):
    """Создаёт на экране один чекбокс задачи, полученной из базы."""
    extra_info = f"[{category}]"
    is_overdue = False
    if due_date is not None:
        extra_info += f" до {due_date.strftime('%d.%m.%Y')}"
        is_overdue = (due_date < date.today()) and not is_done
    display_text = f"{text}  {extra_info}"

    task_var = ctk.BooleanVar(value=bool(is_done))
    text_color = "#FF6B6B" if is_overdue else "white"
    task_checkbox = ctk.CTkCheckBox(
        tasks_frame,
        text=display_text,
        variable=task_var,
        font=("Arial", 14),
        text_color=text_color,
        command=lambda: on_task_toggled(task_id, task_var)
    )
    task_checkbox.pack(anchor="w", pady=5, padx=10)
    tasks[task_id] = (task_checkbox, task_var)


def load_and_display_tasks():
    """Загружает задачи из базы, фильтрует, сортирует и отображает их в окне."""
    for task_id, (checkbox, _) in tasks.items():
        checkbox.destroy()
    tasks.clear()

    all_tasks = load_tasks_from_db()

    selected_filter = filter_var.get()
    if selected_filter != "Все":
        all_tasks = [t for t in all_tasks if t[3] == selected_filter]

    all_tasks.sort(key=lambda t: (t[4] is None, t[4]))

    for task_id, text, is_done, category, due_date in all_tasks:
        render_task(task_id, text, is_done, category, due_date)


def on_task_toggled(task_id, task_var):
    """Срабатывает при клике на чекбокс: сохраняет статус и начисляет/снимает очки."""
    is_done = task_var.get()
    update_task_status(task_id, is_done)
    add_points(POINTS_PER_TASK if is_done else -POINTS_PER_TASK)
    refresh_points_label()
    refresh_streak_label()
    refresh_task_stats_chart()
    check_achievements()


def add_task():
    """Добавляет новую задачу: сохраняет в базу и сразу показывает на экране."""
    text = task_entry.get().strip()
    if text == "":
        return

    category = category_var.get()
    due_date_text = date_entry.get().strip()
    due_date = due_date_text if due_date_text else None
    if due_date is not None:
        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            date_entry.delete(0, "end")
            date_entry.insert(0, "Формат: ГГГГ-ММ-ДД")
            return

    add_task_to_db(text, category, due_date)
    load_and_display_tasks()
    task_entry.delete(0, "end")
    date_entry.delete(0, "end")


def delete_completed():
    """Удаляет все отмеченные задачи из базы и с экрана."""
    completed_ids = [task_id for task_id, (_, var) in tasks.items() if var.get()]
    for task_id in completed_ids:
        delete_task_from_db(task_id)
        checkbox, _ = tasks.pop(task_id)
        checkbox.destroy()


# --- Форма ввода задачи ---
input_frame = ctk.CTkFrame(tab_tasks, fg_color="transparent")
input_frame.pack(pady=(15, 5), padx=15, fill="x")

task_entry = ctk.CTkEntry(input_frame, placeholder_text="Введи новую задачу...")
task_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

add_button = ctk.CTkButton(input_frame, text="Добавить", command=add_task, width=100)
add_button.pack(side="left")
task_entry.bind("<Return>", lambda event: add_task())

options_frame = ctk.CTkFrame(tab_tasks, fg_color="transparent")
options_frame.pack(pady=(0, 10), padx=15, fill="x")

category_var = ctk.StringVar(value=CATEGORIES[0])
category_menu = ctk.CTkOptionMenu(options_frame, values=CATEGORIES, variable=category_var, width=120)
category_menu.pack(side="left", padx=(0, 10))

date_entry = ctk.CTkEntry(options_frame, placeholder_text="Срок ГГГГ-ММ-ДД (необязательно)")
date_entry.pack(side="left", fill="x", expand=True)

# --- Фильтр ---
filter_frame = ctk.CTkFrame(tab_tasks, fg_color="transparent")
filter_frame.pack(pady=(0, 5), padx=15, fill="x")

filter_label = ctk.CTkLabel(filter_frame, text="Фильтр:", font=("Arial", 13))
filter_label.pack(side="left", padx=(0, 10))

filter_var = ctk.StringVar(value="Все")
filter_menu = ctk.CTkOptionMenu(
    filter_frame,
    values=["Все"] + CATEGORIES,
    variable=filter_var,
    width=140,
    command=lambda _: load_and_display_tasks()
)
filter_menu.pack(side="left")

# --- Список задач и кнопка удаления ---
tasks_content = ctk.CTkFrame(tab_tasks, fg_color="transparent")
tasks_content.pack(pady=5, padx=15, fill="both", expand=True)

tasks_frame = ctk.CTkScrollableFrame(tasks_content, label_text="Список задач", height=200)
tasks_frame.pack(fill="both", expand=True)

clear_button = ctk.CTkButton(
    tab_tasks,
    text="Удалить выполненные",
    command=delete_completed,
    fg_color="#8B3A3A",
    hover_color="#6B2A2A"
)
clear_button.pack(pady=(5, 10))

# --- Мини-статистика по категориям (встроенный график) ---
task_stats_label = ctk.CTkLabel(tab_tasks, text="Выполнено по категориям:", font=("Arial", 13, "bold"))
task_stats_label.pack(pady=(5, 2))

task_stats_chart_frame = ctk.CTkFrame(tab_tasks, fg_color="transparent", height=140)
task_stats_chart_frame.pack(pady=(0, 10), padx=15, fill="x")

task_stats_fig, task_stats_ax = create_dark_figure(figsize=(6, 1.6))
task_stats_canvas = FigureCanvasTkAgg(task_stats_fig, master=task_stats_chart_frame)
task_stats_canvas.get_tk_widget().pack(fill="both", expand=True)


def refresh_task_stats_chart():
    task_stats_ax.clear()
    task_stats_ax.set_facecolor("#2b2b2b")
    data = get_completed_tasks_by_category()
    if data:
        labels = [cat for cat, _ in data]
        values = [count for _, count in data]
        task_stats_ax.bar(labels, values, color="#5BD68F")
        task_stats_ax.tick_params(colors="white", labelsize=8)
    else:
        task_stats_ax.text(0.5, 0.5, "Пока нет выполненных задач", ha="center", va="center", color="white", fontsize=9)
    task_stats_canvas.draw()


# =====================================================================
# ВКЛАДКА: СОН
# =====================================================================

sleep_form_frame = ctk.CTkFrame(tab_sleep, fg_color="transparent")
sleep_form_frame.pack(pady=(15, 5), padx=15, fill="x")

bedtime_label = ctk.CTkLabel(sleep_form_frame, text="Время отбоя (ЧЧ:ММ):")
bedtime_label.grid(row=0, column=0, sticky="w", padx=(0, 10))
bedtime_entry = ctk.CTkEntry(sleep_form_frame, placeholder_text="напр. 23:30", width=150)
bedtime_entry.grid(row=1, column=0, padx=(0, 10), pady=(0, 10))

wake_label = ctk.CTkLabel(sleep_form_frame, text="Время подъёма (ЧЧ:ММ):")
wake_label.grid(row=0, column=1, sticky="w")
wake_entry = ctk.CTkEntry(sleep_form_frame, placeholder_text="напр. 07:30", width=150)
wake_entry.grid(row=1, column=1, pady=(0, 10))

sleep_result_label = ctk.CTkLabel(tab_sleep, text="", font=("Arial", 13))
sleep_result_label.pack(pady=2)


def save_sleep():
    bedtime = parse_time(bedtime_entry.get())
    wake_time = parse_time(wake_entry.get())

    if bedtime is None or wake_time is None:
        sleep_result_label.configure(text="Формат времени: ЧЧ:ММ, например 23:30", text_color="#FF6B6B")
        return

    bedtime_dt = datetime.combine(date.today(), bedtime)
    wake_dt = datetime.combine(date.today(), wake_time)
    if wake_dt <= bedtime_dt:
        wake_dt += timedelta(days=1)

    duration = round((wake_dt - bedtime_dt).total_seconds() / 3600, 1)
    add_sleep_log(date.today(), bedtime, wake_time, duration)

    bonus_text = ""
    if duration >= SLEEP_BONUS_THRESHOLD_HOURS:
        add_points(SLEEP_BONUS_POINTS)
        bonus_text = f"  +{SLEEP_BONUS_POINTS} бонусных очков! 🎉"
        refresh_points_label()

    sleep_result_label.configure(text=f"Записано: {duration} ч. сна{bonus_text}", text_color="#4CAF50")
    bedtime_entry.delete(0, "end")
    wake_entry.delete(0, "end")
    refresh_sleep_history()
    refresh_sleep_chart()
    check_achievements()


sleep_save_button = ctk.CTkButton(tab_sleep, text="Сохранить", command=save_sleep)
sleep_save_button.pack(pady=5)

sleep_content = ctk.CTkFrame(tab_sleep, fg_color="transparent")
sleep_content.pack(pady=5, padx=15, fill="both", expand=True)

sleep_history_label = ctk.CTkLabel(sleep_content, text="Последние записи:", font=("Arial", 14, "bold"))
sleep_history_label.pack(pady=(5, 5))

sleep_history_frame = ctk.CTkScrollableFrame(sleep_content, height=120)
sleep_history_frame.pack(pady=(0, 10), fill="x")


def refresh_sleep_history():
    for widget in sleep_history_frame.winfo_children():
        widget.destroy()
    for log_date, bedtime, wake_time, duration in load_sleep_logs():
        entry_text = f"{log_date.strftime('%d.%m')}: {bedtime} → {wake_time}  ({duration} ч.)"
        entry_label = ctk.CTkLabel(sleep_history_frame, text=entry_text, font=("Arial", 12))
        entry_label.pack(anchor="w", pady=2)


sleep_chart_label = ctk.CTkLabel(sleep_content, text="За последние 7 дней:", font=("Arial", 14, "bold"))
sleep_chart_label.pack(pady=(5, 5))

sleep_chart_frame = ctk.CTkFrame(sleep_content, fg_color="transparent")
sleep_chart_frame.pack(fill="both", expand=True)

sleep_fig, sleep_ax = create_dark_figure(figsize=(6, 2))
sleep_canvas = FigureCanvasTkAgg(sleep_fig, master=sleep_chart_frame)
sleep_canvas.get_tk_widget().pack(fill="both", expand=True)


def refresh_sleep_chart():
    sleep_ax.clear()
    sleep_ax.set_facecolor("#2b2b2b")
    data = get_sleep_last_n_days(7)
    if data:
        labels = [d.strftime("%d.%m") for d, _ in data]
        values = [float(h) for _, h in data]
        sleep_ax.bar(labels, values, color="#5B8FD6")
        sleep_ax.axhline(y=SLEEP_BONUS_THRESHOLD_HOURS, color="#4CAF50", linestyle="--", linewidth=1)
        sleep_ax.set_ylabel("часы", fontsize=8)
        sleep_ax.tick_params(colors="white", labelsize=8)
    else:
        sleep_ax.text(0.5, 0.5, "Пока нет данных", ha="center", va="center", color="white")
    sleep_canvas.draw()


# =====================================================================
# ВКЛАДКА: ФИНАНСЫ
# =====================================================================

finance_balance_label = ctk.CTkLabel(tab_finance, text="", font=("Arial", 15, "bold"))
finance_balance_label.pack(pady=(15, 10))

finance_form_frame = ctk.CTkFrame(tab_finance, fg_color="transparent")
finance_form_frame.pack(pady=5, padx=15, fill="x")

finance_type_var = ctk.StringVar(value="Расход")
finance_type_menu = ctk.CTkOptionMenu(finance_form_frame, values=["Доход", "Расход"], variable=finance_type_var, width=120)
finance_type_menu.pack(side="left", padx=(0, 10))

finance_category_var = ctk.StringVar(value=FINANCE_CATEGORIES[0])
finance_category_menu = ctk.CTkOptionMenu(finance_form_frame, values=FINANCE_CATEGORIES, variable=finance_category_var, width=140)
finance_category_menu.pack(side="left")

finance_amount_entry = ctk.CTkEntry(tab_finance, placeholder_text="Сумма, например 500.50")
finance_amount_entry.pack(pady=10, padx=15, fill="x")

finance_note_entry = ctk.CTkEntry(tab_finance, placeholder_text="Комментарий (необязательно)")
finance_note_entry.pack(pady=(0, 5), padx=15, fill="x")

finance_result_label = ctk.CTkLabel(tab_finance, text="", font=("Arial", 13))
finance_result_label.pack(pady=2)


def refresh_finance_balance():
    income_total, expense_total = get_finance_balance()
    balance = income_total - expense_total
    finance_balance_label.configure(
        text=f"Баланс: {balance:.2f} ₽  (доходы: {income_total:.2f} / расходы: {expense_total:.2f})"
    )


def refresh_finance_history():
    for widget in finance_history_frame.winfo_children():
        widget.destroy()
    for entry_id, log_date, entry_type, category, amount, note in load_finance_entries():
        sign = "+" if entry_type == "Доход" else "-"
        color = "#4CAF50" if entry_type == "Доход" else "#FF6B6B"
        entry_text = f"{log_date.strftime('%d.%m')}  {sign}{amount} ₽  [{category}]"
        if note:
            entry_text += f"  {note}"
        entry_label = ctk.CTkLabel(finance_history_frame, text=entry_text, font=("Arial", 12), text_color=color)
        entry_label.pack(anchor="w", pady=2)


def refresh_finance_chart():
    finance_ax.clear()
    finance_ax.set_facecolor("#2b2b2b")
    data = get_expenses_by_category()
    if data:
        labels = [cat for cat, _ in data]
        values = [amount for _, amount in data]
        colors = ["#5B8FD6", "#D65B5B", "#5BD68F", "#D6C15B", "#A55BD6"]
        finance_ax.pie(
            values, labels=labels, autopct="%1.0f%%",
            colors=colors[:len(labels)], textprops={"color": "white", "fontsize": 8}
        )
    else:
        finance_ax.text(0.5, 0.5, "Пока нет расходов", ha="center", va="center", color="white")
    finance_canvas.draw()


def save_finance():
    amount_text = finance_amount_entry.get().strip().replace(",", ".")
    try:
        amount = float(amount_text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        finance_result_label.configure(text="Введи корректную сумму (число больше 0)", text_color="#FF6B6B")
        return

    add_finance_entry(
        date.today(), finance_type_var.get(), finance_category_var.get(),
        amount, finance_note_entry.get().strip()
    )

    finance_result_label.configure(text="Запись добавлена", text_color="#4CAF50")
    finance_amount_entry.delete(0, "end")
    finance_note_entry.delete(0, "end")
    refresh_finance_balance()
    refresh_finance_history()
    refresh_finance_chart()
    check_achievements()


finance_save_button = ctk.CTkButton(tab_finance, text="Сохранить", command=save_finance)
finance_save_button.pack(pady=5)


def import_from_bank():
    file_path = filedialog.askopenfilename(
        title="Выбери файл выписки",
        filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")]
    )
    if not file_path:
        return

    try:
        entries, errors = parse_bank_csv(file_path)
    except ValueError as e:
        messagebox.showerror("Ошибка импорта", str(e))
        return

    if not entries:
        messagebox.showinfo("Импорт", "В файле не найдено ни одной подходящей операции.")
        return

    bulk_add_finance_entries(entries)

    summary = f"Импортировано записей: {len(entries)}"
    if errors:
        summary += f"\nПропущено строк с ошибками: {len(errors)}"
    messagebox.showinfo("Импорт завершён", summary)

    refresh_finance_balance()
    refresh_finance_history()
    refresh_finance_chart()
    check_achievements()


finance_import_button = ctk.CTkButton(
    tab_finance, text="📥 Импорт из банка (CSV)", command=import_from_bank,
    fg_color="#6B5B95", hover_color="#544A78"
)
finance_import_button.pack(pady=5)

finance_content = ctk.CTkFrame(tab_finance, fg_color="transparent")
finance_content.pack(pady=5, padx=15, fill="both", expand=True)

finance_history_label = ctk.CTkLabel(finance_content, text="Последние записи:", font=("Arial", 14, "bold"))
finance_history_label.pack(pady=(5, 5))

finance_history_frame = ctk.CTkScrollableFrame(finance_content, height=110)
finance_history_frame.pack(pady=(0, 10), fill="x")

finance_chart_label = ctk.CTkLabel(finance_content, text="Расходы по категориям:", font=("Arial", 14, "bold"))
finance_chart_label.pack(pady=(5, 5))

finance_chart_frame = ctk.CTkFrame(finance_content, fg_color="transparent")
finance_chart_frame.pack(fill="both", expand=True)

finance_fig, finance_ax = create_dark_figure(figsize=(5, 2))
finance_canvas = FigureCanvasTkAgg(finance_fig, master=finance_chart_frame)
finance_canvas.get_tk_widget().pack(fill="both", expand=True)


# =====================================================================
# ВКЛАДКА: НАГРАДЫ
# =====================================================================

reward_form_frame = ctk.CTkFrame(tab_rewards, fg_color="transparent")
reward_form_frame.pack(pady=(15, 5), padx=15, fill="x")

reward_title_entry = ctk.CTkEntry(reward_form_frame, placeholder_text="Название награды, напр. Новая игра")
reward_title_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

reward_cost_entry = ctk.CTkEntry(reward_form_frame, placeholder_text="Цена в очках", width=120)
reward_cost_entry.pack(side="left", padx=(0, 10))

reward_result_label = ctk.CTkLabel(tab_rewards, text="", font=("Arial", 13))
reward_result_label.pack(pady=(0, 5))


def add_new_reward():
    title = reward_title_entry.get().strip()
    cost_text = reward_cost_entry.get().strip()

    if not title:
        reward_result_label.configure(text="Введи название награды", text_color="#FF6B6B")
        return

    try:
        cost = int(cost_text)
        if cost <= 0:
            raise ValueError
    except ValueError:
        reward_result_label.configure(text="Цена должна быть целым числом больше 0", text_color="#FF6B6B")
        return

    add_reward(title, cost)
    reward_title_entry.delete(0, "end")
    reward_cost_entry.delete(0, "end")
    reward_result_label.configure(text="Награда добавлена", text_color="#4CAF50")
    refresh_rewards_list()


reward_add_button = ctk.CTkButton(reward_form_frame, text="Создать", command=add_new_reward, width=100)
reward_add_button.pack(side="left")

rewards_content = ctk.CTkFrame(tab_rewards, fg_color="transparent")
rewards_content.pack(pady=5, padx=15, fill="both", expand=True)

rewards_list_label = ctk.CTkLabel(rewards_content, text="Доступные награды:", font=("Arial", 14, "bold"))
rewards_list_label.pack(pady=(5, 5))

rewards_list_frame = ctk.CTkScrollableFrame(rewards_content, height=180)
rewards_list_frame.pack(pady=(0, 10), fill="x")


def do_redeem(reward_id, title, cost):
    current_points = get_total_points()
    if current_points < cost:
        messagebox.showwarning("Недостаточно очков", f"Нужно {cost} очков, у тебя {current_points}.")
        return

    confirmed = messagebox.askyesno(
        "Подтверждение",
        f"Обменять {cost} очков на «{title}»?\nПосле подтверждения не забудь на самом деле себя порадовать 🙂"
    )
    if not confirmed:
        return

    redeem_reward(reward_id, title, cost, date.today())
    refresh_points_label()
    refresh_rewards_history()
    reward_result_label.configure(text=f"Награда «{title}» получена!", text_color="#4CAF50")


def refresh_rewards_list():
    for widget in rewards_list_frame.winfo_children():
        widget.destroy()

    rewards = load_rewards()
    if not rewards:
        empty_label = ctk.CTkLabel(rewards_list_frame, text="Пока нет наград — создай первую выше", font=("Arial", 12))
        empty_label.pack(pady=10)
        return

    current_points = get_total_points()

    for reward_id, title, cost in rewards:
        row_frame = ctk.CTkFrame(rewards_list_frame, fg_color="transparent")
        row_frame.pack(fill="x", pady=3, padx=5)

        can_afford = current_points >= cost
        text_color = "white" if can_afford else "#888888"

        label_text = f"🎁 {title}  —  {cost} ⭐"
        item_label = ctk.CTkLabel(row_frame, text=label_text, font=("Arial", 13), text_color=text_color)
        item_label.pack(side="left", padx=(5, 10))

        redeem_button = ctk.CTkButton(
            row_frame, text="Обменять", width=90,
            state="normal" if can_afford else "disabled",
            command=lambda rid=reward_id, t=title, c=cost: do_redeem(rid, t, c)
        )
        redeem_button.pack(side="right", padx=(0, 5))


rewards_history_label = ctk.CTkLabel(rewards_content, text="История полученных наград:", font=("Arial", 14, "bold"))
rewards_history_label.pack(pady=(10, 5))

rewards_history_frame = ctk.CTkScrollableFrame(rewards_content, height=140)
rewards_history_frame.pack(fill="both", expand=True)


def refresh_rewards_history():
    for widget in rewards_history_frame.winfo_children():
        widget.destroy()
    for title, cost, redeemed_date in load_redeemed_rewards():
        entry_text = f"{redeemed_date.strftime('%d.%m.%Y')}  🎁 {title}  (-{cost} ⭐)"
        entry_label = ctk.CTkLabel(rewards_history_frame, text=entry_text, font=("Arial", 12), text_color="#FFD700")
        entry_label.pack(anchor="w", pady=2)
    # Обновляем и сам список наград, т.к. доступность "Обменять" зависит от текущих очков
    refresh_rewards_list()


# =====================================================================
# ВКЛАДКА: ДОСТИЖЕНИЯ
# =====================================================================

achievements_list_frame = ctk.CTkScrollableFrame(tab_achievements)
achievements_list_frame.pack(pady=15, padx=15, fill="both", expand=True)


def refresh_achievements_list():
    for widget in achievements_list_frame.winfo_children():
        widget.destroy()

    unlocked_codes = get_unlocked_achievement_codes()

    for achievement in ACHIEVEMENTS:
        is_unlocked = achievement["code"] in unlocked_codes
        icon = achievement["icon"] if is_unlocked else "🔒"
        color = "white" if is_unlocked else "#666666"

        item_frame = ctk.CTkFrame(achievements_list_frame, fg_color="#333333" if is_unlocked else "transparent")
        item_frame.pack(fill="x", pady=4, padx=2)

        name_label = ctk.CTkLabel(
            item_frame, text=f"{icon} {achievement['title']}",
            font=("Arial", 15, "bold"), text_color=color
        )
        name_label.pack(anchor="w", padx=10, pady=(8, 0))

        desc_label = ctk.CTkLabel(
            item_frame, text=achievement["description"],
            font=("Arial", 12), text_color=color
        )
        desc_label.pack(anchor="w", padx=10, pady=(0, 8))


# =====================================================================
# Первичная загрузка данных при запуске
# =====================================================================
load_and_display_tasks()
refresh_points_label()
refresh_streak_label()
refresh_task_stats_chart()
refresh_sleep_history()
refresh_sleep_chart()
refresh_finance_balance()
refresh_finance_history()
refresh_finance_chart()
refresh_rewards_list()
refresh_rewards_history()
refresh_achievements_list()
check_achievements()

app.mainloop()