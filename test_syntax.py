#!/usr/bin/env python3
"""Быстрый тест синтаксиса"""

try:
    import build_exe
    print("✅ build_exe.py - синтаксис OK")
except SyntaxError as e:
    print(f"❌ Синтаксическая ошибка: {e}")
except ImportError as e:
    print(f"⚠️ Ошибка импорта: {e}")
except Exception as e:
    print(f"⚠️ Другая ошибка: {e}")

# Проверяем определение функций
try:
    if hasattr(build_exe, 'create_exe'):
        print("✅ Функция create_exe() определена")
    else:
        print("❌ Функция create_exe() не найдена")
except:
    pass

print("🏁 Тест завершен")
