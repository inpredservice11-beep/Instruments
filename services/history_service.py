"""
Сервис для работы с историей операций
"""
from database_manager import DatabaseManager


class HistoryService:
    """Сервис для управления историей операций"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def get_operation_history(self, filter_type='Все', limit=100):
        """Получение истории операций"""
        return self.db.get_operation_history(filter_type, limit)

