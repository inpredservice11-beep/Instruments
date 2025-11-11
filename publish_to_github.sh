#!/bin/bash

echo "========================================"
echo " Публикация проекта на GitHub"
echo "========================================"
echo ""

echo "[1/4] Инициализация Git репозитория..."
git init

echo ""
echo "[2/4] Добавление файлов..."
git add .

echo ""
echo "[3/4] Создание первого коммита..."
git commit -m "Initial commit: Система учета выдачи и возврата инструмента"

echo ""
echo "[4/4] Готово! Теперь выполните следующие шаги:"
echo ""
echo "1. Создайте репозиторий на GitHub.com"
echo "2. Выполните команды (замените YOUR_USERNAME на ваш GitHub username):"
echo ""
echo "   git remote add origin https://github.com/YOUR_USERNAME/tool-management-system.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "Подробная инструкция в файле: GITHUB_SETUP.md"

