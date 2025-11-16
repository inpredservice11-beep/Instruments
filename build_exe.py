#!/usr/bin/env python3
"""
Скрипт для компиляции приложения в exe файл с помощью PyInstaller
"""

import os
import sys
import subprocess
from pathlib import Path

def create_exe():
    """Создание exe файла"""

    print("🚀 Начинаем компиляцию приложения в exe...")

    # Определяем разделитель для разных ОС
    delim = ";" if os.name == 'nt' else ":"

    # Проверяем наличие PyInstaller
    try:
        # Проверяем, можем ли мы запустить pyinstaller
        result = subprocess.run([sys.executable, "-c", "import PyInstaller"],
                              capture_output=True, check=True)
        print("✅ PyInstaller найден")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PyInstaller не установлен. Устанавливаем...")
        try:
            # Пробуем установить через pip напрямую
            pip_cmd = ["pip", "install", "pyinstaller"]
            print(f"Выполняем: {' '.join(pip_cmd)}")
            subprocess.check_call(pip_cmd)
            print("✅ PyInstaller установлен")

            # Проверяем установку еще раз
            result = subprocess.run([sys.executable, "-c", "import PyInstaller"],
                                  capture_output=True, check=True)
            print("✅ PyInstaller подтвержден")

        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка установки PyInstaller: {e}")
            print("Попробуйте установить вручную: pip install pyinstaller")
            return False

    # Создаем команду PyInstaller (используем python -m для надежности)
    cmd = [
        sys.executable, "-m", "pyinstaller",
        "--onefile",  # Один exe файл
        "--windowed",  # Без консоли (GUI приложение)
        "--name", "ToolManagement",  # Имя exe файла
    ]

    # Добавляем иконку, если она существует
    if os.path.exists("icon.ico"):
        cmd.extend(["--icon", "icon.ico"])

    # Добавляем данные
    cmd.extend([
        "--add-data", f"database{delim}database",  # Добавить папку database
        "--add-data", f"photos{delim}photos",  # Добавить папку photos
    ])

    # Добавляем конфиг, если существует
    if os.path.exists("window_config.json"):
        cmd.extend(["--add-data", f"window_config.json{delim}."])

    # Добавляем скрытые импорты
    cmd.extend([
        "--hidden-import", "tkinter",  # Скрытые импорты
        "--hidden-import", "tkinter.ttk",
        "--hidden-import", "tkinter.messagebox",
        "--hidden-import", "tkinter.filedialog",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL.Image",
        "--hidden-import", "PIL.ImageTk",
        "--hidden-import", "tkcalendar",
        "--hidden-import", "reportlab",
        "--hidden-import", "openpyxl",
        "--hidden-import", "matplotlib",
        "--hidden-import", "barcode",
        "--hidden-import", "uuid",
        "app.py"  # Главный файл
    ])

    # На Windows добавляем дополнительные импорты
    if os.name == 'nt':
        cmd.extend([
            "--hidden-import", "tkinter.dnd",
        ])

    print("📦 Команда компиляции:")
    print(" ".join(cmd))
    print()

    # Запускаем компиляцию
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Компиляция завершена успешно!")
        print(result.stdout)

        # Проверяем созданный файл
        exe_name = "ToolManagement.exe" if os.name == 'nt' else "ToolManagement"
        exe_path = Path("dist") / exe_name

        if exe_path.exists():
            size = exe_path.stat().st_size / (1024 * 1024)  # Размер в МБ
            print(f"✅ Создан файл: {size:.2f} МБ")
            print(f"📁 Расположение: {exe_path.absolute()}")
            print("🎉 Готово! Теперь вы можете распространять этот exe файл")
        else:
            print("❌ exe файл не найден в папке dist")

    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка компиляции: {e}")
        print("Вывод stderr:")
        print(e.stderr)
        return False

    return True

