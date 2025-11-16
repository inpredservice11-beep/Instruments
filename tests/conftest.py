#!/usr/bin/env python3
"""
Конфигурация pytest для тестов системы учета инструмента
"""

import pytest
import sqlite3
import os
import tempfile
import shutil
from pathlib import Path


@pytest.fixture(scope="session")
def temp_db_path():
    """Создает временный файл базы данных для тестов"""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_tool_management.db")

    yield db_path

    # Очистка после тестов
    if os.path.exists(db_path):
        os.remove(db_path)
    shutil.rmtree(temp_dir)


@pytest.fixture
def db_manager():
    """Фикстура для DatabaseManager с тестовой БД"""
    from database_manager import DatabaseManager
    import tempfile

    # Создаем временный файл для каждого теста
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_tool_management.db")

    # Создаем менеджер с тестовым путем
    manager = DatabaseManager(db_path)

    # Удаляем файл, если он существует, чтобы начать с чистой БД
    if os.path.exists(db_path):
        os.remove(db_path)

    # Создаем базу данных с нуля
    manager.init_database()

    yield manager

    # Очистка
    manager.close()
    shutil.rmtree(temp_dir)


@pytest.fixture
def barcode_manager():
    """Фикстура для BarcodeManager"""
    from barcode_utils import BarcodeManager
    manager = BarcodeManager()
    return manager


@pytest.fixture
def sample_instrument_data():
    """Тестовые данные для инструмента"""
    return {
        'name': 'Тестовый инструмент',
        'description': 'Описание для тестов',
        'inventory_number': 'TEST-001',
        'serial_number': 'SN-TEST-001',
        'category': 'Электроинструмент',
        'status': 'Доступен',
        'photo_path': None,
        'barcode': 'TOOL123456789'
    }


@pytest.fixture
def sample_employee_data():
    """Тестовые данные для сотрудника"""
    return {
        'full_name': 'Иванов Иван Иванович',
        'position': 'Инженер',
        'department': 'Технический отдел',
        'phone': '+7-900-123-45-67',
        'email': 'ivanov@test.com',
        'status': 'Активен',
        'photo_path': None
    }
