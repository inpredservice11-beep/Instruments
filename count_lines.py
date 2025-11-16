#!/usr/bin/env python3
"""
Подсчет строк кода в проекте
"""

import os
import glob

def count_lines(filename):
    """Подсчитывает непустые строки в файле"""
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for line in f if line.strip())
    except:
        return 0

def main():
    """Основная функция"""
    total_lines = 0
    total_files = 0
    py_files = []

    # Ищем все Python файлы
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                lines = count_lines(filepath)
                total_lines += lines
                total_files += 1
                py_files.append((filepath, lines))

    print("📊 Статистика кода проекта ToolManagement"    print("=" * 50)
    print(f"📁 Всего Python файлов: {total_files}")
    print(",")
    print()

    print("🏆 Топ-10 файлов по количеству строк:"    print("-" * 40)
    for i, (filepath, lines) in enumerate(sorted(py_files, key=lambda x: x[1], reverse=True)[:10], 1):
        print("2d")

    print()
    print("📂 Структура проекта:"    print("-" * 40)
    dirs_summary = {}
    for filepath, lines in py_files:
        dir_name = os.path.dirname(filepath).lstrip('./') or 'root'
        dirs_summary[dir_name] = dirs_summary.get(dir_name, 0) + lines

    for dir_name, lines in sorted(dirs_summary.items(), key=lambda x: x[1], reverse=True):
        print("6s")

if __name__ == "__main__":
    main()
