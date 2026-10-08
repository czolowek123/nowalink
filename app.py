import tkinter as tk
from tkinter import messagebox

def on_button_click(response):
    print(f"Вы выбрали: {response}")
    window.destroy()

# Создаем главное окно
window = tk.Tk()
window.title("Успех")
window.geometry("300x150")
window.resizable(False, False)

# Центрируем окно на экране
window.update_idletasks()
x = (window.winfo_screenwidth() // 2) - (window.winfo_width() // 2)
y = (window.winfo_screenheight() // 2) - (window.winfo_height() // 2)
window.geometry(f"+{x}+{y}")

# Добавляем надпись
label = tk.Label(window, text="ПОЛУЧИЛОСЬ", font=("Arial", 24, "bold"))
label.pack(pady=20)

# Создаем фрейм для кнопок
button_frame = tk.Frame(window)
button_frame.pack(pady=10)

# Добавляем кнопки
button1 = tk.Button(button_frame, text="Да", width=10, command=lambda: on_button_click("Да 1"))
button1.grid(row=0, column=0, padx=5)

button2 = tk.Button(button_frame, text="Да", width=10, command=lambda: on_button_click("Да 2"))
button2.grid(row=0, column=1, padx=5)

# Запускаем окно
window.mainloop()
