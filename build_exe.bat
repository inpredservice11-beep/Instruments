@echo off
REM Пакетный файл для компиляции ToolManagement в exe

echo ========================================
echo 🛠️  Сборщик ToolManagement exe
echo ========================================
echo.

cd /d "%~dp0"

REM Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден. Установите Python 3.7+
    pause
    exit /b 1
)

echo ✅ Python найден
echo.

REM Запускаем скрипт сборки
python build_exe.py

echo.
echo ========================================
echo 🎉 Сборка завершена!
echo ========================================
echo.

pause
