#!/usr/bin/env python3
"""
Тест исправления базы данных в тестах
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database_manager import DatabaseManager
import tempfile
import shutil

def test_db_creation():
    """Тест создания базы данных"""
    print("Тест создания базы данных...")

    # Создаем временный файл
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_tool_management.db")

    try:
        # Создаем менеджер
        manager = DatabaseManager(db_path)

        # Удаляем файл, если он существует
        if os.path.exists(db_path):
            os.remove(db_path)

        # Создаем базу данных с нуля
        manager.init_database()

        # Проверяем, что таблицы созданы
        conn = manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [t[0] for t in tables]
        print(f'Созданные таблицы: {table_names}')

        # Проверяем наличие основных таблиц
        required_tables = ['instruments', 'employees', 'issues', 'addresses']
        for table in required_tables:
            assert table in table_names, f"Таблица {table} не создана"

        conn.close()
        manager.conn.close()

        print("✅ Тест пройден!")
        return True

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

    finally:
        # Очистка
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    success = test_db_creation()
    sys.exit(0 if success else 1)


