#!/usr/bin/env python3
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
        print("\n✅ Установка завершена!")
        print("🚀 Запустите ToolManagement.exe")
    else:
        print("\n❌ Установка прервана из-за ошибок")
        sys.exit(1)
