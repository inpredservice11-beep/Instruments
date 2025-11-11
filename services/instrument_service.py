"""
Сервис для работы с инструментами
"""
from database_manager import DatabaseManager


class InstrumentService:
    """Сервис для управления инструментами"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def get_instruments(self, search_text=''):
        """Получение списка инструментов"""
        return self.db.get_instruments(search_text)
    
    def get_instrument_by_id(self, instrument_id):
        """Получение инструмента по ID"""
        return self.db.get_instrument_by_id(instrument_id)
    
    def add_instrument(self, data):
        """Добавление нового инструмента"""
        return self.db.add_instrument(data)
    
    def update_instrument(self, instrument_id, data):
        """Обновление инструмента"""
        return self.db.update_instrument(instrument_id, data)
    
    def delete_instrument(self, instrument_id):
        """Удаление инструмента"""
        return self.db.delete_instrument(instrument_id)

