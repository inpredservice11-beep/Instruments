# Инструкция по публикации проекта на GitHub

## Шаг 1: Инициализация Git репозитория

Откройте терминал в папке проекта и выполните:

```bash
git init
```

## Шаг 2: Добавление файлов

```bash
git add .
```

## Шаг 3: Создание первого коммита

```bash
git commit -m "Initial commit: Система учета выдачи и возврата инструмента"
```

## Шаг 4: Создание репозитория на GitHub

1. Перейдите на [GitHub.com](https://github.com)
2. Нажмите кнопку "+" в правом верхнем углу
3. Выберите "New repository"
4. Заполните:
   - **Repository name**: `tool-management-system` (или другое имя)
   - **Description**: "Система учета выдачи и возврата инструмента на Python с GUI"
   - **Visibility**: Public или Private (на ваш выбор)
   - **НЕ** создавайте README, .gitignore или лицензию (они уже есть)
5. Нажмите "Create repository"

## Шаг 5: Подключение локального репозитория к GitHub

GitHub покажет инструкции. Выполните команды (замените `YOUR_USERNAME` на ваш GitHub username):

```bash
git remote add origin https://github.com/YOUR_USERNAME/tool-management-system.git
git branch -M main
git push -u origin main
```

Если используете SSH:

```bash
git remote add origin git@github.com:YOUR_USERNAME/tool-management-system.git
git branch -M main
git push -u origin main
```

## Шаг 6: Проверка

Откройте ваш репозиторий на GitHub - все файлы должны быть загружены.

## Дополнительные настройки (опционально)

### Добавление тегов версии

```bash
git tag -a v1.0.0 -m "Версия 1.0.0: Базовая функциональность"
git push origin v1.0.0
```

### Настройка GitHub Pages (для документации)

1. Перейдите в Settings → Pages
2. Выберите источник: "Deploy from a branch"
3. Выберите ветку: `main` и папку: `/docs` (если создадите)
4. Сохраните

## Структура проекта на GitHub

После публикации структура будет выглядеть так:

```
tool-management-system/
├── README.md              # Основная документация
├── ARCHITECTURE.md        # Документация по архитектуре
├── requirements.txt       # Зависимости Python
├── .gitignore            # Игнорируемые файлы
├── app.py                # Главное приложение
├── app_controller.py     # Контроллер
├── database_manager.py   # Менеджер БД
├── dialogs.py            # Диалоги
├── pdf_export.py         # Экспорт PDF
├── window_config.py      # Конфигурация окон
├── config/               # Конфигурация
├── services/             # Сервисы
├── ui/                   # UI компоненты
└── database/             # SQL скрипты
```

## Полезные команды для дальнейшей работы

### Обновление репозитория после изменений

```bash
git add .
git commit -m "Описание изменений"
git push
```

### Просмотр статуса

```bash
git status
```

### Просмотр истории коммитов

```bash
git log --oneline
```

## Рекомендации

1. **Коммитьте часто** - делайте коммиты после каждого значимого изменения
2. **Пишите понятные сообщения** - опишите, что было изменено
3. **Используйте ветки** - для больших изменений создавайте отдельные ветки
4. **Обновляйте README** - при добавлении новых функций обновляйте документацию

## Лицензия

Проект использует MIT License. Файл LICENSE можно добавить через GitHub интерфейс (Settings → General → License).

