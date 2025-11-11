"""
Сервис для работы с выдачами инструментов
"""
from database_manager import DatabaseManager


class IssueService:
    """Сервис для управления выдачами"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def get_active_issues(self):
        """Получение активных выдач"""
        return self.db.get_active_issues()
    
    def get_active_issues_for_return(self):
        """Получение активных выдач для возврата"""
        return self.db.get_active_issues_for_return()
    
    def get_issue_by_id(self, issue_id):
        """Получение выдачи по ID"""
        return self.db.get_issue_by_id(issue_id)
    
    def issue_instrument(self, instrument_id, employee_id, expected_return_date, 
                       notes, issued_by, address_id=None):
        """Выдача инструмента"""
        return self.db.issue_instrument(
            instrument_id, employee_id, expected_return_date, 
            notes, issued_by, address_id
        )
    
    def return_instrument(self, issue_id, notes, returned_by):
        """Возврат инструмента"""
        return self.db.return_instrument(issue_id, notes, returned_by)
    
    def get_issues_statistics(self):
        """Получение статистики по выдачам"""
        return self.db.get_issues_statistics()

