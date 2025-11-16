#!/usr/bin/env python3
"""Тест инициализации базы данных"""

try:
    from database_manager import DatabaseManager
    print("🔄 Инициализация базы данных...")
    db = DatabaseManager()
    print("✅ База данных инициализирована успешно!")
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
