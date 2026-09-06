import customtkinter as ctk
print("customtkinter version:", ctk.__version__)

ctk.set_appearance_mode("light")  # пробуем светлую тему для теста

app = ctk.CTk()
app.title("Тест")
app.geometry("400x300")

# Используем обычную tkinter-надпись вместо CTkLabel — для проверки
import tkinter as tk
label = tk.Label(app, text="ТЕСТОВЫЙ ТЕКСТ", font=("Arial", 20), fg="red", bg="white")
label.pack(pady=100)

app.mainloop()
