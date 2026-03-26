import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import logging
from datetime import datetime

# -------------------- НАСТРОЙКИ --------------------

DATA_FILE = "expenses.json"
LOG_FILE = "app.log"
MIN_DATE = datetime(2000, 1, 1)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8"
)

# -------------------- РАБОТА С ДАННЫМИ --------------------

def load_expenses():
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Ошибка загрузки файла: {e}")
        return []

def save_expenses():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(expenses, file, ensure_ascii=False, indent=4)
        logging.info("Данные успешно сохранены в файл")
    except Exception as e:
        logging.error(f"Ошибка сохранения файла: {e}")
        messagebox.showerror("Ошибка", "Не удалось сохранить данные в файл")

# -------------------- ПРОВЕРКИ --------------------

def validate_amount_input(new_value):
    """
    Разрешает ввод только цифр и одной точки.
    Пустое значение тоже разрешается, чтобы можно было стирать.
    """
    if new_value == "":
        return True

    if new_value.count(".") > 1:
        return False

    for char in new_value:
        if not (char.isdigit() or char == "."):
            return False

    return True

def format_date(event=None):
    """
    Автоматически форматирует дату как ДД.ММ.ГГГГ.
    Оставляет только цифры, точки расставляет сама.
    """
    current_text = entry_date.get()

    digits_only = "".join(char for char in current_text if char.isdigit())
    digits_only = digits_only[:8]

    formatted = ""

    if len(digits_only) >= 2:
        formatted += digits_only[:2]
    else:
        formatted += digits_only

    if len(digits_only) > 2:
        formatted += "." + digits_only[2:4]

    if len(digits_only) > 4:
        formatted += "." + digits_only[4:8]

    cursor_position = entry_date.index(tk.INSERT)

    entry_date.delete(0, tk.END)
    entry_date.insert(0, formatted)

    # Ставим курсор в конец для простоты и стабильности
    entry_date.icursor(len(formatted))

def validate_date(date_text):
    """
    Проверяет:
    1. корректность формата ДД.ММ.ГГГГ
    2. дата не раньше 01.01.2000
    3. дата не позже сегодняшней
    """
    try:
        date_obj = datetime.strptime(date_text, "%d.%m.%Y")
    except ValueError:
        return False, "Дата должна быть в формате ДД.ММ.ГГГГ"

    today = datetime.now()

    if date_obj < MIN_DATE:
        return False, "Дата не может быть раньше 01.01.2000"

    if date_obj.date() > today.date():
        return False, "Дата не может быть позже сегодняшнего дня"

    return True, ""

# -------------------- ОСНОВНЫЕ ФУНКЦИИ --------------------

def add_expense():
    amount = entry_amount.get().strip()
    category = combo_category.get().strip()
    date_text = entry_date.get().strip()
    comment = entry_comment.get().strip()

    if not amount or not category or not date_text:
        messagebox.showwarning("Предупреждение", "Заполните сумму, категорию и дату")
        logging.warning("Попытка добавить расход с пустыми обязательными полями")
        return

    try:
        amount_value = float(amount)
        if amount_value <= 0:
            raise ValueError
    except ValueError:
        messagebox.showwarning("Предупреждение", "Сумма должна быть положительным числом")
        logging.warning(f"Некорректная сумма: {amount}")
        return

    is_valid_date, date_error = validate_date(date_text)
    if not is_valid_date:
        messagebox.showwarning("Предупреждение", date_error)
        logging.warning(f"Некорректная дата: {date_text}. Причина: {date_error}")
        return

    expense = {
        "amount": round(amount_value, 2),
        "category": category,
        "date": date_text,
        "comment": comment
    }

    expenses.append(expense)
    save_expenses()
    logging.info(f"Добавлен расход: {expense}")

    messagebox.showinfo("Успех", "Расход успешно добавлен")

    entry_amount.delete(0, tk.END)
    combo_category.set("")
    entry_date.delete(0, tk.END)
    entry_comment.delete(0, tk.END)

def show_expenses():
    window = tk.Toplevel(root)
    window.title("Список расходов")
    window.geometry("750x400")
    window.resizable(False, False)

    columns = ("amount", "category", "date", "comment")

    tree = ttk.Treeview(window, columns=columns, show="headings")
    tree.heading("amount", text="Сумма")
    tree.heading("category", text="Категория")
    tree.heading("date", text="Дата")
    tree.heading("comment", text="Комментарий")

    tree.column("amount", width=100, anchor="center")
    tree.column("category", width=150, anchor="center")
    tree.column("date", width=120, anchor="center")
    tree.column("comment", width=350, anchor="w")

    for index, expense in enumerate(expenses):
        tree.insert(
            "",
            tk.END,
            iid=str(index),
            values=(
                expense["amount"],
                expense["category"],
                expense["date"],
                expense["comment"]
            )
        )

    tree.pack(fill="both", expand=True, padx=10, pady=10)

    def delete_selected():
        selected = tree.selection()

        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите запись для удаления")
            return

        selected_index = int(selected[0])
        deleted_expense = expenses[selected_index]

        confirm = messagebox.askyesno(
            "Подтверждение",
            "Вы действительно хотите удалить выбранный расход?"
        )

        if confirm:
            expenses.pop(selected_index)
            save_expenses()
            logging.info(f"Удалён расход: {deleted_expense}")
            messagebox.showinfo("Успех", "Запись удалена")
            window.destroy()
            show_expenses()

    delete_button = tk.Button(
        window,
        text="Удалить выбранную запись",
        command=delete_selected,
        bg="#d9534f",
        fg="white",
        font=("Arial", 11)
    )
    delete_button.pack(pady=10)

