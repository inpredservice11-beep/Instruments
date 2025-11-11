"""
Контроллер приложения - связывает UI и бизнес-логику
"""
from database_manager import DatabaseManager
from services.instrument_service import InstrumentService
from services.employee_service import EmployeeService
from services.issue_service import IssueService
from services.address_service import AddressService
from services.history_service import HistoryService
from services.statistics_service import StatisticsService


class AppController:
    """Контроллер приложения, управляющий сервисами"""
    
    def __init__(self):
        # Инициализация базы данных
        self.db = DatabaseManager()
        
        # Инициализация сервисов
        self.instrument_service = InstrumentService(self.db)
        self.employee_service = EmployeeService(self.db)
        self.issue_service = IssueService(self.db)
        self.address_service = AddressService(self.db)
        self.history_service = HistoryService(self.db)
        self.statistics_service = StatisticsService(self.db)
    
    @property
    def services(self):
        """Получение всех сервисов"""
        return {
            'instruments': self.instrument_service,
            'employees': self.employee_service,
            'issues': self.issue_service,
            'addresses': self.address_service,
            'history': self.history_service,
            'statistics': self.statistics_service
        }

