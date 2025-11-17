"""
Менеджер базы данных для системы учета инструмента
"""

import sqlite3
from datetime import datetime, timedelta
import os


class DatabaseManager:
    def __init__(self, db_path='tool_management.db'):
        self.db_path = db_path
        self.conn = None  # Для отслеживания соединения
        self.init_database()
        
    def init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Выполнение SQL скрипта создания таблиц (всегда, для гарантии)
        try:
            with open('database/01_create_tables.sql', 'r', encoding='utf-8') as f:
                sql_script = f.read()
                cursor.executescript(sql_script)
            print("✅ Таблицы базы данных созданы")
        except FileNotFoundError:
            print("❌ Ошибка: файл database/01_create_tables.sql не найден")
            raise
        except Exception as e:
            print(f"❌ Ошибка создания таблиц: {e}")
            raise

        conn.commit()
        conn.close()

        # Выполняем миграцию (добавление колонок)
        try:
            self.migrate_database()
            print("✅ Миграция базы данных выполнена")
        except Exception as e:
            print(f"❌ Ошибка миграции: {e}")
            raise

        # Вставка тестовых данных только если таблицы пустые
        if self._is_database_empty():
            self.insert_sample_data()

    def get_statistics(self):
        """Получение общей статистики системы"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            stats = {}

            # Статистика инструментов

            # Общее количество инструментов
            cursor.execute("SELECT COUNT(*) FROM instruments")
            stats['total_instruments'] = cursor.fetchone()[0]

            # Количество по статусам
            cursor.execute("SELECT status, COUNT(*) FROM instruments GROUP BY status")
            status_counts = dict(cursor.fetchall())

            stats['available_instruments'] = status_counts.get('Доступен', 0)
            stats['issued_instruments'] = status_counts.get('Выдан', 0)
            stats['repair_instruments'] = status_counts.get('На ремонте', 0)

            # Статистика сотрудников
            cursor.execute("SELECT COUNT(*) FROM employees WHERE status = 'Активен'")
            stats['total_employees'] = cursor.fetchone()[0]

            # Активные выдачи
            cursor.execute("SELECT COUNT(*) FROM issues WHERE status = 'Выдан'")
            stats['active_issues'] = cursor.fetchone()[0]

            # Просроченные возвраты
            cursor.execute("""
                SELECT COUNT(*) FROM issues
                WHERE status = 'Выдан'
                AND expected_return_date < date('now')
            """)
            stats['overdue_issues'] = cursor.fetchone()[0]

            conn.close()
            return stats

        except Exception as e:
            print(f"Ошибка получения статистики: {e}")
            return {
                'total_instruments': 0,
                'available_instruments': 0,
                'issued_instruments': 0,
                'repair_instruments': 0,
                'total_employees': 0,
                'active_issues': 0,
                'overdue_issues': 0
            }

    def _is_database_empty(self):
        """Проверка, пустая ли база данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Проверяем количество записей в основных таблицах
            tables_to_check = ['instruments', 'employees', 'addresses']
            for table in tables_to_check:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                if count > 0:
                    conn.close()
                    return False

            conn.close()
            return True
        except Exception:
            return True  # Если ошибка, считаем что база пустая

    def close(self):
        """Закрытие соединения с базой данных"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def migrate_database(self):
        """Обновление схемы базы данных до актуальной версии"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Проверяем существование основных таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('instruments', 'employees', 'addresses', 'issues')")
        existing_tables = [row[0] for row in cursor.fetchall()]

        required_tables = ['instruments', 'employees', 'addresses', 'issues']
        missing_tables = [table for table in required_tables if table not in existing_tables]

        if missing_tables:
            raise sqlite3.OperationalError(f"Отсутствуют таблицы: {', '.join(missing_tables)}. Возможно, файл database/01_create_tables.sql не найден или поврежден.")

        # Таблица адресов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                full_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Добавляем колонку address_id в таблицу issues, если её нет
        cursor.execute("PRAGMA table_info(issues)")
        issue_columns = [row[1] for row in cursor.fetchall()]
        if 'address_id' not in issue_columns:
            cursor.execute("ALTER TABLE issues ADD COLUMN address_id INTEGER REFERENCES addresses(id)")

        # Добавляем колонку photo_path в таблицу instruments, если её нет
        cursor.execute("PRAGMA table_info(instruments)")
        instrument_columns = [row[1] for row in cursor.fetchall()]
        if 'photo_path' not in instrument_columns:
            cursor.execute("ALTER TABLE instruments ADD COLUMN photo_path TEXT")

        # Добавляем колонку barcode в таблицу instruments, если её нет
        if 'barcode' not in instrument_columns:
            cursor.execute("ALTER TABLE instruments ADD COLUMN barcode TEXT")
            # Создаем индекс для уникальности barcode
            try:
                cursor.execute("CREATE UNIQUE INDEX idx_instruments_barcode ON instruments(barcode)")
            except sqlite3.OperationalError:
                # Индекс уже существует, пропускаем
                pass

        # Добавляем колонку photo_path в таблицу employees, если её нет
        cursor.execute("PRAGMA table_info(employees)")
        employee_columns = [row[1] for row in cursor.fetchall()]
        if 'photo_path' not in employee_columns:
            cursor.execute("ALTER TABLE employees ADD COLUMN photo_path TEXT")

        # Создаем папку для фотографий, если её нет
        photos_dir = 'photos'
        if not os.path.exists(photos_dir):
            os.makedirs(photos_dir)
            # Создаем подпапки
            os.makedirs(os.path.join(photos_dir, 'instruments'))
            os.makedirs(os.path.join(photos_dir, 'employees'))

        conn.commit()
        conn.close()
    
    def insert_sample_data(self):
        """Вставка тестовых данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            with open('database/02_insert_sample_data.sql', 'r', encoding='utf-8') as f:
                sql_script = f.read()
                cursor.executescript(sql_script)
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Ошибка при вставке тестовых данных: {e}")
    
    def get_connection(self):
        """Получение соединения с БД"""
        conn = sqlite3.connect(self.db_path)
        # Регистрируем функцию для корректного преобразования в нижний регистр (работает с кириллицей)
        conn.create_function("LOWER_PY", 1, lambda s: s.lower() if s else s)
        return conn
    
    # ========== ИНСТРУМЕНТЫ ==========
    
    def get_instruments(self, search_text=''):
        """Получение списка инструментов"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if search_text:
            # Преобразуем поисковый текст в нижний регистр в Python для корректной работы с кириллицей
            search_text_lower = search_text.lower()
            query = """
                SELECT 
                    ins.id,
                    ins.name,
                    ins.inventory_number,
                    ins.serial_number,
                    ins.category,
                    COALESCE(NULLIF(addr.full_address, ''), addr.name, '') as current_address,
                    ins.status,
                    COALESCE(ins.photo_path, '') as photo_path
                FROM instruments ins
                LEFT JOIN issues i ON i.instrument_id = ins.id AND i.status = 'Выдан'
                LEFT JOIN addresses addr ON i.address_id = addr.id
                WHERE LOWER_PY(ins.name) LIKE ? 
                      OR LOWER_PY(ins.inventory_number) LIKE ? 
                      OR LOWER_PY(ins.serial_number) LIKE ? 
                      OR LOWER_PY(ins.category) LIKE ?
                      OR LOWER_PY(COALESCE(NULLIF(addr.full_address, ''), addr.name, '')) LIKE ?
                ORDER BY ins.name, ins.inventory_number
            """
            search_pattern = f'%{search_text_lower}%'
            cursor.execute(query, (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern))
        else:
            query = """
                SELECT 
                    ins.id,
                    ins.name,
                    ins.inventory_number,
                    ins.serial_number,
                    ins.category,
                    COALESCE(NULLIF(addr.full_address, ''), addr.name, '') as current_address,
                    ins.status,
                    COALESCE(ins.photo_path, '') as photo_path
                FROM instruments ins
                LEFT JOIN issues i ON i.instrument_id = ins.id AND i.status = 'Выдан'
                LEFT JOIN addresses addr ON i.address_id = addr.id
                ORDER BY ins.name, ins.inventory_number
            """
            cursor.execute(query)
        
        instruments = cursor.fetchall()
        conn.close()
        
        return instruments
    
    def get_instrument_by_id(self, instrument_id):
        """Получение инструмента по ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, description, inventory_number, serial_number, 
                   category, status, 
                   COALESCE(photo_path, '') as photo_path
            FROM instruments
            WHERE id = ?
        """, (instrument_id,))
        
        instrument = cursor.fetchone()
        conn.close()
        
        return instrument
    
    def add_instrument(self, data):
        """Добавление нового инструмента
        data: кортеж (name, description, inventory_number, serial_number, category,
              status, photo_path, barcode)
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Если barcode не передан, добавляем None
            if len(data) == 7:
                data = data + (None,)

            cursor.execute("""
                INSERT INTO instruments
                (name, description, inventory_number, serial_number, category,
                 status, photo_path, barcode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, data)

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка добавления инструмента: {e}")
            conn.close()
            return False
    
    def update_instrument(self, instrument_id, data):
        """Обновление данных инструмента
        data: кортеж (name, description, inventory_number, serial_number, category,
              status, photo_path, barcode)
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Если barcode не передан, добавляем None
            if len(data) == 7:
                data = data + (None,)

            cursor.execute("""
                UPDATE instruments
                SET name = ?, description = ?, inventory_number = ?, serial_number = ?,
                    category = ?, status = ?,
                    photo_path = ?, barcode = ?
                WHERE id = ?
            """, (*data, instrument_id))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка обновления инструмента: {e}")
            conn.close()
            return False
    
    def delete_instrument(self, instrument_id):
        """Удаление инструмента"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Проверка на активные выдачи
            cursor.execute("""
                SELECT COUNT(*) FROM issues 
                WHERE instrument_id = ? AND status = 'Выдан'
            """, (instrument_id,))
            
            if cursor.fetchone()[0] > 0:
                conn.close()
                return False
            
            cursor.execute("DELETE FROM instruments WHERE id = ?", (instrument_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка удаления инструмента: {e}")
            conn.close()
            return False
    
    # ========== СОТРУДНИКИ ==========
    
    def get_employees(self, search_text=''):
        """Получение списка сотрудников"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if search_text:
            # Преобразуем поисковый текст в нижний регистр в Python для корректной работы с кириллицей
            search_text_lower = search_text.lower()
            query = """
                SELECT id, full_name, position, department, phone, email, status, COALESCE(photo_path, '') as photo_path
                FROM employees
                WHERE LOWER_PY(full_name) LIKE ? OR LOWER_PY(position) LIKE ?
                      OR LOWER_PY(department) LIKE ?
                ORDER BY full_name
            """
            search_pattern = f'%{search_text_lower}%'
            cursor.execute(query, (search_pattern, search_pattern, search_pattern))
        else:
            query = """
                SELECT id, full_name, position, department, phone, email, status, COALESCE(photo_path, '') as photo_path
                FROM employees
                ORDER BY full_name
            """
            cursor.execute(query)
        
        employees = cursor.fetchall()
        conn.close()
        
        return employees
    
    def get_employee_by_id(self, employee_id):
        """Получение сотрудника по ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, full_name, position, department, phone, email, status, 
                   COALESCE(photo_path, '') as photo_path
            FROM employees
            WHERE id = ?
        """, (employee_id,))
        
        employee = cursor.fetchone()
        conn.close()
        
        return employee
    
    def add_employee(self, data):
        """Добавление нового сотрудника
        data: кортеж (full_name, position, department, phone, email, status, photo_path)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Если photo_path не передан, добавляем None
            if len(data) == 6:
                data = data + (None,)
            
            cursor.execute("""
                INSERT INTO employees 
                (full_name, position, department, phone, email, status, photo_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, data)
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка добавления сотрудника: {e}")
            conn.close()
            return False
    
    def update_employee(self, employee_id, data):
        """Обновление данных сотрудника
        data: кортеж (full_name, position, department, phone, email, status, photo_path)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Если photo_path не передан, добавляем None
            if len(data) == 6:
                data = data + (None,)
            
            cursor.execute("""
                UPDATE employees
                SET full_name = ?, position = ?, department = ?, 
                    phone = ?, email = ?, status = ?, photo_path = ?
                WHERE id = ?
            """, (*data, employee_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка обновления сотрудника: {e}")
            conn.close()
            return False
    
    def delete_employee(self, employee_id):
        """Удаление сотрудника"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Проверка на активные выдачи
            cursor.execute("""
                SELECT COUNT(*) FROM issues 
                WHERE employee_id = ? AND status = 'Выдан'
            """, (employee_id,))
            
            if cursor.fetchone()[0] > 0:
                conn.close()
                return False
            
            cursor.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка удаления сотрудника: {e}")
            conn.close()
            return False
    
    # ========== ВЫДАЧИ ==========
    
    def get_active_issues(self):
        """Получение списка активных выдач"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                i.id,
                ins.id as instrument_id,
                ins.inventory_number,
                ins.name,
                e.full_name,
                COALESCE(NULLIF(a.full_address, ''), a.name, ''),
                datetime(i.issue_date, 'localtime'),
                i.expected_return_date,
                i.issued_by,
                i.notes,
                ins.photo_path
            FROM issues i
            JOIN instruments ins ON i.instrument_id = ins.id
            JOIN employees e ON i.employee_id = e.id
            LEFT JOIN addresses a ON i.address_id = a.id
            WHERE i.status = 'Выдан'
            ORDER BY i.issue_date DESC
        """)
        
        issues = cursor.fetchall()
        conn.close()
        
        return issues
    
    def get_active_issues_for_return(self):
        """Получение активных выдач для возврата"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                i.id,
                ins.id as instrument_id,
                ins.inventory_number,
                ins.name,
                e.full_name,
                COALESCE(NULLIF(a.full_address, ''), a.name, ''),
                date(i.issue_date),
                i.expected_return_date,
                CAST((julianday('now') - julianday(i.issue_date)) AS INTEGER) as days_in_use,
                ins.photo_path
            FROM issues i
            JOIN instruments ins ON i.instrument_id = ins.id
            JOIN employees e ON i.employee_id = e.id
            LEFT JOIN addresses a ON i.address_id = a.id
            WHERE i.status = 'Выдан'
            ORDER BY i.issue_date ASC
        """)
        
        issues = cursor.fetchall()
        conn.close()
        
        return issues
    
    def get_issue_by_id(self, issue_id):
        """Получение выдачи по ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT
                i.id,
                i.instrument_id,
                ins.inventory_number,
                ins.name as instrument_name,
                i.employee_id,
                e.full_name as employee_name,
                i.issue_date,
                i.expected_return_date,
                i.notes,
                i.address_id,
                COALESCE(a.name, ''),
                COALESCE(a.full_address, ''),
                ins.photo_path
            FROM issues i
            JOIN instruments ins ON i.instrument_id = ins.id
            JOIN employees e ON i.employee_id = e.id
            LEFT JOIN addresses a ON i.address_id = a.id
            WHERE i.id = ?
        """, (issue_id,))
        
        issue = cursor.fetchone()
        conn.close()
        
        return issue
    
    def issue_instrument(self, instrument_id, employee_id, expected_return_date, notes, issued_by, address_id=None):
        """Выдача инструмента"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Проверка статуса инструмента
            cursor.execute("""
                SELECT status FROM instruments WHERE id = ?
            """, (instrument_id,))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return False, "Инструмент не найден"
            
            status = result[0]
            if status != 'Доступен':
                conn.close()
                return False, f"Инструмент недоступен (статус: {status})"
            
            # Создание записи о выдаче
            cursor.execute("""
                INSERT INTO issues 
                (instrument_id, employee_id, expected_return_date, 
                 notes, issued_by, status, address_id)
                VALUES (?, ?, ?, ?, ?, 'Выдан', ?)
            """, (instrument_id, employee_id, expected_return_date, notes, issued_by, address_id))
            
            issue_id = cursor.lastrowid
            
            # Обновление статуса инструмента
            cursor.execute("""
                UPDATE instruments 
                SET status = 'Выдан'
                WHERE id = ?
            """, (instrument_id,))
            
            # Запись в историю
            cursor.execute("""
                INSERT INTO operation_history
                (issue_id, operation_type, instrument_id, employee_id, 
                 performed_by, notes)
                VALUES (?, 'Выдача', ?, ?, ?, ?)
            """, (issue_id, instrument_id, employee_id, issued_by, notes))
            
            conn.commit()
            conn.close()
            return True, "Инструмент успешно выдан"
        except Exception as e:
            conn.close()
            return False, f"Ошибка выдачи: {e}"
    
    def return_instrument(self, issue_id, notes, returned_by):
        """Возврат инструмента"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Получение информации о выдаче
            cursor.execute("""
                SELECT instrument_id, employee_id, status
                FROM issues
                WHERE id = ?
            """, (issue_id,))

            issue = cursor.fetchone()
            if not issue:
                conn.close()
                return False, "Выдача не найдена"

            if issue[2] != 'Выдан':
                conn.close()
                return False, "Инструмент уже возвращен"

            instrument_id, employee_id, _ = issue

            # Обновление записи о выдаче
            cursor.execute("""
                UPDATE issues
                SET actual_return_date = CURRENT_TIMESTAMP,
                    status = 'Возвращен',
                    notes = CASE
                        WHEN notes IS NULL OR notes = '' THEN ?
                        ELSE notes || '; ' || ?
                    END
                WHERE id = ?
            """, (notes, notes, issue_id))

            # Обновление статуса инструмента
            cursor.execute("""
                UPDATE instruments
                SET status = 'Доступен'
                WHERE id = ?
            """, (instrument_id,))

            # Запись в историю
            cursor.execute("""
                INSERT INTO operation_history
                (issue_id, operation_type, instrument_id, employee_id,
                 performed_by, notes)
                VALUES (?, 'Возврат', ?, ?, ?, ?)
            """, (issue_id, instrument_id, employee_id, returned_by, notes))

            conn.commit()
            conn.close()
            return True, "Инструмент успешно возвращен"
        except Exception as e:
            conn.close()
            return False, f"Ошибка возврата: {e}"

    def return_instruments_batch(self, issue_ids, notes, returned_by):
        """Массовый возврат инструментов"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            returned_count = 0
            errors = []

            for issue_id in issue_ids:
                try:
                    # Получение информации о выдаче
                    cursor.execute("""
                        SELECT instrument_id, employee_id, status
                        FROM issues
                        WHERE id = ?
                    """, (issue_id,))

                    issue = cursor.fetchone()
                    if not issue:
                        errors.append(f"Выдача ID {issue_id}: не найдена")
                        continue

                    if issue[2] != 'Выдан':
                        errors.append(f"Выдача ID {issue_id}: инструмент уже возвращен")
                        continue

                    instrument_id, employee_id, _ = issue

                    # Обновление записи о выдаче
                    cursor.execute("""
                        UPDATE issues
                        SET actual_return_date = CURRENT_TIMESTAMP,
                            status = 'Возвращен',
                            notes = CASE
                                WHEN notes IS NULL OR notes = '' THEN ?
                                ELSE notes || '; ' || ?
                            END
                        WHERE id = ?
                    """, (notes, notes, issue_id))

                    # Обновление статуса инструмента
                    cursor.execute("""
                        UPDATE instruments
                        SET status = 'Доступен'
                        WHERE id = ?
                    """, (instrument_id,))

                    # Запись в историю
                    cursor.execute("""
                        INSERT INTO operation_history
                        (issue_id, operation_type, instrument_id, employee_id,
                         performed_by, notes)
                        VALUES (?, 'Возврат', ?, ?, ?, ?)
                    """, (issue_id, instrument_id, employee_id, returned_by, notes))

                    returned_count += 1

                except Exception as e:
                    errors.append(f"Выдача ID {issue_id}: {e}")

            conn.commit()
            conn.close()

            result_message = f"Успешно возвращено: {returned_count} инструментов"
            if errors:
                result_message += f"\nОшибки: {len(errors)}"
                result_message += "\n" + "\n".join(errors[:5])  # Показываем первые 5 ошибок

            return True, result_message

        except Exception as e:
            conn.close()
            return False, f"Ошибка массового возврата: {e}"
    
    def get_issues_statistics(self):
        """Получение статистики по выдачам"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Всего активных выдач
        cursor.execute("""
            SELECT COUNT(*) FROM issues WHERE status = 'Выдан'
        """)
        total = cursor.fetchone()[0]
        
        # Просроченные выдачи
        cursor.execute("""
            SELECT COUNT(*) FROM issues 
            WHERE status = 'Выдан' 
            AND expected_return_date < date('now')
        """)
        overdue = cursor.fetchone()[0]
        
        conn.close()
        
        return {'total': total, 'overdue': overdue}
    
    # ========== ЖУРНАЛ ОПЕРАЦИЙ ==========
    
    def get_operation_history(self, filter_type='Все', limit=100, search_text='', date_from=None, date_to=None):
        """Получение журнала операций с поиском по всем столбцам и фильтром по дате
        
        Args:
            filter_type: тип операции ('Все', 'Выдача', 'Возврат')
            limit: максимальное количество записей
            search_text: текст для поиска
            date_from: начальная дата (строка в формате 'YYYY-MM-DD' или None)
            date_to: конечная дата (строка в формате 'YYYY-MM-DD' или None)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Функция для преобразования текста в нижний регистр (для поиска)
        conn.create_function('LOWER_PY', 1, lambda x: x.lower() if x else '')
        
        search_text_lower = search_text.lower().strip() if search_text else ''
        has_search = bool(search_text_lower)
        
        # Базовый запрос
        base_query = """
            SELECT 
                oh.id,
                oh.operation_type,
                ins.inventory_number,
                ins.name,
                e.full_name,
                COALESCE(NULLIF(a.full_address, ''), a.name, '') as address,
                datetime(oh.operation_date, 'localtime') as operation_date,
                oh.performed_by,
                oh.notes
            FROM operation_history oh
            JOIN instruments ins ON oh.instrument_id = ins.id
            JOIN employees e ON oh.employee_id = e.id
            LEFT JOIN issues iss ON oh.issue_id = iss.id
            LEFT JOIN addresses a ON iss.address_id = a.id
        """
        
        # Условия WHERE
        where_conditions = []
        params = []
        
        # Фильтр по типу операции
        if filter_type != 'Все':
            where_conditions.append("oh.operation_type = ?")
            params.append(filter_type)
        
        # Фильтр по диапазону дат
        if date_from:
            where_conditions.append("date(oh.operation_date) >= ?")
            params.append(date_from)
        
        if date_to:
            where_conditions.append("date(oh.operation_date) <= ?")
            params.append(date_to)
        
        # Поиск по всем столбцам
        if has_search:
            search_pattern = f'%{search_text_lower}%'
            search_conditions = [
                "CAST(oh.id AS TEXT) LIKE ?",
                "LOWER_PY(oh.operation_type) LIKE ?",
                "LOWER_PY(ins.inventory_number) LIKE ?",
                "LOWER_PY(ins.name) LIKE ?",
                "LOWER_PY(e.full_name) LIKE ?",
                "LOWER_PY(COALESCE(NULLIF(a.full_address, ''), a.name, '')) LIKE ?",
                "LOWER_PY(datetime(oh.operation_date, 'localtime')) LIKE ?",
                "LOWER_PY(oh.performed_by) LIKE ?",
                "LOWER_PY(COALESCE(oh.notes, '')) LIKE ?"
            ]
            where_conditions.append(f"({' OR '.join(search_conditions)})")
            params.extend([search_pattern] * len(search_conditions))
        
        # Формируем полный запрос
        if where_conditions:
            query = base_query + " WHERE " + " AND ".join(where_conditions)
        else:
            query = base_query
        
        query += " ORDER BY oh.operation_date DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        history = cursor.fetchall()
        conn.close()
        
        return history

    # ========== АДРЕСА ==========

    def get_addresses(self):
        """Получение списка адресов"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, COALESCE(full_address, '')
            FROM addresses
            ORDER BY name
        """)

        addresses = cursor.fetchall()
        conn.close()
        return addresses

    def add_address(self, name, full_address=''):
        """Добавление нового адреса"""
        if not name:
            return False, "Название адреса не может быть пустым"

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO addresses (name, full_address)
                VALUES (?, ?)
            """, (name.strip(), full_address.strip() if full_address else None))

            conn.commit()
            new_id = cursor.lastrowid
            conn.close()
            return True, new_id
        except Exception as e:
            conn.close()
            return False, str(e)

    def get_address_by_id(self, address_id):
        """Получение адреса по ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, COALESCE(full_address, '')
            FROM addresses
            WHERE id = ?
        """, (address_id,))

        address = cursor.fetchone()
        conn.close()
        return address
    
    def update_address(self, address_id, name, full_address=''):
        """Обновление адреса"""
        if not name:
            return False, "Название адреса не может быть пустым"

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE addresses
                SET name = ?, full_address = ?
                WHERE id = ?
            """, (name.strip(), full_address.strip() if full_address else None, address_id))

            conn.commit()
            conn.close()
            return True, "Адрес обновлен"
        except Exception as e:
            conn.close()
            return False, str(e)
    
    def delete_address(self, address_id):
        """Удаление адреса"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Проверка на использование адреса в активных выдачах
            cursor.execute("""
                SELECT COUNT(*) FROM issues 
                WHERE address_id = ? AND status = 'Выдан'
            """, (address_id,))
            
            if cursor.fetchone()[0] > 0:
                conn.close()
                return False, "Адрес используется в активных выдачах"
            
            cursor.execute("DELETE FROM addresses WHERE id = ?", (address_id,))
            conn.commit()
            conn.close()
            return True, "Адрес удален"
        except Exception as e:
            conn.close()
            return False, str(e)
    
    # ========== СТАТИСТИКА ==========
    
    def get_general_statistics(self):
        """Получение общей статистики"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Всего инструментов
        cursor.execute("SELECT COUNT(*) FROM instruments")
        stats['total_instruments'] = cursor.fetchone()[0]
        
        # Инструменты по статусам
        cursor.execute("""
            SELECT status, COUNT(*) 
            FROM instruments 
            GROUP BY status
        """)
        stats['instruments_by_status'] = dict(cursor.fetchall())
        
        # Всего сотрудников
        cursor.execute("SELECT COUNT(*) FROM employees WHERE status = 'Активен'")
        stats['active_employees'] = cursor.fetchone()[0]
        
        # Всего активных выдач
        cursor.execute("SELECT COUNT(*) FROM issues WHERE status = 'Выдан'")
        stats['active_issues'] = cursor.fetchone()[0]
        
        # Просроченные выдачи
        cursor.execute("""
            SELECT COUNT(*) FROM issues 
            WHERE status = 'Выдан' 
            AND expected_return_date < date('now')
        """)
        stats['overdue_issues'] = cursor.fetchone()[0]
        
        # Всего операций в истории
        cursor.execute("SELECT COUNT(*) FROM operation_history")
        stats['total_operations'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    
    def get_instruments_by_category(self):
        """Статистика инструментов по категориям"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT category, COUNT(*) as count,
                   SUM(CASE WHEN status = 'Доступен' THEN 1 ELSE 0 END) as available,
                   SUM(CASE WHEN status = 'Выдан' THEN 1 ELSE 0 END) as issued,
                   SUM(CASE WHEN status = 'На ремонте' THEN 1 ELSE 0 END) as repair,
                   SUM(CASE WHEN status = 'Списан' THEN 1 ELSE 0 END) as written_off
            FROM instruments
            GROUP BY category
            ORDER BY count DESC
        """)
        
        result = cursor.fetchall()
        conn.close()
        return result
    
    def get_top_employees_by_issues(self, limit=10):
        """Топ сотрудников по количеству выдач"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                e.full_name,
                e.department,
                COUNT(i.id) as total_issues,
                SUM(CASE WHEN i.status = 'Выдан' THEN 1 ELSE 0 END) as active_issues,
                SUM(CASE WHEN i.status = 'Выдан' AND i.expected_return_date < date('now') THEN 1 ELSE 0 END) as overdue
            FROM employees e
            LEFT JOIN issues i ON e.id = i.employee_id
            WHERE e.status = 'Активен'
            GROUP BY e.id, e.full_name, e.department
            HAVING COUNT(i.id) > 0
            ORDER BY total_issues DESC
            LIMIT ?
        """, (limit,))
        
        result = cursor.fetchall()
        conn.close()
        return result
    
    def get_most_used_instruments(self, limit=10):
        """Самые используемые инструменты"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                ins.name,
                ins.inventory_number,
                ins.category,
                COUNT(oh.id) as usage_count,
                SUM(CASE WHEN oh.operation_type = 'Выдача' THEN 1 ELSE 0 END) as issues_count,
                SUM(CASE WHEN oh.operation_type = 'Возврат' THEN 1 ELSE 0 END) as returns_count
            FROM instruments ins
            LEFT JOIN operation_history oh ON ins.id = oh.instrument_id
            GROUP BY ins.id, ins.name, ins.inventory_number, ins.category
            HAVING COUNT(oh.id) > 0
            ORDER BY usage_count DESC
            LIMIT ?
        """, (limit,))
        
        result = cursor.fetchall()
        conn.close()
        return result
    
    def get_issues_by_period(self, days=30):
        """Статистика выдач за период"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                date(issue_date) as issue_day,
                COUNT(*) as count
            FROM issues
            WHERE issue_date >= date('now', '-' || ? || ' days')
            GROUP BY date(issue_date)
            ORDER BY issue_day DESC
        """, (days,))
        
        result = cursor.fetchall()
        conn.close()
        return result
    
    def get_average_usage_time(self):
        """Среднее время использования инструментов"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                AVG(julianday(actual_return_date) - julianday(issue_date)) as avg_days,
                MIN(julianday(actual_return_date) - julianday(issue_date)) as min_days,
                MAX(julianday(actual_return_date) - julianday(issue_date)) as max_days,
                COUNT(*) as total_returns
            FROM issues
            WHERE status = 'Возвращен' 
            AND actual_return_date IS NOT NULL
            AND issue_date IS NOT NULL
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[3] > 0:
            return {
                'avg_days': round(result[0], 1),
                'min_days': int(result[1]) if result[1] else 0,
                'max_days': int(result[2]) if result[2] else 0,
                'total_returns': result[3]
            }
        return None

    def get_analytics_data(self):
        """Получение данных для расширенной аналитики"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            analytics = {}

            # 1. Выдачи по месяцам за последний год
            cursor.execute("""
                SELECT
                    strftime('%Y-%m', issue_date) as month,
                    COUNT(*) as issue_count
                FROM issues
                WHERE issue_date >= date('now', '-12 months')
                GROUP BY strftime('%Y-%m', issue_date)
                ORDER BY month
            """)
            analytics['issues_by_month'] = cursor.fetchall()

            # 2. Возвраты по месяцам за последний год
            cursor.execute("""
                SELECT
                    strftime('%Y-%m', actual_return_date) as month,
                    COUNT(*) as return_count
                FROM issues
                WHERE actual_return_date IS NOT NULL
                    AND actual_return_date >= date('now', '-12 months')
                GROUP BY strftime('%Y-%m', actual_return_date)
                ORDER BY month
            """)
            analytics['returns_by_month'] = cursor.fetchall()

            # 3. Среднее время использования инструментов
            cursor.execute("""
                SELECT
                    AVG(julianday(actual_return_date) - julianday(issue_date)) as avg_days
                FROM issues
                WHERE actual_return_date IS NOT NULL
                    AND status = 'Возвращен'
                    AND actual_return_date >= date('now', '-12 months')
            """)
            avg_usage_result = cursor.fetchone()
            analytics['avg_usage_days'] = avg_usage_result[0] if avg_usage_result[0] else 0

            # 4. Просроченные выдачи по категориям
            cursor.execute("""
                SELECT
                    COALESCE(i.category, 'Без категории') as category,
                    COUNT(*) as overdue_count
                FROM issues isu
                JOIN instruments i ON isu.instrument_id = i.id
                WHERE isu.status = 'Выдан'
                    AND isu.expected_return_date < date('now')
                GROUP BY i.category
                ORDER BY overdue_count DESC
            """)
            analytics['overdue_by_category'] = cursor.fetchall()

            # 5. Выдачи по адресам
            cursor.execute("""
                SELECT
                    COALESCE(a.name, 'Не указан') as address,
                    COUNT(*) as issue_count
                FROM issues isu
                LEFT JOIN addresses a ON isu.address_id = a.id
                WHERE isu.issue_date >= date('now', '-6 months')
                GROUP BY a.name
                ORDER BY issue_count DESC
                LIMIT 10
            """)
            analytics['issues_by_address'] = cursor.fetchall()

            # 6. Статистика по статусам инструментов
            cursor.execute("""
                SELECT
                    status,
                    COUNT(*) as count
                FROM instruments
                GROUP BY status
            """)
            analytics['instrument_status_stats'] = cursor.fetchall()

            # 7. Динамика активных выдач по дням (последние 30 дней)
            cursor.execute("""
                SELECT
                    date('now', '-' || (30 - n) || ' days') as date,
                    (
                        SELECT COUNT(*)
                        FROM issues
                        WHERE status = 'Выдан'
                            AND issue_date <= date('now', '-' || (30 - n) || ' days')
                            AND (actual_return_date IS NULL OR actual_return_date > date('now', '-' || (30 - n) || ' days'))
                    ) as active_count
                FROM (
                    SELECT 1 as n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION
                    SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10 UNION
                    SELECT 11 UNION SELECT 12 UNION SELECT 13 UNION SELECT 14 UNION SELECT 15 UNION
                    SELECT 16 UNION SELECT 17 UNION SELECT 18 UNION SELECT 19 UNION SELECT 20 UNION
                    SELECT 21 UNION SELECT 22 UNION SELECT 23 UNION SELECT 24 UNION SELECT 25 UNION
                    SELECT 26 UNION SELECT 27 UNION SELECT 28 UNION SELECT 29 UNION SELECT 30
                )
                ORDER BY date
            """)
            analytics['active_issues_trend'] = cursor.fetchall()

            conn.close()
            return analytics

        except Exception as e:
            print(f"Ошибка получения аналитических данных: {e}")
            conn.close()
            return None

