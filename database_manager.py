"""
Менеджер базы данных для системы учета инструмента
"""

import sqlite3
from datetime import datetime, timedelta
import os


class DatabaseManager:
    def __init__(self, db_path='tool_management.db'):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Инициализация базы данных"""
        # Создание БД, если её нет
        if not os.path.exists(self.db_path):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Выполнение SQL скрипта создания таблиц
            with open('database/01_create_tables.sql', 'r', encoding='utf-8') as f:
                sql_script = f.read()
                cursor.executescript(sql_script)
            
            conn.commit()
            conn.close()
            
            # Вставка тестовых данных
            self.insert_sample_data()
    
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
                SELECT id, name, inventory_number, serial_number, category, 
                       location, status
                FROM instruments
                WHERE LOWER_PY(name) LIKE ? OR LOWER_PY(inventory_number) LIKE ? 
                      OR LOWER_PY(serial_number) LIKE ? OR LOWER_PY(category) LIKE ?
                ORDER BY name, inventory_number
            """
            search_pattern = f'%{search_text_lower}%'
            cursor.execute(query, (search_pattern, search_pattern, search_pattern, search_pattern))
        else:
            query = """
                SELECT id, name, inventory_number, serial_number, category, 
                       location, status
                FROM instruments
                ORDER BY name, inventory_number
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
                   category, location, purchase_date, price, status
            FROM instruments
            WHERE id = ?
        """, (instrument_id,))
        
        instrument = cursor.fetchone()
        conn.close()
        
        return instrument
    
    def add_instrument(self, data):
        """Добавление нового инструмента"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO instruments 
                (name, description, inventory_number, serial_number, category, 
                 location, purchase_date, price, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка добавления инструмента: {e}")
            conn.close()
            return False
    
    def update_instrument(self, instrument_id, data):
        """Обновление данных инструмента"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE instruments
                SET name = ?, description = ?, inventory_number = ?, serial_number = ?, 
                    category = ?, location = ?, purchase_date = ?, price = ?, status = ?
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
                SELECT id, full_name, position, department, phone, email, status
                FROM employees
                WHERE LOWER_PY(full_name) LIKE ? OR LOWER_PY(position) LIKE ? 
                      OR LOWER_PY(department) LIKE ?
                ORDER BY full_name
            """
            search_pattern = f'%{search_text_lower}%'
            cursor.execute(query, (search_pattern, search_pattern, search_pattern))
        else:
            query = """
                SELECT id, full_name, position, department, phone, email, status
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
            SELECT id, full_name, position, department, phone, email, status
            FROM employees
            WHERE id = ?
        """, (employee_id,))
        
        employee = cursor.fetchone()
        conn.close()
        
        return employee
    
    def add_employee(self, data):
        """Добавление нового сотрудника"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO employees 
                (full_name, position, department, phone, email, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, data)
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка добавления сотрудника: {e}")
            conn.close()
            return False
    
    def update_employee(self, employee_id, data):
        """Обновление данных сотрудника"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE employees
                SET full_name = ?, position = ?, department = ?, 
                    phone = ?, email = ?, status = ?
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
                ins.inventory_number,
                ins.name,
                e.full_name,
                datetime(i.issue_date, 'localtime'),
                i.expected_return_date,
                i.issued_by,
                i.notes
            FROM issues i
            JOIN instruments ins ON i.instrument_id = ins.id
            JOIN employees e ON i.employee_id = e.id
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
                ins.inventory_number,
                ins.name,
                e.full_name,
                date(i.issue_date),
                i.expected_return_date,
                CAST((julianday('now') - julianday(i.issue_date)) AS INTEGER) as days_in_use
            FROM issues i
            JOIN instruments ins ON i.instrument_id = ins.id
            JOIN employees e ON i.employee_id = e.id
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
                i.notes
            FROM issues i
            JOIN instruments ins ON i.instrument_id = ins.id
            JOIN employees e ON i.employee_id = e.id
            WHERE i.id = ?
        """, (issue_id,))
        
        issue = cursor.fetchone()
        conn.close()
        
        return issue
    
    def issue_instrument(self, instrument_id, employee_id, expected_return_date, notes, issued_by):
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
                 notes, issued_by, status)
                VALUES (?, ?, ?, ?, ?, 'Выдан')
            """, (instrument_id, employee_id, expected_return_date, notes, issued_by))
            
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
    
    # ========== ИСТОРИЯ ==========
    
    def get_operation_history(self, filter_type='Все', limit=100):
        """Получение истории операций"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if filter_type == 'Все':
            query = """
                SELECT 
                    oh.id,
                    oh.operation_type,
                    ins.inventory_number,
                    ins.name,
                    e.full_name,
                    datetime(oh.operation_date, 'localtime'),
                    oh.performed_by,
                    oh.notes
                FROM operation_history oh
                JOIN instruments ins ON oh.instrument_id = ins.id
                JOIN employees e ON oh.employee_id = e.id
                ORDER BY oh.operation_date DESC
                LIMIT ?
            """
            cursor.execute(query, (limit,))
        else:
            query = """
                SELECT 
                    oh.id,
                    oh.operation_type,
                    ins.inventory_number,
                    ins.name,
                    e.full_name,
                    datetime(oh.operation_date, 'localtime'),
                    oh.performed_by,
                    oh.notes
                FROM operation_history oh
                JOIN instruments ins ON oh.instrument_id = ins.id
                JOIN employees e ON oh.employee_id = e.id
                WHERE oh.operation_type = ?
                ORDER BY oh.operation_date DESC
                LIMIT ?
            """
            cursor.execute(query, (filter_type, limit))
        
        history = cursor.fetchall()
        conn.close()
        
        return history

