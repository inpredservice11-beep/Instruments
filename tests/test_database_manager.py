#!/usr/bin/env python3
"""
Тесты для модуля database_manager.py
"""

import pytest


class TestDatabaseManager:
    """Тесты для DatabaseManager"""

    def test_init_database(self, db_manager, temp_db_path):
        """Тест инициализации базы данных"""
        assert os.path.exists(temp_db_path)

        # Проверяем, что основные таблицы созданы
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        # Проверяем существование основных таблиц
        tables = ['instruments', 'employees', 'issues', 'addresses']
        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            assert cursor.fetchone() is not None

        conn.close()

    def test_add_and_get_instrument(self, db_manager, sample_instrument_data):
        """Тест добавления и получения инструмента"""
        # Добавляем инструмент
        data = (
            sample_instrument_data['name'],
            sample_instrument_data['description'],
            sample_instrument_data['inventory_number'],
            sample_instrument_data['serial_number'],
            sample_instrument_data['category'],
            sample_instrument_data['status'],
            sample_instrument_data['photo_path'],
            sample_instrument_data['barcode']
        )

        result = db_manager.add_instrument(data)
        assert result is True

        # Получаем инструмент
        instrument = db_manager.get_instrument_by_id(1)
        assert instrument is not None
        assert instrument[1] == sample_instrument_data['name']
        assert instrument[3] == sample_instrument_data['inventory_number']
        assert instrument[8] == sample_instrument_data['barcode']

    def test_update_instrument(self, db_manager, sample_instrument_data):
        """Тест обновления инструмента"""
        # Сначала добавляем инструмент
        data = (
            sample_instrument_data['name'],
            sample_instrument_data['description'],
            sample_instrument_data['inventory_number'],
            sample_instrument_data['serial_number'],
            sample_instrument_data['category'],
            sample_instrument_data['status'],
            sample_instrument_data['photo_path'],
            sample_instrument_data['barcode']
        )
        db_manager.add_instrument(data)

        # Обновляем данные
        updated_data = (
            "Обновленное название",
            "Обновленное описание",
            sample_instrument_data['inventory_number'],
            "NEW-SERIAL-001",
            "Ручной инструмент",
            "Выдан",
            sample_instrument_data['photo_path'],
            "UPDATED123456"
        )

        result = db_manager.update_instrument(1, updated_data)
        assert result is True

        # Проверяем обновление
        instrument = db_manager.get_instrument_by_id(1)
        assert instrument[1] == "Обновленное название"
        assert instrument[4] == "NEW-SERIAL-001"
        assert instrument[5] == "Ручной инструмент"
        assert instrument[6] == "Выдан"
        assert instrument[8] == "UPDATED123456"

    def test_duplicate_inventory_number(self, db_manager, sample_instrument_data):
        """Тест запрета дублирования инвентарного номера"""
        data = (
            sample_instrument_data['name'],
            sample_instrument_data['description'],
            sample_instrument_data['inventory_number'],
            sample_instrument_data['serial_number'],
            sample_instrument_data['category'],
            sample_instrument_data['status'],
            sample_instrument_data['photo_path'],
            sample_instrument_data['barcode']
        )

        # Добавляем первый инструмент
        result1 = db_manager.add_instrument(data)
        assert result1 is True

        # Пытаемся добавить второй с тем же инвентарным номером
        data2 = (
            "Другой инструмент",
            "Другое описание",
            sample_instrument_data['inventory_number'],  # Тот же номер
            "DIFFERENT-SERIAL",
            "Электроинструмент",
            "Доступен",
            None,
            "DIFFERENT123"
        )

        result2 = db_manager.add_instrument(data2)
        assert result2 is False  # Должно быть False из-за дубликата

    def test_add_and_get_employee(self, db_manager, sample_employee_data):
        """Тест добавления и получения сотрудника"""
        # Добавляем сотрудника
        data = (
            sample_employee_data['full_name'],
            sample_employee_data['position'],
            sample_employee_data['department'],
            sample_employee_data['phone'],
            sample_employee_data['email'],
            sample_employee_data['status'],
            sample_employee_data['photo_path']
        )

        result = db_manager.add_employee(data)
        assert result is True

        # Получаем сотрудника
        employees = db_manager.get_employees()
        assert len(employees) > 0

        # Ищем нашего сотрудника
        found = False
        for emp in employees:
            if emp[1] == sample_employee_data['full_name']:
                found = True
                assert emp[2] == sample_employee_data['position']
                assert emp[5] == sample_employee_data['email']
                break

        assert found, "Сотрудник не найден в списке"

    def test_issue_instrument(self, db_manager, sample_instrument_data, sample_employee_data):
        """Тест выдачи инструмента"""
        # Добавляем инструмент и сотрудника
        inst_data = (
            sample_instrument_data['name'],
            sample_instrument_data['description'],
            sample_instrument_data['inventory_number'],
            sample_instrument_data['serial_number'],
            sample_instrument_data['category'],
            "Доступен",
            sample_instrument_data['photo_path'],
            sample_instrument_data['barcode']
        )
        db_manager.add_instrument(inst_data)

        emp_data = (
            sample_employee_data['full_name'],
            sample_employee_data['position'],
            sample_employee_data['department'],
            sample_employee_data['phone'],
            sample_employee_data['email'],
            sample_employee_data['status'],
            sample_employee_data['photo_path']
        )
        db_manager.add_employee(emp_data)

        # Создаем адрес
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO addresses (name, full_address) VALUES (?, ?)",
                      ("Тестовый адрес", "г. Тест, ул. Тестовая, д. 1"))
        conn.commit()
        conn.close()

        # Выдаем инструмент
        from datetime import datetime, timedelta
        expected_return = datetime.now() + timedelta(days=7)

        result = db_manager.issue_instrument(
            instrument_id=1,
            employee_id=1,
            expected_return_date=expected_return.date(),
            notes="Тестовая выдача",
            issued_by="Тестовый пользователь",
            address_id=1
        )

        assert result[0] is True  # Успешная выдача

        # Проверяем, что инструмент теперь выдан
        instrument = db_manager.get_instrument_by_id(1)
        assert instrument[6] == "Выдан"  # Статус должен измениться

    def test_return_instrument(self, db_manager, sample_instrument_data, sample_employee_data):
        """Тест возврата инструмента"""
        # Сначала выдаем инструмент (используем код из предыдущего теста)
        inst_data = (
            sample_instrument_data['name'],
            sample_instrument_data['description'],
            sample_instrument_data['inventory_number'],
            sample_instrument_data['serial_number'],
            sample_instrument_data['category'],
            "Доступен",
            sample_instrument_data['photo_path'],
            sample_instrument_data['barcode']
        )
        db_manager.add_instrument(inst_data)

        emp_data = (
            sample_employee_data['full_name'],
            sample_employee_data['position'],
            sample_employee_data['department'],
            sample_employee_data['phone'],
            sample_employee_data['email'],
            sample_employee_data['status'],
            sample_employee_data['photo_path']
        )
        db_manager.add_employee(emp_data)

        # Создаем адрес
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO addresses (name, full_address) VALUES (?, ?)",
                      ("Тестовый адрес", "г. Тест, ул. Тестовая, д. 1"))
        conn.commit()
        conn.close()

        # Выдаем инструмент
        from datetime import datetime, timedelta
        expected_return = datetime.now() + timedelta(days=7)

        issue_result = db_manager.issue_instrument(
            instrument_id=1,
            employee_id=1,
            expected_return_date=expected_return.date(),
            notes="Тестовая выдача",
            issued_by="Тестовый пользователь",
            address_id=1
        )
        assert issue_result[0] is True

        # Возвращаем инструмент
        result = db_manager.return_instrument(
            issue_id=1,
            notes="Тестовый возврат",
            returned_by="Тестовый пользователь"
        )

        assert result[0] is True  # Успешный возврат

        # Проверяем, что инструмент снова доступен
        instrument = db_manager.get_instrument_by_id(1)
        assert instrument[6] == "Возвращен"  # Статус должен измениться на "Возвращен"

    def test_get_instruments_with_search(self, db_manager, sample_instrument_data):
        """Тест поиска инструментов"""
        # Добавляем несколько инструментов
        instruments = [
            ("Дрель электрическая", "Мощная дрель", "INV-001", "DR-001", "Электроинструмент", "Доступен"),
            ("Отвертка крестовая", "Крестовая отвертка", "INV-002", "SC-001", "Ручной инструмент", "Доступен"),
            ("Молоток слесарный", "500г молоток", "INV-003", "HM-001", "Ручной инструмент", "Доступен")
        ]

        for inst in instruments:
            data = inst + (None, f"BC{inst[2]}")
            db_manager.add_instrument(data)

        # Тестируем поиск
        results = db_manager.get_instruments("дрель")
        assert len(results) == 1
        assert "Дрель" in results[0][1]

        results = db_manager.get_instruments("ручной")
        assert len(results) == 2

        results = db_manager.get_instruments("несуществующий")
        assert len(results) == 0


