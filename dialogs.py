"""
Диалоговые окна для системы учета инструмента
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
from tkcalendar import DateEntry, Calendar
from window_config import WindowConfig
import locale
import os
import shutil
import uuid
from PIL import Image, ImageTk
from barcode_utils import barcode_manager

# Глобальный объект для управления конфигурацией окон
window_config = WindowConfig()

# Глобальный реестр открытых диалогов: {window_name: dialog}
_open_dialogs = {}

def register_dialog(dialog, window_name):
    """Регистрация открытого диалога для отслеживания"""
    _open_dialogs[window_name] = dialog
    
    # Удаляем из реестра при закрытии
    def on_destroy(event=None):
        if window_name in _open_dialogs:
            del _open_dialogs[window_name]
    dialog.bind('<Destroy>', on_destroy)

def save_all_dialogs_geometry():
    """Сохранение геометрии всех открытых диалогов"""
    for window_name, dialog in list(_open_dialogs.items()):
        try:
            if dialog.winfo_exists() and dialog.winfo_viewable():
                geometry = dialog.geometry()
                if geometry and geometry != "1x1+0+0":  # Игнорируем некорректную геометрию
                    window_config.save_window_geometry(window_name, geometry)
        except:
            pass

def close_dialog_with_save(dialog, window_name):
    """Закрытие диалога с сохранением настроек окна (размер и положение)"""
    try:
        if dialog.winfo_exists():
            # Получаем геометрию окна (формат: "widthxheight+x+y")
            geometry = dialog.geometry()
            if geometry:
                # Сохраняем геометрию перед закрытием
                window_config.save_window_geometry(window_name, geometry)
    except Exception as e:
        # Игнорируем ошибки при сохранении, но пытаемся закрыть окно
        pass
    try:
        if dialog.winfo_exists():
            dialog.destroy()
    except:
        pass

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
        register_dialog(self.dialog, "AddAddressDialog")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Закрытие по ESC и через крестик с сохранением настроек
        def close_with_save():
            close_dialog_with_save(self.dialog, "AddAddressDialog")
        self.dialog.protocol("WM_DELETE_WINDOW", close_with_save)
        self.dialog.bind('<Escape>', lambda e: close_with_save())

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
            command=lambda: close_dialog_with_save(self.dialog, "AddAddressDialog")
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
        close_dialog_with_save(self.dialog, "AddAddressDialog")


class EditAddressDialog:
    def __init__(self, parent, db, address_id, callback):
        self.db = db
        self.address_id = address_id
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Редактировать адрес")
        default_geometry = "420x220"
        window_config.restore_window(self.dialog, "EditAddressDialog", default_geometry)
        register_dialog(self.dialog, "EditAddressDialog")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Закрытие по ESC и через крестик с сохранением настроек
        def close_with_save():
            close_dialog_with_save(self.dialog, "EditAddressDialog")
        self.dialog.protocol("WM_DELETE_WINDOW", close_with_save)
        self.dialog.bind('<Escape>', lambda e: close_with_save())
        
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
            command=lambda: close_dialog_with_save(self.dialog, "EditAddressDialog")
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
            close_dialog_with_save(self.dialog, "EditAddressDialog")
        else:
            messagebox.showerror("Ошибка", f"Не удалось обновить адрес:\n{message}")

class AddInstrumentDialog:
    def __init__(self, parent, db, callback):
        self.db = db
        self.callback = callback
        self.photo_path = None
        self.photo_preview_label = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Добавить инструмент")
        default_geometry = "900x700"
        window_config.restore_window(self.dialog, "AddInstrumentDialog", default_geometry)
        register_dialog(self.dialog, "AddInstrumentDialog")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Закрытие по ESC и через крестик с сохранением настроек
        def close_with_save():
            close_dialog_with_save(self.dialog, "AddInstrumentDialog")
        self.dialog.protocol("WM_DELETE_WINDOW", close_with_save)
        self.dialog.bind('<Escape>', lambda e: close_with_save())
        
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
            ("Штрих-код:", "barcode"),
            ("Категория:", "category"),
        ]
        
        self.entries = {}
        
        for i, (label, field) in enumerate(fields):
            ttk.Label(main_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=5)

            if field == "description":
                entry = tk.Text(main_frame, width=50, height=3)
                entry.grid(row=i, column=1, pady=5, sticky=tk.W)
            elif field == "barcode":
                # Контейнер для поля штрих-кода и кнопок
                barcode_frame = ttk.Frame(main_frame)
                barcode_frame.grid(row=i, column=1, pady=5, sticky=tk.W)

                entry = ttk.Entry(barcode_frame, width=30)
                entry.pack(side=tk.LEFT)

                # Кнопка генерации штрих-кода
                ttk.Button(
                    barcode_frame,
                    text="🔄 Генерировать",
                    command=lambda: self.generate_barcode(entry)
                ).pack(side=tk.LEFT, padx=5)

                # Кнопка просмотра штрих-кода
                ttk.Button(
                    barcode_frame,
                    text="👁 Просмотр",
                    command=lambda: self.preview_barcode(entry.get())
                ).pack(side=tk.LEFT, padx=5)
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
        
        # Фотография
        photo_frame = ttk.LabelFrame(main_frame, text="Фотография", padding="10")
        photo_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=10, sticky=tk.W+tk.E)
        
        photo_buttons_frame = ttk.Frame(photo_frame)
        photo_buttons_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(
            photo_buttons_frame,
            text="Загрузить фото",
            command=self.load_photo
        ).pack(side=tk.TOP, pady=5)
        
        ttk.Button(
            photo_buttons_frame,
            text="Удалить фото",
            command=self.remove_photo
        ).pack(side=tk.TOP, pady=5)
        
        # Превью фотографии
        self.photo_preview_label = tk.Label(photo_frame, text="Фото не загружено", width=30, height=10, bg='lightgray')
        self.photo_preview_label.pack(side=tk.LEFT, padx=10)
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=len(fields)+2, column=0, columnspan=2, pady=20)
        
        ttk.Button(
            button_frame,
            text="Сохранить",
            command=self.save
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Отмена",
            command=lambda: close_dialog_with_save(self.dialog, "AddInstrumentDialog")
        ).pack(side=tk.LEFT, padx=5)
        
    def save(self):
        # Получение значений
        name = self.entries['name'].get().strip()
        description = self.entries['description'].get("1.0", tk.END).strip()
        inventory_number = self.entries['inventory_number'].get().strip()
        serial_number = self.entries['serial_number'].get().strip()
        barcode = self.entries['barcode'].get().strip()
        category = self.entries['category'].get().strip()
        status = self.status_var.get()

        # Валидация
        if not name:
            messagebox.showerror("Ошибка", "Введите название инструмента")
            return

        if not inventory_number:
            messagebox.showerror("Ошибка", "Введите инвентарный номер")
            return

        # Проверка штрих-кода
        if barcode and not barcode_manager.validate_barcode(barcode):
            messagebox.showerror("Ошибка", "Некорректный формат штрих-кода")
            return

        # Сохранение
        data = (
            name, description, inventory_number, serial_number, category,
            status, self.photo_path, barcode
        )
        
        if self.db.add_instrument(data):
            messagebox.showinfo("Успех", "Инструмент добавлен")
            self.callback()
            close_dialog_with_save(self.dialog, "AddInstrumentDialog")
        else:
            messagebox.showerror("Ошибка", "Не удалось добавить инструмент (возможно, инвентарный номер уже существует)")

    def generate_barcode(self, entry_widget):
        """Генерация уникального штрих-кода"""
        barcode = barcode_manager.generate_unique_barcode()
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, barcode)
        messagebox.showinfo("Штрих-код", f"Сгенерирован штрих-код: {barcode}")

    def preview_barcode(self, barcode_str):
        """Просмотр штрих-кода"""
        if not barcode_str:
            messagebox.showwarning("Предупреждение", "Введите штрих-код для просмотра")
            return

        if not barcode_manager.validate_barcode(barcode_str):
            messagebox.showerror("Ошибка", "Некорректный формат штрих-кода")
            return

        # Создаем диалог для просмотра штрих-кода
        preview_dialog = tk.Toplevel(self.dialog)
        preview_dialog.title("Просмотр штрих-кода")
        preview_dialog.geometry("400x250")
        preview_dialog.transient(self.dialog)
        preview_dialog.grab_set()

        ttk.Label(preview_dialog, text=f"Штрих-код: {barcode_str}", font=('Arial', 12, 'bold')).pack(pady=10)

        # Получаем изображение штрих-кода
        barcode_image = barcode_manager.get_barcode_image(barcode_str, width=350, height=100)
        if barcode_image:
            image_label = tk.Label(preview_dialog, image=barcode_image)
            image_label.image = barcode_image  # Сохраняем ссылку
            image_label.pack(pady=10)
        else:
            ttk.Label(preview_dialog, text="Ошибка генерации изображения", foreground='red').pack(pady=10)

        ttk.Button(preview_dialog, text="Закрыть", command=preview_dialog.destroy).pack(pady=10)

    def load_photo(self):
        """Загрузка фотографии инструмента"""
        file_path = filedialog.askopenfilename(
            title="Выберите фотографию",
            filetypes=[("Изображения", "*.jpg *.jpeg *.png *.gif *.bmp"), ("Все файлы", "*.*")]
        )
        
        if file_path:
            try:
                # Копируем файл в папку photos/instruments
                photos_dir = 'photos/instruments'
                if not os.path.exists(photos_dir):
                    os.makedirs(photos_dir)
                
                # Генерируем уникальное имя файла
                file_ext = os.path.splitext(file_path)[1]
                unique_filename = f"{uuid.uuid4()}{file_ext}"
                dest_path = os.path.join(photos_dir, unique_filename)
                
                shutil.copy2(file_path, dest_path)
                self.photo_path = dest_path
                
                # Отображаем превью
                self.display_photo_preview(dest_path)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить фотографию: {e}")
    
    def remove_photo(self):
        """Удаление фотографии"""
        if self.photo_path and os.path.exists(self.photo_path):
            try:
                os.remove(self.photo_path)
            except:
                pass
        
        self.photo_path = None
        self.photo_preview_label.config(image='', text="Фото не загружено")
        self.photo_preview_label.image = None
    
    def display_photo_preview(self, photo_path):
        """Отображение превью фотографии"""
        try:
            # Загружаем и изменяем размер изображения
            img = Image.open(photo_path)
            img.thumbnail((200, 200), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            self.photo_preview_label.config(image=photo, text='')
            self.photo_preview_label.image = photo  # Сохраняем ссылку
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось отобразить фотографию: {e}")


class EditInstrumentDialog:
    def __init__(self, parent, db, instrument_id, callback):
        self.db = db
        self.instrument_id = instrument_id
        self.callback = callback
        self.photo_path = None
        self.photo_preview_label = None
        self.old_photo_path = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Редактировать инструмент")
        default_geometry = "900x700"
        window_config.restore_window(self.dialog, "EditInstrumentDialog", default_geometry)
        register_dialog(self.dialog, "EditInstrumentDialog")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Закрытие по ESC и через крестик с сохранением настроек
        def close_with_save():
            close_dialog_with_save(self.dialog, "EditInstrumentDialog")
        self.dialog.protocol("WM_DELETE_WINDOW", close_with_save)
        self.dialog.bind('<Escape>', lambda e: close_with_save())
        
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
                'barcode': instrument[8] if len(instrument) > 8 else '',
                'category': instrument[5] or '',
                'status': instrument[6],
                'photo_path': instrument[7] if len(instrument) > 7 else ''
            }
            self.photo_path = self.instrument_data.get('photo_path') or None
            self.old_photo_path = self.photo_path
        
    def create_widgets(self):
        # Основной контейнер с прокруткой для содержимого
        content_frame = ttk.Frame(self.dialog)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Создаем скроллируемый контейнер для полей формы
        canvas = tk.Canvas(content_frame)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Функция для обновления размера окна в canvas
        def configure_scroll_region(event=None):
            canvas.update_idletasks()
            bbox = canvas.bbox("all")
            if bbox:
                canvas.configure(scrollregion=bbox)
        
        scrollable_frame.bind("<Configure>", configure_scroll_region)
        
        main_frame = ttk.Frame(scrollable_frame, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        fields = [
            ("Название*:", "name"),
            ("Описание:", "description"),
            ("Инвентарный номер*:", "inventory_number"),
            ("Серийный номер:", "serial_number"),
            ("Штрих-код:", "barcode"),
            ("Категория:", "category"),
        ]
        
        self.entries = {}
        
        for i, (label, field) in enumerate(fields):
            ttk.Label(main_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=5)

            if field == "description":
                entry = tk.Text(main_frame, width=50, height=3)
                entry.insert("1.0", self.instrument_data[field])
                entry.grid(row=i, column=1, pady=5, sticky=tk.W)
            elif field == "barcode":
                # Контейнер для поля штрих-кода и кнопок
                barcode_frame = ttk.Frame(main_frame)
                barcode_frame.grid(row=i, column=1, pady=5, sticky=tk.W)

                entry = ttk.Entry(barcode_frame, width=30)
                entry.insert(0, str(self.instrument_data.get(field, '')))
                entry.pack(side=tk.LEFT)

                # Кнопка генерации штрих-кода
                ttk.Button(
                    barcode_frame,
                    text="🔄 Генерировать",
                    command=lambda: self.generate_barcode(entry)
                ).pack(side=tk.LEFT, padx=5)

                # Кнопка просмотра штрих-кода
                ttk.Button(
                    barcode_frame,
                    text="👁 Просмотр",
                    command=lambda: self.preview_barcode(entry.get())
                ).pack(side=tk.LEFT, padx=5)
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
            values=["Доступен", "Выдан", "На ремонте", "Списан"],
            state='readonly',
            width=47
        )
        status_combo.grid(row=len(fields), column=1, pady=5, sticky=tk.W)
        
        # Фотография
        photo_frame = ttk.LabelFrame(main_frame, text="Фотография", padding="10")
        photo_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=10, sticky=tk.W+tk.E)
        
        photo_buttons_frame = ttk.Frame(photo_frame)
        photo_buttons_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(
            photo_buttons_frame,
            text="Загрузить фото",
            command=self.load_photo
        ).pack(side=tk.TOP, pady=5)
        
        ttk.Button(
            photo_buttons_frame,
            text="Удалить фото",
            command=self.remove_photo
        ).pack(side=tk.TOP, pady=5)
        
        # Превью фотографии
        self.photo_preview_label = tk.Label(photo_frame, text="Фото не загружено", width=30, height=10, bg='lightgray')
        self.photo_preview_label.pack(side=tk.LEFT, padx=10)
        
        # Загружаем существующую фотографию, если есть
        if self.photo_path:
            if os.path.exists(self.photo_path):
                self.display_photo_preview(self.photo_path)
            else:
                # Если файл не найден, очищаем путь
                self.photo_path = None
                self.old_photo_path = None
        
        # Размещаем canvas и scrollbar в content_frame
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Привязка прокрутки колесом мыши ко всем элементам
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # Привязываем прокрутку к canvas и всем дочерним элементам
        canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
        main_frame.bind("<MouseWheel>", _on_mousewheel)
        
        # Обновляем область прокрутки при изменении содержимого
        main_frame.bind("<Configure>", configure_scroll_region)
        
        # Настройка grid для правильного отображения
        main_frame.grid_columnconfigure(1, weight=1)
        
        # Кнопки - размещаем внизу диалога отдельно, чтобы они всегда были видны
        button_frame = ttk.Frame(self.dialog, padding="10")
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Button(
            button_frame,
            text="Сохранить",
            command=self.save
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Отмена",
            command=lambda: close_dialog_with_save(self.dialog, "EditInstrumentDialog")
        ).pack(side=tk.LEFT, padx=5)
        
    def save(self):
        name = self.entries['name'].get().strip()
        description = self.entries['description'].get("1.0", tk.END).strip()
        inventory_number = self.entries['inventory_number'].get().strip()
        serial_number = self.entries['serial_number'].get().strip()
        barcode = self.entries['barcode'].get().strip()
        category = self.entries['category'].get().strip()
        status = self.status_var.get()

        if not name:
            messagebox.showerror("Ошибка", "Введите название инструмента")
            return

        if not inventory_number:
            messagebox.showerror("Ошибка", "Введите инвентарный номер")
            return

        # Проверка штрих-кода
        if barcode and not barcode_manager.validate_barcode(barcode):
            messagebox.showerror("Ошибка", "Некорректный формат штрих-кода")
            return

        # Удаляем старое фото, если было загружено новое или удалено
        if self.old_photo_path and self.old_photo_path != self.photo_path:
            if os.path.exists(self.old_photo_path):
                try:
                    os.remove(self.old_photo_path)
                except:
                    pass

        data = (
            name, description, inventory_number, serial_number, category,
            status, self.photo_path, barcode
        )
        
        if self.db.update_instrument(self.instrument_id, data):
            messagebox.showinfo("Успех", "Инструмент обновлен")
            self.callback()
            close_dialog_with_save(self.dialog, "EditInstrumentDialog")
        else:
            messagebox.showerror("Ошибка", "Не удалось обновить инструмент (возможно, инвентарный номер уже существует)")

    def generate_barcode(self, entry_widget):
        """Генерация уникального штрих-кода"""
        barcode = barcode_manager.generate_unique_barcode()
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, barcode)
        messagebox.showinfo("Штрих-код", f"Сгенерирован штрих-код: {barcode}")

    def preview_barcode(self, barcode_str):
        """Просмотр штрих-кода"""
        if not barcode_str:
            messagebox.showwarning("Предупреждение", "Введите штрих-код для просмотра")
            return

        if not barcode_manager.validate_barcode(barcode_str):
            messagebox.showerror("Ошибка", "Некорректный формат штрих-кода")
            return

        # Создаем диалог для просмотра штрих-кода
        preview_dialog = tk.Toplevel(self.dialog)
        preview_dialog.title("Просмотр штрих-кода")
        preview_dialog.geometry("400x250")
        preview_dialog.transient(self.dialog)
        preview_dialog.grab_set()

        ttk.Label(preview_dialog, text=f"Штрих-код: {barcode_str}", font=('Arial', 12, 'bold')).pack(pady=10)

        # Получаем изображение штрих-кода
        barcode_image = barcode_manager.get_barcode_image(barcode_str, width=350, height=100)
        if barcode_image:
            image_label = tk.Label(preview_dialog, image=barcode_image)
            image_label.image = barcode_image  # Сохраняем ссылку
            image_label.pack(pady=10)
        else:
            ttk.Label(preview_dialog, text="Ошибка генерации изображения", foreground='red').pack(pady=10)

        ttk.Button(preview_dialog, text="Закрыть", command=preview_dialog.destroy).pack(pady=10)

    def load_photo(self):
        """Загрузка фотографии инструмента"""
        file_path = filedialog.askopenfilename(
            title="Выберите фотографию",
            filetypes=[("Изображения", "*.jpg *.jpeg *.png *.gif *.bmp"), ("Все файлы", "*.*")]
        )
        
        if file_path:
            try:
                # Удаляем старую фотографию, если она была загружена в этой сессии редактирования
                old_path = self.photo_path
                if old_path and old_path != self.old_photo_path and os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except:
                        pass
                
                # Копируем файл в папку photos/instruments
                photos_dir = 'photos/instruments'
                if not os.path.exists(photos_dir):
                    os.makedirs(photos_dir)
                
                # Генерируем уникальное имя файла
                file_ext = os.path.splitext(file_path)[1]
                unique_filename = f"{uuid.uuid4()}{file_ext}"
                dest_path = os.path.join(photos_dir, unique_filename)
                
                shutil.copy2(file_path, dest_path)
                self.photo_path = dest_path
                
                # Отображаем превью
                self.display_photo_preview(dest_path)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить фотографию: {e}")
    
    def remove_photo(self):
        """Удаление фотографии"""
        # Удаляем текущую фотографию, если она была загружена в этой сессии редактирования
        # (но не удаляем старое фото, которое было в БД - оно удалится при сохранении)
        if self.photo_path and self.photo_path != self.old_photo_path and os.path.exists(self.photo_path):
            try:
                os.remove(self.photo_path)
            except:
                pass
        
        # Устанавливаем photo_path в None - это означает, что фото нужно удалить
        self.photo_path = None
        if self.photo_preview_label:
            self.photo_preview_label.config(image='', text="Фото не загружено")
            self.photo_preview_label.image = None
    
    def display_photo_preview(self, photo_path):
        """Отображение превью фотографии"""
        try:
            # Загружаем и изменяем размер изображения
            img = Image.open(photo_path)
            img.thumbnail((200, 200), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            if self.photo_preview_label:
                self.photo_preview_label.config(image=photo, text='')
                self.photo_preview_label.image = photo  # Сохраняем ссылку
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось отобразить фотографию: {e}")


# ========== СОТРУДНИКИ ==========

class AddEmployeeDialog:
    def __init__(self, parent, db, callback):
        self.db = db
        self.callback = callback
        self.photo_path = None
        self.photo_preview_label = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Добавить сотрудника")
        default_geometry = "700x600"
        window_config.restore_window(self.dialog, "AddEmployeeDialog", default_geometry)
        register_dialog(self.dialog, "AddEmployeeDialog")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Убеждаемся, что обработчик закрытия установлен (может быть переопределен grab_set)
        def on_closing():
            close_dialog_with_save(self.dialog, "AddEmployeeDialog")
        self.dialog.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Закрытие по ESC с сохранением настроек
        def close_with_save():
            close_dialog_with_save(self.dialog, "AddEmployeeDialog")
        self.dialog.bind('<Escape>', lambda e: close_with_save())
        
        self.create_widgets()
        
    def create_widgets(self):
        # Основной контейнер с прокруткой для содержимого
        content_frame = ttk.Frame(self.dialog)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Создаем скроллируемый контейнер для полей формы
        canvas = tk.Canvas(content_frame)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Функция для обновления размера окна в canvas
        def configure_scroll_region(event=None):
            canvas.update_idletasks()
            bbox = canvas.bbox("all")
            if bbox:
                canvas.configure(scrollregion=bbox)
        
        scrollable_frame.bind("<Configure>", configure_scroll_region)
        
        main_frame = ttk.Frame(scrollable_frame, padding="20")
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
        
        # Фотография
        photo_frame = ttk.LabelFrame(main_frame, text="Фотография", padding="10")
        photo_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=10, sticky=tk.W+tk.E)
        
        photo_buttons_frame = ttk.Frame(photo_frame)
        photo_buttons_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(
            photo_buttons_frame,
            text="Загрузить фото",
            command=self.load_photo
        ).pack(side=tk.TOP, pady=5)
        
        ttk.Button(
            photo_buttons_frame,
            text="Удалить фото",
            command=self.remove_photo
        ).pack(side=tk.TOP, pady=5)
        
        # Превью фотографии
        self.photo_preview_label = tk.Label(photo_frame, text="Фото не загружено", width=30, height=10, bg='lightgray')
        self.photo_preview_label.pack(side=tk.LEFT, padx=10)
        
        # Размещаем canvas и scrollbar в content_frame
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Привязка прокрутки колесом мыши ко всем элементам
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # Привязываем прокрутку к canvas и всем дочерним элементам
        canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
        main_frame.bind("<MouseWheel>", _on_mousewheel)
        
        # Обновляем область прокрутки при изменении содержимого
        main_frame.bind("<Configure>", configure_scroll_region)
        
        # Настройка grid для правильного отображения
        main_frame.grid_columnconfigure(1, weight=1)
        
        # Кнопки - размещаем внизу диалога отдельно, чтобы они всегда были видны
        button_frame = ttk.Frame(self.dialog, padding="10")
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Button(
            button_frame,
            text="Сохранить",
            command=self.save
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Отмена",
            command=lambda: close_dialog_with_save(self.dialog, "AddEmployeeDialog")
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
        
        data = (full_name, position, department, phone, email, status, self.photo_path)
        
        if self.db.add_employee(data):
            messagebox.showinfo("Успех", "Сотрудник добавлен")
            self.callback()
            close_dialog_with_save(self.dialog, "AddEmployeeDialog")
        else:
            messagebox.showerror("Ошибка", "Не удалось добавить сотрудника")
    
    def load_photo(self):
        """Загрузка фотографии сотрудника"""
        file_path = filedialog.askopenfilename(
            title="Выберите фотографию",
            filetypes=[("Изображения", "*.jpg *.jpeg *.png *.gif *.bmp"), ("Все файлы", "*.*")]
        )
        
        if file_path:
            try:
                photos_dir = 'photos/employees'
                if not os.path.exists(photos_dir):
                    os.makedirs(photos_dir)
                
                file_ext = os.path.splitext(file_path)[1]
                import uuid
                unique_filename = f"{uuid.uuid4()}{file_ext}"
                dest_path = os.path.join(photos_dir, unique_filename)
                
                shutil.copy2(file_path, dest_path)
                self.photo_path = dest_path
                self.display_photo_preview(dest_path)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить фотографию: {e}")
    
    def remove_photo(self):
        """Удаление фотографии"""
        if self.photo_path and os.path.exists(self.photo_path):
            try:
                os.remove(self.photo_path)
            except:
                pass
        self.photo_path = None
        self.photo_preview_label.config(image='', text="Фото не загружено")
        self.photo_preview_label.image = None
    
    def display_photo_preview(self, photo_path):
        """Отображение превью фотографии"""
        try:
            img = Image.open(photo_path)
            img.thumbnail((200, 200), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.photo_preview_label.config(image=photo, text='')
            self.photo_preview_label.image = photo
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось отобразить фотографию: {e}")


class EditEmployeeDialog:
    def __init__(self, parent, db, employee_id, callback):
        self.db = db
        self.employee_id = employee_id
        self.callback = callback
        self.photo_path = None
        self.photo_preview_label = None
        self.old_photo_path = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Редактировать сотрудника")
        default_geometry = "500x450"
        window_config.restore_window(self.dialog, "EditEmployeeDialog", default_geometry)
        register_dialog(self.dialog, "EditEmployeeDialog")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Закрытие по ESC и через крестик с сохранением настроек
        def close_with_save():
            close_dialog_with_save(self.dialog, "EditEmployeeDialog")
        self.dialog.protocol("WM_DELETE_WINDOW", close_with_save)
        self.dialog.bind('<Escape>', lambda e: close_with_save())
        
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
                'status': employee[6],
                'photo_path': employee[7] if len(employee) > 7 else ''
            }
            self.photo_path = self.employee_data.get('photo_path') or None
            self.old_photo_path = self.photo_path
        
    def create_widgets(self):
        # Основной контейнер с прокруткой для содержимого
        content_frame = ttk.Frame(self.dialog)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Создаем скроллируемый контейнер для полей формы
        canvas = tk.Canvas(content_frame)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Функция для обновления размера окна в canvas
        def configure_scroll_region(event=None):
            canvas.update_idletasks()
            bbox = canvas.bbox("all")
            if bbox:
                canvas.configure(scrollregion=bbox)
        
        scrollable_frame.bind("<Configure>", configure_scroll_region)
        
        main_frame = ttk.Frame(scrollable_frame, padding="20")
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
        
        # Фотография
        photo_frame = ttk.LabelFrame(main_frame, text="Фотография", padding="10")
        photo_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=10, sticky=tk.W+tk.E)
        
        photo_buttons_frame = ttk.Frame(photo_frame)
        photo_buttons_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(
            photo_buttons_frame,
            text="Загрузить фото",
            command=self.load_photo
        ).pack(side=tk.TOP, pady=5)
        
        ttk.Button(
            photo_buttons_frame,
            text="Удалить фото",
            command=self.remove_photo
        ).pack(side=tk.TOP, pady=5)
        
        # Превью фотографии
        self.photo_preview_label = tk.Label(photo_frame, text="Фото не загружено", width=30, height=10, bg='lightgray')
        self.photo_preview_label.pack(side=tk.LEFT, padx=10)
        
        # Загружаем существующую фотографию, если есть
        if self.photo_path and os.path.exists(self.photo_path):
            self.display_photo_preview(self.photo_path)
        
        # Размещаем canvas и scrollbar в content_frame
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Привязка прокрутки колесом мыши ко всем элементам
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # Привязываем прокрутку к canvas и всем дочерним элементам
        canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
        main_frame.bind("<MouseWheel>", _on_mousewheel)
        
        # Обновляем область прокрутки при изменении содержимого
        main_frame.bind("<Configure>", configure_scroll_region)
        
        # Настройка grid для правильного отображения
        main_frame.grid_columnconfigure(1, weight=1)
        
        # Кнопки - размещаем внизу диалога отдельно, чтобы они всегда были видны
        button_frame = ttk.Frame(self.dialog, padding="10")
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Button(
            button_frame,
            text="Сохранить",
            command=self.save
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Отмена",
            command=lambda: close_dialog_with_save(self.dialog, "EditEmployeeDialog")
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
        
        # Удаляем старое фото, если было загружено новое или удалено
        if self.old_photo_path and self.old_photo_path != self.photo_path:
            if os.path.exists(self.old_photo_path):
                try:
                    os.remove(self.old_photo_path)
                except:
                    pass
        
        data = (full_name, position, department, phone, email, status, self.photo_path)
        
        if self.db.update_employee(self.employee_id, data):
            messagebox.showinfo("Успех", "Сотрудник обновлен")
            self.callback()
            close_dialog_with_save(self.dialog, "EditEmployeeDialog")
        else:
            messagebox.showerror("Ошибка", "Не удалось обновить сотрудника")
    
    def load_photo(self):
        """Загрузка фотографии сотрудника"""
        file_path = filedialog.askopenfilename(
            title="Выберите фотографию",
            filetypes=[("Изображения", "*.jpg *.jpeg *.png *.gif *.bmp"), ("Все файлы", "*.*")]
        )
        
        if file_path:
            try:
                # Удаляем старую фотографию, если она была загружена в этой сессии редактирования
                old_path = self.photo_path
                if old_path and old_path != self.old_photo_path and os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except:
                        pass
                
                # Копируем файл в папку photos/employees
                photos_dir = 'photos/employees'
                if not os.path.exists(photos_dir):
                    os.makedirs(photos_dir)
                
                # Генерируем уникальное имя файла
                file_ext = os.path.splitext(file_path)[1]
                unique_filename = f"{uuid.uuid4()}{file_ext}"
                dest_path = os.path.join(photos_dir, unique_filename)
                
                shutil.copy2(file_path, dest_path)
                self.photo_path = dest_path
                
                # Отображаем превью
                self.display_photo_preview(dest_path)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить фотографию: {e}")
    
    def remove_photo(self):
        """Удаление фотографии"""
        # Удаляем текущую фотографию, если она была загружена в этой сессии редактирования
        # (но не удаляем старое фото, которое было в БД - оно удалится при сохранении)
        if self.photo_path and self.photo_path != self.old_photo_path and os.path.exists(self.photo_path):
            try:
                os.remove(self.photo_path)
            except:
                pass
        
        # Устанавливаем photo_path в None - это означает, что фото нужно удалить
        self.photo_path = None
        if self.photo_preview_label:
            self.photo_preview_label.config(image='', text="Фото не загружено")
            self.photo_preview_label.image = None
    
    def display_photo_preview(self, photo_path):
        """Отображение превью фотографии"""
        try:
            img = Image.open(photo_path)
            img.thumbnail((200, 200), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            if self.photo_preview_label:
                self.photo_preview_label.config(image=photo, text='')
                self.photo_preview_label.image = photo  # Сохраняем ссылку
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось отобразить фотографию: {e}")


# ========== ВЫДАЧА И ВОЗВРАТ ==========

class IssueInstrumentDialog:
    def __init__(self, parent, db, callback):
        self.db = db
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Выдать инструмент")
        default_geometry = "800x650"
        window_config.restore_window(self.dialog, "IssueInstrumentDialog", default_geometry)
        register_dialog(self.dialog, "IssueInstrumentDialog")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Закрытие по ESC и через крестик с сохранением настроек
        def close_with_save():
            close_dialog_with_save(self.dialog, "IssueInstrumentDialog")
        self.dialog.protocol("WM_DELETE_WINDOW", close_with_save)
        self.dialog.bind('<Escape>', lambda e: close_with_save())
        
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
                    # Фильтрация по первым символам (по началу строки)
                    filtered = [item for item in self.all_instrument_values 
                               if item.lower().startswith(value.lower())]
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
                    # Фильтрация по первым символам (по началу строки)
                    filtered = [item for item in self.all_employee_values 
                               if item.lower().startswith(value.lower())]
                    self.employee_combo['values'] = filtered
                else:
                    self.employee_combo['values'] = self.all_employee_values
            
            self._employee_update_id = self.dialog.after(100, do_update)
    
    def reset_instrument_values(self, event=None):
        """Сброс списка значений инструмента к полному списку при взаимодействии"""
        if hasattr(self, 'instrument_combo') and hasattr(self, 'all_instrument_values'):
            self.instrument_combo['values'] = self.all_instrument_values
    
    def reset_employee_values(self, event=None):
        """Сброс списка значений сотрудника к полному списку при взаимодействии"""
        if hasattr(self, 'employee_combo') and hasattr(self, 'all_employee_values'):
            self.employee_combo['values'] = self.all_employee_values
    
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
        
        # Загрузка списка сотрудников (только активные, уволенные не показываются)
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
        # Сброс фильтра при взаимодействии, чтобы всегда можно было поменять выбор
        instrument_combo.bind('<FocusIn>', self.reset_instrument_values)
        instrument_combo.bind('<Button-1>', self.reset_instrument_values)
        instrument_combo.bind('<Down>', self.reset_instrument_values)
        
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
        # Сброс фильтра при взаимодействии, чтобы можно было менять выбор повторно
        employee_combo.bind('<FocusIn>', self.reset_employee_values)
        employee_combo.bind('<Button-1>', self.reset_employee_values)
        employee_combo.bind('<Down>', self.reset_employee_values)

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
            command=lambda: close_dialog_with_save(self.dialog, "IssueInstrumentDialog")
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
        
        # Дополнительная проверка: убеждаемся, что сотрудник активен
        # (на случай, если статус изменился после открытия диалога)
        if len(selected_employee) > 6 and selected_employee[6] != 'Активен':
            messagebox.showerror("Ошибка", f"Нельзя выдать инструмент уволенному сотруднику.")
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
            close_dialog_with_save(self.dialog, "IssueInstrumentDialog")
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


class BatchReturnDialog:
    def __init__(self, parent, db, callback):
        self.db = db
        self.callback = callback
        self.selected_issues = []

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Массовая сдача инструментов")
        default_geometry = "800x600"
        window_config.restore_window(self.dialog, "BatchReturnDialog", default_geometry)
        register_dialog(self.dialog, "BatchReturnDialog")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Закрытие по ESC и через крестик с сохранением настроек
        def close_with_save():
            close_dialog_with_save(self.dialog, "BatchReturnDialog")
        self.dialog.protocol("WM_DELETE_WINDOW", close_with_save)
        self.dialog.bind('<Escape>', lambda e: close_with_save())

        self.load_data()
        self.create_widgets()

    def load_data(self):
        """Загрузка списка активных выдач"""
        self.issues_data = self.db.get_active_issues_for_return()

    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(title_frame, text="Массовая сдача инструментов",
                 font=('Arial', 16, 'bold')).pack(side=tk.LEFT)

        ttk.Label(title_frame, text=f"Найдено активных выдач: {len(self.issues_data)}").pack(side=tk.RIGHT)

        # Таблица с чекбоксами
        table_frame = ttk.LabelFrame(main_frame, text="Выберите инструменты для возврата", padding="10")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # Создаем фрейм для таблицы с прокруткой
        tree_frame = ttk.Frame(table_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Полоса прокрутки
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Treeview с чекбоксами
        columns = ('select', 'id', 'inventory_number', 'name', 'employee', 'issue_date', 'expected_return')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', yscrollcommand=scrollbar.set)

        # Настраиваем столбцы
        self.tree.heading('select', text='✓')
        self.tree.heading('id', text='ID выдачи')
        self.tree.heading('inventory_number', text='Инв. номер')
        self.tree.heading('name', text='Инструмент')
        self.tree.heading('employee', text='Сотрудник')
        self.tree.heading('issue_date', text='Дата выдачи')
        self.tree.heading('expected_return', text='Ожидаемый возврат')

        self.tree.column('select', width=50, anchor='center')
        self.tree.column('id', width=80, anchor='center')
        self.tree.column('inventory_number', width=100, anchor='center')
        self.tree.column('name', width=200, anchor='w')
        self.tree.column('employee', width=150, anchor='w')
        self.tree.column('issue_date', width=120, anchor='center')
        self.tree.column('expected_return', width=120, anchor='center')

        # Заполняем таблицу данными
        for issue in self.issues_data:
            issue_id = issue[0]
            inventory_number = issue[2]
            name = issue[3]
            employee = issue[4]
            issue_date = issue[5].split(' ')[0] if issue[5] else ''
            expected_return = issue[6] if issue[6] else ''

            # Проверяем просроченность
            is_overdue = False
            if expected_return:
                try:
                    from datetime import datetime
                    expected_date = datetime.strptime(expected_return, '%Y-%m-%d').date()
                    if expected_date < datetime.now().date():
                        is_overdue = True
                except:
                    pass

            # Определяем тег для подсветки просроченных
            tags = ('overdue',) if is_overdue else ()

            self.tree.insert('', 'end', values=('☐', issue_id, inventory_number, name, employee, issue_date, expected_return), tags=tags)

        # Настраиваем цвета для просроченных
        self.tree.tag_configure('overdue', background='#ffe6e6')

        # Обработчик клика по чекбоксу
        self.tree.bind('<Button-1>', self.on_tree_click)

        self.tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)

        # Кнопки выбора
        buttons_frame = ttk.Frame(table_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(buttons_frame, text="Выбрать все", command=self.select_all).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons_frame, text="Снять все", command=self.deselect_all).pack(side=tk.LEFT)
        ttk.Button(buttons_frame, text="Инвертировать", command=self.invert_selection).pack(side=tk.LEFT, padx=(10, 0))

        # Форма возврата
        return_frame = ttk.LabelFrame(main_frame, text="Информация о возврате", padding="10")
        return_frame.pack(fill=tk.X, pady=(0, 20))

        # Поле примечания
        ttk.Label(return_frame, text="Примечание:").pack(anchor=tk.W)
        self.notes_text = tk.Text(return_frame, height=3, width=50)
        self.notes_text.pack(fill=tk.X, pady=(5, 10))

        # Кнопки
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(buttons_frame, text="Отмена", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(buttons_frame, text="Выполнить возврат",
                  command=self.perform_batch_return).pack(side=tk.RIGHT)

        # Счетчик выбранных
        self.counter_label = ttk.Label(buttons_frame, text="Выбрано: 0")
        self.counter_label.pack(side=tk.LEFT)

    def on_tree_click(self, event):
        """Обработка клика по чекбоксу в таблице"""
        region = self.tree.identify_region(event.x, event.y)
        if region == 'cell':
            column = self.tree.identify_column(event.x)
            if column == '#1':  # Столбец с чекбоксами
                item = self.tree.identify_row(event.y)
                if item:
                    values = list(self.tree.item(item, 'values'))
                    # Переключаем чекбокс
                    values[0] = '☑' if values[0] == '☐' else '☐'
                    self.tree.item(item, values=values)
                    self.update_counter()

    def select_all(self):
        """Выбрать все инструменты"""
        for item in self.tree.get_children():
            values = list(self.tree.item(item, 'values'))
            values[0] = '☑'
            self.tree.item(item, values=values)
        self.update_counter()

    def deselect_all(self):
        """Снять выбор со всех"""
        for item in self.tree.get_children():
            values = list(self.tree.item(item, 'values'))
            values[0] = '☐'
            self.tree.item(item, values=values)
        self.update_counter()

    def invert_selection(self):
        """Инвертировать выбор"""
        for item in self.tree.get_children():
            values = list(self.tree.item(item, 'values'))
            values[0] = '☑' if values[0] == '☐' else '☐'
            self.tree.item(item, values=values)
        self.update_counter()

    def update_counter(self):
        """Обновление счетчика выбранных элементов"""
        selected_count = sum(1 for item in self.tree.get_children()
                           if self.tree.item(item, 'values')[0] == '☑')
        self.counter_label.config(text=f"Выбрано: {selected_count}")

    def perform_batch_return(self):
        """Выполнение массового возврата"""
        selected_issues = []
        for item in self.tree.get_children():
            values = self.tree.item(item, 'values')
            if values[0] == '☑':  # Выбран
                issue_id = int(values[1])
                selected_issues.append(issue_id)

        if not selected_issues:
            messagebox.showwarning("Предупреждение", "Не выбрано ни одного инструмента для возврата!")
            return

        notes = self.notes_text.get("1.0", tk.END).strip()

        # Подтверждение
        if not messagebox.askyesno("Подтверждение",
                                  f"Вернуть {len(selected_issues)} инструментов?",
                                  parent=self.dialog):
            return

        # Выполняем возврат
        success, message = self.db.return_instruments_batch(selected_issues, notes, "Пользователь")

        if success:
            messagebox.showinfo("Успех", message, parent=self.dialog)
            if self.callback:
                self.callback()
            self.dialog.destroy()
        else:
            messagebox.showerror("Ошибка", message, parent=self.dialog)


class ReturnInstrumentDialog:
    def __init__(self, parent, db, issue_id, callback):
        self.db = db
        self.issue_id = issue_id
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Оформить возврат")
        default_geometry = "500x400"
        window_config.restore_window(self.dialog, "ReturnInstrumentDialog", default_geometry)
        register_dialog(self.dialog, "ReturnInstrumentDialog")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Закрытие по ESC и через крестик с сохранением настроек
        def close_with_save():
            close_dialog_with_save(self.dialog, "ReturnInstrumentDialog")
        self.dialog.protocol("WM_DELETE_WINDOW", close_with_save)
        self.dialog.bind('<Escape>', lambda e: close_with_save())
        
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
            command=lambda: close_dialog_with_save(self.dialog, "ReturnInstrumentDialog")
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
            close_dialog_with_save(self.dialog, "ReturnInstrumentDialog")
        else:
            messagebox.showerror("Ошибка", message)

