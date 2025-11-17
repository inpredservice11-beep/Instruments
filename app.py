"""
Система учета выдачи и возврата инструмента
Графический интерфейс на tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime, timedelta
import sys
import platform
import os
import shutil

from database_manager import DatabaseManager
from window_config import WindowConfig
from pdf_export import PDFExporter
from excel_export import ExcelExporter
from xml_json_export import XMLJSONExporter
from config.constants import (
    TABLES_CONFIG, OFFICE_COLORS, TREEVIEW_HEIGHT,
    INSTRUMENT_STATUSES, EMPLOYEE_STATUSES, INSTRUMENT_CATEGORIES,
    MESSAGES
)
from dialogs import (
    AddInstrumentDialog, EditInstrumentDialog,
    AddEmployeeDialog, EditEmployeeDialog,
    IssueInstrumentDialog, ReturnInstrumentDialog,
    BatchReturnDialog,
    AddAddressDialog, EditAddressDialog,
    save_all_dialogs_geometry,
    create_russian_date_entry
)

# Исправление размытости шрифтов на Windows (high DPI)
if platform.system() == 'Windows':
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass


# Константы для конфигурации таблиц
TABLES_CONFIG = {
    'instruments': {
        'columns': ('ID', 'Название', 'Инв. номер', 'Серийный номер', 'Штрих-код', 'Категория', 'Статус'),
        'column_widths': {
            'ID': 50, 'Название': 200, 'Инв. номер': 100, 'Серийный номер': 110,
            'Штрих-код': 140, 'Категория': 140, 'Статус': 100
        }
    },
    'employees': {
        'columns': ('ID', 'ФИО', 'Должность', 'Отдел', 'Телефон', 'Email', 'Статус'),
        'column_widths': {
            'ID': 50, 'ФИО': 200, 'Должность': 150, 'Отдел': 200,
            'Телефон': 120, 'Email': 180, 'Статус': 100
        }
    },
    'issues': {
        'columns': ('ID', 'Инв. номер', 'Инструмент', 'Сотрудник', 
                   'Адрес', 'Дата выдачи', 'Ожид. возврат', 'Выдал', 'Примечание'),
        'column_widths': {
            'ID': 50, 'Инв. номер': 110, 'Инструмент': 200, 'Сотрудник': 180,
            'Адрес': 220, 'Дата выдачи': 130, 'Ожид. возврат': 110,
            'Выдал': 140, 'Примечание': 200
        }
    },
    'returns': {
        'columns': ('ID', 'Инв. номер', 'Инструмент', 'Сотрудник', 
                   'Адрес', 'Дата выдачи', 'Ожид. возврат', 'Дней в использовании'),
        'column_widths': {
            'ID': 50, 'Инв. номер': 110, 'Инструмент': 230, 'Сотрудник': 200,
            'Адрес': 220, 'Дата выдачи': 130, 'Ожид. возврат': 120, 'Дней в использовании': 160
        },
        'tags': {'overdue': {'background': '#ffcccc'}}
    },
    'history': {
        'columns': ('ID', 'Тип', 'Инв. номер', 'Инструмент', 'Сотрудник', 
                   'Адрес', 'Дата операции', 'Выполнил', 'Примечание'),
        'column_widths': {
            'ID': 50, 'Тип': 80, 'Инв. номер': 110, 'Инструмент': 200,
            'Сотрудник': 180, 'Адрес': 220, 'Дата операции': 140,
            'Выполнил': 140, 'Примечание': 200
        },
        'tags': {
            'issue': {'background': '#ffffcc'},
            'return': {'background': '#ccffcc'}
        }
    },
    'addresses': {
        'columns': ('ID', 'Название', 'Полный адрес'),
        'column_widths': {
            'ID': 50, 'Название': 250, 'Полный адрес': 500
        }
    }
}

BUTTON_PADDING = 10
# TREEVIEW_HEIGHT импортируется из constants


class ToolManagementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Система учета инструмента")

        # Ранняя инициализация основных атрибутов
        self.office_colors = OFFICE_COLORS.copy()  # Создаем копию для модификации

        # Инициализация конфигурации окон
        self.window_config = WindowConfig()

        # Инициализация менеджера тем
        try:
            print("🔄 Инициализация менеджера тем...")
            from theme_manager import init_theme_manager, ThemeManager
            print("📦 Импорт theme_manager успешен")

            # Проверяем, можем ли мы создать экземпляр ThemeManager
            temp_manager = ThemeManager()
            print("🎨 ThemeManager создан успешно")

            self.theme_manager = init_theme_manager()
            print("✅ Менеджер тем инициализирован")

            # Синхронизируем office_colors с текущей темой
            if self.theme_manager:
                try:
                    theme_colors = self.theme_manager.get_current_theme()
                    print(f"🎨 Текущая тема: {theme_colors.get('name', 'неизвестна')}")
                    self.office_colors.update({
                        'bg_white': theme_colors.get('tree_bg', '#ffffff'),
                        'bg_main': theme_colors.get('bg', '#f0f0f0'),
                        'bg_header': theme_colors.get('tree_heading_bg', '#e8e8e8'),
                        'bg_header_light': theme_colors.get('notebook_active', '#f0f0f0'),
                        'bg_selected': theme_colors.get('tree_selected', '#cce4ff'),
                        'bg_hover': theme_colors.get('button_hover', '#f0f0f0'),
                        'hover': theme_colors.get('button_hover', '#f0f0f0'),
                        'fg_main': theme_colors.get('tree_fg', '#000000'),
                        'fg_secondary': theme_colors.get('fg', '#666666'),
                        'fg_header': theme_colors.get('tree_heading_fg', '#000000'),
                        'selected': theme_colors.get('accent', '#0078d4'),
                        'border': theme_colors.get('border', '#c0c0c0'),
                        'overdue': theme_colors.get('error', '#ffcccc'),
                        'warning': theme_colors.get('warning', '#ffffcc'),
                        'success': theme_colors.get('success', '#ccffcc')
                    })
                    print("🎨 Цвета office_colors обновлены")
                except Exception as color_e:
                    print(f"⚠️ Ошибка обновления цветов: {color_e}")
                    # Используем цвета по умолчанию
        except ImportError as ie:
            print(f"❌ Ошибка импорта theme_manager: {ie}")
            print("💡 Проверьте наличие файла theme_manager.py")
            print("⚠️ Приложение продолжит работу без поддержки тем")
            self.theme_manager = None
        except Exception as e:
            print(f"❌ Ошибка инициализации менеджера тем: {e}")
            import traceback
            print(f"📋 Подробности ошибки:\n{traceback.format_exc()}")
            print("⚠️ Приложение продолжит работу с базовой темой")
            self.theme_manager = None

        # Если theme_manager не инициализирован, используем базовые цвета
        if not self.theme_manager:
            print("ℹ️ Используются базовые цвета интерфейса")
            # office_colors уже инициализирован базовыми значениями из OFFICE_COLORS

        # Загружаем сохраненный токен Telegram бота
        self._load_telegram_token()

        # Инициализация Telegram бота
        try:
            from telegram_bot import init_telegram_bot, start_telegram_bot
            self.telegram_bot = init_telegram_bot()
            if self.telegram_bot:
                print("✅ Telegram бот инициализирован")
                # Запуск бота в отдельном потоке
                try:
                    bot_thread = start_telegram_bot()
                    if bot_thread:
                        print("✅ Telegram бот запущен в фоне")
                except RuntimeError as re:
                    if "Несовместимость python-telegram-bot с Python 3.13" in str(re):
                        print("❌ Telegram бот не запущен из-за несовместимости с Python 3.13")
                        print("💡 Рекомендации:")
                        print("   1. Обновите python-telegram-bot: pip install --upgrade python-telegram-bot")
                        print("   2. Или используйте Python 3.12 или ниже")
                        print("   3. Проверьте версию: pip show python-telegram-bot")
                        self.telegram_bot = None
                    else:
                        raise
            else:
                print("⚠️ Telegram бот не настроен (отсутствует токен)")
        except ImportError:
            print("⚠️ Telegram бот недоступен (не установлена библиотека python-telegram-bot)")
            self.telegram_bot = None
        except Exception as e:
            print(f"❌ Ошибка инициализации Telegram бота: {e}")
            self.telegram_bot = None


        # Восстановление размера и позиции основного окна
        # auto_save=False, так как мы используем оптимизированный обработчик с debouncing
        default_geometry = "1200x700"
        self.window_config.restore_window(self.root, "main_window", default_geometry, auto_save=False)
        
        # Переменная для debouncing сохранения размера окна
        self._save_geometry_job = None
        
        # Сохранение размера окна при изменении (с debouncing)
        def on_configure(event):
            if self.root.winfo_viewable() and event.widget == self.root:
                # Отменяем предыдущую отложенную задачу
                if self._save_geometry_job:
                    self.root.after_cancel(self._save_geometry_job)
                
                # Откладываем сохранение на 500мс после последнего изменения
                self._save_geometry_job = self.root.after(500, self._save_window_geometry)
        
        self.root.bind('<Configure>', on_configure)
        
        # Сохранение при закрытии окна
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Инициализация базы данных
        self.db = DatabaseManager()

        # Инициализация системы уведомлений
        try:
            from notification_manager import init_notification_manager, start_notifications
            self.notification_manager = init_notification_manager(self.db, self.telegram_bot)
            print("✅ Система уведомлений инициализирована")

            # Запуск мониторинга уведомлений
            start_notifications()
            print("✅ Мониторинг уведомлений запущен")

        except Exception as e:
            print(f"❌ Ошибка инициализации уведомлений: {e}")
            self.notification_manager = None

        # Инициализация экспортеров
        self.xml_json_exporter = XMLJSONExporter()
        
        # Настройка стиля в стиле MS Office
        self.setup_office_style()
        
        # Состояние сортировки для каждой таблицы: {column: 'asc'/'desc'}
        self.sort_states = {
            'instruments': {'column': None, 'direction': 'asc'},
            'employees': {'column': None, 'direction': 'asc'},
            'issues': {'column': None, 'direction': 'asc'},
            'returns': {'column': None, 'direction': 'asc'},
            'history': {'column': None, 'direction': 'asc'},
            'statistics': {'column': None, 'direction': 'asc'},
            'addresses': {'column': None, 'direction': 'asc'}
        }
        
        # Маппинг имен таблиц на виджеты Treeview (инициализируется после создания вкладок)
        self.tree_mapping = {}
        
        # Создание интерфейса
        self.create_widgets()
        self.load_data()

        # Запуск обработки уведомлений в главном потоке
        self._schedule_notification_check()

    def _schedule_notification_check(self):
        """Планирование периодической проверки уведомлений"""
        # Проверяем уведомления каждые 2 секунды
        self.root.after(2000, self._process_pending_notifications)

    def _process_pending_notifications(self):
        """Обработка ожидающих уведомлений в главном потоке"""
        try:
            if self.notification_manager:
                notifications = self.notification_manager.get_pending_notifications()
                for title, message in notifications:
                    self._show_desktop_notification_main_thread(title, message)

            # Планируем следующую проверку
            self.root.after(2000, self._process_pending_notifications)

        except Exception as e:
            print(f"Ошибка обработки уведомлений: {e}")
            # Продолжаем планировать проверки даже при ошибке
            self.root.after(2000, self._process_pending_notifications)

    def _show_desktop_notification_main_thread(self, title, message):
        """Показать desktop уведомление в главном потоке"""
        try:
            from tkinter import messagebox

            # Показываем диалог с сообщением
            if len(message) > 500:
                # Для длинных сообщений показываем только начало
                short_message = message[:500] + "..."
                messagebox.showwarning(title, short_message)
            else:
                messagebox.showwarning(title, message)

        except Exception as e:
            print(f"Ошибка показа desktop уведомления: {e}")

    def setup_office_style(self):
        """Настройка стиля в стиле MS Office"""
        style = ttk.Style()
        
        # Единый шрифт для всех платформ - Arial
        default_font = ("Arial", 9)
        title_font = ("Arial", 16, "bold")
        tab_font = ("Arial", 11, "bold")
        
        self.default_font = default_font
        self.title_font = title_font
        self.tab_font = tab_font
        
        # Настройка фона главного окна
        self.root.configure(bg=self.office_colors['bg_main'])
        
        # Настройка Treeview
        style.configure("Treeview", 
                       rowheight=32,
                       background=self.office_colors['bg_white'],
                       foreground=self.office_colors['fg_main'],
                       fieldbackground=self.office_colors['bg_white'],
                       font=default_font,
                       borderwidth=1,
                       relief='flat')
        
        style.map("Treeview",
                 background=[('selected', self.office_colors['selected'])],
                 foreground=[('selected', '#ffffff')])
        
        # Настройка заголовков Treeview
        style.configure("Treeview.Heading",
                      background=self.office_colors['bg_header'],
                      foreground=self.office_colors['fg_header'],
                      font=(default_font[0], default_font[1], "bold"),
                      relief='flat',
                      borderwidth=0,
                      padding=8)
        
        style.map("Treeview.Heading",
                 background=[('active', self.office_colors['bg_header_light'])])
        
        # Настройка вкладок (Notebook)
        style.configure("TNotebook",
                       background=self.office_colors['bg_main'],
                       borderwidth=0)
        
        style.configure("TNotebook.Tab",
                       font=tab_font,
                       padding=[20, 10],
                       background=self.office_colors['bg_white'],
                       foreground=self.office_colors['fg_main'],
                       borderwidth=1,
                       relief='flat')
        
        style.map("TNotebook.Tab",
                 background=[('selected', self.office_colors['bg_white']),
                            ('!selected', self.office_colors['bg_main'])],
                 expand=[('selected', [1, 1, 1, 0])])
        
        # Настройка кнопок
        style.configure("TButton",
                       font=default_font,
                       padding=[12, 6],
                       relief='flat',
                       borderwidth=1)
        
        style.map("TButton",
                 background=[('active', self.office_colors['hover']),
                            ('!active', self.office_colors['bg_white'])],
                 foreground=[('active', self.office_colors['fg_main']),
                            ('!active', self.office_colors['fg_main'])],
                 bordercolor=[('active', self.office_colors['border']),
                             ('!active', self.office_colors['border'])],
                 focuscolor=[('', 'none')])
        
        # Настройка Frame
        style.configure("TFrame",
                      background=self.office_colors['bg_white'])
        
        # Настройка Label
        style.configure("TLabel",
                       background=self.office_colors['bg_white'],
                       foreground=self.office_colors['fg_main'],
                       font=default_font)
        
        # Настройка Entry
        style.configure("TEntry",
                      fieldbackground=self.office_colors['bg_white'],
                      foreground=self.office_colors['fg_main'],
                      borderwidth=1,
                      relief='flat',
                      font=default_font,
                      padding=6)
        
        style.map("TEntry",
                 bordercolor=[('focus', self.office_colors['selected']),
                             ('!focus', self.office_colors['border'])],
                 lightcolor=[('focus', self.office_colors['selected']),
                           ('!focus', self.office_colors['border'])],
                 darkcolor=[('focus', self.office_colors['selected']),
                           ('!focus', self.office_colors['border'])])
        
        # Настройка Combobox
        style.configure("TCombobox",
                      fieldbackground=self.office_colors['bg_white'],
                      foreground=self.office_colors['fg_main'],
                      borderwidth=1,
                      relief='flat',
                      font=default_font,
                      padding=6)
        
        style.map("TCombobox",
                 fieldbackground=[('readonly', self.office_colors['bg_white'])],
                 bordercolor=[('focus', self.office_colors['selected']),
                             ('!focus', self.office_colors['border'])])
        
        # Настройка LabelFrame
        style.configure("TLabelframe",
                       background=self.office_colors['bg_white'],
                       borderwidth=1,
                       relief='flat')
        
        style.configure("TLabelframe.Label",
                       background=self.office_colors['bg_white'],
                       foreground=self.office_colors['fg_main'],
                       font=(default_font[0], default_font[1], "bold"))
        
    def create_widgets(self):
        """Создание элементов интерфейса в стиле MS Office"""
        # Создание меню
        self.create_menu()
        
        # Верхняя панель (Header) в стиле MS Office
        header_frame = tk.Frame(self.root, bg=self.office_colors['bg_header'], height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Заголовок приложения
        title_label = tk.Label(
            header_frame,
            text="Журнал учета выдачи и возврата инструмента",
            font=self.title_font,
            bg=self.office_colors['bg_header'],
            fg=self.office_colors['fg_header'],
            pady=15
        )
        title_label.pack()
        
        # Панель инструментов (Toolbar) в стиле MS Office
        toolbar_frame = tk.Frame(self.root, bg=self.office_colors['bg_white'], height=50)
        toolbar_frame.pack(fill=tk.X, padx=0, pady=0)
        toolbar_frame.pack_propagate(False)
        
        # Внутренний фрейм для кнопок панели инструментов
        toolbar_inner = tk.Frame(toolbar_frame, bg=self.office_colors['bg_white'])
        toolbar_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        
        # Разделитель
        separator = tk.Frame(self.root, bg=self.office_colors['border'], height=1)
        separator.pack(fill=tk.X)
        
        # Notebook для вкладок
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Вкладки

        self.create_issues_tab()
        self.create_returns_tab()
        self.create_history_tab()
        self.create_instruments_tab()
        self.create_employees_tab()
        self.create_addresses_tab()
        self.create_statistics_tab()
        self.create_analytics_tab()

        # Применение темы к интерфейсу
        if self.theme_manager:
            try:
                from theme_manager import apply_theme_to_app
                apply_theme_to_app(self.root)
                print("✅ Тема применена к интерфейсу")
            except Exception as e:
                print(f"❌ Ошибка применения темы: {e}")

    def create_menu(self):
        """Создание меню приложения"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Меню "Файл"
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Создать резервную копию", command=self.backup_database, accelerator="Ctrl+B")
        file_menu.add_command(label="Восстановить из резервной копии", command=self.restore_database, accelerator="Ctrl+R")
        file_menu.add_separator()
        file_menu.add_command(label="Экспорт данных в CSV", command=self.export_to_csv)
        file_menu.add_command(label="Экспорт в XML", command=self.export_to_xml)
        file_menu.add_command(label="Экспорт в JSON", command=self.export_to_json)
        file_menu.add_command(label="Импорт данных из CSV", command=self.import_from_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self._on_closing, accelerator="Alt+F4")
        
        # Меню "Инструменты"
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Инструменты", menu=tools_menu)
        tools_menu.add_command(label="Настройки Telegram бота", command=self.configure_telegram_bot)

        # Подменю тем
        theme_menu = tk.Menu(tools_menu, tearoff=0)
        tools_menu.add_cascade(label="Тема интерфейса", menu=theme_menu)
        theme_menu.add_command(label="Светлая тема", command=lambda: self.change_theme('light'))
        theme_menu.add_command(label="Темная тема", command=lambda: self.change_theme('dark'))

        tools_menu.add_separator()
        tools_menu.add_command(label="Настройки уведомлений", command=self.configure_notifications)

        # Меню "Справка"
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)
        
        # Привязка горячих клавиш
        self.root.bind('<Control-b>', lambda e: self.backup_database())
        self.root.bind('<Control-r>', lambda e: self.restore_database())
        self.root.bind('<F11>', lambda e: self.toggle_theme())  # Переключение темы
    
    def _create_button(self, parent, text, command, side=tk.LEFT, style='default'):
        """Создание кнопки в стиле MS Office"""
        if style == 'primary':
            # Основная кнопка (синяя)
            btn_frame = tk.Frame(parent, bg=self.office_colors['bg_white'])
            btn_frame.pack(side=side, padx=2)
            
            button = tk.Button(
                btn_frame,
                text=text,
                command=command,
                bg=self.office_colors['selected'],
                fg='#ffffff',
                font=self.default_font,
                relief='flat',
                padx=16,
                pady=8,
                cursor='hand2',
                activebackground=self.office_colors['bg_header_light'],
                activeforeground='#ffffff',
                borderwidth=0
            )
            button.pack()
        else:
            # Обычная кнопка
            button = ttk.Button(parent, text=text, command=command)
            button.pack(side=side, padx=2)
        
        return button
    
    def _create_search_widget(self, parent, on_change_callback):
        """Создание виджета поиска в стиле MS Office"""
        search_frame = tk.Frame(parent, bg=self.office_colors['bg_white'])
        search_frame.pack(side=tk.RIGHT, padx=5)
        
        tk.Label(
            search_frame,
            text="Поиск:",
            bg=self.office_colors['bg_white'],
            fg=self.office_colors['fg_main'],
            font=self.default_font
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        search_entry = ttk.Entry(search_frame, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind('<KeyRelease>', lambda e: on_change_callback())
        return search_entry
    
    def _create_treeview(self, parent, table_name):
        """Создание таблицы Treeview с настройками в стиле MS Office"""
        config = TABLES_CONFIG[table_name]
        columns = config['columns']
        column_widths = config['column_widths']
        tags = config.get('tags', {})
        
        # Контейнер для таблицы
        tree_container = tk.Frame(parent, bg=self.office_colors['bg_white'])
        tree_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Применяем текущую тему к контейнеру
        if self.theme_manager:
            theme_colors = self.theme_manager.get_current_theme()
            tree_container.configure(bg=theme_colors.get('frame_bg', self.office_colors['bg_white']))
        
        tree = ttk.Treeview(tree_container, columns=columns, show='headings', height=TREEVIEW_HEIGHT)
        
        # Настройка столбцов
        for col in columns:
            tree.column(col, width=column_widths.get(col, 100))
            tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(table_name, c))
        
        # Настройка тегов с обновленными цветами
        for tag_name, tag_config in tags.items():
            # Обновляем цвета тегов в стиле Office
            updated_config = tag_config.copy()
            if 'background' in updated_config:
                # Сохраняем оригинальные цвета, но делаем их более мягкими
                if updated_config['background'] == '#ffcccc':  # overdue
                    updated_config['background'] = '#fff4f4'
                elif updated_config['background'] == '#ffffcc':  # issue
                    updated_config['background'] = '#fffef0'
                elif updated_config['background'] == '#ccffcc':  # return
                    updated_config['background'] = '#f0f9f0'
            tree.tag_configure(tag_name, **updated_config)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        return tree
    
    def _create_control_frame(self, tab):
        """Создание панели управления для вкладки в стиле MS Office"""
        control_frame = tk.Frame(tab, bg=self.office_colors['bg_white'], padx=10, pady=8)
        control_frame.pack(fill=tk.X)
        return control_frame
        
    def create_instruments_tab(self):
        """Вкладка управления инструментами"""
        tab = tk.Frame(self.notebook, bg=self.office_colors['bg_white'])
        self.notebook.add(tab, text="🔧 Инструменты")
        
        control_frame = self._create_control_frame(tab)
        
        self._create_button(control_frame, "Добавить инструмент", self.add_instrument)
        self._create_button(control_frame, "Редактировать", self.edit_instrument)
        self._create_button(control_frame, "Удалить", self.delete_instrument)
        self._create_button(control_frame, "Обновить", self.load_instruments)

        # Виджет поиска по штрих-коду
        barcode_search_frame = tk.Frame(control_frame, bg=self.office_colors['bg_white'])
        barcode_search_frame.pack(side=tk.RIGHT, padx=5)

        tk.Label(
            barcode_search_frame,
            text="Штрих-код:",
            bg=self.office_colors['bg_white'],
            fg=self.office_colors['fg_main'],
            font=self.default_font
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.barcode_search = ttk.Entry(barcode_search_frame, width=20)
        self.barcode_search.pack(side=tk.LEFT, padx=5)
        self.barcode_search.bind('<Return>', lambda e: self.search_by_barcode())

        ttk.Button(
            barcode_search_frame,
            text="🔍 Найти",
            command=self.search_by_barcode
        ).pack(side=tk.LEFT, padx=5)
        
        self.instrument_search = self._create_search_widget(control_frame, self.load_instruments)
        self.instruments_tree = self._create_treeview(tab, 'instruments')
        self.tree_mapping['instruments'] = self.instruments_tree
        
        # Словарь для хранения photo_path по ID инструмента
        self.instrument_photos = {}
        
        # Всплывающее окно для фотографии
        self.photo_tooltip = None
        self.photo_tooltip_job = None  # Для задержки показа tooltip
        
        # Обработчик наведения мыши для показа фотографии
        self.instruments_tree.bind('<Motion>', self._on_instrument_hover)
        self.instruments_tree.bind('<Leave>', self._on_instrument_leave)

        # Обработчик двойного клика для редактирования инструмента
        self.instruments_tree.bind('<Double-1>', self._on_instrument_double_click)
        
    def create_employees_tab(self):
        """Вкладка управления сотрудниками"""
        tab = tk.Frame(self.notebook, bg=self.office_colors['bg_white'])
        self.notebook.add(tab, text="👥 Сотрудники")

        control_frame = self._create_control_frame(tab)

        self._create_button(control_frame, "Добавить сотрудника", self.add_employee)
        self._create_button(control_frame, "Редактировать", self.edit_employee)
        self._create_button(control_frame, "Удалить", self.delete_employee)
        self._create_button(control_frame, "Обновить", self.load_employees)

        self.employee_search = self._create_search_widget(control_frame, self.load_employees)
        self.employees_tree = self._create_treeview(tab, 'employees')
        self.tree_mapping['employees'] = self.employees_tree

        # Словарь для хранения photo_path по ID сотрудника
        self.employee_photos = {}

        # Обработчик наведения мыши для показа фотографии
        self.employees_tree.bind('<Motion>', self._on_employee_hover)
        self.employees_tree.bind('<Leave>', self._on_employee_leave)

        # Обработчик двойного клика для редактирования сотрудника
        self.employees_tree.bind('<Double-1>', self._on_employee_double_click)
        
    def create_issues_tab(self):
        """Вкладка выдачи инструмента"""
        tab = tk.Frame(self.notebook, bg=self.office_colors['bg_white'])
        self.notebook.add(tab, text="📤 Выдача инструмента")
        
        control_frame = self._create_control_frame(tab)
        
        self._create_button(control_frame, "Выдать инструмент", self.issue_instrument)
        self._create_button(control_frame, "Обновить", self.load_active_issues)
        self._create_button(control_frame, "Экспорт в PDF", self.export_issues_to_pdf)
        
        # Статистика
        stats_frame = tk.Frame(control_frame, bg=self.office_colors['bg_white'])
        stats_frame.pack(side=tk.RIGHT, padx=5)
        self.stats_label = tk.Label(
            stats_frame,
            text="",
            font=self.default_font,
            bg=self.office_colors['bg_white'],
            fg=self.office_colors['fg_secondary']
        )
        self.stats_label.pack()
        
        self.issues_tree = self._create_treeview(tab, 'issues')
        self.tree_mapping['issues'] = self.issues_tree
        
        # Словарь для хранения photo_path по ID инструмента для выдач
        self.issue_instrument_photos = {}
        
        # Обработчик наведения мыши для показа фотографии
        self.issues_tree.bind('<Motion>', self._on_issue_hover)
        self.issues_tree.bind('<Leave>', self._on_issue_leave)
        
    def create_returns_tab(self):
        """Вкладка возврата инструмента"""
        tab = tk.Frame(self.notebook, bg=self.office_colors['bg_white'])
        self.notebook.add(tab, text="📥 Возврат инструмента")
        
        control_frame = self._create_control_frame(tab)
        
        self._create_button(control_frame, "Оформить возврат", self.return_instrument)
        self._create_button(control_frame, "Массовая сдача", self.batch_return_instruments)
        self._create_button(control_frame, "Обновить", self.load_active_issues_for_return)
        self._create_button(control_frame, "Экспорт в PDF", self.export_returns_to_pdf)
        
        self.returns_tree = self._create_treeview(tab, 'returns')
        self.tree_mapping['returns'] = self.returns_tree
        
        # Словарь для хранения photo_path по ID инструмента для возвратов
        self.return_instrument_photos = {}
        
        # Обработчик наведения мыши для показа фотографии
        self.returns_tree.bind('<Motion>', self._on_return_hover)
        self.returns_tree.bind('<Leave>', self._on_return_leave)
        
    def create_history_tab(self):
        """Вкладка журнала операций"""
        tab = tk.Frame(self.notebook, bg=self.office_colors['bg_white'])
        self.notebook.add(tab, text="📋 Журнал операций")
        
        control_frame = self._create_control_frame(tab)
        
        self._create_button(control_frame, "Обновить", self.load_history)
        self._create_button(control_frame, "Экспорт в PDF", self.export_history_to_pdf)
        self._create_button(control_frame, "Экспорт в Excel", self.export_history_to_excel)
        
        # Фильтр
        filter_frame = tk.Frame(control_frame, bg=self.office_colors['bg_white'])
        filter_frame.pack(side=tk.LEFT, padx=20)
        
        # Тип операции
        tk.Label(
            filter_frame,
            text="Тип операции:",
            bg=self.office_colors['bg_white'],
            fg=self.office_colors['fg_main'],
            font=self.default_font
        ).pack(side=tk.LEFT, padx=(0, 5))
        self.history_filter = ttk.Combobox(
            filter_frame, values=['Все', 'Выдача', 'Возврат'],
            state='readonly', width=15
        )
        self.history_filter.set('Все')
        self.history_filter.pack(side=tk.LEFT, padx=5)
        self.history_filter.bind('<<ComboboxSelected>>', lambda e: self.load_history())
        
        # Диапазон дат
        tk.Label(
            filter_frame,
            text="Дата с:",
            bg=self.office_colors['bg_white'],
            fg=self.office_colors['fg_main'],
            font=self.default_font
        ).pack(side=tk.LEFT, padx=(10, 5))
        self.history_date_from = create_russian_date_entry(
            filter_frame,
            width=12,
            date_pattern='yyyy-mm-dd'
        )
        self.history_date_from.pack(side=tk.LEFT, padx=2)
        self.history_date_from.bind('<<DateEntrySelected>>', lambda e: self.load_history())
        
        tk.Label(
            filter_frame,
            text="по:",
            bg=self.office_colors['bg_white'],
            fg=self.office_colors['fg_main'],
            font=self.default_font
        ).pack(side=tk.LEFT, padx=(5, 5))
        self.history_date_to = create_russian_date_entry(
            filter_frame,
            width=12,
            date_pattern='yyyy-mm-dd'
        )
        self.history_date_to.pack(side=tk.LEFT, padx=2)
        self.history_date_to.bind('<<DateEntrySelected>>', lambda e: self.load_history())
        
        # Кнопка сброса фильтра дат
        ttk.Button(
            filter_frame,
            text="Сбросить даты",
            command=self.reset_history_dates
        ).pack(side=tk.LEFT, padx=5)
        
        # Поиск по всем столбцам
        self.history_search = self._create_search_widget(control_frame, self.load_history)
        
        self.history_tree = self._create_treeview(tab, 'history')
        self.tree_mapping['history'] = self.history_tree
    
    def create_addresses_tab(self):
        """Вкладка управления адресами выдачи"""
        tab = tk.Frame(self.notebook, bg=self.office_colors['bg_white'])
        self.notebook.add(tab, text="📍 Адреса выдачи")
        
        control_frame = self._create_control_frame(tab)
        
        self._create_button(control_frame, "Добавить адрес", self.add_address)
        self._create_button(control_frame, "Редактировать", self.edit_address)
        self._create_button(control_frame, "Удалить", self.delete_address)
        self._create_button(control_frame, "Обновить", self.load_addresses)
        
        self.address_search = self._create_search_widget(control_frame, self.load_addresses)
        self.addresses_tree = self._create_treeview(tab, 'addresses')
        self.tree_mapping['addresses'] = self.addresses_tree
    
    def create_statistics_tab(self):
        """Вкладка статистики и отчетов"""
        tab = tk.Frame(self.notebook, bg=self.office_colors['bg_white'])
        self.notebook.add(tab, text="📊 Статистика")
        
        # Создаем скроллируемый фрейм
        canvas = tk.Canvas(tab, bg=self.office_colors['bg_white'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.office_colors['bg_white'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Панель управления
        control_frame = self._create_control_frame(scrollable_frame)
        self._create_button(control_frame, "Обновить", self.load_statistics)
        
        # Общая статистика
        self._create_statistics_section(scrollable_frame, "Общая статистика", self._create_general_stats)
        
        # Статистика по категориям
        self._create_statistics_section(scrollable_frame, "Инструменты по категориям", self._create_category_stats)
        
        # Топ сотрудников
        self._create_statistics_section(scrollable_frame, "Топ сотрудников по выдачам", self._create_employees_stats)
        
        # Самые используемые инструменты
        self._create_statistics_section(scrollable_frame, "Самые используемые инструменты", self._create_instruments_usage_stats)
        
        # Среднее время использования
        self._create_statistics_section(scrollable_frame, "Среднее время использования", self._create_usage_time_stats)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Привязка прокрутки колесом мыши
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # Обновление области прокрутки при изменении размера
        def update_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        scrollable_frame.bind("<Configure>", update_scroll_region)
        
        # Настройка фона canvas
        canvas.configure(bg=self.office_colors['bg_white'])
        
    def create_analytics_tab(self):
        """Вкладка расширенной аналитики с графиками"""
        tab = tk.Frame(self.notebook, bg=self.office_colors['bg_white'])
        self.notebook.add(tab, text="📈 Аналитика")

        # Создаем скроллируемый фрейм
        canvas = tk.Canvas(tab, bg=self.office_colors['bg_white'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.office_colors['bg_white'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Панель управления
        control_frame = self._create_control_frame(scrollable_frame)
        self._create_button(control_frame, "Обновить", self.load_analytics)

        # Графики
        self._create_chart_section(scrollable_frame, "Выдачи и возвраты по месяцам", self._create_issues_returns_chart)
        self._create_chart_section(scrollable_frame, "Динамика активных выдач", self._create_active_trend_chart)
        self._create_chart_section(scrollable_frame, "Просроченные выдачи по категориям", self._create_overdue_chart)
        self._create_chart_section(scrollable_frame, "Выдачи по адресам", self._create_addresses_chart)
        self._create_chart_section(scrollable_frame, "Статусы инструментов", self._create_status_chart)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Привязка прокрутки колесом мыши
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)

        # Обновление области прокрутки при изменении размера
        def update_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        scrollable_frame.bind("<Configure>", update_scroll_region)

        canvas.configure(bg=self.office_colors['bg_white'])

    def _create_chart_section(self, parent, title, content_func):
        """Создание секции графика в стиле MS Office"""
        section_frame = ttk.LabelFrame(parent, text=title, padding="10")
        section_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        content_func(section_frame)

    def _create_statistics_section(self, parent, title, content_func):
        """Создание секции статистики в стиле MS Office"""
        section_frame = ttk.LabelFrame(parent, text=title, padding="10")
        section_frame.pack(fill=tk.X, padx=10, pady=5)
        content_func(section_frame)
    
    def _create_general_stats(self, parent):
        """Создание общей статистики"""
        stats = self.db.get_general_statistics()
        
        # Создаем фрейм для метрик
        metrics_frame = tk.Frame(parent, bg=self.office_colors['bg_white'])
        metrics_frame.pack(fill=tk.X, pady=5)
        
        # Метрики в две колонки
        left_frame = tk.Frame(metrics_frame, bg=self.office_colors['bg_white'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        right_frame = tk.Frame(metrics_frame, bg=self.office_colors['bg_white'])
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Левая колонка
        self._create_metric(left_frame, "Всего инструментов", stats['total_instruments'])
        self._create_metric(left_frame, "Активных сотрудников", stats['active_employees'])
        self._create_metric(left_frame, "Активных выдач", stats['active_issues'])
        
        # Правая колонка
        self._create_metric(right_frame, "Просроченных выдач", stats['overdue_issues'], 
                           color='red' if stats['overdue_issues'] > 0 else 'black')
        self._create_metric(right_frame, "Всего операций", stats['total_operations'])
        
        # Статусы инструментов
        if stats['instruments_by_status']:
            status_frame = ttk.LabelFrame(parent, text="Инструменты по статусам", padding="5")
            status_frame.pack(fill=tk.X, pady=5)
            
            status_inner = tk.Frame(status_frame, bg=self.office_colors['bg_white'])
            status_inner.pack(fill=tk.X)
            
            for status, count in stats['instruments_by_status'].items():
                self._create_metric(status_inner, status, count)
    
    def _create_category_stats(self, parent):
        """Статистика по категориям"""
        data = self.db.get_instruments_by_category()
        
        if not data:
            no_data_label = tk.Label(
                parent,
                text="Нет данных",
                bg=self.office_colors['bg_white'],
                fg=self.office_colors['fg_secondary'],
                font=self.default_font
            )
            no_data_label.pack(pady=5)
            return
        
        # Таблица
        columns = ('Категория', 'Всего', 'Доступно', 'Выдано', 'На ремонте', 'Списано')
        tree = ttk.Treeview(parent, columns=columns, show='headings', height=min(len(data), 10))
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        for row in data:
            tree.insert('', tk.END, values=row)
        
        tree.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def _create_employees_stats(self, parent):
        """Статистика по сотрудникам"""
        data = self.db.get_top_employees_by_issues(10)
        
        if not data:
            no_data_label = tk.Label(
                parent,
                text="Нет данных",
                bg=self.office_colors['bg_white'],
                fg=self.office_colors['fg_secondary'],
                font=self.default_font
            )
            no_data_label.pack(pady=5)
            return
        
        columns = ('Сотрудник', 'Отдел', 'Всего выдач', 'Активных', 'Просрочено')
        tree = ttk.Treeview(parent, columns=columns, show='headings', height=min(len(data), 10))
        
        tree.column('Сотрудник', width=200)
        tree.column('Отдел', width=150)
        tree.column('Всего выдач', width=100)
        tree.column('Активных', width=100)
        tree.column('Просрочено', width=100)
        
        for col in columns:
            tree.heading(col, text=col)
        
        for row in data:
            tags = ('overdue',) if row[4] > 0 else ()
            tree.insert('', tk.END, values=row, tags=tags)
        
        tree.tag_configure('overdue', background='#ffcccc')
        tree.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def _create_instruments_usage_stats(self, parent):
        """Статистика использования инструментов"""
        data = self.db.get_most_used_instruments(10)
        
        if not data:
            no_data_label = tk.Label(
                parent,
                text="Нет данных",
                bg=self.office_colors['bg_white'],
                fg=self.office_colors['fg_secondary'],
                font=self.default_font
            )
            no_data_label.pack(pady=5)
            return
        
        columns = ('Инструмент', 'Инв. номер', 'Категория', 'Всего операций', 'Выдач', 'Возвратов')
        tree = ttk.Treeview(parent, columns=columns, show='headings', height=min(len(data), 10))
        
        tree.column('Инструмент', width=200)
        tree.column('Инв. номер', width=120)
        tree.column('Категория', width=150)
        tree.column('Всего операций', width=120)
        tree.column('Выдач', width=100)
        tree.column('Возвратов', width=100)
        
        for col in columns:
            tree.heading(col, text=col)
        
        for row in data:
            tree.insert('', tk.END, values=row)
        
        tree.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def _create_usage_time_stats(self, parent):
        """Статистика времени использования"""
        data = self.db.get_average_usage_time()
        
        if not data:
            no_data_label = tk.Label(
                parent,
                text="Недостаточно данных для расчета",
                bg=self.office_colors['bg_white'],
                fg=self.office_colors['fg_secondary'],
                font=self.default_font
            )
            no_data_label.pack(pady=5)
            return
        
        metrics_frame = tk.Frame(parent, bg=self.office_colors['bg_white'])
        metrics_frame.pack(fill=tk.X, pady=5)
        
        self._create_metric(metrics_frame, "Среднее время (дней)", data['avg_days'])
        self._create_metric(metrics_frame, "Минимальное время (дней)", data['min_days'])
        self._create_metric(metrics_frame, "Максимальное время (дней)", data['max_days'])
        self._create_metric(metrics_frame, "Всего возвратов", data['total_returns'])
    
    def _create_metric(self, parent, label, value, color='black'):
        """Создание метрики в стиле MS Office"""
        frame = tk.Frame(parent, bg=self.office_colors['bg_white'])
        frame.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Используем цвет из office_colors если это стандартный цвет
        if color == 'black':
            text_color = self.office_colors['fg_main']
        elif color == 'red':
            text_color = '#d13438'  # Красный в стиле Office
        else:
            text_color = color
        
        label_widget = tk.Label(
            frame,
            text=label,
            font=(self.default_font[0], 9),
            bg=self.office_colors['bg_white'],
            fg=self.office_colors['fg_secondary']
        )
        label_widget.pack()
        
        value_widget = tk.Label(
            frame,
            text=str(value),
            font=(self.default_font[0], 14, "bold"),
            fg=text_color,
            bg=self.office_colors['bg_white']
        )
        value_widget.pack()
    
    def load_statistics(self):
        """Обновление статистики"""
        # Находим индекс вкладки статистики
        stats_tab_index = None
        for i in range(self.notebook.index("end")):
            tab_text = self.notebook.tab(i, "text")
            if "Статистика" in tab_text:
                stats_tab_index = i
                break
        
        if stats_tab_index is not None:
            # Удаляем старую вкладку
            self.notebook.forget(stats_tab_index)
            # Создаем новую
            self.create_statistics_tab()
            # Выбираем её
            for i in range(self.notebook.index("end")):
                tab_text = self.notebook.tab(i, "text")
                if "Статистика" in tab_text:
                    self.notebook.select(i)
                    break
        
    def sort_treeview(self, table_name, column, toggle_direction=True):
        """Сортировка таблицы по столбцу
        
        Args:
            table_name: имя таблицы ('instruments', 'employees', и т.д.)
            column: имя столбца для сортировки
            toggle_direction: если True, переключает направление при клике на тот же столбец
        """
        tree = self.tree_mapping.get(table_name)
        if not tree:
            return
        
        # Получаем индекс столбца
        columns = tree['columns']
        try:
            col_index = columns.index(column)
        except ValueError:
            return
        
        # Определяем направление сортировки
        sort_state = self.sort_states[table_name]
        if sort_state['column'] == column:
            # Тот же столбец - переключаем направление только если toggle_direction=True
            if toggle_direction:
                sort_state['direction'] = 'desc' if sort_state['direction'] == 'asc' else 'asc'
        else:
            # Новый столбец - начинаем с возрастания
            sort_state['column'] = column
            sort_state['direction'] = 'asc'
        
        # Получаем все элементы
        items = [(tree.set(item, column), item) for item in tree.get_children('')]
        
        # Определяем функцию сравнения
        def try_convert(value):
            """Попытка преобразовать значение в число или дату"""
            if value is None or value == '':
                return (0, value)  # Пустые значения в начало
            
            # Попытка преобразовать в число
            try:
                return (1, float(value))
            except ValueError:
                pass
            
            # Попытка преобразовать в дату
            try:
                # Формат: YYYY-MM-DD или YYYY-MM-DD HH:MM:SS
                if ' ' in value:
                    dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                else:
                    dt = datetime.strptime(value, '%Y-%m-%d')
                return (2, dt)
            except ValueError:
                pass
            
            # Строка
            return (3, str(value).lower())
        
        # Сортируем
        items.sort(key=lambda x: try_convert(x[0]), reverse=(sort_state['direction'] == 'desc'))
        
        # Перемещаем элементы в отсортированном порядке
        for index, (val, item) in enumerate(items):
            tree.move(item, '', index)
        
        # Обновляем заголовки столбцов с индикаторами
        self.update_sort_indicators(table_name)
    
    def update_sort_indicators(self, table_name):
        """Обновление индикаторов направления сортировки в заголовках"""
        tree = self.tree_mapping.get(table_name)
        if not tree:
            return
        
        sort_state = self.sort_states[table_name]
        columns = tree['columns']
        
        for col in columns:
            base_text = col
            if sort_state['column'] == col:
                indicator = ' ▲' if sort_state['direction'] == 'asc' else ' ▼'
                tree.heading(col, text=base_text + indicator)
            else:
                tree.heading(col, text=base_text)
    
    def load_data(self):
        """Загрузка всех данных"""
        self.load_instruments()
        self.load_employees()
        self.load_active_issues()
        self.load_active_issues_for_return()
        self.load_history()
        self.load_addresses()
    
    def _load_treeview_data(self, table_name, tree, data_func, search_widget=None, 
                            item_processor=None, post_load_callback=None):
        """Универсальный метод загрузки данных в Treeview
        
        Args:
            table_name: имя таблицы для сортировки
            tree: виджет Treeview
            data_func: функция получения данных (callable, может принимать search_text)
            search_widget: виджет поиска (опционально)
            item_processor: функция обработки каждого элемента (опционально), возвращает (values, tags)
            post_load_callback: функция вызываемая после загрузки (опционально)
        """
        # Очистка таблицы
        for item in tree.get_children():
            tree.delete(item)
        
        # Получаем данные
        if search_widget:
            data = data_func(search_widget.get())
        else:
            data = data_func()
        
        # Вставка данных
        for item_data in data:
            tags = ()
            values = item_data
            if item_processor:
                result = item_processor(item_data)
                if isinstance(result, tuple) and len(result) == 2:
                    values, tags = result
                else:
                    values = result
            
            tree.insert('', tk.END, values=values, tags=tags)
        
        # Применяем текущую сортировку
        sort_state = self.sort_states[table_name]
        if sort_state['column']:
            self.sort_treeview(table_name, sort_state['column'], toggle_direction=False)
        else:
            self.update_sort_indicators(table_name)
        
        # Вызываем постобработку
        if post_load_callback:
            post_load_callback()
        
    def load_instruments(self):
        """Загрузка списка инструментов"""
        # Очищаем словарь фотографий
        if not hasattr(self, 'instrument_photos'):
            self.instrument_photos = {}
        else:
            self.instrument_photos.clear()
        
        def process_item(item_data):
            # item_data: (id, name, inventory_number, serial_number, category, current_address, status, photo_path, barcode)
            instrument_id = item_data[0]
            photo_path = item_data[7] if len(item_data) > 7 else ''
            barcode = item_data[8] if len(item_data) > 8 else ''
            
            # Сохраняем photo_path в словаре
            if photo_path:
                self.instrument_photos[instrument_id] = photo_path
            
            # Возвращаем видимые столбцы (без current_address и photo_path)
            # id, name, inventory_number, serial_number, barcode, category, status
            values = (item_data[0], item_data[1], item_data[2], item_data[3], barcode, item_data[4], item_data[6])
            return values, ()
        
        self._load_treeview_data(
            'instruments', 
            self.instruments_tree, 
            lambda search: self.db.get_instruments(search),
            getattr(self, 'instrument_search', None),
            item_processor=process_item
        )
            
    def search_by_barcode(self):
        """Поиск инструмента по штрих-коду"""
        barcode = self.barcode_search.get().strip()
        if not barcode:
            messagebox.showwarning("Предупреждение", "Введите штрих-код для поиска")
            return

        # Импортируем менеджер штрих-кодов
        from barcode_utils import barcode_manager

        # Ищем инструмент по штрих-коду
        instrument = barcode_manager.search_by_barcode(barcode, self.db)

        if instrument:
            # Очищаем таблицу
            for item in self.instruments_tree.get_children():
                self.instruments_tree.delete(item)

            # Добавляем найденный инструмент
            values = (
                instrument['id'],
                instrument['name'],
                instrument['inventory_number'],
                instrument['serial_number'],
                instrument['barcode'],
                instrument['category'],
                instrument['status']
            )
            self.instruments_tree.insert('', 'end', values=values)

            # Очищаем поле поиска
            self.barcode_search.delete(0, tk.END)

            messagebox.showinfo("Найден инструмент",
                              f"Найден инструмент: {instrument['name']}\n"
                              f"Инв. номер: {instrument['inventory_number']}")
        else:
            messagebox.showwarning("Не найдено", f"Инструмент со штрих-кодом '{barcode}' не найден")

    def load_employees(self):
        """Загрузка списка сотрудников"""
        # Очищаем словарь фотографий
        if not hasattr(self, 'employee_photos'):
            self.employee_photos = {}
        else:
            self.employee_photos.clear()

        def process_item(item_data):
            # item_data: (id, full_name, position, department, phone, email, status, photo_path)
            employee_id = item_data[0]
            photo_path = item_data[7] if len(item_data) > 7 else ''

            # Сохраняем photo_path в словаре
            if photo_path:
                self.employee_photos[employee_id] = photo_path

            # Возвращаем видимые столбцы (без photo_path)
            # id, full_name, position, department, phone, email, status
            values = item_data[:7]
            return values, ()

        self._load_treeview_data(
            'employees',
            self.employees_tree,
            lambda search: self.db.get_employees(search),
            getattr(self, 'employee_search', None),
            item_processor=process_item
        )
            
    def load_active_issues(self):
        """Загрузка активных выдач"""
        # Очищаем словари фотографий и соответствий
        if not hasattr(self, 'issue_instrument_photos'):
            self.issue_instrument_photos = {}
        else:
            self.issue_instrument_photos.clear()
        
        if not hasattr(self, 'issue_issue_to_instrument'):
            self.issue_issue_to_instrument = {}
        else:
            self.issue_issue_to_instrument.clear()
        
        def process_item(issue):
            # issue: (id, instrument_id, inventory_number, name, full_name, address, issue_date, expected_return_date, issued_by, notes, photo_path)
            issue_id = issue[0]
            instrument_id = issue[1] if len(issue) > 1 else None
            photo_path = issue[10] if len(issue) > 10 else ''
            
            # Сохраняем соответствие issue_id -> instrument_id
            if issue_id and instrument_id:
                self.issue_issue_to_instrument[issue_id] = instrument_id
            
            # Сохраняем photo_path в словаре
            if instrument_id and photo_path:
                self.issue_instrument_photos[instrument_id] = photo_path
            
            # Возвращаем только видимые столбцы (без instrument_id и photo_path)
            # id, inventory_number, name, full_name, address, issue_date, expected_return_date, issued_by, notes
            values = (issue[0], issue[2], issue[3], issue[4], issue[5], issue[6], issue[7], issue[8], issue[9])
            return values, ()
        
        def post_load():
            stats = self.db.get_issues_statistics()
            self.stats_label.config(
                text=f"Всего выдано: {stats['total']} | Просрочено: {stats['overdue']}"
            )
        
        self._load_treeview_data(
            'issues',
            self.issues_tree,
            self.db.get_active_issues,
            item_processor=process_item,
            post_load_callback=post_load
        )
        
    def load_active_issues_for_return(self):
        """Загрузка активных выдач для возврата"""
        # Очищаем словари фотографий и соответствий
        if not hasattr(self, 'return_instrument_photos'):
            self.return_instrument_photos = {}
        else:
            self.return_instrument_photos.clear()
        
        if not hasattr(self, 'return_issue_to_instrument'):
            self.return_issue_to_instrument = {}
        else:
            self.return_issue_to_instrument.clear()
        
        def process_item(issue):
            # issue: (id, instrument_id, inventory_number, name, full_name, address, issue_date, expected_return_date, days_in_use, photo_path)
            issue_id = issue[0]
            instrument_id = issue[1] if len(issue) > 1 else None
            photo_path = issue[9] if len(issue) > 9 else ''
            
            # Сохраняем соответствие issue_id -> instrument_id
            if issue_id and instrument_id:
                self.return_issue_to_instrument[issue_id] = instrument_id
            
            # Сохраняем photo_path в словаре
            if instrument_id and photo_path:
                self.return_instrument_photos[instrument_id] = photo_path
            
            expected_return = datetime.strptime(issue[7], '%Y-%m-%d').date() if len(issue) > 7 and issue[7] else None
            tags = ('overdue',) if expected_return and expected_return < datetime.now().date() else ()
            
            # Возвращаем только видимые столбцы (без instrument_id и photo_path)
            # id, inventory_number, name, full_name, address, issue_date, expected_return_date, days_in_use
            values = (issue[0], issue[2], issue[3], issue[4], issue[5], issue[6], issue[7], issue[8])
            return values, tags
        
        self._load_treeview_data(
            'returns',
            self.returns_tree,
            self.db.get_active_issues_for_return,
            item_processor=process_item
        )
            
    def load_history(self):
        """Загрузка журнала операций"""
        def process_item(record):
            tags = ('issue',) if record[1] == 'Выдача' else ('return',)
            return record, tags
        
        filter_type = getattr(self, 'history_filter', None)
        filter_value = filter_type.get() if filter_type else 'Все'
        search_text = getattr(self, 'history_search', None)
        search_value = search_text.get() if search_text else ''
        
        # Получаем диапазон дат
        date_from = None
        date_to = None
        if hasattr(self, 'history_date_from'):
            date_from_val = self.history_date_from.get_date()
            if date_from_val:
                date_from = date_from_val.strftime('%Y-%m-%d')
        if hasattr(self, 'history_date_to'):
            date_to_val = self.history_date_to.get_date()
            if date_to_val:
                date_to = date_to_val.strftime('%Y-%m-%d')
        
        self._load_treeview_data(
            'history',
            self.history_tree,
            lambda: self.db.get_operation_history(
                filter_value, 
                search_text=search_value,
                date_from=date_from,
                date_to=date_to
            ),
            item_processor=process_item
        )
    
    def reset_history_dates(self):
        """Сброс фильтра дат в журнале операций - устанавливает диапазон за последние 3 месяца"""
        from datetime import date, timedelta
        
        # Вычисляем дату три месяца назад
        today = date.today()
        three_months_ago = today - timedelta(days=90)  # Примерно 3 месяца
        
        if hasattr(self, 'history_date_from'):
            try:
                self.history_date_from.set_date(three_months_ago)
            except:
                pass
        if hasattr(self, 'history_date_to'):
            try:
                self.history_date_to.set_date(today)
            except:
                pass
        self.load_history()
            
    def add_instrument(self):
        """Добавление нового инструмента"""
        AddInstrumentDialog(self.root, self.db, self.load_instruments)
        
    def _get_selected_item_id(self, tree, warning_message):
        """Получение ID выбранного элемента из таблицы"""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", warning_message)
            return None
        item = tree.item(selected[0])
        return item['values'][0]
    
    def _delete_item(self, tree, item_id, delete_func, success_message, error_message, reload_func):
        """Универсальный метод удаления элемента"""
        if delete_func(item_id):
            messagebox.showinfo("Успех", success_message)
            reload_func()
        else:
            messagebox.showerror("Ошибка", error_message)
    
    def edit_instrument(self):
        """Редактирование инструмента"""
        instrument_id = self._get_selected_item_id(
            self.instruments_tree, "Выберите инструмент для редактирования"
        )
        if instrument_id:
            EditInstrumentDialog(self.root, self.db, instrument_id, self.load_instruments)
        
    def delete_instrument(self):
        """Удаление инструмента"""
        instrument_id = self._get_selected_item_id(
            self.instruments_tree, "Выберите инструмент для удаления"
        )
        if instrument_id and messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить инструмент?"):
            self._delete_item(
                self.instruments_tree,
                instrument_id,
                self.db.delete_instrument,
                "Инструмент удален",
                "Невозможно удалить инструмент (возможно, есть активные выдачи)",
                self.load_instruments
            )
                
    def add_employee(self):
        """Добавление нового сотрудника"""
        AddEmployeeDialog(self.root, self.db, self.load_employees)
        
    def edit_employee(self):
        """Редактирование сотрудника"""
        employee_id = self._get_selected_item_id(
            self.employees_tree, "Выберите сотрудника для редактирования"
        )
        if employee_id:
            EditEmployeeDialog(self.root, self.db, employee_id, self.load_employees)
        
    def delete_employee(self):
        """Удаление сотрудника"""
        employee_id = self._get_selected_item_id(
            self.employees_tree, "Выберите сотрудника для удаления"
        )
        if employee_id and messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить сотрудника?"):
            self._delete_item(
                self.employees_tree,
                employee_id,
                self.db.delete_employee,
                "Сотрудник удален",
                "Невозможно удалить сотрудника (возможно, есть активные выдачи)",
                self.load_employees
            )
                
    def issue_instrument(self):
        """Выдача инструмента"""
        IssueInstrumentDialog(self.root, self.db, self.load_data)
        
    def return_instrument(self):
        """Возврат инструмента"""
        issue_id = self._get_selected_item_id(
            self.returns_tree, "Выберите выдачу для оформления возврата"
        )
        if issue_id:
            ReturnInstrumentDialog(self.root, self.db, issue_id, self.load_data)
    
    def batch_return_instruments(self):
        """Массовая сдача инструментов"""
        BatchReturnDialog(self.root, self.db, self.load_data)

    def load_addresses(self):
        """Загрузка списка адресов"""
        self._load_treeview_data(
            'addresses',
            self.addresses_tree,
            lambda search: self.db.get_addresses() if not search else [
                addr for addr in self.db.get_addresses()
                if search.lower() in (addr[1] or '').lower() or search.lower() in (addr[2] or '').lower()
            ],
            getattr(self, 'address_search', None)
        )
    
    def add_address(self):
        """Добавление нового адреса"""
        AddAddressDialog(self.root, self.db, self.load_addresses)
    
    def edit_address(self):
        """Редактирование адреса"""
        address_id = self._get_selected_item_id(
            self.addresses_tree, "Выберите адрес для редактирования"
        )
        if address_id:
            EditAddressDialog(self.root, self.db, address_id, self.load_addresses)
    
    def delete_address(self):
        """Удаление адреса"""
        address_id = self._get_selected_item_id(
            self.addresses_tree, "Выберите адрес для удаления"
        )
        if address_id and messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить адрес?"):
            success, message = self.db.delete_address(address_id)
            if success:
                messagebox.showinfo("Успех", message)
                self.load_addresses()
            else:
                messagebox.showerror("Ошибка", message)
    
    def export_issues_to_pdf(self):
        """Экспорт журнала выдачи инструмента в PDF"""
        # Диалог выбора файла
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Сохранить журнал выдачи в PDF",
            initialfile=f"Журнал_выдачи_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        
        if not filename:
            return  # Пользователь отменил
        
        try:
            # Создаем экспортер
            exporter = PDFExporter()
            
            # Получаем данные о выдачах
            issues = self.db.get_active_issues()
            
            if not issues:
                messagebox.showwarning(
                    "Предупреждение", 
                    "Нет данных для экспорта. Нет активных выдач."
                )
                return
            
            # Экспортируем в PDF
            exporter.export_issues_journal(issues, filename)
            
            messagebox.showinfo(
                "Успех", 
                f"Журнал выдачи успешно экспортирован в PDF.\n\nФайл: {filename}"
            )
        except Exception as e:
            messagebox.showerror(
                "Ошибка", 
                f"Ошибка при экспорте в PDF:\n{str(e)}"
            )
    
    def export_returns_to_pdf(self):
        """Экспорт журнала возврата инструмента в PDF"""
        # Диалог выбора файла
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Сохранить журнал возврата в PDF",
            initialfile=f"Журнал_возврата_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        
        if not filename:
            return  # Пользователь отменил
        
        try:
            # Создаем экспортер
            exporter = PDFExporter()
            
            # Получаем данные о возвратах
            returns = self.db.get_active_issues_for_return()
            
            if not returns:
                messagebox.showwarning(
                    "Предупреждение", 
                    "Нет данных для экспорта. Нет активных выдач для возврата."
                )
                return
            
            # Экспортируем в PDF
            exporter.export_returns_journal(returns, filename)
            
            messagebox.showinfo(
                "Успех", 
                f"Журнал возврата успешно экспортирован в PDF.\n\nФайл: {filename}"
            )
        except Exception as e:
            messagebox.showerror(
                "Ошибка", 
                f"Ошибка при экспорте в PDF:\n{str(e)}"
            )
    
    def export_history_to_pdf(self):
        """Экспорт журнала операций в PDF"""
        # Диалог выбора файла
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Сохранить журнал операций в PDF",
            initialfile=f"Журнал_операций_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        
        if not filename:
            return  # Пользователь отменил
        
        try:
            # Создаем экспортер
            exporter = PDFExporter()
            
            # Получаем данные журнала операций с учетом фильтров
            filter_type = getattr(self, 'history_filter', None)
            filter_value = filter_type.get() if filter_type else 'Все'
            search_text = getattr(self, 'history_search', None)
            search_value = search_text.get() if search_text else ''
            
            # Получаем диапазон дат
            date_from = None
            date_to = None
            if hasattr(self, 'history_date_from'):
                date_from_val = self.history_date_from.get_date()
                if date_from_val:
                    date_from = date_from_val.strftime('%Y-%m-%d')
            if hasattr(self, 'history_date_to'):
                date_to_val = self.history_date_to.get_date()
                if date_to_val:
                    date_to = date_to_val.strftime('%Y-%m-%d')
            
            history = self.db.get_operation_history(
                filter_value, 
                search_text=search_value,
                date_from=date_from,
                date_to=date_to
            )
            
            if not history:
                messagebox.showwarning(
                    "Предупреждение", 
                    "Нет данных для экспорта. Нет записей в журнале операций."
                )
                return
            
            # Экспортируем в PDF
            exporter.export_history_journal(history, filename, filter_value)
            
            messagebox.showinfo(
                "Успех", 
                f"Журнал операций успешно экспортирован в PDF.\n\nФайл: {filename}"
            )
        except Exception as e:
            messagebox.showerror(
                "Ошибка", 
                f"Ошибка при экспорте в PDF:\n{str(e)}"
            )
    
    def export_history_to_excel(self):
        """Экспорт журнала операций в Excel"""
        # Диалог выбора файла
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Сохранить журнал операций в Excel",
            initialfile=f"Журнал_операций_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        
        if not filename:
            return  # Пользователь отменил
        
        try:
            # Создаем экспортер
            exporter = ExcelExporter()
            
            # Получаем данные журнала операций с учетом фильтров
            filter_type = getattr(self, 'history_filter', None)
            filter_value = filter_type.get() if filter_type else 'Все'
            search_text = getattr(self, 'history_search', None)
            search_value = search_text.get() if search_text else ''
            
            # Получаем диапазон дат
            date_from = None
            date_to = None
            if hasattr(self, 'history_date_from'):
                date_from_val = self.history_date_from.get_date()
                if date_from_val:
                    date_from = date_from_val.strftime('%Y-%m-%d')
            if hasattr(self, 'history_date_to'):
                date_to_val = self.history_date_to.get_date()
                if date_to_val:
                    date_to = date_to_val.strftime('%Y-%m-%d')
            
            history = self.db.get_operation_history(
                filter_value, 
                search_text=search_value,
                date_from=date_from,
                date_to=date_to
            )
            
            if not history:
                messagebox.showwarning(
                    "Предупреждение", 
                    "Нет данных для экспорта. Нет записей в журнале операций."
                )
                return
            
            # Экспортируем в Excel
            exporter.export_history_journal(history, filename, filter_value)
            
            messagebox.showinfo(
                "Успех", 
                f"Журнал операций успешно экспортирован в Excel.\n\nФайл: {filename}"
            )
        except Exception as e:
            messagebox.showerror(
                "Ошибка",
                f"Ошибка при экспорте в Excel:\n{str(e)}"
            )

    def export_to_xml(self):
        """Экспорт данных в XML формат"""
        # Диалог выбора типа данных
        data_types = {
            'Инструменты': 'instruments',
            'Сотрудники': 'employees',
            'Выдачи': 'issues',
            'История операций': 'history'
        }

        # Создаем диалог выбора
        dialog = tk.Toplevel(self.root)
        dialog.title("Экспорт в XML")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="Выберите тип данных для экспорта:").pack(pady=10)

        data_type_var = tk.StringVar(value='Инструменты')
        for display_name in data_types.keys():
            tk.Radiobutton(dialog, text=display_name, variable=data_type_var,
                          value=display_name).pack(anchor=tk.W, padx=20)

        def do_export():
            data_type_display = data_type_var.get()
            data_type = data_types[data_type_display]

            # Диалог выбора файла
            filename = filedialog.asksaveasfilename(
                defaultextension=".xml",
                filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
                title=f"Сохранить {data_type_display.lower()} в XML",
                initialfile=f"{data_type_display}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
            )

            if not filename:
                dialog.destroy()
                return

            try:
                # Получаем данные
                if data_type == 'instruments':
                    data = self.db.get_instruments()
                elif data_type == 'employees':
                    data = self.db.get_employees()
                elif data_type == 'issues':
                    data = self.db.get_active_issues()
                elif data_type == 'history':
                    filter_type = getattr(self, 'history_filter', None)
                    filter_value = filter_type.get() if filter_type else 'Все'
                    search_text = getattr(self, 'history_search', None)
                    search_value = search_text.get() if search_text else ''
                    date_from = None
                    date_to = None
                    if hasattr(self, 'history_date_from'):
                        date_from_val = self.history_date_from.get_date()
                        if date_from_val:
                            date_from = date_from_val.strftime('%Y-%m-%d')
                    if hasattr(self, 'history_date_to'):
                        date_to_val = self.history_date_to.get_date()
                        if date_to_val:
                            date_to = date_to_val.strftime('%Y-%m-%d')
                    data = self.db.get_operation_history(filter_value, search_text=search_value,
                                                       date_from=date_from, date_to=date_to)

                if not data:
                    messagebox.showwarning("Предупреждение", "Нет данных для экспорта.")
                    dialog.destroy()
                    return

                # Экспортируем в XML
                success, message = self.xml_json_exporter.export_to_xml(data, filename, data_type)

                if success:
                    messagebox.showinfo("Успех", f"{message}\n\nФайл: {filename}")
                else:
                    messagebox.showerror("Ошибка", message)

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при экспорте в XML:\n{str(e)}")

            dialog.destroy()

        tk.Button(dialog, text="Экспортировать", command=do_export).pack(pady=10)
        tk.Button(dialog, text="Отмена", command=dialog.destroy).pack()

    def export_to_json(self):
        """Экспорт данных в JSON формат"""
        # Диалог выбора типа данных
        data_types = {
            'Инструменты': 'instruments',
            'Сотрудники': 'employees',
            'Выдачи': 'issues',
            'История операций': 'history'
        }

        # Создаем диалог выбора
        dialog = tk.Toplevel(self.root)
        dialog.title("Экспорт в JSON")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="Выберите тип данных для экспорта:").pack(pady=10)

        data_type_var = tk.StringVar(value='Инструменты')
        for display_name in data_types.keys():
            tk.Radiobutton(dialog, text=display_name, variable=data_type_var,
                          value=display_name).pack(anchor=tk.W, padx=20)

        def do_export():
            data_type_display = data_type_var.get()
            data_type = data_types[data_type_display]

            # Диалог выбора файла
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title=f"Сохранить {data_type_display.lower()} в JSON",
                initialfile=f"{data_type_display}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

            if not filename:
                dialog.destroy()
                return

            try:
                # Получаем данные
                if data_type == 'instruments':
                    data = self.db.get_instruments()
                elif data_type == 'employees':
                    data = self.db.get_employees()
                elif data_type == 'issues':
                    data = self.db.get_active_issues()
                elif data_type == 'history':
                    filter_type = getattr(self, 'history_filter', None)
                    filter_value = filter_type.get() if filter_type else 'Все'
                    search_text = getattr(self, 'history_search', None)
                    search_value = search_text.get() if search_text else ''
                    date_from = None
                    date_to = None
                    if hasattr(self, 'history_date_from'):
                        date_from_val = self.history_date_from.get_date()
                        if date_from_val:
                            date_from = date_from_val.strftime('%Y-%m-%d')
                    if hasattr(self, 'history_date_to'):
                        date_to_val = self.history_date_to.get_date()
                        if date_to_val:
                            date_to = date_to_val.strftime('%Y-%m-%d')
                    data = self.db.get_operation_history(filter_value, search_text=search_value,
                                                       date_from=date_from, date_to=date_to)

                if not data:
                    messagebox.showwarning("Предупреждение", "Нет данных для экспорта.")
                    dialog.destroy()
                    return

                # Экспортируем в JSON
                success, message = self.xml_json_exporter.export_to_json(data, filename, data_type)

                if success:
                    messagebox.showinfo("Успех", f"{message}\n\nФайл: {filename}")
                else:
                    messagebox.showerror("Ошибка", message)

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при экспорте в JSON:\n{str(e)}")

            dialog.destroy()

        tk.Button(dialog, text="Экспортировать", command=do_export).pack(pady=10)
        tk.Button(dialog, text="Отмена", command=dialog.destroy).pack()
    
    def _save_window_geometry(self):
        """Сохранение геометрии окна (вызывается с задержкой)"""
        if self.root.winfo_viewable():
            geometry = self.root.geometry()
            self.window_config.save_window_geometry("main_window", geometry)
        self._save_geometry_job = None
    
    def _on_closing(self):
        """Обработка закрытия окна - сохраняем геометрию перед выходом"""
        try:
            # Отменяем все отложенные задачи
            if hasattr(self, '_save_geometry_job') and self._save_geometry_job:
                try:
                    self.root.after_cancel(self._save_geometry_job)
                except:
                    pass

            if hasattr(self, 'photo_tooltip_job') and self.photo_tooltip_job:
                try:
                    self.root.after_cancel(self.photo_tooltip_job)
                except:
                    pass

            # Закрываем все дочерние окна и диалоги
            for child in self.root.winfo_children():
                try:
                    if hasattr(child, 'destroy'):
                        child.destroy()
                except:
                    pass

            # Сохраняем геометрию главного окна немедленно
            if self.root.winfo_viewable():
                geometry = self.root.geometry()
                self.window_config.save_window_geometry("main_window", geometry)

            # Сохраняем геометрию всех открытых диалогов
            save_all_dialogs_geometry()

        except Exception as e:
            print(f"Ошибка при подготовке к закрытию: {e}")

        finally:
            # Принудительное завершение процесса
            import os
            try:
                self.root.destroy()
            except:
                pass
            # Гарантированное завершение
            os._exit(0)
    
    def _on_instrument_hover(self, event):
        """Обработчик наведения мыши на инструмент"""
        # Отменяем предыдущую отложенную задачу, если есть
        if hasattr(self, 'photo_tooltip_job') and self.photo_tooltip_job:
            self.root.after_cancel(self.photo_tooltip_job)
            self.photo_tooltip_job = None
        
        # Определяем, на какой строке находится курсор
        item = self.instruments_tree.identify_row(event.y)
        if item:
            # Получаем данные строки
            values = self.instruments_tree.item(item, 'values')
            if values:
                try:
                    instrument_id = int(values[0])  # ID - первый столбец
                    
                    # Проверяем, есть ли фотография для этого инструмента
                    if hasattr(self, 'instrument_photos') and instrument_id in self.instrument_photos:
                        photo_path = self.instrument_photos[instrument_id]
                        if photo_path and os.path.exists(photo_path):
                            # Откладываем показ tooltip на 300мс
                            self.photo_tooltip_job = self.root.after(300, lambda p=photo_path: self._show_photo_tooltip(p))
                            return
                except (ValueError, IndexError):
                    pass
        
        # Если нет фотографии, скрываем tooltip
        self._hide_photo_tooltip()

    def _on_employee_hover(self, event):
        """Обработчик наведения мыши на сотрудника"""
        # Отменяем предыдущую отложенную задачу, если есть
        if hasattr(self, 'photo_tooltip_job') and self.photo_tooltip_job:
            self.root.after_cancel(self.photo_tooltip_job)
            self.photo_tooltip_job = None

        # Определяем, на какой строке находится курсор
        item = self.employees_tree.identify_row(event.y)
        if item:
            # Получаем данные строки
            values = self.employees_tree.item(item, 'values')
            if values:
                try:
                    employee_id = int(values[0])  # ID - первый столбец

                    # Проверяем, есть ли фотография для этого сотрудника
                    if hasattr(self, 'employee_photos') and employee_id in self.employee_photos:
                        photo_path = self.employee_photos[employee_id]
                        if photo_path and os.path.exists(photo_path):
                            # Откладываем показ tooltip на 300мс
                            self.photo_tooltip_job = self.root.after(300, lambda p=photo_path: self._show_photo_tooltip(p))
                            return
                except (ValueError, IndexError):
                    pass

        # Если нет фотографии, скрываем tooltip
        self._hide_photo_tooltip()

    def _on_employee_leave(self, event):
        """Обработчик ухода мыши с таблицы сотрудников"""
        # Отменяем отложенную задачу показа tooltip
        if hasattr(self, 'photo_tooltip_job') and self.photo_tooltip_job:
            self.root.after_cancel(self.photo_tooltip_job)
            self.photo_tooltip_job = None
        self._hide_photo_tooltip()

    def _on_instrument_leave(self, event):
        """Обработчик ухода мыши с таблицы инструментов"""
        # Отменяем отложенную задачу показа tooltip
        if hasattr(self, 'photo_tooltip_job') and self.photo_tooltip_job:
            self.root.after_cancel(self.photo_tooltip_job)
            self.photo_tooltip_job = None
        self._hide_photo_tooltip()
    
    def _show_photo_tooltip(self, photo_path):
        """Показ всплывающего окна с фотографией"""
        # Удаляем предыдущее окно, если есть
        self._hide_photo_tooltip()
        
        try:
            from PIL import Image, ImageTk
            
            # Загружаем и изменяем размер изображения
            img = Image.open(photo_path)
            # Увеличиваем размер для tooltip (500x500 пикселей)
            img.thumbnail((500, 500), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            # Создаем всплывающее окно
            self.photo_tooltip = tk.Toplevel(self.root)
            self.photo_tooltip.overrideredirect(True)  # Убираем рамку окна
            self.photo_tooltip.attributes('-topmost', True)  # Поверх всех окон
            
            # Создаем Label с фотографией
            photo_label = tk.Label(self.photo_tooltip, image=photo, bg='white', relief='solid', borderwidth=2)
            photo_label.image = photo  # Сохраняем ссылку
            photo_label.pack()
            
            # Позиционируем окно рядом с курсором
            x = self.root.winfo_pointerx() + 20
            y = self.root.winfo_pointery() + 20
            
            # Проверяем, чтобы окно не выходило за границы экрана
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Учитываем новый размер (500x500)
            tooltip_width = 500
            tooltip_height = 500
            
            if x + tooltip_width > screen_width:
                x = self.root.winfo_pointerx() - tooltip_width - 20
            if y + tooltip_height > screen_height:
                y = self.root.winfo_pointery() - tooltip_height - 20
            
            self.photo_tooltip.geometry(f"+{x}+{y}")
            
        except Exception as e:
            # Если не удалось загрузить изображение, просто не показываем tooltip
            pass
    
    def _hide_photo_tooltip(self):
        """Скрытие всплывающего окна с фотографией"""
        if hasattr(self, 'photo_tooltip') and self.photo_tooltip:
            try:
                self.photo_tooltip.destroy()
            except:
                pass
            self.photo_tooltip = None

    def _on_instrument_double_click(self, event):
        """Обработчик двойного клика на инструменте для редактирования"""
        # Определяем, на какой строке был двойной клик
        item = self.instruments_tree.identify_row(event.y)
        if item:
            # Получаем данные строки
            values = self.instruments_tree.item(item, 'values')
            if values:
                try:
                    instrument_id = int(values[0])  # ID - первый столбец
                    # Открываем диалог редактирования
                    EditInstrumentDialog(self.root, self.db, instrument_id, self.load_instruments)
                except (ValueError, IndexError):
                    pass

    def _on_employee_double_click(self, event):
        """Обработчик двойного клика на сотруднике для редактирования"""
        # Определяем, на какой строке был двойной клик
        item = self.employees_tree.identify_row(event.y)
        if item:
            # Получаем данные строки
            values = self.employees_tree.item(item, 'values')
            if values:
                try:
                    employee_id = int(values[0])  # ID - первый столбец
                    # Открываем диалог редактирования
                    EditEmployeeDialog(self.root, self.db, employee_id, self.load_employees)
                except (ValueError, IndexError):
                    pass

    def _on_return_hover(self, event):
        """Обработчик наведения мыши на инструмент в закладке возврата"""
        # Отменяем предыдущую отложенную задачу, если есть
        if hasattr(self, 'photo_tooltip_job') and self.photo_tooltip_job:
            self.root.after_cancel(self.photo_tooltip_job)
            self.photo_tooltip_job = None
        
        # Определяем, на какой строке находится курсор
        item = self.returns_tree.identify_row(event.y)
        if item:
            # Получаем данные строки
            values = self.returns_tree.item(item, 'values')
            if values:
                try:
                    # Получаем ID выдачи (первый столбец)
                    issue_id = int(values[0])
                    
                    # Получаем instrument_id из словаря соответствий
                    if hasattr(self, 'return_issue_to_instrument') and issue_id in self.return_issue_to_instrument:
                        instrument_id = self.return_issue_to_instrument[issue_id]
                        
                        # Проверяем, есть ли фотография для этого инструмента
                        if hasattr(self, 'return_instrument_photos') and instrument_id in self.return_instrument_photos:
                            photo_path = self.return_instrument_photos[instrument_id]
                            if photo_path and os.path.exists(photo_path):
                                # Откладываем показ tooltip на 300мс
                                self.photo_tooltip_job = self.root.after(300, lambda p=photo_path: self._show_photo_tooltip(p))
                                return
                except (ValueError, IndexError, TypeError):
                    pass
        
        # Если нет фотографии, скрываем tooltip
        self._hide_photo_tooltip()
    
    def _on_return_leave(self, event):
        """Обработчик ухода мыши с таблицы возвратов"""
        # Отменяем отложенную задачу показа tooltip
        if hasattr(self, 'photo_tooltip_job') and self.photo_tooltip_job:
            self.root.after_cancel(self.photo_tooltip_job)
            self.photo_tooltip_job = None
        self._hide_photo_tooltip()
    
    def _on_issue_hover(self, event):
        """Обработчик наведения мыши на инструмент в закладке выдачи"""
        # Отменяем предыдущую отложенную задачу, если есть
        if hasattr(self, 'photo_tooltip_job') and self.photo_tooltip_job:
            self.root.after_cancel(self.photo_tooltip_job)
            self.photo_tooltip_job = None
        
        # Определяем, на какой строке находится курсор
        item = self.issues_tree.identify_row(event.y)
        if item:
            # Получаем данные строки
            values = self.issues_tree.item(item, 'values')
            if values:
                try:
                    # Получаем ID выдачи (первый столбец)
                    issue_id = int(values[0])
                    
                    # Получаем instrument_id из словаря соответствий
                    if hasattr(self, 'issue_issue_to_instrument') and issue_id in self.issue_issue_to_instrument:
                        instrument_id = self.issue_issue_to_instrument[issue_id]
                        
                        # Проверяем, есть ли фотография для этого инструмента
                        if hasattr(self, 'issue_instrument_photos') and instrument_id in self.issue_instrument_photos:
                            photo_path = self.issue_instrument_photos[instrument_id]
                            if photo_path and os.path.exists(photo_path):
                                # Откладываем показ tooltip на 300мс
                                self.photo_tooltip_job = self.root.after(300, lambda p=photo_path: self._show_photo_tooltip(p))
                                return
                except (ValueError, IndexError, TypeError):
                    pass
        
        # Если нет фотографии, скрываем tooltip
        self._hide_photo_tooltip()
    
    def _on_issue_leave(self, event):
        """Обработчик ухода мыши с таблицы выдач"""
        # Отменяем отложенную задачу показа tooltip
        if hasattr(self, 'photo_tooltip_job') and self.photo_tooltip_job:
            self.root.after_cancel(self.photo_tooltip_job)
            self.photo_tooltip_job = None
        self._hide_photo_tooltip()
    
    def backup_database(self):
        """Создание резервной копии базы данных"""
        try:
            db_path = 'tool_management.db'
            if not os.path.exists(db_path):
                messagebox.showerror("Ошибка", "База данных не найдена!")
                return
            
            # Диалог выбора места сохранения
            filename = filedialog.asksaveasfilename(
                defaultextension=".db",
                filetypes=[
                    ("Database files", "*.db"),
                    ("Backup files", "*.backup"),
                    ("All files", "*.*")
                ],
                title="Сохранить резервную копию базы данных",
                initialfile=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            )
            
            if not filename:
                return  # Пользователь отменил
            
            # Копируем файл базы данных
            shutil.copy2(db_path, filename)
            
            # Получаем размер файла
            file_size = os.path.getsize(filename) / (1024 * 1024)  # Размер в МБ
            
            messagebox.showinfo(
                "Успех",
                f"Резервная копия успешно создана!\n\n"
                f"Файл: {filename}\n"
                f"Размер: {file_size:.2f} МБ"
            )
        except Exception as e:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось создать резервную копию:\n{str(e)}"
            )
    
    def restore_database(self):
        """Восстановление базы данных из резервной копии"""
        try:
            # Предупреждение пользователя
            if not messagebox.askyesno(
                "Предупреждение",
                "Восстановление базы данных заменит текущую базу данных.\n\n"
                "Рекомендуется создать резервную копию текущей базы данных перед восстановлением.\n\n"
                "Продолжить?"
            ):
                return
            
            # Диалог выбора файла резервной копии
            filename = filedialog.askopenfilename(
                defaultextension=".db",
                filetypes=[
                    ("Database files", "*.db"),
                    ("Backup files", "*.backup"),
                    ("All files", "*.*")
                ],
                title="Выберите файл резервной копии для восстановления"
            )
            
            if not filename:
                return  # Пользователь отменил
            
            if not os.path.exists(filename):
                messagebox.showerror("Ошибка", "Выбранный файл не существует!")
                return
            
            # Проверяем, что это действительно файл базы данных SQLite
            try:
                test_conn = sqlite3.connect(filename)
                test_conn.close()
            except sqlite3.Error:
                messagebox.showerror(
                    "Ошибка",
                    "Выбранный файл не является корректной базой данных SQLite!"
                )
                return
            
            db_path = 'tool_management.db'
            
            # Создаем резервную копию текущей базы данных перед восстановлением
            backup_path = f"tool_management_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_path)
            
            # Закрываем все возможные соединения с базой данных
            # SQLite автоматически закроет соединения при замене файла
            
            # Копируем резервную копию на место основной базы данных
            shutil.copy2(filename, db_path)
            
            # Пересоздаем соединение с базой данных
            self.db = DatabaseManager()
            
            # Обновляем все таблицы
            self.load_instruments()
            self.load_employees()
            self.load_active_issues()
            self.load_active_issues_for_return()
            self.load_history()
            self.load_addresses()
            
            messagebox.showinfo(
                "Успех",
                f"База данных успешно восстановлена из резервной копии!\n\n"
                f"Файл: {filename}\n\n"
                f"Текущая база данных сохранена как: {backup_path}"
            )
        except Exception as e:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось восстановить базу данных:\n{str(e)}\n\n"
                f"Попробуйте перезапустить приложение."
            )
            # Пытаемся пересоздать соединение с базой данных
            try:
                self.db = DatabaseManager()
            except:
                pass
    
    def export_to_csv(self):
        """Экспорт данных в CSV формат"""
        try:
            # Диалог выбора места сохранения
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("All files", "*.*")
                ],
                title="Экспорт данных в CSV",
                initialfile=f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            
            if not filename:
                return  # Пользователь отменил
            
            import csv
            
            # Получаем данные из всех таблиц
            data_to_export = []
            
            # Инструменты
            instruments = self.db.get_instruments()
            data_to_export.append(("=== ИНСТРУМЕНТЫ ===",))
            data_to_export.append(("ID", "Название", "Инв. номер", "Серийный номер", "Категория", "Статус"))
            for inst in instruments:
                data_to_export.append(inst[:6])  # Без photo_path
            
            data_to_export.append(())  # Пустая строка
            
            # Сотрудники
            employees = self.db.get_employees()
            data_to_export.append(("=== СОТРУДНИКИ ===",))
            data_to_export.append(("ID", "ФИО", "Должность", "Отдел", "Телефон", "Email", "Статус"))
            for emp in employees:
                data_to_export.append(emp[:7])  # Без photo_path
            
            data_to_export.append(())  # Пустая строка
            
            # Выдачи
            issues = self.db.get_active_issues()
            data_to_export.append(("=== ВЫДАЧИ ===",))
            data_to_export.append(("ID", "Инв. номер", "Инструмент", "Сотрудник", "Адрес", "Дата выдачи", "Ожид. возврат", "Выдал", "Примечание"))
            for issue in issues:
                # Форматируем данные выдачи
                row = (
                    issue[0],  # ID
                    issue[2] if len(issue) > 2 else '',  # Инв. номер
                    issue[3] if len(issue) > 3 else '',  # Инструмент
                    issue[4] if len(issue) > 4 else '',  # Сотрудник
                    issue[5] if len(issue) > 5 else '',  # Адрес
                    issue[6] if len(issue) > 6 else '',  # Дата выдачи
                    issue[7] if len(issue) > 7 else '',  # Ожид. возврат
                    issue[8] if len(issue) > 8 else '',  # Выдал
                    issue[9] if len(issue) > 9 else ''   # Примечание
                )
                data_to_export.append(row)
            
            # Записываем в CSV файл
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                for row in data_to_export:
                    writer.writerow(row)
            
            messagebox.showinfo(
                "Успех",
                f"Данные успешно экспортированы в CSV!\n\n"
                f"Файл: {filename}"
            )
        except Exception as e:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось экспортировать данные:\n{str(e)}"
            )
    
    def import_from_csv(self):
        """Импорт данных из CSV файла с проверкой дубликатов"""
        try:
            # Диалог выбора файла
            filename = filedialog.askopenfilename(
                defaultextension=".csv",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("All files", "*.*")
                ],
                title="Импорт данных из CSV"
            )
            
            if not filename:
                return  # Пользователь отменил
            
            if not os.path.exists(filename):
                messagebox.showerror("Ошибка", "Выбранный файл не существует!")
                return
            
            import csv
            
            # Читаем CSV файл
            with open(filename, 'r', encoding='utf-8-sig') as csvfile:
                reader = csv.reader(csvfile, delimiter=';')
                rows = list(reader)
            
            if not rows:
                messagebox.showwarning("Предупреждение", "Файл пуст!")
                return
            
            # Парсим данные
            instruments_data = []
            employees_data = []
            current_section = None
            
            for row in rows:
                if not row or not row[0]:
                    continue
                
                # Определяем секцию
                if row[0].startswith('===') and 'ИНСТРУМЕНТЫ' in row[0]:
                    current_section = 'instruments'
                    continue
                elif row[0].startswith('===') and 'СОТРУДНИКИ' in row[0]:
                    current_section = 'employees'
                    continue
                elif row[0].startswith('===') and 'ВЫДАЧИ' in row[0]:
                    current_section = 'issues'
                    continue
                
                # Пропускаем заголовки
                if row[0] in ['ID', 'id'] or 'ID' in row[0]:
                    continue
                
                # Добавляем данные в соответствующий список
                if current_section == 'instruments' and len(row) >= 6:
                    instruments_data.append({
                        'name': row[1].strip() if len(row) > 1 else '',
                        'inventory_number': row[2].strip() if len(row) > 2 else '',
                        'serial_number': row[3].strip() if len(row) > 3 else '',
                        'category': row[4].strip() if len(row) > 4 else '',
                        'status': row[5].strip() if len(row) > 5 else 'Доступен'
                    })
                elif current_section == 'employees' and len(row) >= 7:
                    employees_data.append({
                        'full_name': row[1].strip() if len(row) > 1 else '',
                        'position': row[2].strip() if len(row) > 2 else '',
                        'department': row[3].strip() if len(row) > 3 else '',
                        'phone': row[4].strip() if len(row) > 4 else '',
                        'email': row[5].strip() if len(row) > 5 else '',
                        'status': row[6].strip() if len(row) > 6 else 'Активен'
                    })
            
            # Статистика импорта
            stats = {
                'instruments': {'added': 0, 'skipped': 0, 'errors': 0},
                'employees': {'added': 0, 'skipped': 0, 'errors': 0}
            }
            
            # Получаем существующие данные для проверки дубликатов
            existing_instruments = self.db.get_instruments()
            existing_inventory_numbers = {inst[2] for inst in existing_instruments if inst[2]}  # Инвентарные номера
            
            existing_employees = self.db.get_employees()
            existing_employee_names = {emp[1].lower() for emp in existing_employees if emp[1]}  # ФИО в нижнем регистре
            
            # Импортируем инструменты
            for inst_data in instruments_data:
                if not inst_data['name'] or not inst_data['inventory_number']:
                    stats['instruments']['errors'] += 1
                    continue
                
                # Проверка дубликата по инвентарному номеру
                if inst_data['inventory_number'] in existing_inventory_numbers:
                    stats['instruments']['skipped'] += 1
                    continue
                
                # Добавляем инструмент
                try:
                    # Формируем кортеж данных для add_instrument
                    data_tuple = (
                        inst_data['name'],
                        '',  # description
                        inst_data['inventory_number'],
                        inst_data['serial_number'],
                        inst_data['category'],
                        inst_data['status'] if inst_data['status'] in ['Доступен', 'Выдан', 'На ремонте', 'Списан'] else 'Доступен',
                        None  # photo_path
                    )
                    success = self.db.add_instrument(data_tuple)
                    if success:
                        stats['instruments']['added'] += 1
                        existing_inventory_numbers.add(inst_data['inventory_number'])  # Добавляем в список существующих
                    else:
                        stats['instruments']['errors'] += 1
                except Exception as e:
                    stats['instruments']['errors'] += 1
            
            # Импортируем сотрудников
            for emp_data in employees_data:
                if not emp_data['full_name']:
                    stats['employees']['errors'] += 1
                    continue
                
                # Проверка дубликата по ФИО (без учета регистра)
                if emp_data['full_name'].lower() in existing_employee_names:
                    stats['employees']['skipped'] += 1
                    continue
                
                # Добавляем сотрудника
                try:
                    # Формируем кортеж данных для add_employee
                    data_tuple = (
                        emp_data['full_name'],
                        emp_data['position'],
                        emp_data['department'],
                        emp_data['phone'],
                        emp_data['email'],
                        emp_data['status'] if emp_data['status'] in ['Активен', 'Уволен'] else 'Активен',
                        None  # photo_path
                    )
                    success = self.db.add_employee(data_tuple)
                    if success:
                        stats['employees']['added'] += 1
                        existing_employee_names.add(emp_data['full_name'].lower())  # Добавляем в список существующих
                    else:
                        stats['employees']['errors'] += 1
                except Exception as e:
                    stats['employees']['errors'] += 1
            
            # Обновляем таблицы
            self.load_instruments()
            self.load_employees()
            
            # Показываем результаты
            result_message = "Импорт завершен!\n\n"
            
            if instruments_data:
                result_message += f"Инструменты:\n"
                result_message += f"  Добавлено: {stats['instruments']['added']}\n"
                result_message += f"  Пропущено (дубликаты): {stats['instruments']['skipped']}\n"
                result_message += f"  Ошибок: {stats['instruments']['errors']}\n\n"
            
            if employees_data:
                result_message += f"Сотрудники:\n"
                result_message += f"  Добавлено: {stats['employees']['added']}\n"
                result_message += f"  Пропущено (дубликаты): {stats['employees']['skipped']}\n"
                result_message += f"  Ошибок: {stats['employees']['errors']}\n"
            
            if stats['instruments']['added'] == 0 and stats['employees']['added'] == 0:
                if stats['instruments']['skipped'] > 0 or stats['employees']['skipped'] > 0:
                    messagebox.showwarning("Импорт", result_message)
                else:
                    messagebox.showwarning("Импорт", "Не удалось импортировать данные. Проверьте формат файла.")
            else:
                messagebox.showinfo("Импорт", result_message)
                
        except Exception as e:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось импортировать данные:\n{str(e)}"
            )
    
    def show_about(self):
        """Показ информации о программе"""
        about_text = (
            "Журнал учета выдачи и возврата инструмента\n\n"
            "Версия: 1.0\n\n"
            "Приложение для учета выдачи и возврата инструментов\n"
            "с поддержкой экспорта данных и резервного копирования.\n\n"
            "Создано с помощью Python и tkinter\n\n"
            "Автор: Андрей Орлов\n\n"
            "Email: andrew_metal@mail.ru\n\n"
            "GitHub: https://github.com/inpredservice11-beep/Instruments"
        )
        messagebox.showinfo("О программе", about_text)

    def configure_telegram_bot(self):
        """Настройка Telegram бота"""
        import os

        # Создаем диалог настройки
        dialog = tk.Toplevel(self.root)
        dialog.title("Настройки Telegram бота")
        dialog.geometry("550x500")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # Центрируем диалог
        dialog.geometry("+{}+{}".format(
            self.root.winfo_x() + (self.root.winfo_width() - 550) // 2,
            self.root.winfo_y() + (self.root.winfo_height() - 500) // 2
        ))

        # Создаем фрейм с отступами
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        ttk.Label(main_frame, text="Настройки Telegram бота",
                 font=("Arial", 12, "bold")).pack(pady=(0, 20))

        # Инструкция
        instruction_text = (
            "1. Создайте бота в Telegram:\n"
            "   • Напишите @BotFather\n"
            "   • Отправьте /newbot\n"
            "   • Следуйте инструкциям\n\n"
            "2. Скопируйте токен бота\n\n"
            "3. Вставьте токен ниже:"
        )

        ttk.Label(main_frame, text=instruction_text, justify=tk.LEFT).pack(pady=(0, 15))

        # Поле для токена
        token_frame = ttk.Frame(main_frame)
        token_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(token_frame, text="Токен бота:").pack(anchor=tk.W)
        # Загружаем токен из файла или переменной окружения
        saved_token = self._load_telegram_token() or os.getenv('TELEGRAM_BOT_TOKEN', '')
        token_var = tk.StringVar(value=saved_token)
        token_entry = ttk.Entry(token_frame, textvariable=token_var, width=50)
        token_entry.pack(fill=tk.X, pady=(5, 0))

        # Добавляем поддержку горячих клавиш
        def handle_key_press(event):
            # Ctrl+V для вставки
            if event.state & 0x4 and event.keysym.lower() == 'v':
                try:
                    clipboard_text = dialog.clipboard_get()
                    current_text = token_var.get()
                    cursor_pos = token_entry.index(tk.INSERT)
                    new_text = current_text[:cursor_pos] + clipboard_text + current_text[cursor_pos:]
                    token_var.set(new_text)
                    token_entry.icursor(cursor_pos + len(clipboard_text))
                    return "break"
                except:
                    pass
            # Ctrl+A для выделения всего текста
            elif event.state & 0x4 and event.keysym.lower() == 'a':
                token_entry.select_range(0, tk.END)
                token_entry.icursor(tk.END)
                return "break"
            # Ctrl+X для вырезания
            elif event.state & 0x4 and event.keysym.lower() == 'x':
                try:
                    if token_entry.selection_present():
                        selected_text = token_entry.selection_get()
                        dialog.clipboard_clear()
                        dialog.clipboard_append(selected_text)
                        # Удаляем выделенный текст
                        start = token_entry.index(tk.SEL_FIRST)
                        end = token_entry.index(tk.SEL_LAST)
                        current_text = token_var.get()
                        new_text = current_text[:int(start)] + current_text[int(end):]
                        token_var.set(new_text)
                        token_entry.icursor(int(start))
                    return "break"
                except:
                    pass
            # Ctrl+C для копирования
            elif event.state & 0x4 and event.keysym.lower() == 'c':
                try:
                    if token_entry.selection_present():
                        selected_text = token_entry.selection_get()
                        dialog.clipboard_clear()
                        dialog.clipboard_append(selected_text)
                    return "break"
                except:
                    pass
            return None

        token_entry.bind('<Key>', handle_key_press)

        # Добавляем контекстное меню
        def show_context_menu(event):
            try:
                menu = tk.Menu(dialog, tearoff=0)
                menu.add_command(label="Вырезать", command=lambda: cut_selection())
                menu.add_command(label="Копировать", command=lambda: copy_selection())
                menu.add_command(label="Вставить", command=lambda: paste_from_clipboard())
                menu.add_separator()
                menu.add_command(label="Выделить все", command=lambda: select_all_text())
                menu.tk_popup(event.x_root, event.y_root)
            except:
                pass

        def cut_selection():
            try:
                if token_entry.selection_present():
                    selected_text = token_entry.selection_get()
                    dialog.clipboard_clear()
                    dialog.clipboard_append(selected_text)
                    # Удаляем выделенный текст
                    start = token_entry.index(tk.SEL_FIRST)
                    end = token_entry.index(tk.SEL_LAST)
                    current_text = token_var.get()
                    new_text = current_text[:int(start)] + current_text[int(end):]
                    token_var.set(new_text)
                    token_entry.icursor(int(start))
            except:
                pass

        def copy_selection():
            try:
                if token_entry.selection_present():
                    selected_text = token_entry.selection_get()
                    dialog.clipboard_clear()
                    dialog.clipboard_append(selected_text)
            except:
                pass

        def select_all_text():
            token_entry.select_range(0, tk.END)
            token_entry.focus_set()

        def paste_from_clipboard():
            try:
                clipboard_text = dialog.clipboard_get()
                current_text = token_var.get()
                cursor_pos = token_entry.index(tk.INSERT)
                new_text = current_text[:cursor_pos] + clipboard_text + current_text[cursor_pos:]
                token_var.set(new_text)
                token_entry.icursor(cursor_pos + len(clipboard_text))
            except:
                pass

        token_entry.bind('<Button-3>', show_context_menu)  # Правая кнопка мыши

        # Статус бота
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        if self.telegram_bot:
            status_text = "✅ Бот активен"
            status_color = "green"
        else:
            status_text = "❌ Бот не настроен"
            status_color = "red"

        status_label = ttk.Label(status_frame, text=f"Статус: {status_text}", foreground=status_color)
        status_label.pack(anchor=tk.W)

        # Разделитель
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=(20, 10))

        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 20))

        def save_token():
            token = token_var.get().strip()
            if token:
                # Сохраняем токен в файл конфигурации
                try:
                    self._save_telegram_token(token)
                    print(f"✅ Токен Telegram бота сохранен")
                except Exception as save_e:
                    messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить токен: {save_e}")
                    return

                # Сохраняем токен в переменную окружения для текущего сеанса
                os.environ['TELEGRAM_BOT_TOKEN'] = token

                # Перезапускаем бота если возможно
                try:
                    from telegram_bot import init_telegram_bot, start_telegram_bot
                    if self.telegram_bot:
                        # Здесь можно добавить логику перезапуска бота
                        pass

                    new_bot = init_telegram_bot(token)
                    if new_bot:
                        bot_thread = start_telegram_bot()
                        if bot_thread:
                            self.telegram_bot = new_bot
                            status_label.config(text="Статус: ✅ Бот активен", foreground="green")
                            messagebox.showinfo("Успех", "Telegram бот настроен и запущен!")
                        else:
                            status_label.config(text="Статус: ❌ Ошибка запуска", foreground="red")
                    else:
                        status_label.config(text="Статус: ❌ Ошибка инициализации", foreground="red")

                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось запустить бота: {e}")
                    status_label.config(text="Статус: ❌ Ошибка", foreground="red")
            else:
                messagebox.showwarning("Предупреждение", "Введите токен бота")

        def test_bot():
            if self.telegram_bot:
                messagebox.showinfo("Тест", "Бот активен! Отправьте /start в Telegram чат с ботом.")
            else:
                messagebox.showwarning("Тест", "Бот не активен. Настройте токен и сохраните.")

        ttk.Button(button_frame, text="Сохранить и запустить", command=save_token).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Button(button_frame, text="Тестировать", command=test_bot).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Button(button_frame, text="Закрыть", command=dialog.destroy).pack(side=tk.RIGHT)

        # Фокус на поле токена
        token_entry.focus_set()

    def configure_notifications(self):
        """Настройка системы уведомлений"""
        if not self.notification_manager:
            messagebox.showwarning("Предупреждение", "Система уведомлений не инициализирована")
            return

        # Создаем диалог настройки
        dialog = tk.Toplevel(self.root)
        dialog.title("Настройки уведомлений")
        dialog.geometry("500x500")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # Центрируем диалог
        dialog.geometry("+{}+{}".format(
            self.root.winfo_x() + (self.root.winfo_width() - 500) // 2,
            self.root.winfo_y() + (self.root.winfo_height() - 500) // 2
        ))

        # Создаем фрейм с отступами
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        ttk.Label(main_frame, text="Настройки уведомлений",
                 font=("Arial", 12, "bold")).pack(pady=(0, 20))

        # Получаем текущие настройки
        settings = self.notification_manager.settings

        # Фрейм для настроек
        settings_frame = ttk.LabelFrame(main_frame, text="Общие настройки", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 20))

        # Переменные для чекбоксов
        desktop_var = tk.BooleanVar(value=settings.get('enable_desktop_notifications', True))
        telegram_var = tk.BooleanVar(value=settings.get('enable_telegram_notifications', True))

        # Чекбоксы настроек
        ttk.Checkbutton(settings_frame, text="Включить desktop уведомления",
                        variable=desktop_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(settings_frame, text="Включить Telegram уведомления",
                        variable=telegram_var).pack(anchor=tk.W, pady=2)

        # Фрейм для настроек сроков
        timing_frame = ttk.LabelFrame(main_frame, text="Настройки сроков", padding="10")
        timing_frame.pack(fill=tk.X, pady=(0, 20))

        # Поля для настройки дней
        ttk.Label(timing_frame, text="Предупреждать за дней до просрочки:").pack(anchor=tk.W)
        warning_days_var = tk.IntVar(value=settings.get('overdue_warning_days', 1))
        warning_spin = tk.Spinbox(timing_frame, from_=0, to=30, textvariable=warning_days_var, width=5)
        warning_spin.pack(anchor=tk.W, pady=(0, 10))

        ttk.Label(timing_frame, text="Критическая просрочка через дней:").pack(anchor=tk.W)
        critical_days_var = tk.IntVar(value=settings.get('overdue_critical_days', 3))
        critical_spin = tk.Spinbox(timing_frame, from_=1, to=30, textvariable=critical_days_var, width=5)
        critical_spin.pack(anchor=tk.W, pady=(0, 10))

        # Статус системы уведомлений
        status_frame = ttk.LabelFrame(main_frame, text="Статус системы", padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 20))

        # Получаем информацию о просрочках
        overdue_summary = self.notification_manager.get_overdue_summary()

        status_text = f"""Система уведомлений: {'✅ Активна' if self.notification_manager.is_running else '❌ Не активна'}

Текущая статистика:
• Просроченных возвратов: {overdue_summary['total_overdue']}
• Критических просрочек: {overdue_summary['critical_overdue']}
• Предстоящих возвратов: {overdue_summary['upcoming_deadlines']}

Интервал проверки: {self.notification_manager.check_interval // 60} мин"""

        status_label = ttk.Label(status_frame, text=status_text, justify=tk.LEFT)
        status_label.pack(anchor=tk.W)

        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        def save_settings():
            new_settings = {
                'enable_desktop_notifications': desktop_var.get(),
                'enable_telegram_notifications': telegram_var.get(),
                'overdue_warning_days': warning_days_var.get(),
                'overdue_critical_days': critical_days_var.get(),
            }

            self.notification_manager.update_settings(new_settings)
            messagebox.showinfo("Успех", "Настройки уведомлений сохранены!")
            dialog.destroy()

        def test_notification():
            # Тестируем уведомление
            test_message = "🔔 Это тестовое уведомление!\n\nСистема уведомлений работает корректно."
            self.notification_manager._show_desktop_notification("Тест уведомления", test_message)
            messagebox.showinfo("Тест", "Тестовое уведомление отправлено!")

        ttk.Button(button_frame, text="Сохранить настройки", command=save_settings).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Тест уведомления", command=test_notification).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Закрыть", command=dialog.destroy).pack(side=tk.RIGHT)

    def change_theme(self, theme_name):
        """Изменение темы интерфейса"""
        if not self.theme_manager:
            messagebox.showwarning("Предупреждение", "Менеджер тем не инициализирован")
            return

        # Проверяем наличие office_colors
        if not hasattr(self, 'office_colors'):
            print("❌ Ошибка: office_colors не инициализирован")
            messagebox.showerror("Ошибка", "Цветовая схема не инициализирована")
            return

        try:
            print(f"🔄 Изменение темы на: {theme_name}")
            if self.theme_manager.set_theme(theme_name):
                print(f"✅ Тема {theme_name} установлена в theme_manager")

                # Обновляем office_colors на основе новой темы
                theme_colors = self.theme_manager.get_current_theme()
                print(f"🎨 Получены цвета темы: {theme_colors.get('name', 'неизвестная')}")

                self.office_colors.update({
                    'bg_white': theme_colors.get('tree_bg', '#ffffff'),
                    'bg_main': theme_colors.get('bg', '#f0f0f0'),
                    'bg_header': theme_colors.get('tree_heading_bg', '#e8e8e8'),
                    'bg_header_light': theme_colors.get('notebook_active', '#f0f0f0'),
                    'bg_selected': theme_colors.get('tree_selected', '#cce4ff'),
                    'bg_hover': theme_colors.get('button_hover', '#f0f0f0'),
                    'hover': theme_colors.get('button_hover', '#f0f0f0'),
                    'fg_main': theme_colors.get('tree_fg', '#000000'),
                    'fg_secondary': theme_colors.get('fg', '#666666'),
                    'fg_header': theme_colors.get('tree_heading_fg', '#000000'),
                    'selected': theme_colors.get('accent', '#0078d4'),
                    'border': theme_colors.get('border', '#c0c0c0'),
                    'overdue': theme_colors.get('error', '#ffcccc'),
                    'warning': theme_colors.get('warning', '#ffffcc'),
                    'success': theme_colors.get('success', '#ccffcc')
                })
                print("🎨 office_colors обновлены")

                # Перерисовываем интерфейс с новыми цветами
                print("🔄 Обновление интерфейса...")
                self._update_interface_colors()

                # Применяем новую тему через theme_manager
                from theme_manager import apply_theme_to_app
                apply_theme_to_app(self.root)
                print("🎨 apply_theme_to_app выполнен")

                theme_names = {
                    'light': 'светлая',
                    'dark': 'темная'
                }
                theme_display_name = theme_names.get(theme_name, theme_name)

                print(f"✅ Тема изменена на {theme_display_name}")
                # Не показываем messagebox для быстрого переключения
            else:
                print(f"❌ Неизвестная тема: {theme_name}")
                messagebox.showerror("Ошибка", f"Неизвестная тема: {theme_name}")
        except Exception as e:
            print(f"❌ Ошибка изменения темы: {e}")
            import traceback
            print(f"📋 Подробности ошибки:\n{traceback.format_exc()}")
            messagebox.showerror("Ошибка", f"Не удалось изменить тему: {e}")

    def _save_telegram_token(self, token):
        """Сохранение токена Telegram бота в файл"""
        import json
        import os
        try:
            config_file = 'telegram_config.json'
            config = {'telegram_bot_token': token}

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            print(f"✅ Токен сохранен в {config_file}")
        except Exception as e:
            print(f"❌ Ошибка сохранения токена: {e}")
            raise

    def _load_telegram_token(self):
        """Загрузка токена Telegram бота из файла"""
        import json
        import os
        try:
            config_file = 'telegram_config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    token = config.get('telegram_bot_token')
                    if token:
                        # Устанавливаем в переменную окружения
                        os.environ['TELEGRAM_BOT_TOKEN'] = token
                        print(f"✅ Токен загружен из {config_file}")
                        return token
        except Exception as e:
            print(f"⚠️ Ошибка загрузки токена: {e}")

        return None

    def _update_interface_colors(self):
        """Обновление цветов интерфейса при смене темы"""
        # Проверяем наличие office_colors
        if not hasattr(self, 'office_colors'):
            print("❌ Ошибка: office_colors не инициализирован в _update_interface_colors")
            return

        try:
            # Обновляем основной фон
            self.root.configure(bg=self.office_colors['bg_main'])

            # Обновляем header и toolbar
            for widget in self.root.winfo_children():
                if isinstance(widget, tk.Frame):
                    # Header frame
                    if hasattr(widget, 'cget') and widget.cget('height') == 60:
                        widget.configure(bg=self.office_colors['bg_header'])
                        for child in widget.winfo_children():
                            if isinstance(child, tk.Label):
                                child.configure(bg=self.office_colors['bg_header'], fg=self.office_colors['fg_header'])

                    # Toolbar frame
                    elif hasattr(widget, 'cget') and widget.cget('height') == 50:
                        widget.configure(bg=self.office_colors['bg_white'])
                        for child in widget.winfo_children():
                            if isinstance(child, tk.Frame):
                                child.configure(bg=self.office_colors['bg_white'])

                    # Separator
                    elif hasattr(widget, 'cget') and widget.cget('height') == 1:
                        widget.configure(bg=self.office_colors['border'])

            # Обновляем цвета вкладок
            for tab_id in self.notebook.tabs():
                tab = self.notebook.nametowidget(tab_id)
                if tab:
                    tab.configure(bg=self.office_colors['bg_white'])
                    # Рекурсивно обновляем все дочерние элементы вкладки
                    self._update_widget_colors_recursive(tab)

            # Обновляем цвета в областях статистики
            self._update_stats_colors()

            # Обновляем цвета в диалогах (если они открыты)
            self._update_dialog_colors()

        except Exception as e:
            print(f"Ошибка обновления цветов интерфейса: {e}")

    def _update_widget_colors_recursive(self, widget):
        """Рекурсивное обновление цветов виджетов"""
        # Проверяем наличие office_colors
        if not hasattr(self, 'office_colors'):
            return

        try:
            if isinstance(widget, tk.Frame):
                widget.configure(bg=self.office_colors['bg_white'])
            elif isinstance(widget, tk.Label):
                widget.configure(bg=self.office_colors['bg_white'], fg=self.office_colors['fg_main'])
            elif isinstance(widget, tk.Button):
                widget.configure(bg=self.office_colors['bg_white'], fg=self.office_colors['fg_main'])
            elif isinstance(widget, tk.Entry):
                widget.configure(bg=self.office_colors['bg_white'], fg=self.office_colors['fg_main'],
                               insertbackground=self.office_colors['fg_main'])
            elif isinstance(widget, tk.Text):
                widget.configure(bg=self.office_colors['bg_white'], fg=self.office_colors['fg_main'])

            # Рекурсивно обрабатываем дочерние виджеты
            for child in widget.winfo_children():
                self._update_widget_colors_recursive(child)

        except:
            pass

    def _update_stats_colors(self):
        """Обновление цветов в области статистики"""
        # Проверяем наличие office_colors
        if not hasattr(self, 'office_colors'):
            return

        try:
            # Находим область статистики и обновляем цвета
            for widget in self.root.winfo_children():
                if isinstance(widget, tk.Frame) and hasattr(widget, 'winfo_children'):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Frame):
                            child.configure(bg=self.office_colors['bg_white'])
                            for subchild in child.winfo_children():
                                if isinstance(subchild, tk.Label):
                                    subchild.configure(bg=self.office_colors['bg_white'], fg=self.office_colors['fg_main'])
        except:
            pass

    def _update_dialog_colors(self):
        """Обновление цветов в открытых диалогах"""
        try:
            # Обновляем цвета в дочерних окнах (диалогах)
            for child in self.root.winfo_children():
                if isinstance(child, tk.Toplevel):
                    try:
                        from theme_manager import apply_theme_to_app
                        apply_theme_to_app(child)
                    except:
                        pass
        except:
            pass

    def toggle_theme(self):
        """Переключение между темами (F11)"""
        if not self.theme_manager:
            return

        try:
            current_theme = self.theme_manager.current_theme
            new_theme = 'dark' if current_theme == 'light' else 'light'
            self.change_theme(new_theme)
        except Exception as e:
            print(f"❌ Ошибка переключения темы: {e}")

    def load_analytics(self):
        """Загрузка данных аналитики"""
        # Этот метод будет вызван при обновлении вкладки аналитики
        pass

    def _create_issues_returns_chart(self, parent):
        """График выдач и возвратов по месяцам"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            import matplotlib.dates as mdates
        except ImportError:
            error_label = tk.Label(
                parent,
                text="Для просмотра графиков установите matplotlib:\npip install matplotlib",
                bg=self.office_colors['bg_white'],
                fg='red',
                font=self.default_font
            )
            error_label.pack(pady=20)
            return

        # Получаем данные
        analytics = self.db.get_analytics_data()
        if not analytics:
            no_data_label = tk.Label(
                parent,
                text="Недостаточно данных для построения графика",
                bg=self.office_colors['bg_white'],
                fg=self.office_colors['fg_secondary'],
                font=self.default_font
            )
            no_data_label.pack(pady=20)
            return

        # Создаем фигуру
        fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
        fig.patch.set_facecolor('white')

        # Устанавливаем единый шрифт Arial для графиков
        plt.rcParams['font.family'] = 'Arial'
        plt.rcParams['font.size'] = 9

        # Подготавливаем данные
        months = []
        issues = []
        returns = []

        # Собираем все месяцы
        all_months = set()
        for month, _ in analytics['issues_by_month']:
            all_months.add(month)
        for month, _ in analytics['returns_by_month']:
            all_months.add(month)

        sorted_months = sorted(list(all_months))

        # Заполняем данные
        for month in sorted_months:
            months.append(month)

            # Выдачи
            issue_count = next((count for m, count in analytics['issues_by_month'] if m == month), 0)
            issues.append(issue_count)

            # Возвраты
            return_count = next((count for m, count in analytics['returns_by_month'] if m == month), 0)
            returns.append(return_count)

        # Строим график
        x = range(len(months))
        ax.bar(x, issues, width=0.35, label='Выдачи', color='#4472C4', alpha=0.8)
        ax.bar([i + 0.35 for i in x], returns, width=0.35, label='Возвраты', color='#ED7D31', alpha=0.8)

        ax.set_xlabel('Месяц')
        ax.set_ylabel('Количество')
        ax.set_title('Выдачи и возвраты по месяцам')
        ax.set_xticks([i + 0.175 for i in x])
        ax.set_xticklabels([month for month in months], rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        # Встраиваем в tkinter
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _create_active_trend_chart(self, parent):
        """График динамики активных выдач"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            import matplotlib.dates as mdates
        except ImportError:
            error_label = tk.Label(
                parent,
                text="Для просмотра графиков установите matplotlib:\npip install matplotlib",
                bg=self.office_colors['bg_white'],
                fg='red',
                font=self.default_font
            )
            error_label.pack(pady=20)
            return

        # Получаем данные
        analytics = self.db.get_analytics_data()
        if not analytics or not analytics['active_issues_trend']:
            no_data_label = tk.Label(
                parent,
                text="Недостаточно данных для построения графика",
                bg=self.office_colors['bg_white'],
                fg=self.office_colors['fg_secondary'],
                font=self.default_font
            )
            no_data_label.pack(pady=20)
            return

        # Создаем фигуру
        fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
        fig.patch.set_facecolor('white')

        # Устанавливаем единый шрифт Arial для графиков
        plt.rcParams['font.family'] = 'Arial'
        plt.rcParams['font.size'] = 9

        # Подготавливаем данные
        dates = []
        active_counts = []

        for date_str, count in analytics['active_issues_trend']:
            dates.append(date_str)
            active_counts.append(count)

        # Строим график
        ax.plot(dates, active_counts, marker='o', linewidth=2, color='#4472C4', markersize=4)
        ax.fill_between(dates, active_counts, alpha=0.3, color='#4472C4')

        ax.set_xlabel('Дата')
        ax.set_ylabel('Количество активных выдач')
        ax.set_title('Динамика активных выдач (последние 30 дней)')
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', rotation=45)

        plt.tight_layout()

        # Встраиваем в tkinter
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _create_overdue_chart(self, parent):
        """Круговая диаграмма просроченных выдач по категориям"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        except ImportError:
            error_label = tk.Label(
                parent,
                text="Для просмотра графиков установите matplotlib:\npip install matplotlib",
                bg=self.office_colors['bg_white'],
                fg='red',
                font=self.default_font
            )
            error_label.pack(pady=20)
            return

        # Получаем данные
        analytics = self.db.get_analytics_data()
        if not analytics or not analytics['overdue_by_category']:
            no_data_label = tk.Label(
                parent,
                text="Нет просроченных выдач",
                bg=self.office_colors['bg_white'],
                fg=self.office_colors['fg_secondary'],
                font=self.default_font
            )
            no_data_label.pack(pady=20)
            return

        # Создаем фигуру
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_facecolor('white')

        # Устанавливаем единый шрифт Arial для графиков
        plt.rcParams['font.family'] = 'Arial'
        plt.rcParams['font.size'] = 9

        # Подготавливаем данные
        categories = [item[0] for item in analytics['overdue_by_category']]
        counts = [item[1] for item in analytics['overdue_by_category']]

        # Строим круговую диаграмму
        wedges, texts, autotexts = ax.pie(counts, labels=categories, autopct='%1.1f%%',
                                         startangle=90, colors=plt.cm.Set3.colors)

        ax.set_title('Просроченные выдачи по категориям')
        ax.axis('equal')  # Делаем круг ровным

        plt.tight_layout()

        # Встраиваем в tkinter
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _create_addresses_chart(self, parent):
        """Столбчатая диаграмма выдач по адресам"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        except ImportError:
            error_label = tk.Label(
                parent,
                text="Для просмотра графиков установите matplotlib:\npip install matplotlib",
                bg=self.office_colors['bg_white'],
                fg='red',
                font=self.default_font
            )
            error_label.pack(pady=20)
            return

        # Получаем данные
        analytics = self.db.get_analytics_data()
        if not analytics or not analytics['issues_by_address']:
            no_data_label = tk.Label(
                parent,
                text="Недостаточно данных для построения графика",
                bg=self.office_colors['bg_white'],
                fg=self.office_colors['fg_secondary'],
                font=self.default_font
            )
            no_data_label.pack(pady=20)
            return

        # Создаем фигуру
        fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
        fig.patch.set_facecolor('white')

        # Устанавливаем единый шрифт Arial для графиков
        plt.rcParams['font.family'] = 'Arial'
        plt.rcParams['font.size'] = 9

        # Подготавливаем данные
        addresses = [item[0] for item in analytics['issues_by_address']]
        counts = [item[1] for item in analytics['issues_by_address']]

        # Строим столбчатую диаграмму
        bars = ax.bar(range(len(addresses)), counts, color='#4472C4', alpha=0.8)

        ax.set_xlabel('Адрес')
        ax.set_ylabel('Количество выдач')
        ax.set_title('Выдачи по адресам (последние 6 месяцев)')
        ax.set_xticks(range(len(addresses)))
        ax.set_xticklabels(addresses, rotation=45, ha='right')
        ax.grid(True, alpha=0.3)

        # Добавляем значения над столбцами
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{count}', ha='center', va='bottom')

        plt.tight_layout()

        # Встраиваем в tkinter
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _create_status_chart(self, parent):
        """Круговая диаграмма статусов инструментов"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        except ImportError:
            error_label = tk.Label(
                parent,
                text="Для просмотра графиков установите matplotlib:\npip install matplotlib",
                bg=self.office_colors['bg_white'],
                fg='red',
                font=self.default_font
            )
            error_label.pack(pady=20)
            return

        # Получаем данные
        analytics = self.db.get_analytics_data()
        if not analytics or not analytics['instrument_status_stats']:
            no_data_label = tk.Label(
                parent,
                text="Недостаточно данных для построения графика",
                bg=self.office_colors['bg_white'],
                fg=self.office_colors['fg_secondary'],
                font=self.default_font
            )
            no_data_label.pack(pady=20)
            return

        # Создаем фигуру
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_facecolor('white')

        # Устанавливаем единый шрифт Arial для графиков
        plt.rcParams['font.family'] = 'Arial'
        plt.rcParams['font.size'] = 9

        # Подготавливаем данные
        statuses = [item[0] for item in analytics['instrument_status_stats']]
        counts = [item[1] for item in analytics['instrument_status_stats']]

        # Строим круговую диаграмму
        wedges, texts, autotexts = ax.pie(counts, labels=statuses, autopct='%1.1f%%',
                                         startangle=90, colors=['#4472C4', '#ED7D31', '#A5A5A5', '#FFC000', '#5B9BD5'])

        ax.set_title('Распределение инструментов по статусам')
        ax.axis('equal')  # Делаем круг ровным

        plt.tight_layout()

        # Встраиваем в tkinter
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


def main():
    root = tk.Tk()
    app = ToolManagementApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