def create_portable_version():
    """Создание портативной версии без одного файла"""

    print("📦 Создаем портативную версию (папка с файлами)...")

    # Проверяем наличие PyInstaller
    try:
        # Проверяем, можем ли мы запустить pyinstaller
        result = subprocess.run([sys.executable, "-c", "import PyInstaller"],
                              capture_output=True, check=True)
        print("✅ PyInstaller найден")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PyInstaller не установлен. Устанавливаем...")
        try:
            # Пробуем установить через pip напрямую
            pip_cmd = ["pip", "install", "pyinstaller"]
            print(f"Выполняем: {' '.join(pip_cmd)}")
            subprocess.check_call(pip_cmd)
            print("✅ PyInstaller установлен")

            # Проверяем установку еще раз
            result = subprocess.run([sys.executable, "-c", "import PyInstaller"],
                                  capture_output=True, check=True)
            print("✅ PyInstaller подтвержден")

        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка установки PyInstaller: {e}")
            print("Попробуйте установить вручную: pip install pyinstaller")
            return

    # Определяем разделитель для разных ОС
    delim = ";" if os.name == 'nt' else ":"

    cmd = [
        sys.executable, "-m", "pyinstaller",
        "--onedir",  # Папка с файлами вместо одного exe
        "--windowed",
        "--name", "ToolManagement_Portable",
        "--add-data", f"database{delim}database",
        "--add-data", f"photos{delim}photos",
        "--add-data", f"window_config.json{delim}.",
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.ttk",
        "--hidden-import", "tkinter.messagebox",
        "--hidden-import", "tkinter.filedialog",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL.Image",
        "--hidden-import", "PIL.ImageTk",
        "--hidden-import", "tkcalendar",
        "--hidden-import", "reportlab",
        "--hidden-import", "openpyxl",
        "--hidden-import", "matplotlib",
        "--hidden-import", "barcode",
        "--hidden-import", "uuid",
        "app.py"
    ]

    try:
        subprocess.run(cmd, check=True)
        print("✅ Портативная версия создана в папке dist/ToolManagement_Portable/")
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка создания портативной версии: {e}")

def create_installer_script():
    """Создание скрипта для автоматической установки"""

    installer_content = '''#!/usr/bin/env python3
"""
Автоматический установщик для ToolManagement
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_dependencies():
    """Установка зависимостей"""
    print("📦 Устанавливаем зависимости...")

    dependencies = [
        "tkcalendar==1.6.1",
        "reportlab==4.0.7",
        "openpyxl==3.1.2",
        "matplotlib==3.10.7",
        "python-barcode==0.15.1",
        "Pillow"
    ]

    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ {dep} установлен")
        except subprocess.CalledProcessError:
            print(f"❌ Ошибка установки {dep}")
            return False

    return True

def create_shortcut():
    """Создание ярлыка на рабочем столе"""
    try:
        import winshell
        from win32com.client import Dispatch

        desktop = winshell.desktop()
        exe_path = Path.cwd() / "ToolManagement.exe"
        shortcut_path = os.path.join(desktop, "ToolManagement.lnk")

        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = str(exe_path)
        shortcut.WorkingDirectory = str(Path.cwd())
        shortcut.IconLocation = str(exe_path)
        shortcut.save()

        print(f"✅ Ярлык создан: {shortcut_path}")
    except ImportError:
        print("ℹ️  Для создания ярлыка установите pywin32 и winshell")
    except Exception as e:
        print(f"❌ Ошибка создания ярлыка: {e}")

if __name__ == "__main__":
    print("🎯 Установка ToolManagement")
    print("=" * 40)

    if install_dependencies():
        create_shortcut()
        print("\\n✅ Установка завершена!")
        print("🚀 Запустите ToolManagement.exe")
    else:
        print("\\n❌ Установка прервана из-за ошибок")
        sys.exit(1)
'''

    with open("installer.py", "w", encoding="utf-8") as f:
        f.write(installer_content)

    print("✅ Создан скрипт installer.py")

if __name__ == "__main__":
    print("🛠️  Сборщик exe для ToolManagement")
    print("=" * 40)

    # Проверяем наличие PyInstaller в начале
    try:
        result = subprocess.run([sys.executable, "-c", "import PyInstaller"],
                              capture_output=True, check=True)
        print("✅ PyInstaller найден")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PyInstaller не установлен. Устанавливаем...")
        try:
            # Пробуем установить через pip напрямую
            pip_cmd = ["pip", "install", "pyinstaller"]
            print(f"Выполняем: {' '.join(pip_cmd)}")
            subprocess.check_call(pip_cmd)
            print("✅ PyInstaller установлен")

            # Проверяем установку еще раз
            result = subprocess.run([sys.executable, "-c", "import PyInstaller"],
                                  capture_output=True, check=True)
            print("✅ PyInstaller подтвержден")

        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка установки PyInstaller: {e}")
            print("Попробуйте установить вручную: pip install pyinstaller")
            sys.exit(1)

    while True:
        print("\\nВыберите вариант сборки:")
        print("1. Одиночный exe файл (рекомендуется)")
        print("2. Портативная версия (папка)")
        print("3. Создать установщик")
        print("4. Выход")

        choice = input("\\nВаш выбор (1-4): ").strip()

        if choice == "1":
            if create_exe():
                print("\\n🎉 Рекомендуем протестировать exe файл перед распространением!")
        elif choice == "2":
            create_portable_version()
        elif choice == "3":
            create_installer_script()
        elif choice == "4":
            break
        else:
            print("❌ Неверный выбор. Попробуйте снова.")

    print("\\n👋 До свидания!")
