"""
Сервис для работы с сотрудниками
"""
from database_manager import DatabaseManager


class EmployeeService:
    """Сервис для управления сотрудниками"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def get_employees(self, search_text=''):
        """Получение списка сотрудников"""
        return self.db.get_employees(search_text)
    
    def get_employee_by_id(self, employee_id):
        """Получение сотрудника по ID"""
        return self.db.get_employee_by_id(employee_id)
    
    def add_employee(self, data):
        """Добавление нового сотрудника"""
        return self.db.add_employee(data)
    
    def update_employee(self, employee_id, data):
        """Обновление сотрудника"""
        return self.db.update_employee(employee_id, data)
    
    def delete_employee(self, employee_id):
        """Удаление сотрудника"""
        return self.db.delete_employee(employee_id)

