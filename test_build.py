#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работоспособности перед компиляцией
"""

import sys
import os

def test_imports():
    """Тестирование импортов"""
    print("🧪 Тестирование импортов...")

    try:
        import tkinter
        import tkinter.ttk
        print("✅ tkinter - OK")
    except ImportError as e:
        print(f"❌ tkinter - Ошибка: {e}")
        return False

    try:
        from PIL import Image, ImageTk
        print("✅ PIL - OK")
    except ImportError as e:
        print(f"❌ PIL - Ошибка: {e}")
        return False

    try:
        import tkcalendar
        print("✅ tkcalendar - OK")
    except ImportError as e:
        print(f"❌ tkcalendar - Ошибка: {e}")
        return False

    try:
        import reportlab
        print("✅ reportlab - OK")
    except ImportError as e:
        print(f"❌ reportlab - Ошибка: {e}")
        return False

    try:
        import openpyxl
        print("✅ openpyxl - OK")
    except ImportError as e:
        print(f"❌ openpyxl - Ошибка: {e}")
        return False

    try:
        import matplotlib
        print("✅ matplotlib - OK")
    except ImportError as e:
        print(f"❌ matplotlib - Ошибка: {e}")
        return False

    return True

def test_files():
    """Проверка наличия файлов"""
    print("\\n📁 Проверка файлов...")

    required_files = [
        "app.py",
        "database_manager.py",
        "dialogs.py",
        "requirements.txt"
    ]

    required_dirs = [
        "database",
        "photos"
    ]

    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - отсутствует")
            return False

    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✅ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ - отсутствует")
            return False

    return True

def test_app_import():
    """Тестирование импорта основного приложения"""
    print("\\n🚀 Тестирование импорта приложения...")

    try:
        import app
        print("✅ app.py импортируется без ошибок")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта app.py: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Предварительное тестирование перед компиляцией")
    print("=" * 50)

    all_good = True

    if not test_files():
        all_good = False

    if not test_imports():
        all_good = False

    if not test_app_import():
        all_good = False

    print("\\n" + "=" * 50)
    if all_good:
        print("✅ Все тесты пройдены! Можно компилировать в exe")
        print("\\n💡 Рекомендации:")
        print("   - Запустите: python build_exe.py")
        print("   - Или используйте: build_exe.bat")
    else:
        print("❌ Найдены проблемы. Исправьте их перед компиляцией")
        print("\\n🔧 Возможные решения:")
        print("   - pip install -r requirements.txt")
        print("   - Проверьте наличие всех файлов")

    sys.exit(0 if all_good else 1)
