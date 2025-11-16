#!/usr/bin/env python3
"""
Модуль для работы со штрих-кодами инструментов
"""

import os
import barcode
from barcode.writer import ImageWriter
from pathlib import Path
from PIL import Image, ImageTk
import tkinter as tk

class BarcodeManager:
    """Менеджер для работы со штрих-кодами"""

    def __init__(self):
        self.barcode_dir = Path("barcodes")
        self.barcode_dir.mkdir(exist_ok=True)

    def generate_barcode(self, code_data, filename=None):
        """Генерация штрих-кода Code128

        Args:
            code_data (str): Данные для кодирования в штрих-код
            filename (str, optional): Имя файла для сохранения

        Returns:
            str: Путь к файлу штрих-кода или None при ошибке
        """
        try:
            if not filename:
                filename = f"{code_data}.png"

            filepath = self.barcode_dir / filename

            # Генерируем штрих-код Code128
            code128 = barcode.get('code128', code_data, writer=ImageWriter())

            # Сохраняем как изображение
            code128.save(str(filepath.with_suffix('')))

            return str(filepath)

        except Exception as e:
            print(f"Ошибка генерации штрих-кода: {e}")
            return None

    def get_barcode_image(self, code_data, width=300, height=100):
        """Получение изображения штрих-кода для отображения в Tkinter

        Args:
            code_data (str): Данные штрих-кода
            width (int): Ширина изображения
            height (int): Высота изображения

        Returns:
            ImageTk.PhotoImage or PIL.Image: Изображение для Tkinter или PIL изображение
        """
        try:
            filepath = self.generate_barcode(code_data)
            if filepath and os.path.exists(filepath):
                # Загружаем изображение
                image = Image.open(filepath)

                # Изменяем размер
                image = image.resize((width, height), Image.Resampling.LANCZOS)

                # Проверяем, инициализирован ли Tkinter
                try:
                    import tkinter as tk
                    root = tk._default_root
                    if root is not None:
                        # Tkinter инициализирован, возвращаем PhotoImage
                        photo = ImageTk.PhotoImage(image)
                        return photo
                except (AttributeError, ImportError):
                    pass

                # Tkinter не инициализирован, возвращаем PIL изображение
                return image

            return None

        except Exception as e:
            print(f"Ошибка загрузки штрих-кода: {e}")
            return None

    def generate_unique_barcode(self, prefix="TOOL"):
        """Генерация уникального штрих-кода

        Args:
            prefix (str): Префикс для штрих-кода

        Returns:
            str: Уникальный код штрих-кода
        """
        import random
        import time

        # Генерируем уникальный код
        timestamp = str(int(time.time()))[-6:]  # Последние 6 цифр timestamp
        random_part = str(random.randint(100, 999))  # 3 случайные цифры

        return f"{prefix}{timestamp}{random_part}"

    def validate_barcode(self, barcode_str):
        """Проверка валидности штрих-кода

        Args:
            barcode_str (str): Штрих-код для проверки

        Returns:
            bool: True если штрих-код валиден
        """
        if not barcode_str:
            return False

        # Проверяем длину и символы
        if len(barcode_str) < 3:
            return False

        # Проверяем что содержит только допустимые символы для Code128
        valid_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!\"%&'()*+,-./:;<=>?@[\\]^_`{|}~"
        return all(c in valid_chars for c in barcode_str)

    def search_by_barcode(self, barcode_str, db_manager):
        """Поиск инструмента по штрих-коду

        Args:
            barcode_str (str): Штрих-код для поиска
            db_manager: Экземпляр DatabaseManager

        Returns:
            dict: Данные инструмента или None
        """
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, name, description, inventory_number, serial_number,
                       category, status, photo_path, barcode
                FROM instruments
                WHERE barcode = ?
            """, (barcode_str,))

            result = cursor.fetchone()
            conn.close()

            if result:
                return {
                    'id': result[0],
                    'name': result[1],
                    'description': result[2],
                    'inventory_number': result[3],
                    'serial_number': result[4],
                    'category': result[5],
                    'status': result[6],
                    'photo_path': result[7],
                    'barcode': result[8]
                }
            return None

        except Exception as e:
            print(f"Ошибка поиска по штрих-коду: {e}")
            return None

    def print_barcode(self, code_data, printer_name=None):
        """Печать штрих-кода

        Args:
            code_data (str): Данные штрих-кода
            printer_name (str, optional): Имя принтера

        Returns:
            bool: True если печать успешна
        """
        try:
            filepath = self.generate_barcode(code_data)
            if filepath and os.path.exists(filepath):
                # Здесь можно добавить логику печати
                # Для простоты пока только сообщение
                print(f"Штрих-код {code_data} готов к печати: {filepath}")
                return True
            return False

        except Exception as e:
            print(f"Ошибка печати штрих-кода: {e}")
            return False

# Глобальный экземпляр менеджера штрих-кодов
barcode_manager = BarcodeManager()
