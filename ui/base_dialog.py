#!/usr/bin/env python3
"""
Базовый класс для диалоговых окон
"""

import tkinter as tk
from tkinter import ttk, messagebox
from window_config import window_config
from dialogs import register_dialog, close_dialog_with_save


class BaseDialog:
    """Базовый класс для всех диалогов"""

    def __init__(self, parent, title, db_manager, default_geometry="800x600"):
        self.db = db_manager
        self.parent = parent

        # Создание диалога
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        window_config.restore_window(self.dialog, self.__class__.__name__, default_geometry)
        register_dialog(self.dialog, self.__class__.__name__)

        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Закрытие по ESC и через крестик
        self._setup_close_handlers()

        # Основной контейнер
        self.main_frame = ttk.Frame(self.dialog, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Словарь для хранения виджетов ввода
        self.entries = {}

    def _setup_close_handlers(self):
        """Настройка обработчиков закрытия"""
        def close_with_save_handler():
            close_dialog_with_save(self.dialog, self.__class__.__name__)

        self.dialog.protocol("WM_DELETE_WINDOW", close_with_save_handler)
        self.dialog.bind('<Escape>', lambda e: close_with_save_handler())

    def create_label_entry_pair(self, label_text, field_name, row, width=50):
        """Создание пары метка-поле ввода"""
        ttk.Label(self.main_frame, text=label_text).grid(row=row, column=0, sticky=tk.W, pady=5)

        if field_name == "description":
            # Многострочное поле для описания
            entry = tk.Text(self.main_frame, width=width, height=3)
            entry.grid(row=row, column=1, pady=5, sticky=tk.W)
        else:
            # Обычное поле ввода
            entry = ttk.Entry(self.main_frame, width=width)
            entry.grid(row=row, column=1, pady=5, sticky=tk.W)

        self.entries[field_name] = entry
        return entry

    def create_combobox(self, label_text, field_name, values, row, default_value=None):
        """Создание выпадающего списка"""
        ttk.Label(self.main_frame, text=label_text).grid(row=row, column=0, sticky=tk.W, pady=5)

        combo = ttk.Combobox(self.main_frame, values=values, state='readonly', width=47)
        if default_value:
            combo.set(default_value)
        combo.grid(row=row, column=1, pady=5, sticky=tk.W)

        self.entries[field_name] = combo
        return combo

    def create_buttons_frame(self, buttons_config, row):
        """Создание рамки с кнопками"""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)

        for text, command in buttons_config:
            if command is None:
                # Разделитель
                ttk.Label(button_frame, text="").pack(side=tk.LEFT, padx=10)
            else:
                ttk.Button(button_frame, text=text, command=command).pack(side=tk.LEFT, padx=5)

        return button_frame

    def validate_required_fields(self, required_fields):
        """Валидация обязательных полей"""
        for field in required_fields:
            if field == "description":
                value = self.entries[field].get("1.0", tk.END).strip()
            else:
                value = self.entries[field].get().strip()

            if not value:
                messagebox.showerror("Ошибка", f"Заполните поле: {field}")
                return False
        return True

    def get_field_value(self, field_name):
        """Получение значения поля"""
        if field_name == "description":
            return self.entries[field_name].get("1.0", tk.END).strip()
        else:
            return self.entries[field_name].get().strip()

    def set_field_value(self, field_name, value):
        """Установка значения поля"""
        if field_name == "description":
            self.entries[field_name].delete("1.0", tk.END)
            self.entries[field_name].insert("1.0", value or "")
        else:
            self.entries[field_name].delete(0, tk.END)
            self.entries[field_name].insert(0, value or "")

    def show_success_message(self, message):
        """Показать сообщение об успехе"""
        messagebox.showinfo("Успех", message)

    def show_error_message(self, message):
        """Показать сообщение об ошибке"""
        messagebox.showerror("Ошибка", message)

    def close_dialog(self):
        """Закрыть диалог"""
        close_dialog_with_save(self.dialog, self.__class__.__name__)


class PhotoDialogMixin:
    """Миксин для диалогов с поддержкой фотографий"""

    def __init__(self):
        self.photo_path = None
        self.photo_preview_label = None
        self.old_photo_path = None

    def create_photo_frame(self, row):
        """Создание рамки для работы с фотографиями"""
        photo_frame = ttk.LabelFrame(self.main_frame, text="Фотография", padding="10")
        photo_frame.grid(row=row, column=0, columnspan=2, pady=10, sticky=tk.W+tk.E)

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
        self.photo_preview_label = tk.Label(
            photo_frame,
            text="Фото не загружено",
            width=30,
            height=10,
            bg='lightgray'
        )
        self.photo_preview_label.pack(side=tk.LEFT, padx=10)

        return photo_frame

    def load_photo(self):
        """Загрузка фотографии"""
        from tkinter import filedialog
        import shutil
        import uuid

        file_path = filedialog.askopenfilename(
            title="Выберите фотографию",
            filetypes=[("Изображения", "*.jpg *.jpeg *.png *.gif *.bmp"), ("Все файлы", "*.*")]
        )

        if file_path:
            try:
                # Копируем файл в папку photos
                photos_dir = 'photos/instruments' if 'instrument' in self.__class__.__name__.lower() else 'photos/employees'
                if not os.path.exists(photos_dir):
                    os.makedirs(photos_dir)

                # Генерируем уникальное имя файла
                file_ext = os.path.splitext(file_path)[1]
                new_filename = f"{uuid.uuid4()}{file_ext}"
                new_path = os.path.join(photos_dir, new_filename)

                shutil.copy2(file_path, new_path)

                # Удаляем старую фотографию
                if self.photo_path and os.path.exists(self.photo_path):
                    try:
                        os.remove(self.photo_path)
                    except:
                        pass

                self.photo_path = new_path
                self.update_photo_preview()

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить фото: {e}")

    def remove_photo(self):
        """Удаление фотографии"""
        if self.photo_path and os.path.exists(self.photo_path):
            try:
                os.remove(self.photo_path)
            except:
                pass

        self.photo_path = None
        self.update_photo_preview()

    def update_photo_preview(self):
        """Обновление превью фотографии"""
        if self.photo_path and os.path.exists(self.photo_path):
            try:
                from PIL import Image, ImageTk
                image = Image.open(self.photo_path)
                image.thumbnail((200, 150))
                photo = ImageTk.PhotoImage(image)
                self.photo_preview_label.config(image=photo, text="")
                self.photo_preview_label.image = photo
            except Exception as e:
                self.photo_preview_label.config(image="", text=f"Ошибка загрузки: {e}")
        else:
            self.photo_preview_label.config(image="", text="Фото не загружено")


class BarcodeDialogMixin:
    """Миксин для диалогов с поддержкой штрих-кодов"""

    def create_barcode_field(self, row):
        """Создание поля для штрих-кода с кнопками"""
        ttk.Label(self.main_frame, text="Штрих-код:").grid(row=row, column=0, sticky=tk.W, pady=5)

        barcode_frame = ttk.Frame(self.main_frame)
        barcode_frame.grid(row=row, column=1, pady=5, sticky=tk.W)

        entry = ttk.Entry(barcode_frame, width=30)
        entry.pack(side=tk.LEFT)

        ttk.Button(
            barcode_frame,
            text="🔄 Генерировать",
            command=lambda: self.generate_barcode(entry)
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            barcode_frame,
            text="👁 Просмотр",
            command=lambda: self.preview_barcode(entry.get())
        ).pack(side=tk.LEFT, padx=5)

        self.entries['barcode'] = entry
        return entry

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



