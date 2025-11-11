# Архитектура приложения

## Структура проекта после рефакторинга

```
.
├── app.py                    # Главный файл приложения
├── app_controller.py         # Контроллер, связывающий UI и сервисы
├── database_manager.py       # Менеджер базы данных
├── dialogs.py                # Диалоговые окна
├── pdf_export.py             # Экспорт в PDF
├── window_config.py          # Управление конфигурацией окон
│
├── config/                   # Конфигурация
│   ├── __init__.py
│   └── ui_config.py          # Конфигурация UI (таблицы, цвета, константы)
│
├── services/                 # Бизнес-логика (сервисы)
│   ├── __init__.py
│   ├── instrument_service.py    # Сервис для работы с инструментами
│   ├── employee_service.py      # Сервис для работы с сотрудниками
│   ├── issue_service.py         # Сервис для работы с выдачами
│   ├── address_service.py       # Сервис для работы с адресами
│   ├── history_service.py       # Сервис для работы с историей
│   └── statistics_service.py    # Сервис для работы со статистикой
│
├── ui/                       # Пользовательский интерфейс
│   ├── __init__.py
│   ├── main_window.py        # Главное окно приложения
│   │
│   ├── components/           # Переиспользуемые UI компоненты
│   │   ├── __init__.py
│   │   ├── style_manager.py  # Менеджер стилей
│   │   └── widgets.py        # Переиспользуемые виджеты
│   │
│   └── tabs/                 # Вкладки главного окна
│       ├── __init__.py
│       ├── instruments_tab.py    # Вкладка инструментов
│       ├── employees_tab.py      # Вкладка сотрудников
│       ├── issues_tab.py          # Вкладка выдач
│       ├── returns_tab.py        # Вкладка возвратов
│       ├── history_tab.py        # Вкладка истории
│       ├── addresses_tab.py      # Вкладка адресов
│       └── statistics_tab.py    # Вкладка статистики
│
└── database/                 # SQL скрипты
    ├── 01_create_tables.sql
    └── 02_insert_sample_data.sql
```

## Принципы архитектуры

### 1. Разделение ответственности (Separation of Concerns)

- **UI слой** (`ui/`) - отвечает только за отображение и взаимодействие с пользователем
- **Сервисный слой** (`services/`) - содержит бизнес-логику
- **Слой данных** (`database_manager.py`) - работа с базой данных
- **Конфигурация** (`config/`) - настройки и константы

### 2. Dependency Injection

Сервисы получают зависимости (например, `DatabaseManager`) через конструктор, что упрощает тестирование и замену компонентов.

### 3. Single Responsibility Principle

Каждый сервис отвечает за работу с одной сущностью:
- `InstrumentService` - только инструменты
- `EmployeeService` - только сотрудники
- и т.д.

### 4. Переиспользуемость компонентов

UI компоненты вынесены в отдельные модули и могут использоваться в разных частях приложения.

## Как использовать новую архитектуру

### Пример использования сервиса:

```python
from app_controller import AppController

controller = AppController()
instrument_service = controller.services['instruments']

# Получение списка инструментов
instruments = instrument_service.get_instruments()

# Добавление инструмента
data = (name, description, inventory_number, ...)
instrument_service.add_instrument(data)
```

### Пример создания UI компонента:

```python
from ui.components.widgets import OfficeButton, SearchWidget, TreeViewWidget

# Создание кнопки
button = OfficeButton.create(parent, "Добавить", on_click)

# Создание виджета поиска
search = SearchWidget.create(parent, on_search_change)

# Создание таблицы
tree = TreeViewWidget.create(parent, 'instruments', sort_callback)
```

## Миграция на новую архитектуру

1. **Постепенная миграция**: Основной код в `app.py`, архитектура позволяет легко расширять функциональность
2. **Вынос вкладок**: Каждая вкладка выносится в отдельный модуль в `ui/tabs/`
3. **Использование сервисов**: Вместо прямого обращения к `DatabaseManager` используются сервисы
4. **Тестирование**: Новая архитектура упрощает написание unit-тестов

## Преимущества новой архитектуры

1. **Тестируемость**: Сервисы можно тестировать независимо от UI
2. **Поддерживаемость**: Код разделен по ответственности, легче найти и исправить ошибки
3. **Расширяемость**: Легко добавлять новые функции и сервисы
4. **Переиспользование**: UI компоненты можно использовать в разных местах
5. **Читаемость**: Код более структурирован и понятен

