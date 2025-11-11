"""
Сервис для работы со статистикой
"""
from database_manager import DatabaseManager


class StatisticsService:
    """Сервис для получения статистики"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def get_general_statistics(self):
        """Получение общей статистики"""
        return self.db.get_general_statistics()
    
    def get_instruments_by_category(self):
        """Статистика инструментов по категориям"""
        return self.db.get_instruments_by_category()
    
    def get_top_employees_by_issues(self, limit=10):
        """Топ сотрудников по количеству выдач"""
        return self.db.get_top_employees_by_issues(limit)
    
    def get_most_used_instruments(self, limit=10):
        """Самые используемые инструменты"""
        return self.db.get_most_used_instruments(limit)
    
    def get_average_usage_time(self):
        """Среднее время использования инструментов"""
        return self.db.get_average_usage_time()

