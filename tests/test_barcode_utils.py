#!/usr/bin/env python3
"""
Тесты для модуля barcode_utils.py
"""

import pytest
import os
from pathlib import Path


class TestBarcodeManager:
    """Тесты для BarcodeManager"""

    def test_generate_unique_barcode(self, barcode_manager):
        """Тест генерации уникального штрих-кода"""
        barcode1 = barcode_manager.generate_unique_barcode()
        barcode2 = barcode_manager.generate_unique_barcode()

        # Проверяем, что штрих-коды уникальны
        assert barcode1 != barcode2

        # Проверяем формат
        assert barcode1.startswith("TOOL")
        assert len(barcode1) > 10  # Должен быть достаточно длинным

    def test_validate_barcode_valid(self, barcode_manager):
        """Тест валидации корректного штрих-кода"""
        valid_barcodes = [
            "TOOL123456789",
            "ABC123456789",
            "TEST123",
            "CODE128TEST"
        ]

        for barcode in valid_barcodes:
            assert barcode_manager.validate_barcode(barcode)

    def test_validate_barcode_invalid(self, barcode_manager):
        """Тест валидации некорректного штрих-кода"""
        invalid_barcodes = [
            "",  # Пустой
            "AB",  # Слишком короткий
            "INVALID!@#$%",  # С недопустимыми символами
            "ТестКириллица"  # С кириллицей
        ]

        for barcode in invalid_barcodes:
            assert not barcode_manager.validate_barcode(barcode)

    def test_generate_barcode_image(self, barcode_manager):
        """Тест генерации изображения штрих-кода"""
        test_code = "TEST123456789"

        # Генерируем штрих-код
        filepath = barcode_manager.generate_barcode(test_code)

        # Проверяем, что файл создан
        assert filepath is not None
        assert os.path.exists(filepath)

        # Проверяем, что файл имеет правильное расширение
        assert filepath.endswith('.png')

        # Очистка
        if os.path.exists(filepath):
            os.remove(filepath)

    def test_get_barcode_image(self, barcode_manager):
        """Тест получения изображения штрих-кода для Tkinter"""
        test_code = "TEST123456"

        # Получаем изображение
        image = barcode_manager.get_barcode_image(test_code)

        # Проверяем, что изображение создано
        assert image is not None

        # Проверяем тип (может быть PIL.Image или PhotoImage)
        image_type_str = str(type(image))
        assert ("PhotoImage" in image_type_str) or ("Image" in image_type_str)

    def test_search_by_barcode_not_found(self, barcode_manager, db_manager):
        """Тест поиска несуществующего штрих-кода"""
        result = barcode_manager.search_by_barcode("NONEXISTENT", db_manager)
        assert result is None

    def test_barcode_directory_creation(self, barcode_manager):
        """Тест создания директории для штрих-кодов"""
        # Директория должна быть создана при инициализации
        assert os.path.exists(barcode_manager.barcode_dir)
        assert barcode_manager.barcode_dir.name == "barcodes"
