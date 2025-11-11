"""
Сервис для работы с адресами выдачи
"""
from database_manager import DatabaseManager


class AddressService:
    """Сервис для управления адресами"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def get_addresses(self):
        """Получение списка адресов"""
        return self.db.get_addresses()
    
    def get_address_by_id(self, address_id):
        """Получение адреса по ID"""
        return self.db.get_address_by_id(address_id)
    
    def add_address(self, name, full_address=''):
        """Добавление нового адреса"""
        return self.db.add_address(name, full_address)
    
    def update_address(self, address_id, name, full_address=''):
        """Обновление адреса"""
        return self.db.update_address(address_id, name, full_address)
    
    def delete_address(self, address_id):
        """Удаление адреса"""
        return self.db.delete_address(address_id)

