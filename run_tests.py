#!/usr/bin/env python3
"""
Скрипт для запуска тестов системы учета инструмента
"""

import subprocess
import sys
import os

def run_tests():
    """Запуск всех тестов"""
    print("🚀 Запуск тестов системы учета инструмента...")
    print("=" * 50)

    # Проверяем наличие pytest
    try:
        import pytest
        print("✅ pytest найден")
    except ImportError:
        print("❌ pytest не установлен. Установите зависимости:")
        print("pip install -r requirements.txt")
        return False

    # Запуск тестов
    try:
        # Unit-тесты
        print("\n📋 Запуск unit-тестов...")
        result_unit = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/test_barcode_utils.py",
            "tests/test_database_manager.py",
            "-v", "--tb=short"
        ], capture_output=True, text=True, cwd=os.getcwd())

        print("Unit-тесты:")
        print(result_unit.stdout)
        if result_unit.stderr:
            print("Ошибки:", result_unit.stderr)

        # Интеграционные тесты
        print("\n📋 Запуск интеграционных тестов...")
        result_integration = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/test_integration.py",
            "-v", "--tb=short"
        ], capture_output=True, text=True, cwd=os.getcwd())

        print("Интеграционные тесты:")
        print(result_integration.stdout)
        if result_integration.stderr:
            print("Ошибки:", result_integration.stderr)

        # Общая статистика
        print("\n" + "=" * 50)
        print("📊 Результаты тестирования:")

        unit_success = result_unit.returncode == 0
        integration_success = result_integration.returncode == 0

        if unit_success and integration_success:
            print("✅ Все тесты пройдены успешно!")
            return True
        else:
            print("❌ Некоторые тесты провалились")
            if not unit_success:
                print("  - Unit-тесты: ❌")
            if not integration_success:
                print("  - Интеграционные тесты: ❌")
            return False

    except Exception as e:
        print(f"❌ Ошибка при запуске тестов: {e}")
        return False

def run_specific_test(test_file, test_class=None, test_method=None):
    """Запуск конкретного теста"""
    cmd = [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"]

    if test_class and test_method:
        cmd.append(f"{test_class}::{test_method}")
    elif test_class:
        cmd.append(f"--collect-only={test_class}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        print(result.stdout)
        if result.stderr:
            print("Ошибки:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Запуск конкретного теста
        test_file = sys.argv[1]
        test_class = sys.argv[2] if len(sys.argv) > 2 else None
        test_method = sys.argv[3] if len(sys.argv) > 3 else None

        success = run_specific_test(test_file, test_class, test_method)
    else:
        # Запуск всех тестов
        success = run_tests()

    sys.exit(0 if success else 1)



