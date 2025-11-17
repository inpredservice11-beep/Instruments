#!/usr/bin/env python3
"""
Менеджер тем для ToolManagement
Управление светлой и темной темами интерфейса
"""

import tkinter as tk
from tkinter import ttk
import json
import os


class ThemeManager:
    """Класс для управления темами интерфейса"""

    def __init__(self, config_file='theme_config.json'):
        self.config_file = config_file
        self.current_theme = 'light'
        self.themes = {
            'light': {
                'name': 'Светлая',
                'bg': '#f0f0f0',
                'fg': '#000000',
                'button_bg': '#e1e1e1',
                'button_fg': '#000000',
                'button_hover': '#f0f0f0',
                'entry_bg': '#ffffff',
                'entry_fg': '#000000',
                'entry_border': '#c0c0c0',
                'frame_bg': '#f8f8f8',
                'notebook_bg': '#e8e8e8',
                'notebook_active': '#f0f0f0',
                'tree_bg': '#ffffff',
                'tree_fg': '#000000',
                'tree_selected': '#cce4ff',
                'tree_heading_bg': '#e8e8e8',
                'tree_heading_fg': '#000000',
                'text_bg': '#ffffff',
                'text_fg': '#000000',
                'scrollbar_bg': '#d0d0d0',
                'scrollbar_fg': '#a0a0a0',
                'border': '#c0c0c0',
                'accent': '#0078d4',
                'success': '#28a745',
                'warning': '#ffc107',
                'error': '#dc3545'
            },
            'dark': {
                'name': 'Темная',
                'bg': '#1e1e1e',        # Более глубокий черный
                'fg': '#e0e0e0',        # Светло-серый текст для лучшей читаемости
                'button_bg': '#3c3c3c',  # Темно-серый для кнопок
                'button_fg': '#ffffff',  # Белый текст на кнопках
                'button_hover': '#4a4a4a', # Светлее при наведении
                'entry_bg': '#2d2d2d',   # Темный фон для полей ввода
                'entry_fg': '#ffffff',   # Белый текст в полях ввода
                'entry_border': '#555555', # Бордер полей ввода
                'frame_bg': '#252525',   # Средне-серый для фреймов
                'notebook_bg': '#2d2d2d', # Темный фон для вкладок
                'notebook_active': '#3a3a3a', # Активная вкладка
                'tree_bg': '#2d2d2d',    # Темный фон для таблиц
                'tree_fg': '#e0e0e0',    # Светло-серый текст в таблицах
                'tree_selected': '#4a4a4a', # Выделенная строка
                'tree_heading_bg': '#3a3a3a', # Более светлый заголовок таблиц
                'tree_heading_fg': '#ffffff', # Белый текст заголовков
                'text_bg': '#2d2d2d',    # Темный фон для текстовых областей
                'text_fg': '#ffffff',    # Белый текст
                'scrollbar_bg': '#505050', # Серый для полос прокрутки
                'scrollbar_fg': '#707070', # Светлее для бегунка
                'border': '#555555',     # Более светлый бордер
                'accent': '#4a9eff',      # Более яркий синий акцент
                'success': '#28a745',     # Зеленый для успешных операций
                'warning': '#ffc107',     # Желтый для предупреждений
                'error': '#dc3545'        # Красный для ошибок
            }
        }

        self.load_theme()

    def load_theme(self):
        """Загрузка темы из файла конфигурации"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.current_theme = config.get('theme', 'light')
            else:
                self.current_theme = 'light'
        except Exception as e:
            print(f"Ошибка загрузки темы: {e}")
            self.current_theme = 'light'

    def save_theme(self):
        """Сохранение текущей темы"""
        try:
            config = {'theme': self.current_theme}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения темы: {e}")

    def set_theme(self, theme_name):
        """Установка темы"""
        if theme_name in self.themes:
            self.current_theme = theme_name
            self.save_theme()
            return True
        return False

    def get_current_theme(self):
        """Получение текущей темы"""
        return self.themes[self.current_theme]

    def get_theme_names(self):
        """Получение списка доступных тем"""
        return [(key, theme['name']) for key, theme in self.themes.items()]

    def toggle_theme(self):
        """Переключение между темами"""
        if self.current_theme == 'light':
            self.set_theme('dark')
        else:
            self.set_theme('light')
        return self.current_theme

    def apply_theme_to_root(self, root):
        """Применение темы к главному окну"""
        theme = self.get_current_theme()

        try:
            # Настройка главного окна
            root.configure(bg=theme['bg'])
        except:
            pass

        # Применение стилей ttk (более безопасный подход)
        try:
            style = ttk.Style()

            # Настройка стилей для виджетов
            style.configure('TFrame', background=theme['frame_bg'])
            style.configure('TLabel', background=theme['frame_bg'], foreground=theme['fg'])
            style.configure('TButton', background=theme['button_bg'], foreground=theme['button_fg'])
            style.configure('TEntry', fieldbackground=theme['entry_bg'], foreground=theme['entry_fg'],
                           bordercolor=theme.get('entry_border', theme['border']))
            style.configure('TCombobox', fieldbackground=theme['entry_bg'], foreground=theme['entry_fg'])
            style.configure('TNotebook', background=theme['notebook_bg'])
            style.configure('TNotebook.Tab', background=theme['button_bg'], foreground=theme['button_fg'])

            # Настройка Treeview с улучшенными цветами
            style.configure('Treeview',
                           background=theme['tree_bg'],
                           foreground=theme['tree_fg'],
                           fieldbackground=theme['tree_bg'])
            style.configure('Treeview.Heading',
                           background=theme['tree_heading_bg'],
                           foreground=theme['tree_heading_fg'])

            # Настройка выделения в Treeview
            if 'tree_selected' in theme:
                style.map('Treeview',
                         background=[('selected', theme['tree_selected'])],
                         foreground=[('selected', theme['fg'])])

            # Настройка scrollbar с улучшенными цветами
            style.configure('TScrollbar',
                           background=theme['scrollbar_bg'],
                           troughcolor=theme['bg'],
                           bordercolor=theme['border'])

            # Настройка Checkbutton
            style.configure('TCheckbutton', background=theme['frame_bg'], foreground=theme['fg'])

            # Настройка Labelframe
            style.configure('TLabelframe', background=theme['frame_bg'])
            style.configure('TLabelframe.Label', background=theme['frame_bg'], foreground=theme['fg'])

            # Настройка Text
            style.configure('TText', background=theme['text_bg'], foreground=theme['text_fg'])

            # Настройка Progressbar
            style.configure('TProgressbar',
                           background=theme['accent'],
                           troughcolor=theme['bg'],
                           bordercolor=theme['border'])

        except Exception as e:
            print(f"Ошибка при настройке стилей ttk: {e}")

        # Применение цветов ко всем дочерним виджетам (только базовые виджеты)
        try:
            self._apply_theme_to_widget_safe(root, theme)
        except Exception as e:
            print(f"Ошибка при применении темы к виджетам: {e}")

    def _apply_theme_to_widget_safe(self, widget, theme):
        """Безопасное применение темы только к основным виджетам tkinter"""
        try:
            # Получаем имя класса виджета
            widget_class = widget.winfo_class()

            # Пропускаем проблемные виджеты
            skip_classes = ['Calendar', 'DateEntry', 'TCalendar', 'TCombobox']
            if any(skip_class in widget_class for skip_class in skip_classes):
                return

            # Применяем тему только к безопасным виджетам tkinter
            if isinstance(widget, tk.Frame):
                try:
                    widget.configure(bg=theme['frame_bg'])
                except:
                    pass
            elif isinstance(widget, tk.Label):
                try:
                    widget.configure(bg=theme['frame_bg'], fg=theme['fg'])
                except:
                    pass
            elif isinstance(widget, tk.Button):
                try:
                    widget.configure(bg=theme['button_bg'], fg=theme['button_fg'],
                                   activebackground=theme.get('button_hover', theme['button_bg']),
                                   activeforeground=theme['button_fg'])
                except:
                    pass
            elif isinstance(widget, tk.Entry):
                try:
                    widget.configure(bg=theme['entry_bg'], fg=theme['entry_fg'],
                                   insertbackground=theme['fg'],  # Цвет курсора
                                   selectbackground=theme.get('accent', '#0078d4'),  # Цвет выделения
                                   selectforeground=theme['entry_bg'])  # Цвет текста при выделении
                except:
                    pass
            elif isinstance(widget, tk.Text):
                try:
                    widget.configure(bg=theme['text_bg'], fg=theme['text_fg'],
                                   insertbackground=theme['fg'],  # Цвет курсора
                                   selectbackground=theme.get('accent', '#0078d4'),  # Цвет выделения
                                   selectforeground=theme['text_bg'])  # Цвет текста при выделении
                except:
                    pass
            elif isinstance(widget, tk.Listbox):
                try:
                    widget.configure(bg=theme['tree_bg'], fg=theme['tree_fg'],
                                   selectbackground=theme.get('tree_selected', theme['accent']),
                                   selectforeground=theme['tree_fg'])
                except:
                    pass

            # Рекурсивный обход дочерних виджетов (с ограничением глубины)
            try:
                children = widget.winfo_children()
                for child in children[:20]:  # Ограничиваем количество дочерних виджетов
                    self._apply_theme_to_widget_safe(child, theme)
            except:
                pass

        except Exception:
            # Тихо пропускаем все ошибки в безопасном режиме
            pass

    def _apply_theme_to_widget(self, widget, theme):
        """Рекурсивное применение темы ко всем виджетам"""
        try:
            # Получаем имя класса виджета для диагностики
            widget_class = widget.winfo_class()

            # Пропускаем специальные виджеты, которые могут конфликтовать с темами
            if widget_class in ['Calendar', 'DateEntry', 'TCalendar']:
                # Эти виджеты имеют собственную логику стилизации, пропускаем
                return

            # Настройка обычных виджетов tkinter
            if isinstance(widget, tk.Frame):
                widget.configure(bg=theme['frame_bg'])
            elif isinstance(widget, tk.Label):
                widget.configure(bg=theme['frame_bg'], fg=theme['fg'])
            elif isinstance(widget, tk.Button):
                widget.configure(bg=theme['button_bg'], fg=theme['button_fg'],
                               activebackground=theme.get('button_hover', theme['button_bg']),
                               activeforeground=theme['button_fg'])
            elif isinstance(widget, tk.Entry):
                widget.configure(bg=theme['entry_bg'], fg=theme['entry_fg'],
                               insertbackground=theme['fg'],
                               selectbackground=theme.get('accent', '#0078d4'),
                               selectforeground=theme['entry_bg'])
            elif isinstance(widget, tk.Text):
                widget.configure(bg=theme['text_bg'], fg=theme['text_fg'],
                               insertbackground=theme['fg'],
                               selectbackground=theme.get('accent', '#0078d4'),
                               selectforeground=theme['text_bg'])
            elif isinstance(widget, tk.Canvas):
                widget.configure(bg=theme['bg'])
            elif isinstance(widget, tk.Listbox):
                widget.configure(bg=theme['tree_bg'], fg=theme['tree_fg'],
                               selectbackground=theme.get('tree_selected', theme['accent']),
                               selectforeground=theme['tree_fg'])

            # Рекурсивный обход дочерних виджетов
            for child in widget.winfo_children():
                self._apply_theme_to_widget(child, theme)

        except tk.TclError:
            # Виджет уже уничтожен, пропускаем
            pass
        except AttributeError as e:
            # Некоторые виджеты не имеют определенных атрибутов
            # Логируем для отладки, но продолжаем
            print(f"Предупреждение: виджет {widget} не поддерживает настройку темы: {e}")
            pass
        except Exception as e:
            # Общая обработка других ошибок
            print(f"Ошибка при применении темы к виджету {widget}: {e}")
            pass

    def create_theme_switcher(self, parent, callback=None):
        """Создание переключателя тем"""
        frame = ttk.Frame(parent)

        ttk.Label(frame, text="Тема:").pack(side=tk.LEFT, padx=(0, 5))

        # Создание выпадающего списка тем
        themes = self.get_theme_names()
        theme_names = [name for _, name in themes]

        current_theme_name = dict(themes)[self.current_theme]

        var = tk.StringVar(value=current_theme_name)
        combo = ttk.Combobox(frame, textvariable=var, values=theme_names, state='readonly', width=10)
        combo.pack(side=tk.LEFT)

        def on_theme_change(event=None):
            selected_name = var.get()
            for theme_key, theme_name in themes:
                if theme_name == selected_name:
                    self.set_theme(theme_key)
                    if callback:
                        callback()
                    break

        combo.bind('<<ComboboxSelected>>', on_theme_change)

        return frame


# Глобальный экземпляр менеджера тем
theme_manager = ThemeManager()


def init_theme_manager():
    """Инициализация глобального менеджера тем"""
    global theme_manager
    return theme_manager


def apply_theme_to_app(root):
    """Применение темы ко всему приложению"""
    global theme_manager
    theme_manager.apply_theme_to_root(root)


def toggle_theme():
    """Переключение темы"""
    global theme_manager
    new_theme = theme_manager.toggle_theme()
    return new_theme
