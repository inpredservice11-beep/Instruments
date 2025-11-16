#!/usr/bin/env python3
"""Тест сохранения размеров окон"""

import tkinter as tk
from window_config import WindowConfig

def test_window_save():
    """Тестирование сохранения размеров окна"""
    root = tk.Tk()
    root.title("Тест сохранения размеров")
    root.geometry("400x300+100+100")

    config = WindowConfig()

    # Создаем тестовое окно
    test_window = tk.Toplevel(root)
    test_window.title("Тестовое окно")
    test_window.geometry("500x400+200+150")

    # Настраиваем сохранение
    config.restore_window(test_window, "TestDialog", "500x400+200+150")

    def on_save():
        geometry = test_window.geometry()
        print(f"Текущая геометрия: {geometry}")
        config.save_window_geometry("TestDialog", geometry)
        print("Геометрия сохранена!")

    def on_load():
        geometry = config.get_window_geometry("TestDialog")
        print(f"Загруженная геометрия: {geometry}")

    def on_close():
        config.close_window_with_save(test_window, "TestDialog")
        root.quit()

    # Кнопки
    frame = tk.Frame(test_window)
    frame.pack(pady=20)

    tk.Button(frame, text="Сохранить размер", command=on_save).pack(side=tk.LEFT, padx=5)
    tk.Button(frame, text="Показать сохраненный", command=on_load).pack(side=tk.LEFT, padx=5)
    tk.Button(frame, text="Закрыть", command=on_close).pack(side=tk.LEFT, padx=5)

    print("Измените размер окна и нажмите 'Сохранить размер'")
    print("Затем закройте окно и проверьте файл window_config.json")

    root.mainloop()

if __name__ == "__main__":
    test_window_save()
