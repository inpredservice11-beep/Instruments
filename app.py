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

from database_manager import DatabaseManager
from window_config import WindowConfig
from pdf_export import PDFExporter
from dialogs import (
    AddInstrumentDialog, EditInstrumentDialog,
    AddEmployeeDialog, EditEmployeeDialog,
    IssueInstrumentDialog, ReturnInstrumentDialog,
    AddAddressDialog, EditAddressDialog
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
        'columns': ('ID', 'Название', 'Инв. номер', 'Серийный номер', 'Категория', 
                   'Адрес выдачи', 'Статус'),
        'column_widths': {
            'ID': 50, 'Название': 220, 'Инв. номер': 110, 'Серийный номер': 120,
            'Категория': 160, 'Адрес выдачи': 200, 'Статус': 110
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
TREEVIEW_HEIGHT = 20


class ToolManagementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Система учета инструмента")
        
        # Инициализация конфигурации окон
        self.window_config = WindowConfig()
        
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
    
    def setup_office_style(self):
        """Настройка стиля в стиле MS Office"""
        style = ttk.Style()
        
        # Определяем шрифт (Segoe UI для Windows, иначе Arial)
        if platform.system() == 'Windows':
            try:
                # Пробуем использовать Segoe UI
                default_font = ("Segoe UI", 9)
                title_font = ("Segoe UI", 16, "bold")
                tab_font = ("Segoe UI", 11, "bold")
            except:
                default_font = ("Arial", 9)
                title_font = ("Arial", 16, "bold")
                tab_font = ("Arial", 11, "bold")
        else:
            default_font = ("Arial", 9)
            title_font = ("Arial", 16, "bold")
            tab_font = ("Arial", 11, "bold")
        
        self.default_font = default_font
        self.title_font = title_font
        self.tab_font = tab_font
        
        # Цветовая схема MS Office
        self.office_colors = {
            'bg_main': '#f3f3f3',  # Светло-серый фон
            'bg_white': '#ffffff',  # Белый
            'bg_header': '#2b579a',  # Синий заголовок (Office blue)
            'bg_header_light': '#4472c4',  # Светло-синий
            'fg_header': '#4472c4',  # Светло-желтый текст на заголовке
            'fg_main': '#323130',  # Темно-серый текст
            'fg_secondary': '#605e5c',  # Серый текст
            'border': '#d2d0ce',  # Светло-серая граница
            'hover': '#e1dfdd',  # Цвет при наведении
            'selected': '#0078d4',  # Синий выбранный элемент
            'accent': '#0078d4',  # Акцентный синий
        }
        
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
        # Верхняя панель (Header) в стиле MS Office
        header_frame = tk.Frame(self.root, bg=self.office_colors['bg_header'], height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Заголовок приложения
        title_label = tk.Label(
            header_frame,
            text="Система учета выдачи и возврата инструмента",
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
        self.create_instruments_tab()
        self.create_employees_tab()
        self.create_issues_tab()
        self.create_returns_tab()
        self.create_history_tab()
        self.create_addresses_tab()
        self.create_statistics_tab()
    
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
        
        self.instrument_search = self._create_search_widget(control_frame, self.load_instruments)
        self.instruments_tree = self._create_treeview(tab, 'instruments')
        self.tree_mapping['instruments'] = self.instruments_tree
        
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
        
    def create_returns_tab(self):
        """Вкладка возврата инструмента"""
        tab = tk.Frame(self.notebook, bg=self.office_colors['bg_white'])
        self.notebook.add(tab, text="📥 Возврат инструмента")
        
        control_frame = self._create_control_frame(tab)
        
        self._create_button(control_frame, "Оформить возврат", self.return_instrument)
        self._create_button(control_frame, "Обновить", self.load_active_issues_for_return)
        
        self.returns_tree = self._create_treeview(tab, 'returns')
        self.tree_mapping['returns'] = self.returns_tree
        
    def create_history_tab(self):
        """Вкладка истории операций"""
        tab = tk.Frame(self.notebook, bg=self.office_colors['bg_white'])
        self.notebook.add(tab, text="📋 История операций")
        
        control_frame = self._create_control_frame(tab)
        
        self._create_button(control_frame, "Обновить", self.load_history)
        
        # Фильтр
        filter_frame = tk.Frame(control_frame, bg=self.office_colors['bg_white'])
        filter_frame.pack(side=tk.LEFT, padx=20)
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
        self._load_treeview_data(
            'instruments', 
            self.instruments_tree, 
            lambda search: self.db.get_instruments(search),
            getattr(self, 'instrument_search', None)
        )
            
    def load_employees(self):
        """Загрузка списка сотрудников"""
        self._load_treeview_data(
            'employees',
            self.employees_tree,
            lambda search: self.db.get_employees(search),
            getattr(self, 'employee_search', None)
        )
            
    def load_active_issues(self):
        """Загрузка активных выдач"""
        def post_load():
            stats = self.db.get_issues_statistics()
            self.stats_label.config(
                text=f"Всего выдано: {stats['total']} | Просрочено: {stats['overdue']}"
            )
        
        self._load_treeview_data(
            'issues',
            self.issues_tree,
            self.db.get_active_issues,
            post_load_callback=post_load
        )
        
    def load_active_issues_for_return(self):
        """Загрузка активных выдач для возврата"""
        def process_item(issue):
            expected_return = datetime.strptime(issue[6], '%Y-%m-%d').date() if issue[6] else None
            tags = ('overdue',) if expected_return and expected_return < datetime.now().date() else ()
            return issue, tags
        
        self._load_treeview_data(
            'returns',
            self.returns_tree,
            self.db.get_active_issues_for_return,
            item_processor=process_item
        )
            
    def load_history(self):
        """Загрузка истории операций"""
        def process_item(record):
            tags = ('issue',) if record[1] == 'Выдача' else ('return',)
            return record, tags
        
        filter_type = getattr(self, 'history_filter', None)
        filter_value = filter_type.get() if filter_type else 'Все'
        
        self._load_treeview_data(
            'history',
            self.history_tree,
            lambda: self.db.get_operation_history(filter_value),
            item_processor=process_item
        )
            
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
    
    def _save_window_geometry(self):
        """Сохранение геометрии окна (вызывается с задержкой)"""
        if self.root.winfo_viewable():
            geometry = self.root.geometry()
            self.window_config.save_window_geometry("main_window", geometry)
        self._save_geometry_job = None
    
    def _on_closing(self):
        """Обработка закрытия окна - сохраняем геометрию перед выходом"""
        # Отменяем отложенное сохранение, если оно есть
        if self._save_geometry_job:
            self.root.after_cancel(self._save_geometry_job)
        
        # Сохраняем геометрию немедленно
        if self.root.winfo_viewable():
            geometry = self.root.geometry()
            self.window_config.save_window_geometry("main_window", geometry)
        
        # Закрываем окно
        self.root.destroy()




def main():
    root = tk.Tk()
    app = ToolManagementApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

