# Тесты системы учета инструмента

Этот каталог содержит автоматизированные тесты для системы учета выдачи и возврата инструмента.

## Структура тестов

```
tests/
├── __init__.py              # Инициализация пакета тестов
├── conftest.py              # Конфигурация pytest и фикстуры
├── test_barcode_utils.py    # Тесты модуля штрих-кодов
├── test_database_manager.py # Тесты работы с базой данных
├── test_integration.py      # Интеграционные тесты
└── README.md               # Эта документация
```

## Запуск тестов

### Все тесты
```bash
pytest
```

### С покрытием кода
```bash
pytest --cov=. --cov-report=html
```

### Только unit-тесты
```bash
pytest -m "unit"
```

### Только интеграционные тесты
```bash
pytest -m "integration"
```

### Конкретный тест
```bash
pytest tests/test_barcode_utils.py::TestBarcodeManager::test_generate_unique_barcode
```

## Типы тестов

### Unit-тесты (`test_*.py`)
- **test_barcode_utils.py**: Тестирование генерации, валидации и отображения штрих-кодов
- **test_database_manager.py**: Тестирование CRUD операций с базой данных

### Интеграционные тесты (`test_integration.py`)
- **test_full_workflow**: Полный цикл работы (добавление → выдача → возврат)
- **test_barcode_workflow**: Работа со штрих-кодами
- **test_bulk_operations**: Массовые операции
- **test_data_integrity**: Целостность данных и обработка ошибок

## Фикстуры

### Основные фикстуры
- `temp_db_path`: Временный файл базы данных для тестов
- `db_manager`: Экземпляр DatabaseManager с тестовой БД
- `barcode_manager`: Экземпляр BarcodeManager
- `sample_instrument_data`: Тестовые данные инструмента
- `sample_employee_data`: Тестовые данные сотрудника

## Покрытие кода

Тесты обеспечивают покрытие следующих компонентов:

- ✅ Генерация и валидация штрих-кодов
- ✅ CRUD операции с инструментами и сотрудниками
- ✅ Выдача и возврат инструментов
- ✅ Поиск и фильтрация данных
- ✅ Обработка ошибок и исключений
- ✅ Целостность данных

## Добавление новых тестов

### Unit-тест
```python
def test_new_feature(self, fixture):
    """Тест новой функциональности"""
    # Arrange
    expected = "ожидаемый результат"

    # Act
    result = some_function()

    # Assert
    assert result == expected
```

### Интеграционный тест
```python
def test_feature_integration(self, db_manager, barcode_manager):
    """Интеграционный тест функциональности"""
    # Подготовка данных
    # Выполнение операций
    # Проверка результатов
```

## CI/CD

Для автоматического запуска тестов в CI/CD:

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=. --cov-report=xml
```

## Метрики качества

- **Покрытие кода**: > 80%
- **Количество тестов**: > 20
- **Время выполнения**: < 30 секунд
- **Процент успешных тестов**: 100%



