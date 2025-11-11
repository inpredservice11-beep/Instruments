"""
Диалоговые окна для системы учета инструмента
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from tkcalendar import DateEntry, Calendar
from window_config import WindowConfig
import locale

# Глобальный объект для управления конфигурацией окон
window_config = WindowConfig()

# Настройка русской локализации для календаря
try:
    # Пытаемся установить русскую локаль для времени
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'Russian_Russia.1251')
    except:
        try:
            locale.setlocale(locale.LC_TIME, 'ru')
        except:
            pass  # Если не удалось установить локаль, используем английский

# Русские названия для календаря
RUSSIAN_MONTHS = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

RUSSIAN_DAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

# Функция для создания DateEntry с русской локализацией
def create_russian_date_entry(parent, **kwargs):
    """Создает DateEntry с русской локализацией"""
    # Сохраняем оригинальные kwargs
    original_kwargs = kwargs.copy()
    
    # Способ 1: Пробуем использовать locale напрямую
    try:
        date_entry = DateEntry(parent, locale='ru_RU', **kwargs)
        return date_entry
    except:
        pass
    
    # Способ 2: Создаем DateEntry и настраиваем через внутренний календарь
    try:
        # Удаляем locale из kwargs, если он там есть
        kwargs.pop('locale', None)
        
        # Создаем DateEntry
        date_entry = DateEntry(parent, **kwargs)
        
        # Функция для настройки календаря
        def find_and_configure_calendar(widget):
            """Рекурсивно находит и настраивает календарь"""
            try:
                # Проверяем, является ли виджет календарем
                if isinstance(widget, Calendar):
                    widget.month_names = RUSSIAN_MONTHS
                    widget.day_names = RUSSIAN_DAYS
                    widget.firstweekday = 0
                    return True
                
                # Проверяем атрибуты виджета
                if hasattr(widget, 'month_names'):
                    widget.month_names = RUSSIAN_MONTHS
                if hasattr(widget, 'day_names'):
                    widget.day_names = RUSSIAN_DAYS
                if hasattr(widget, 'firstweekday'):
                    widget.firstweekday = 0
                
                # Рекурсивно проверяем дочерние виджеты
                for child in widget.winfo_children():
                    if find_and_configure_calendar(child):
                        return True
                return False
            except:
                return False
        
        # Настраиваем календарь сразу и при открытии
        def setup_russian_calendar():
            find_and_configure_calendar(date_entry)
        
        # Настраиваем сразу и при открытии календаря
        parent.after_idle(setup_russian_calendar)
        
        # Также настраиваем при открытии календаря (когда пользователь кликает на поле)
        def on_focus_in(event):
            parent.after(50, setup_russian_calendar)
        
        date_entry.bind('<FocusIn>', on_focus_in)
        
        # Настраиваем при открытии выпадающего календаря
        if hasattr(date_entry, '_top_cal'):
            def on_calendar_open():
                parent.after(100, setup_russian_calendar)
            # Пытаемся перехватить открытие календаря
            try:
                original_dropdown = date_entry._make_dropdown
                def new_dropdown():
                    result = original_dropdown()
                    parent.after(50, setup_russian_calendar)
                    return result
                date_entry._make_dropdown = new_dropdown
            except:
                pass
        
        return date_entry
    except:
        # Способ 3: Просто создаем стандартный DateEntry
        kwargs.pop('locale', None)
        return DateEntry(parent, **kwargs)


# ========== ИНСТРУМЕНТЫ ==========


class AddAddressDialog:
    def __init__(self, parent, db, callback=None):
        self.db = db
        self.callback = callback
        self.result_id = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Добавить адрес")
        default_geometry = "420x220"
        window_config.restore_window(self.dialog, "AddAddressDialog", default_geometry)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Закрытие по ESC
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Название адреса*:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(main_frame, width=45)
        self.name_entry.grid(row=0, column=1, pady=5, sticky=tk.W)

        ttk.Label(main_frame, text="Полный адрес:").grid(row=1, column=0, sticky=tk.NW, pady=5)
        self.full_address_text = tk.Text(main_frame, width=44, height=4)
        self.full_address_text.grid(row=1, column=1, pady=5, sticky=tk.W)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=15)

        ttk.Button(
            button_frame,
            text="Сохранить",
            command=self.save
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Отмена",
            command=self.dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

        self.name_entry.focus_set()

    def save(self):
        name = self.name_entry.get().strip()
        full_address = self.full_address_text.get("1.0", tk.END).strip()

        if not name:
            messagebox.showerror("Ошибка", "Введите название адреса")
            return

        success, result = self.db.add_address(name, full_address)
        if not success:
            messagebox.showerror("Ошибка", f"Не удалось сохранить адрес:\n{result}")
            return

        self.result_id = result
        messagebox.showinfo("Успех", "Адрес добавлен")
        if self.callback:
            self.callback()
        self.dialog.destroy()


class EditAddressDialog:
    def __init__(self, parent, db, address_id, callback):
        self.db = db
        self.address_id = address_id
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Редактировать адрес")
        default_geometry = "420x220"
        window_config.restore_window(self.dialog, "EditAddressDialog", default_geometry)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Закрытие по ESC
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        
        self.load_data()
        self.create_widgets()
        
    def load_data(self):
        address = self.db.get_address_by_id(self.address_id)
        if address:
            self.address_data = {
                'name': address[1],
                'full_address': address[2] or ''
            }
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Название адреса*:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(main_frame, width=45)
        self.name_entry.insert(0, self.address_data['name'])
        self.name_entry.grid(row=0, column=1, pady=5, sticky=tk.W)

        ttk.Label(main_frame, text="Полный адрес:").grid(row=1, column=0, sticky=tk.NW, pady=5)
        self.full_address_text = tk.Text(main_frame, width=44, height=4)
        self.full_address_text.insert("1.0", self.address_data['full_address'])
        self.full_address_text.grid(row=1, column=1, pady=5, sticky=tk.W)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=15)

        ttk.Button(
            button_frame,
            text="Сохранить",
            command=self.save
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Отмена",
            command=self.dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

        self.name_entry.focus_set()
    
    def save(self):
        name = self.name_entry.get().strip()
        full_address = self.full_address_text.get("1.0", tk.END).strip()

        if not name:
            messagebox.showerror("Ошибка", "Введите название адреса")
            return

        success, message = self.db.update_address(self.address_id, name, full_address)
        if success:
            messagebox.showinfo("Успех", message)
            self.callback()
            self.dialog.destroy()
        else:
            messagebox.showerror("Ошибка", f"Не удалось обновить адрес:\n{message}")

class AddInstrumentDialog:
    def __init__(self, parent, db, callback):
        self.db = db
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Добавить инструмент")
        default_geometry = "700x600"
        window_config.restore_window(self.dialog, "AddInstrumentDialog", default_geometry)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Закрытие по ESC
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        
        self.create_widgets()
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Поля ввода
        fields = [
            ("Название*:", "name"),
            ("Описание:", "description"),
            ("Инвентарный номер*:", "inventory_number"),
            ("Серийный номер:", "serial_number"),
            ("Категория:", "category"),
            ("Адрес:", "location"),
            ("Дата покупки:", "purchase_date"),
            ("Цена:", "price"),
        ]
        
        self.entries = {}
        
        for i, (label, field) in enumerate(fields):
            ttk.Label(main_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=5)
            
            if field == "description":
                entry = tk.Text(main_frame, width=50, height=3)
                entry.grid(row=i, column=1, pady=5, sticky=tk.W)
            elif field == "purchase_date":
                entry = create_russian_date_entry(
                    main_frame, 
                    width=48, 
                    date_pattern='yyyy-mm-dd'
                )
                entry.grid(row=i, column=1, pady=5, sticky=tk.W)
            else:
                entry = ttk.Entry(main_frame, width=50)
                entry.grid(row=i, column=1, pady=5, sticky=tk.W)
            
            self.entries[field] = entry
        
        # Статус
        ttk.Label(main_frame, text="Статус:").grid(row=len(fields), column=0, sticky=tk.W, pady=5)
        self.status_var = tk.StringVar(value="Доступен")
        status_combo = ttk.Combobox(
            main_frame, 
            textvariable=self.status_var,
            values=["Доступен", "Выдан", "На ремонте", "Списан"],
            state='readonly',
            width=47
        )
        status_combo.grid(row=len(fields), column=1, pady=5, sticky=tk.W)
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=20)
        
        ttk.Button(
            button_frame,
            text="Сохранить",
            command=self.save
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Отмена",
            command=self.dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
        
    def save(self):
        # Получение значений
        name = self.entries['name'].get().strip()
        description = self.entries['description'].get("1.0", tk.END).strip()
        inventory_number = self.entries['inventory_number'].get().strip()
        serial_number = self.entries['serial_number'].get().strip()
        category = self.entries['category'].get().strip()
        location = self.entries['location'].get().strip()
        purchase_date = self.entries['purchase_date'].get()
        price_str = self.entries['price'].get().strip()
        status = self.status_var.get()
        
        # Валидация
        if not name:
            messagebox.showerror("Ошибка", "Введите название инструмента")
            return
        
        if not inventory_number:
            messagebox.showerror("Ошибка", "Введите инвентарный номер")
            return
        
        price = 0.0
        if price_str:
            try:
                price = float(price_str)
            except ValueError:
                messagebox.showerror("Ошибка", "Неверный формат цены")
                return
        
        # Сохранение
        data = (
            name, description, inventory_number, serial_number, category,
            location, purchase_date, price, status
        )
        
        if self.db.add_instrument(data):
            messagebox.showinfo("Успех", "Инструмент добавлен")
            self.callback()
            self.dialog.destroy()
        else:
            messagebox.showerror("Ошибка", "Не удалось добавить инструмент (возможно, инвентарный номер уже существует)")


class EditInstrumentDialog:
    def __init__(self, parent, db, instrument_id, callback):
        self.db = db
        self.instrument_id = instrument_id
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Редактировать инструмент")
        default_geometry = "700x600"
        window_config.restore_window(self.dialog, "EditInstrumentDialog", default_geometry)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Закрытие по ESC
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        
        self.load_data()
        self.create_widgets()
        
    def load_data(self):
        instrument = self.db.get_instrument_by_id(self.instrument_id)
        if instrument:
            self.instrument_data = {
                'name': instrument[1],
                'description': instrument[2] or '',
                'inventory_number': instrument[3] or '',
                'serial_number': instrument[4] or '',
                'category': instrument[5] or '',
                'location': instrument[6] or '',
                'purchase_date': instrument[7] or '',
                'price': instrument[8] or 0,
                'status': instrument[9]
            }
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        fields = [
            ("Название*:", "name"),
            ("Описание:", "description"),
            ("Инвентарный номер*:", "inventory_number"),
            ("Серийный номер:", "serial_number"),
            ("Категория:", "category"),
            ("Адрес:", "location"),
            ("Дата покупки:", "purchase_date"),
            ("Цена:", "price"),
        ]
        
        self.entries = {}
        
        for i, (label, field) in enumerate(fields):
            ttk.Label(main_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=5)
            
            if field == "description":
                entry = tk.Text(main_frame, width=50, height=3)
                entry.insert("1.0", self.instrument_data[field])
                entry.grid(row=i, column=1, pady=5, sticky=tk.W)
            elif field == "purchase_date":
                entry = create_russian_date_entry(
                    main_frame, 
                    width=48, 
                    date_pattern='yyyy-mm-dd'
                )
                if self.instrument_data[field]:
                    entry.set_date(self.instrument_data[field])
                entry.grid(row=i, column=1, pady=5, sticky=tk.W)
            else:
                entry = ttk.Entry(main_frame, width=50)
                entry.insert(0, str(self.instrument_data[field]))
                entry.grid(row=i, column=1, pady=5, sticky=tk.W)
            
            self.entries[field] = entry
        
        # Статус
        ttk.Label(main_frame, text="Статус:").grid(row=len(fields), column=0, sticky=tk.W, pady=5)
        self.status_var = tk.StringVar(value=self.instrument_data['status'])
        status_combo = ttk.Combobox(
            main_frame, 
            textvariable=self.status_var,
            values=["Активен", "На ремонте", "Списан"],
            state='readonly',
            width=47
        )
        status_combo.grid(row=len(fields), column=1, pady=5, sticky=tk.W)
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=20)
        
        ttk.Button(
            button_frame,
            text="Сохранить",
            command=self.save
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Отмена",
            command=self.dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
        
    def save(self):
        name = self.entries['name'].get().strip()
        description = self.entries['description'].get("1.0", tk.END).strip()
        inventory_number = self.entries['inventory_number'].get().strip()
        serial_number = self.entries['serial_number'].get().strip()
        category = self.entries['category'].get().strip()
        location = self.entries['location'].get().strip()
        purchase_date = self.entries['purchase_date'].get()
        price_str = self.entries['price'].get().strip()
        status = self.status_var.get()
        
        if not name:
            messagebox.showerror("Ошибка", "Введите название инструмента")
            return
        
        if not inventory_number:
            messagebox.showerror("Ошибка", "Введите инвентарный номер")
            return
        
        price = 0.0
        if price_str:
            try:
                price = float(price_str)
            except ValueError:
                messagebox.showerror("Ошибка", "Неверный формат цены")
                return
        
        data = (
            name, description, inventory_number, serial_number, category,
            location, purchase_date, price, status
        )
        
        if self.db.update_instrument(self.instrument_id, data):
            messagebox.showinfo("Успех", "Инструмент обновлен")
            self.callback()
            self.dialog.destroy()
        else:
            messagebox.showerror("Ошибка", "Не удалось обновить инструмент (возможно, инвентарный номер уже существует)")


# ========== СОТРУДНИКИ ==========

class AddEmployeeDialog:
    def __init__(self, parent, db, callback):
        self.db = db
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Добавить сотрудника")
        default_geometry = "500x450"
        window_config.restore_window(self.dialog, "AddEmployeeDialog", default_geometry)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Закрытие по ESC
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        
        self.create_widgets()
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        fields = [
            ("ФИО*:", "full_name"),
            ("Должность:", "position"),
            ("Отдел:", "department"),
            ("Телефон:", "phone"),
            ("Email:", "email"),
        ]
        
        self.entries = {}
        
        for i, (label, field) in enumerate(fields):
            ttk.Label(main_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=5)
            entry = ttk.Entry(main_frame, width=35)
            entry.grid(row=i, column=1, pady=5, sticky=tk.W)
            self.entries[field] = entry
        
        # Статус
        ttk.Label(main_frame, text="Статус:").grid(row=len(fields), column=0, sticky=tk.W, pady=5)
        self.status_var = tk.StringVar(value="Активен")
        status_combo = ttk.Combobox(
            main_frame, 
            textvariable=self.status_var,
            values=["Активен", "Уволен"],
            state='readonly',
            width=32
        )
        status_combo.grid(row=len(fields), column=1, pady=5, sticky=tk.W)
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=20)
        
        ttk.Button(
            button_frame,
            text="Сохранить",
            command=self.save
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Отмена",
            command=self.dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
        
    def save(self):
        full_name = self.entries['full_name'].get().strip()
        position = self.entries['position'].get().strip()
        department = self.entries['department'].get().strip()
        phone = self.entries['phone'].get().strip()
        email = self.entries['email'].get().strip()
        status = self.status_var.get()
        
        if not full_name:
            messagebox.showerror("Ошибка", "Введите ФИО сотрудника")
            return
        
        data = (full_name, position, department, phone, email, status)
        
        if self.db.add_employee(data):
            messagebox.showinfo("Успех", "Сотрудник добавлен")
            self.callback()
            self.dialog.destroy()
        else:
            messagebox.showerror("Ошибка", "Не удалось добавить сотрудника")


class EditEmployeeDialog:
    def __init__(self, parent, db, employee_id, callback):
        self.db = db
        self.employee_id = employee_id
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Редактировать сотрудника")
        default_geometry = "500x450"
        window_config.restore_window(self.dialog, "EditEmployeeDialog", default_geometry)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Закрытие по ESC
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        
        self.load_data()
        self.create_widgets()
        
    def load_data(self):
        employee = self.db.get_employee_by_id(self.employee_id)
        if employee:
            self.employee_data = {
                'full_name': employee[1],
                'position': employee[2] or '',
                'department': employee[3] or '',
                'phone': employee[4] or '',
                'email': employee[5] or '',
                'status': employee[6]
            }
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        fields = [
            ("ФИО*:", "full_name"),
            ("Должность:", "position"),
            ("Отдел:", "department"),
            ("Телефон:", "phone"),
            ("Email:", "email"),
        ]
        
        self.entries = {}
        
        for i, (label, field) in enumerate(fields):
            ttk.Label(main_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=5)
            entry = ttk.Entry(main_frame, width=35)
            entry.insert(0, self.employee_data[field])
            entry.grid(row=i, column=1, pady=5, sticky=tk.W)
            self.entries[field] = entry
        
        # Статус
        ttk.Label(main_frame, text="Статус:").grid(row=len(fields), column=0, sticky=tk.W, pady=5)
        self.status_var = tk.StringVar(value=self.employee_data['status'])
        status_combo = ttk.Combobox(
            main_frame, 
            textvariable=self.status_var,
            values=["Активен", "Уволен"],
            state='readonly',
            width=32
        )
        status_combo.grid(row=len(fields), column=1, pady=5, sticky=tk.W)
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=20)
        
        ttk.Button(
            button_frame,
            text="Сохранить",
            command=self.save
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Отмена",
            command=self.dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
        
    def save(self):
        full_name = self.entries['full_name'].get().strip()
        position = self.entries['position'].get().strip()
        department = self.entries['department'].get().strip()
        phone = self.entries['phone'].get().strip()
        email = self.entries['email'].get().strip()
        status = self.status_var.get()
        
        if not full_name:
            messagebox.showerror("Ошибка", "Введите ФИО сотрудника")
            return
        
        data = (full_name, position, department, phone, email, status)
        
        if self.db.update_employee(self.employee_id, data):
            messagebox.showinfo("Успех", "Сотрудник обновлен")
            self.callback()
            self.dialog.destroy()
        else:
            messagebox.showerror("Ошибка", "Не удалось обновить сотрудника")


# ========== ВЫДАЧА И ВОЗВРАТ ==========

class IssueInstrumentDialog:
    def __init__(self, parent, db, callback):
        self.db = db
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Выдать инструмент")
        default_geometry = "800x650"
        window_config.restore_window(self.dialog, "IssueInstrumentDialog", default_geometry)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Закрытие по ESC
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        
        # Список выбранных инструментов для выдачи
        self.selected_instruments = []  # Список кортежей (instrument_id, display_text)
        self.address_placeholder = "Не указан"
        self.address_display_to_id = {}
        
        self.load_data()
        self.create_widgets()
    
    def on_instrument_keyrelease(self, event, combo):
        """Обработка ввода текста в поле инструмента для автодополнения"""
        # Игнорируем служебные клавиши
        if event.keysym in ('Up', 'Down', 'Return', 'Tab', 'Escape', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R'):
            return
        
        # Обновление значений происходит через trace_add, но здесь можем добавить дополнительную логику
        pass
    
    def on_employee_keyrelease(self, event, combo):
        """Обработка ввода текста в поле сотрудника для автодополнения"""
        # Игнорируем служебные клавиши
        if event.keysym in ('Up', 'Down', 'Return', 'Tab', 'Escape', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R'):
            return
        
        # Обновление значений происходит через trace_add, но здесь можем добавить дополнительную логику
        pass
        
    def update_instrument_values(self, *args):
        """Обновление списка значений для инструмента при изменении текста"""
        if hasattr(self, 'instrument_combo') and hasattr(self, 'all_instrument_values'):
            # Отменяем предыдущий запрос, если он был
            if hasattr(self, '_instrument_update_id'):
                self.dialog.after_cancel(self._instrument_update_id)
            
            # Запланируем обновление через небольшую задержку
            def do_update():
                value = self.instrument_var.get().strip()
                if value:
                    filtered = [item for item in self.all_instrument_values 
                               if value.lower() in item.lower()]
                    self.instrument_combo['values'] = filtered
                else:
                    self.instrument_combo['values'] = self.all_instrument_values
            
            self._instrument_update_id = self.dialog.after(100, do_update)
    
    def update_employee_values(self, *args):
        """Обновление списка значений для сотрудника при изменении текста"""
        if hasattr(self, 'employee_combo') and hasattr(self, 'all_employee_values'):
            # Отменяем предыдущий запрос, если он был
            if hasattr(self, '_employee_update_id'):
                self.dialog.after_cancel(self._employee_update_id)
            
            # Запланируем обновление через небольшую задержку
            def do_update():
                value = self.employee_var.get().strip()
                if value:
                    filtered = [item for item in self.all_employee_values 
                               if value.lower() in item.lower()]
                    self.employee_combo['values'] = filtered
                else:
                    self.employee_combo['values'] = self.all_employee_values
            
            self._employee_update_id = self.dialog.after(100, do_update)
    
    def _format_address_display(self, address_row):
        """Формирование строки отображения адреса"""
        if not address_row:
            return ""
        _, name, full_address = address_row
        name = (name or '').strip()
        full_address = (full_address or '').strip()

        if full_address and full_address.lower() != name.lower():
            return f"{name} — {full_address}" if name else full_address
        return name or full_address

    def refresh_address_values(self, selected_id=None):
        """Обновление списка адресов"""
        addresses = self.db.get_addresses()
        self.address_display_to_id = {}

        values = []
        for address in addresses:
            display = self._format_address_display(address)
            if not display:
                display = f"Адрес #{address[0]}"
            self.address_display_to_id[display] = address[0]
            values.append(display)

        combo_values = [self.address_placeholder] + values
        if hasattr(self, 'address_combo'):
            self.address_combo['values'] = combo_values

        if selected_id:
            for display, addr_id in self.address_display_to_id.items():
                if addr_id == selected_id:
                    self.address_var.set(display)
                    break
            else:
                self.address_var.set(self.address_placeholder)
        else:
            current_value = self.address_var.get() if hasattr(self, 'address_var') else ''
            if current_value not in combo_values:
                self.address_var.set(self.address_placeholder)

    def open_add_address_dialog(self):
        """Открытие диалога добавления адреса"""
        dialog = AddAddressDialog(self.dialog, self.db, callback=lambda: self.refresh_address_values())
        self.dialog.wait_window(dialog.dialog)
        if dialog.result_id:
            self.refresh_address_values(selected_id=dialog.result_id)
    
    def load_data(self):
        # Загрузка списка инструментов (только доступные)
        self.instruments = self.db.get_instruments()
        self.instrument_dict = {f"{i[2]} - {i[1]}": i for i in self.instruments if i[6] == 'Доступен'}
        
        # Загрузка списка сотрудников
        self.employees = self.db.get_employees()
        self.employee_dict = {f"{e[1]} (ID: {e[0]})": e for e in self.employees if e[6] == 'Активен'}
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Выбор инструмента
        instrument_frame = ttk.Frame(main_frame)
        instrument_frame.grid(row=0, column=0, columnspan=2, sticky=tk.W+tk.E, pady=5)
        
        ttk.Label(instrument_frame, text="Инструмент:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.instrument_var = tk.StringVar()
        instrument_combo = ttk.Combobox(
            instrument_frame,
            textvariable=self.instrument_var,
            values=sorted(list(self.instrument_dict.keys())),
            state='normal',  # Разрешаем ввод с клавиатуры
            width=35
        )
        instrument_combo.grid(row=0, column=1, pady=5, padx=5, sticky=tk.W)
        # Настройка автодополнения
        instrument_combo.bind('<KeyRelease>', lambda e: self.on_instrument_keyrelease(e, instrument_combo))
        # Также отслеживаем изменения через StringVar
        self.instrument_var.trace_add('write', lambda *args: self.update_instrument_values())
        self.instrument_combo = instrument_combo
        self.all_instrument_values = sorted(list(self.instrument_dict.keys()))
        
        # Кнопка добавления инструмента
        ttk.Button(
            instrument_frame,
            text="Добавить",
            command=self.add_instrument_to_list
        ).grid(row=0, column=2, pady=5, padx=5)
        
        # Список выбранных инструментов
        ttk.Label(main_frame, text="Выбранные инструменты:").grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        
        # Фрейм для списка инструментов
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W+tk.E+tk.N+tk.S, pady=5)
        
        # Treeview для списка выбранных инструментов
        columns = ('Инструмент',)
        self.instruments_list = ttk.Treeview(list_frame, columns=columns, show='headings', height=6)
        self.instruments_list.heading('Инструмент', text='Инструмент')
        self.instruments_list.column('Инструмент', width=650)
        self.instruments_list.grid(row=0, column=0, sticky=tk.W+tk.E+tk.N+tk.S)
        
        # Скроллбар для списка
        scrollbar_list = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.instruments_list.yview)
        self.instruments_list.configure(yscroll=scrollbar_list.set)
        scrollbar_list.grid(row=0, column=1, sticky=tk.N+tk.S)
        
        # Кнопка удаления из списка
        ttk.Button(
            list_frame,
            text="Удалить выбранное",
            command=self.remove_instrument_from_list
        ).grid(row=1, column=0, columnspan=2, pady=5)
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Выбор сотрудника
        ttk.Label(main_frame, text="Сотрудник*:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.employee_var = tk.StringVar()
        employee_combo = ttk.Combobox(
            main_frame,
            textvariable=self.employee_var,
            values=list(self.employee_dict.keys()),
            state='normal',  # Разрешаем ввод с клавиатуры
            width=40
        )
        employee_combo.grid(row=3, column=1, pady=5, sticky=tk.W)
        # Настройка автодополнения
        employee_combo.bind('<KeyRelease>', lambda e: self.on_employee_keyrelease(e, employee_combo))
        # Также отслеживаем изменения через StringVar
        self.employee_var.trace_add('write', lambda *args: self.update_employee_values())
        self.employee_combo = employee_combo
        self.all_employee_values = list(self.employee_dict.keys())

        # Адрес выдачи
        ttk.Label(main_frame, text="Адрес выдачи:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.address_var = tk.StringVar()
        self.address_combo = ttk.Combobox(
            main_frame,
            textvariable=self.address_var,
            state='readonly',
            width=40
        )
        self.address_combo.grid(row=4, column=1, pady=5, sticky=tk.W)
        ttk.Button(
            main_frame,
            text="Добавить адрес",
            command=self.open_add_address_dialog
        ).grid(row=4, column=2, pady=5, padx=5, sticky=tk.W)
        self.refresh_address_values()
        
        # Ожидаемая дата возврата
        ttk.Label(main_frame, text="Ожидаемая дата возврата:").grid(row=5, column=0, sticky=tk.W, pady=5)
        default_date = datetime.now() + timedelta(days=7)
        self.return_date = create_russian_date_entry(
            main_frame, 
            width=39, 
            date_pattern='yyyy-mm-dd'
        )
        self.return_date.set_date(default_date)
        self.return_date.grid(row=5, column=1, pady=5, sticky=tk.W)
        
        # Выдал
        ttk.Label(main_frame, text="Выдал*:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.issued_by_entry = ttk.Entry(main_frame, width=42)
        self.issued_by_entry.insert(0, "Кладовщик")
        self.issued_by_entry.grid(row=6, column=1, pady=5, sticky=tk.W)
        
        # Примечание
        ttk.Label(main_frame, text="Примечание:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.notes_text = tk.Text(main_frame, width=42, height=4)
        self.notes_text.grid(row=7, column=1, pady=5, sticky=tk.W)
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=20)
        
        ttk.Button(
            button_frame,
            text="Выдать все",
            command=self.issue
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Отмена",
            command=self.dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
        
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
    def add_instrument_to_list(self):
        """Добавление инструмента в список для выдачи"""
        instrument_text = self.instrument_var.get().strip()
        if not instrument_text:
            messagebox.showwarning("Предупреждение", "Введите или выберите инструмент")
            return
        
        # Получение ID инструмента
        selected_instrument = None
        instrument_id = None
        
        if instrument_text in self.instrument_dict:
            selected_instrument = self.instrument_dict[instrument_text]
            instrument_id = selected_instrument[0]
        else:
            # Пытаемся найти инструмент по частичному совпадению
            found = False
            for key, instrument in self.instrument_dict.items():
                if (instrument_text.lower() in key.lower() or 
                    instrument_text.lower() in instrument[1].lower() or
                    instrument_text.lower() in instrument[2].lower()):
                    selected_instrument = instrument
                    instrument_id = instrument[0]
                    found = True
                    break
            
            if not found:
                messagebox.showerror("Ошибка", f"Инструмент '{instrument_text}' не найден.")
                return
        
        # Проверяем, не добавлен ли уже этот инструмент
        for inst_id, _ in self.selected_instruments:
            if inst_id == instrument_id:
                messagebox.showwarning("Предупреждение", "Этот инструмент уже добавлен в список")
                return
        
        # Проверяем, доступен ли инструмент
        if selected_instrument[6] != 'Доступен':
            messagebox.showerror("Ошибка", f"Инструмент '{instrument_text}' недоступен для выдачи (статус: {selected_instrument[6]})")
            return
        
        # Добавляем в список
        display_text = f"{selected_instrument[2]} - {selected_instrument[1]}"
        self.selected_instruments.append((instrument_id, display_text))
        self.instruments_list.insert('', tk.END, values=(display_text,))
        
        # Очищаем поле ввода
        self.instrument_var.set('')
    
    def remove_instrument_from_list(self):
        """Удаление инструмента из списка"""
        selected = self.instruments_list.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите инструмент для удаления из списка")
            return
        
        # Удаляем в обратном порядке, чтобы индексы не сдвигались
        items_to_delete = list(selected)
        for item in reversed(items_to_delete):
            # Получаем значение из Treeview
            item_values = self.instruments_list.item(item, 'values')
            if item_values:
                display_text = item_values[0]
                # Находим и удаляем из списка selected_instruments
                self.selected_instruments = [
                    (inst_id, text) for inst_id, text in self.selected_instruments 
                    if text != display_text
                ]
            self.instruments_list.delete(item)
    
    def issue(self):
        # Валидация
        if not self.selected_instruments:
            messagebox.showerror("Ошибка", "Добавьте хотя бы один инструмент в список")
            return
        
        employee_text = self.employee_var.get().strip()
        if not employee_text:
            messagebox.showerror("Ошибка", "Введите или выберите сотрудника")
            return
        
        issued_by = self.issued_by_entry.get().strip()
        if not issued_by:
            messagebox.showerror("Ошибка", "Введите, кто выдает инструмент")
            return
        
        address_id = None
        if hasattr(self, 'address_var'):
            address_value = self.address_var.get().strip()
            if address_value and address_value != self.address_placeholder:
                address_id = self.address_display_to_id.get(address_value)
                if address_id is None:
                    messagebox.showerror(
                        "Ошибка", 
                        "Выберите адрес из списка или добавьте новый с помощью кнопки 'Добавить адрес'"
                    )
                    return
        
        # Получение ID сотрудника
        if employee_text in self.employee_dict:
            selected_employee = self.employee_dict[employee_text]
            employee_id = selected_employee[0]
        else:
            # Пытаемся найти сотрудника по частичному совпадению
            found = False
            for key, employee in self.employee_dict.items():
                if (employee_text.lower() in key.lower() or 
                    employee_text.lower() in employee[1].lower() or
                    employee_text == str(employee[0])):
                    selected_employee = employee
                    employee_id = employee[0]
                    found = True
                    break
            
            if not found:
                messagebox.showerror("Ошибка", f"Сотрудник '{employee_text}' не найден. Выберите из списка или введите точное ФИО.")
                return
        
        return_date = self.return_date.get()
        notes = self.notes_text.get("1.0", tk.END).strip()
        
        # Выполнение выдачи для всех инструментов
        success_count = 0
        error_messages = []
        
        for instrument_id, display_text in self.selected_instruments:
            success, message = self.db.issue_instrument(
                instrument_id, employee_id, return_date, notes, issued_by, address_id=address_id
            )
            
            if success:
                success_count += 1
            else:
                error_messages.append(f"{display_text}: {message}")
        
        # Показываем результат
        if success_count == len(self.selected_instruments):
            messagebox.showinfo("Успех", f"Успешно выдано инструментов: {success_count}")
            self.callback()
            self.dialog.destroy()
        elif success_count > 0:
            error_text = "\n".join(error_messages)
            messagebox.showwarning(
                "Частичный успех", 
                f"Выдано инструментов: {success_count} из {len(self.selected_instruments)}\n\nОшибки:\n{error_text}"
            )
            self.callback()
        else:
            error_text = "\n".join(error_messages)
            messagebox.showerror("Ошибка", f"Не удалось выдать инструменты:\n{error_text}")


class ReturnInstrumentDialog:
    def __init__(self, parent, db, issue_id, callback):
        self.db = db
        self.issue_id = issue_id
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Оформить возврат")
        default_geometry = "500x400"
        window_config.restore_window(self.dialog, "ReturnInstrumentDialog", default_geometry)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Закрытие по ESC
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        
        self.load_data()
        self.create_widgets()
        
    def load_data(self):
        self.issue = self.db.get_issue_by_id(self.issue_id)
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Информация о выдаче
        info_frame = ttk.LabelFrame(main_frame, text="Информация о выдаче", padding="10")
        info_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(info_frame, text=f"Инв. номер: {self.issue[2]}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Инструмент: {self.issue[3]}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Сотрудник: {self.issue[5]}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Дата выдачи: {self.issue[6]}").pack(anchor=tk.W)
        
        address_display = self.issue[11] or self.issue[10]
        if address_display:
            ttk.Label(info_frame, text=f"Адрес: {address_display}").pack(anchor=tk.W)
        
        if self.issue[8]:
            ttk.Label(info_frame, text=f"Примечание при выдаче: {self.issue[8]}").pack(anchor=tk.W)
        
        # Форма возврата
        return_frame = ttk.LabelFrame(main_frame, text="Возврат", padding="10")
        return_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Принял
        ttk.Label(return_frame, text="Принял*:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.returned_by_entry = ttk.Entry(return_frame, width=35)
        self.returned_by_entry.insert(0, "Кладовщик")
        self.returned_by_entry.grid(row=0, column=1, pady=5, sticky=tk.W)
        
        # Примечание
        ttk.Label(return_frame, text="Примечание:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.notes_text = tk.Text(return_frame, width=35, height=5)
        self.notes_text.grid(row=1, column=1, pady=5, sticky=tk.W)
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(
            button_frame,
            text="Оформить возврат",
            command=self.return_instrument
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Отмена",
            command=self.dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
        
    def return_instrument(self):
        returned_by = self.returned_by_entry.get().strip()
        if not returned_by:
            messagebox.showerror("Ошибка", "Введите, кто принимает инструмент")
            return
        
        notes = self.notes_text.get("1.0", tk.END).strip()
        
        success, message = self.db.return_instrument(self.issue_id, notes, returned_by)
        
        if success:
            messagebox.showinfo("Успех", message)
            self.callback()
            self.dialog.destroy()
        else:
            messagebox.showerror("Ошибка", message)

