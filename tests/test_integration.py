#!/usr/bin/env python3
"""
Интеграционные тесты для системы учета инструмента
"""

import pytest
import os
import tempfile


class TestIntegration:
    """Интеграционные тесты"""

    def test_full_workflow(self, db_manager, barcode_manager, sample_instrument_data, sample_employee_data):
        """Тест полного рабочего процесса: добавление -> выдача -> возврат"""
        # 1. Добавляем инструмент со штрих-кодом
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

        result = db_manager.add_instrument(inst_data)
        assert result is True

        # 2. Добавляем сотрудника
        emp_data = (
            sample_employee_data['full_name'],
            sample_employee_data['position'],
            sample_employee_data['department'],
            sample_employee_data['phone'],
            sample_employee_data['email'],
            sample_employee_data['status'],
            sample_employee_data['photo_path']
        )

        result = db_manager.add_employee(emp_data)
        assert result is True

        # 3. Создаем адрес
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO addresses (name, full_address) VALUES (?, ?)",
                      ("Офис", "г. Санкт-Петербург, Невский пр., д. 1"))
        address_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # 4. Проверяем, что можем найти инструмент по штрих-коду
        found_instrument = barcode_manager.search_by_barcode(
            sample_instrument_data['barcode'], db_manager)
        assert found_instrument is not None
        assert found_instrument['name'] == sample_instrument_data['name']

        # 5. Выдаем инструмент сотруднику
        from datetime import datetime, timedelta
        expected_return = datetime.now() + timedelta(days=7)

        issue_result = db_manager.issue_instrument(
            instrument_id=1,
            employee_id=1,
            expected_return_date=expected_return.date(),
            notes="Интеграционный тест выдачи",
            issued_by="Система тестирования",
            address_id=address_id
        )
        assert issue_result[0] is True

        # 6. Проверяем, что инструмент отмечен как выданный
        instrument = db_manager.get_instrument_by_id(1)
        assert instrument[6] == "Выдан"

        # 7. Проверяем активные выдачи
        active_issues = db_manager.get_active_issues()
        assert len(active_issues) == 1
        assert active_issues[0][1] == sample_instrument_data['inventory_number']

        # 8. Возвращаем инструмент
        return_result = db_manager.return_instrument(
            issue_id=1,
            notes="Интеграционный тест возврата",
            returned_by="Система тестирования"
        )
        assert return_result[0] is True

        # 9. Проверяем, что инструмент отмечен как возвращенный
        instrument = db_manager.get_instrument_by_id(1)
        assert instrument[6] == "Возвращен"

        # 10. Проверяем историю операций
        operations = db_manager.get_operation_history()
        assert len(operations) >= 2  # Выдача и возврат

        # 11. Проверяем статистику
        stats = db_manager.get_issues_statistics()
        assert 'total_issues' in stats
        assert 'active_issues' in stats
        assert 'returned_today' in stats

    def test_barcode_workflow(self, db_manager, barcode_manager):
        """Тест рабочего процесса со штрих-кодами"""
        # 1. Генерируем штрих-код
        barcode = barcode_manager.generate_unique_barcode()
        assert barcode_manager.validate_barcode(barcode)

        # 2. Добавляем инструмент со сгенерированным штрих-кодом
        inst_data = (
            "Тестовый инструмент с ШК",
            "Инструмент для тестирования штрих-кодов",
            "BC-TEST-001",
            "BC-SN-001",
            "Электроинструмент",
            "Доступен",
            None,
            barcode
        )

        result = db_manager.add_instrument(inst_data)
        assert result is True

        # 3. Ищем инструмент по штрих-коду
        found = barcode_manager.search_by_barcode(barcode, db_manager)
        assert found is not None
        assert found['barcode'] == barcode
        assert found['inventory_number'] == "BC-TEST-001"

        # 4. Генерируем изображение штрих-кода
        image_path = barcode_manager.generate_barcode(barcode)
        assert image_path is not None
        assert os.path.exists(image_path)

        # 5. Проверяем, что можем получить изображение для Tkinter
        tk_image = barcode_manager.get_barcode_image(barcode)
        assert tk_image is not None

        # Очистка
        if os.path.exists(image_path):
            os.remove(image_path)

    def test_bulk_operations(self, db_manager):
        """Тест массовых операций"""
        # 1. Добавляем несколько инструментов
        instruments = []
        for i in range(5):
            inst_data = (
                f"Инструмент #{i+1}",
                f"Описание инструмента #{i+1}",
                f"BULK-{i+1:03d}",
                f"SN-BULK-{i+1:03d}",
                "Ручной инструмент",
                "Доступен",
                None,
                f"BULKCODE{i+1:03d}"
            )
            db_manager.add_instrument(inst_data)
            instruments.append(inst_data)

        # 2. Добавляем сотрудника
        emp_data = (
            "Бригадир Иванов",
            "Бригадир",
            "Производственный цех",
            "+7-900-999-99-99",
            "brigadir@test.com",
            "Активен",
            None
        )
        db_manager.add_employee(emp_data)

        # 3. Создаем адрес
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO addresses (name, full_address) VALUES (?, ?)",
                      ("Склад", "г. СПб, ул. Складская, д. 10"))
        address_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # 4. Выдаем все инструменты массово (имитируем batch_issues)
        from datetime import datetime, timedelta
        expected_return = datetime.now() + timedelta(days=14)

        # Создаем запись о массовой выдаче
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO batch_issues (employee_id, issue_date, expected_return_date, notes, issued_by)
            VALUES (?, ?, ?, ?, ?)
        """, (1, datetime.now(), expected_return.date(), "Массовый тест", "Система"))
        batch_id = cursor.lastrowid

        # Выдаем каждый инструмент
        issued_ids = []
        for i in range(1, 6):  # ID инструментов 1-5
            cursor.execute("""
                INSERT INTO issues (batch_id, instrument_id, employee_id, address_id,
                                  issue_date, expected_return_date, notes, issued_by, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Выдан')
            """, (batch_id, i, 1, address_id, datetime.now(), expected_return.date(),
                  f"Массовый тест #{i}", "Система"))
            issued_ids.append(cursor.lastrowid)

        conn.commit()
        conn.close()

        # 5. Проверяем, что все инструменты выданы
        for i in range(1, 6):
            instrument = db_manager.get_instrument_by_id(i)
            assert instrument[6] == "Выдан"

        # 6. Проверяем активные выдачи
        active_issues = db_manager.get_active_issues()
        assert len(active_issues) >= 5

        # 7. Возвращаем все инструменты массово
        return_result = db_manager.return_instruments_batch(
            issued_ids, "Массовый возврат", "Система")
        assert return_result[0] is True

        # 8. Проверяем, что все инструменты возвращены
        for i in range(1, 6):
            instrument = db_manager.get_instrument_by_id(i)
            assert instrument[6] == "Возвращен"

    def test_data_integrity(self, db_manager):
        """Тест целостности данных"""
        # 1. Добавляем инструмент и сотрудника
        inst_data = ("Тест целостности", "Описание", "INT-001", "SN-001",
                    "Электроинструмент", "Доступен", None, "INT123")
        emp_data = ("Тестов Тест Тестович", "Тестер", "Тестовый отдел",
                   "+7-999-999-99-99", "test@test.com", "Активен", None)

        db_manager.add_instrument(inst_data)
        db_manager.add_employee(emp_data)

        # 2. Пытаемся выдать несуществующий инструмент
        from datetime import datetime, timedelta
        future_date = datetime.now() + timedelta(days=7)

        result = db_manager.issue_instrument(999, 1, future_date.date(), "Тест", "Система")
        assert result[0] is False
        assert "не найден" in result[1].lower()

        # 3. Пытаемся выдать уже выданный инструмент
        # Сначала выдаем нормально
        db_manager.issue_instrument(1, 1, future_date.date(), "Тест", "Система")

        # Пытаемся выдать повторно
        result = db_manager.issue_instrument(1, 1, future_date.date(), "Тест", "Система")
        assert result[0] is False
        assert "недоступен" in result[1].lower()

        # 4. Пытаемся вернуть несуществующую выдачу
        result = db_manager.return_instrument(999, "Тест", "Система")
        assert result[0] is False
        assert "не найдена" in result[1].lower()

        # 5. Пытаемся вернуть уже возвращенную выдачу
        db_manager.return_instrument(1, "Тест", "Система")

        result = db_manager.return_instrument(1, "Тест", "Система")
        assert result[0] is False
        assert "уже возвращен" in result[1].lower()


