"""
Модуль импорта банковской выписки (CSV) в формат приложения.
Поддерживает два распространённых варианта структуры:
  1) Одна колонка суммы, где знак (+/-) определяет доход/расход (формат Т-Банка).
  2) Колонка суммы всегда положительная + отдельная колонка типа операции
     со значениями вроде "Списание"/"Пополнение" (формат Альфа-Банка).
"""

import csv
import io
from datetime import datetime

# Как сопоставлять банковские категории с категориями приложения.
# Если ни одно ключевое слово не подошло — используется "Другое".
CATEGORY_KEYWORDS = {
    "Еда": ["продукт", "супермаркет", "кафе", "ресторан", "фастфуд", "food"],
    "Транспорт": ["такси", "транспорт", "метро", "автобус", "азс", "топливо", "каршеринг"],
    "Развлечения": ["развлечен", "кино", "игр", "подписк", "музык", "стриминг"],
    "Учёба": ["образован", "книг", "курс", "учеб"],
}

# Ключевые слова, по которым определяем направление операции из колонки "тип"
EXPENSE_KEYWORDS = ["списание", "расход", "debit", "дебет", "withdraw"]
INCOME_KEYWORDS = ["пополнение", "доход", "credit", "кредит", "deposit"]

# Статусы, при которых операцию нужно пропустить (явный отказ/ошибка)
REJECTED_STATUS_KEYWORDS = ["отклон", "ошибк", "failed", "cancel", "отказ"]


def guess_category(*texts):
    """Пытается сопоставить категорию из банка с одной из категорий приложения."""
    combined = " ".join(t for t in texts if t).lower()
    for app_category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in combined:
                return app_category
    return "Другое"


def read_file_text(file_path):
    """Читает файл, перебирая распространённые кодировки банковских выписок."""
    for encoding in ("utf-8-sig", "cp1251", "utf-8"):
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError("Не удалось прочитать файл ни в одной из известных кодировок")


def detect_delimiter(sample_text):
    """Определяет разделитель CSV — точку с запятой или запятую."""
    first_line = sample_text.splitlines()[0] if sample_text else ""
    return ";" if first_line.count(";") >= first_line.count(",") else ","


def find_column(headers, keywords):
    """Ищет в списке заголовков колонку, содержащую одно из ключевых слов."""
    for header in headers:
        header_lower = header.lower()
        for keyword in keywords:
            if keyword in header_lower:
                return header
    return None


def parse_amount(amount_text):
    """Превращает текст суммы (с запятой как разделителем, возможными пробелами) в float."""
    cleaned = amount_text.strip().replace(" ", "").replace("\xa0", "").replace(",", ".")
    return float(cleaned)


def parse_date(date_text):
    """Пытается распознать дату в нескольких распространённых форматах."""
    date_text = date_text.strip().split(" ")[0]  # отбрасываем время, если есть
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Не удалось распознать дату: {date_text}")


def determine_entry_type(amount, type_text):
    """Определяет 'Доход' или 'Расход' по колонке типа операции (если есть) или по знаку суммы."""
    if type_text:
        type_lower = type_text.lower()
        for keyword in EXPENSE_KEYWORDS:
            if keyword in type_lower:
                return "Расход"
        for keyword in INCOME_KEYWORDS:
            if keyword in type_lower:
                return "Доход"
    # Если колонки типа нет или она не распознана — судим по знаку суммы
    return "Расход" if amount < 0 else "Доход"


def parse_bank_csv(file_path):
    """Разбирает CSV-выписку и возвращает (список записей, список ошибок).

    Каждая запись — кортеж (log_date, entry_type, category, amount, note),
    готовый для передачи в database.bulk_add_finance_entries.
    """
    text = read_file_text(file_path)
    delimiter = detect_delimiter(text)
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)

    headers = reader.fieldnames or []
    date_col = find_column(headers, ["дата операции", "operationdate", "дата платежа", "transactiondate", "дата"])
    amount_col = find_column(headers, ["сумма операции", "сумма платежа", "сумма", "amount"])
    type_col = find_column(headers, ["тип операции", "тип", "type"])
    category_col = find_column(headers, ["категория", "category"])
    description_col = find_column(headers, ["описание", "назначение", "merchant", "comment"])
    status_col = find_column(headers, ["статус", "status"])

    if date_col is None or amount_col is None:
        raise ValueError(
            f"Не нашёл нужные колонки в файле. Заголовки в файле: {headers}"
        )

    entries = []
    errors = []

    for i, row in enumerate(reader, start=2):  # start=2, т.к. первая строка — заголовок
        # Пропускаем явно отклонённые/неуспешные операции
        status_text = row.get(status_col, "") if status_col else ""
        if status_text and any(kw in status_text.lower() for kw in REJECTED_STATUS_KEYWORDS):
            continue

        try:
            log_date = parse_date(row[date_col])
            amount = parse_amount(row[amount_col])
        except (ValueError, KeyError) as e:
            errors.append(f"Строка {i}: {e}")
            continue

        if amount == 0:
            continue

        type_text = row.get(type_col, "") if type_col else ""
        entry_type = determine_entry_type(amount, type_text)

        bank_category = row.get(category_col, "") if category_col else ""
        description = row.get(description_col, "") if description_col else ""
        category = guess_category(bank_category, description)

        note_parts = [p for p in [bank_category, description] if p]
        note = " / ".join(note_parts)[:255]

        entries.append((log_date, entry_type, category, abs(amount), note))

    return entries, errors