def show_total():
    total = sum(expense["amount"] for expense in expenses)
    logging.info(f"Подсчитана общая сумма расходов: {total}")
    messagebox.showinfo("Общая сумма", f"Общая сумма расходов: {round(total, 2)} руб.")

def show_statistics():
    window = tk.Toplevel(root)
    window.title("Статистика расходов")
    window.geometry("450x350")
    window.resizable(False, False)

    stats = {}

    for expense in expenses:
        category = expense["category"]
        stats[category] = stats.get(category, 0) + expense["amount"]

    title_label = tk.Label(
        window,
        text="Статистика по категориям",
        font=("Arial", 14, "bold")
    )
    title_label.pack(pady=10)

    text_box = tk.Text(window, width=50, height=15, font=("Arial", 11))
    text_box.pack(padx=10, pady=10)

    if not stats:
        text_box.insert(tk.END, "Расходов пока нет.\n")
    else:
        for category, total in stats.items():
            text_box.insert(tk.END, f"{category}: {round(total, 2)} руб.\n")

    text_box.config(state="disabled")
    logging.info("Открыто окно статистики")

def show_logs_info():
    window = tk.Toplevel(root)
    window.title("Информация о логировании")
    window.geometry("500x250")
    window.resizable(False, False)

    text = (
        "Программа ведёт логирование действий в файл app.log.\n\n"
        "В лог записываются:\n"
        "- запуск программы\n"
        "- добавление расходов\n"
        "- удаление расходов\n"
        "- ошибки ввода\n"
        "- подсчёт общей суммы\n"
        "- открытие окон программы\n"
        "- автоматическая проверка данных\n"
    )

    label = tk.Label(
        window,
        text=text,
        justify="left",
        font=("Arial", 11),
        padx=20,
        pady=20
    )
    label.pack()

def auto_check():
    count = len(expenses)
    total = sum(expense["amount"] for expense in expenses)
    logging.info(
        f"Автоматическая проверка данных: записей = {count}, общая сумма = {round(total, 2)}"
    )
    root.after(30000, auto_check)

# -------------------- ИНТЕРФЕЙС --------------------

expenses = load_expenses()

root = tk.Tk()
root.title("Система учёта личных расходов студента")
root.geometry("520x430")
root.resizable(False, False)

logging.info("Программа запущена")

title_label = tk.Label(
    root,
    text="Учёт личных расходов студента",
    font=("Arial", 16, "bold")
)
title_label.pack(pady=15)

frame = tk.Frame(root)
frame.pack(pady=10)

label_amount = tk.Label(frame, text="Сумма:", font=("Arial", 11))
label_amount.grid(row=0, column=0, padx=10, pady=8, sticky="e")

vcmd_amount = (root.register(validate_amount_input), "%P")

entry_amount = tk.Entry(
    frame,
    font=("Arial", 11),
    width=25,
    validate="key",
    validatecommand=vcmd_amount
)
entry_amount.grid(row=0, column=1, padx=10, pady=8)

label_category = tk.Label(frame, text="Категория:", font=("Arial", 11))
label_category.grid(row=1, column=0, padx=10, pady=8, sticky="e")

combo_category = ttk.Combobox(
    frame,
    font=("Arial", 11),
    width=23,
    state="readonly"
)
combo_category["values"] = (
    "Еда",
    "Транспорт",
    "Учёба",
    "Развлечения",
    "Связь",
    "Одежда",
    "Другое"
)
combo_category.grid(row=1, column=1, padx=10, pady=8)

label_date = tk.Label(frame, text="Дата (ДД.ММ.ГГГГ):", font=("Arial", 11))
label_date.grid(row=2, column=0, padx=10, pady=8, sticky="e")

entry_date = tk.Entry(frame, font=("Arial", 11), width=25)
entry_date.grid(row=2, column=1, padx=10, pady=8)
entry_date.bind("<KeyRelease>", format_date)

label_comment = tk.Label(frame, text="Комментарий:", font=("Arial", 11))
label_comment.grid(row=3, column=0, padx=10, pady=8, sticky="e")

entry_comment = tk.Entry(frame, font=("Arial", 11), width=25)
entry_comment.grid(row=3, column=1, padx=10, pady=8)

buttons_frame = tk.Frame(root)
buttons_frame.pack(pady=20)

button_add = tk.Button(
    buttons_frame,
    text="Добавить расход",
    command=add_expense,
    width=22,
    bg="#5cb85c",
    fg="white",
    font=("Arial", 11)
)
button_add.grid(row=0, column=0, padx=8, pady=8)

button_show = tk.Button(
    buttons_frame,
    text="Показать расходы",
    command=show_expenses,
    width=22,
    bg="#0275d8",
    fg="white",
    font=("Arial", 11)
)
button_show.grid(row=0, column=1, padx=8, pady=8)

button_total = tk.Button(
    buttons_frame,
    text="Подсчитать итог",
    command=show_total,
    width=22,
    bg="#f0ad4e",
    fg="white",
    font=("Arial", 11)
)
button_total.grid(row=1, column=0, padx=8, pady=8)

button_stats = tk.Button(
    buttons_frame,
    text="Статистика",
    command=show_statistics,
    width=22,
    bg="#6f42c1",
    fg="white",
    font=("Arial", 11)
)
button_stats.grid(row=1, column=1, padx=8, pady=8)

button_logs = tk.Button(
    root,
    text="О логировании",
    command=show_logs_info,
    width=25,
    bg="#343a40",
    fg="white",
    font=("Arial", 11)
)
button_logs.pack(pady=10)

info_label = tk.Label(
    root,
    text="Все данные сохраняются в expenses.json\nЛоги сохраняются в app.log",
    font=("Arial", 10),
    fg="gray"
)
info_label.pack(pady=10)

auto_check()
root.mainloop()