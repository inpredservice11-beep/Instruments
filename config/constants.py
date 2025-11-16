#!/usr/bin/env python3
"""
Константы и конфигурация приложения
"""

# Размеры интерфейса
TREEVIEW_HEIGHT = 15
DEFAULT_DIALOG_WIDTH = 900
DEFAULT_DIALOG_HEIGHT = 700

# Цветовая схема в стиле MS Office
OFFICE_COLORS = {
    'bg_white': '#FFFFFF',
    'bg_main': '#F0F0F0',
    'bg_header': '#E6E6E6',
    'bg_header_light': '#F5F5F5',
    'bg_selected': '#CCE4F7',
    'bg_hover': '#E5F3FF',
    'hover': '#E1DFDD',     # Цвет при наведении (как в старом коде)
    'fg_main': '#000000',
    'fg_secondary': '#666666',
    'fg_header': '#000000',  # Темный текст на заголовках
    'selected': '#0078D4',   # Синий цвет выделения (MS Office blue)
    'border': '#CCCCCC',
    'overdue': '#FFCCCC',
    'warning': '#FFFFCC',
    'success': '#CCFFCC'
}

# Конфигурация таблиц
TABLES_CONFIG = {
    'instruments': {
        'columns': ('ID', 'Название', 'Инв. номер', 'Серийный номер', 'Штрих-код', 'Категория', 'Статус'),
        'column_widths': {
            'ID': 50, 'Название': 200, 'Инв. номер': 100, 'Серийный номер': 110,
            'Штрих-код': 140, 'Категория': 140, 'Статус': 100
        }
    },
    'employees': {
        'columns': ('ID', 'ФИО', 'Должность', 'Отдел', 'Телефон', 'Email', 'Статус'),
        'column_widths': {
            'ID': 50, 'ФИО': 200, 'Должность': 150, 'Отдел': 200,
            'Телефон': 120, 'Email': 180, 'Статус': 100
        }
    },
    'issues': {
        'columns': ('ID', 'Инв. номер', 'Инструмент', 'Сотрудник',
                   'Адрес', 'Дата выдачи', 'Ожид. возврат', 'Выдал', 'Примечание'),
        'column_widths': {
            'ID': 50, 'Инв. номер': 110, 'Инструмент': 200, 'Сотрудник': 180,
            'Адрес': 220, 'Дата выдачи': 130, 'Ожид. возврат': 110,
            'Выдал': 140, 'Примечание': 200
        },
        'tags': {
            'overdue': {'background': OFFICE_COLORS['overdue']}
        }
    },
    'returns': {
        'columns': ('ID', 'Инв. номер', 'Инструмент', 'Сотрудник',
                   'Адрес', 'Дата выдачи', 'Ожид. возврат', 'Дней в использовании'),
        'column_widths': {
            'ID': 50, 'Инв. номер': 110, 'Инструмент': 230, 'Сотрудник': 200,
            'Адрес': 220, 'Дата выдачи': 130, 'Ожид. возврат': 120, 'Дней в использовании': 160
        }
    },
    'history': {
        'columns': ('ID', 'Дата', 'Тип', 'Инструмент', 'Сотрудник', 'Пользователь'),
        'column_widths': {
            'ID': 50, 'Дата': 130, 'Тип': 100, 'Инструмент': 250,
            'Сотрудник': 200, 'Пользователь': 150
        },
        'tags': {
            'issue': {'background': OFFICE_COLORS['warning']},
            'return': {'background': OFFICE_COLORS['success']}
        }
    },
    'addresses': {
        'columns': ('ID', 'Название', 'Полный адрес'),
        'column_widths': {
            'ID': 50, 'Название': 250, 'Полный адрес': 400
        }
    }
}

# Статусы инструментов
INSTRUMENT_STATUSES = ["Доступен", "Выдан", "На ремонте", "Списан"]

# Статусы сотрудников
EMPLOYEE_STATUSES = ["Активен", "В отпуске", "На больничном", "Уволен", "В командировке"]

# Категории инструментов
INSTRUMENT_CATEGORIES = [
    "Электроинструмент", "Ручной инструмент", "Измерительный инструмент",
    "Слесарный инструмент", "Столярный инструмент", "Сварочное оборудование",
    "Пневматический инструмент", "Гидравлический инструмент", "Электроприводы",
    "Крепежные изделия", "Расходные материалы", "Защитное оборудование"
]

# Типы операций
OPERATION_TYPES = ["Выдача", "Возврат"]

# Пути к директориям
PHOTOS_DIR = "photos"
BARCODE_DIR = "barcodes"
EXPORT_DIR = "exports"

# Настройки базы данных
DB_PATH = "tool_management.db"
DB_BACKUP_DIR = "backups"

# Настройки экспорта
PDF_PAGE_SIZE = "A4"
PDF_MARGIN = 50
EXCEL_SHEET_NAME = "Отчет"

# Лимиты
MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5MB
MAX_SEARCH_RESULTS = 1000
TREEVIEW_HEIGHT = 15

# Сообщения
MESSAGES = {
    'success': {
        'instrument_added': "Инструмент добавлен",
        'instrument_updated': "Инструмент обновлен",
        'instrument_deleted': "Инструмент удален",
        'employee_added': "Сотрудник добавлен",
        'employee_updated': "Сотрудник обновлен",
        'employee_deleted': "Сотрудник удален",
        'issue_created': "Инструмент выдан",
        'return_created': "Инструмент возвращен",
        'address_added': "Адрес добавлен",
        'address_updated': "Адрес обновлен",
        'address_deleted': "Адрес удален"
    },
    'error': {
        'required_field': "Заполните обязательное поле: {field}",
        'invalid_barcode': "Некорректный формат штрих-кода",
        'instrument_not_found': "Инструмент не найден",
        'employee_not_found': "Сотрудник не найден",
        'address_not_found': "Адрес не найден",
        'duplicate_inventory': "Инструмент с таким инвентарным номером уже существует",
        'duplicate_barcode': "Инструмент с таким штрих-кодом уже существует",
        'instrument_not_available': "Инструмент недоступен",
        'instrument_already_returned': "Инструмент уже возвращен",
        'photo_load_error': "Ошибка загрузки фотографии: {error}",
        'export_error': "Ошибка экспорта: {error}"
    },
    'warning': {
        'no_barcode': "Введите штрих-код для поиска",
        'no_selection': "Выберите элемент для действия",
        'confirm_delete': "Вы действительно хотите удалить выбранный элемент?"
    }
}
