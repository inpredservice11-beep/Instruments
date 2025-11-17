#!/usr/bin/env python3
"""
Модуль вкладок пользовательского интерфейса
"""

import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from barcode_utils import barcode_manager
import os


class TabManager:
    """Менеджер вкладок приложения"""

    def __init__(self, parent, db_manager, office_colors, default_font):
        self.parent = parent
        self.db = db_manager
        self.office_colors = office_colors
        self.default_font = default_font

        # Словари для хранения виджетов
        self.tabs = {}
        self.search_widgets = {}
        self.tree_mappings = {}

        # Данные для фотографий
        self.instrument_photos = {}
        self.issue_instrument_photos = {}
        self.return_instrument_photos = {}
        self.issue_issue_to_instrument = {}
        self.return_issue_to_instrument = {}

        # Переменные для tooltip
        self.photo_tooltip = None
        self.photo_tooltip_job = None

    def create_instruments_tab(self):
        """Создание вкладки управления инструментами"""
        tab = tk.Frame(self.parent, bg=self.office_colors['bg_white'])
        self.tabs['instruments'] = tab

        # Панель управления
        control_frame = self._create_control_frame(tab)

        # Кнопки действий
        self._create_action_buttons(control_frame, 'instruments')

        # Виджет поиска по штрих-коду
        self._create_barcode_search(control_frame)

        # Поиск по названию
        self.search_widgets['instruments'] = self._create_search_widget(control_frame)

        # Таблица инструментов
        self.tree_mappings['instruments'] = self._create_treeview(tab, 'instruments')

        # Обработчики событий
        self._setup_instrument_event_handlers()

        return tab

    def create_employees_tab(self):
        """Создание вкладки управления сотрудниками"""
        tab = tk.Frame(self.parent, bg=self.office_colors['bg_white'])
        self.tabs['employees'] = tab

        # Панель управления
        control_frame = self._create_control_frame(tab)

        # Кнопки действий
        self._create_action_buttons(control_frame, 'employees')

        # Поиск
        self.search_widgets['employees'] = self._create_search_widget(control_frame)

        # Таблица сотрудников
        self.tree_mappings['employees'] = self._create_treeview(tab, 'employees')

        # Обработчики событий
        self._setup_employee_event_handlers()

        return tab

    def create_issues_tab(self):
        """Создание вкладки выдачи инструментов"""
        tab = tk.Frame(self.parent, bg=self.office_colors['bg_white'])
        self.tabs['issues'] = tab

        # Панель управления
        control_frame = self._create_control_frame(tab)

        # Кнопки действий
        self._create_issue_buttons(control_frame)

        # Фильтры
        self._create_issue_filters(control_frame)

        # Таблица выдач
        self.tree_mappings['issues'] = self._create_treeview(tab, 'issues')

        # Обработчики событий
        self._setup_issue_event_handlers()

        return tab

    def create_returns_tab(self):
        """Создание вкладки возврата инструментов"""
        tab = tk.Frame(self.parent, bg=self.office_colors['bg_white'])
        self.tabs['returns'] = tab

        # Панель управления
        control_frame = self._create_control_frame(tab)

        # Кнопки действий
        self._create_return_buttons(control_frame)

        # Таблица возвратов
        self.tree_mappings['returns'] = self._create_treeview(tab, 'returns')

        # Обработчики событий
        self._setup_return_event_handlers()

        return tab

    def create_history_tab(self):
        """Создание вкладки истории операций"""
        tab = tk.Frame(self.parent, bg=self.office_colors['bg_white'])
        self.tabs['history'] = tab

        # Панель управления
        control_frame = self._create_control_frame(tab)

        # Кнопки экспорта
        self._create_history_buttons(control_frame)

        # Фильтры истории
        self._create_history_filters(control_frame)

        # Таблица истории
        self.tree_mappings['history'] = self._create_treeview(tab, 'history')

        return tab

    def create_addresses_tab(self):
        """Создание вкладки управления адресами"""
        tab = tk.Frame(self.parent, bg=self.office_colors['bg_white'])
        self.tabs['addresses'] = tab

        # Панель управления
        control_frame = self._create_control_frame(tab)

        # Кнопки действий
        self._create_address_buttons(control_frame)

        # Поиск
        self.search_widgets['addresses'] = self._create_search_widget(control_frame)

        # Таблица адресов
        self.tree_mappings['addresses'] = self._create_treeview(tab, 'addresses')

        return tab

    def create_analytics_tab(self):
        """Создание вкладки аналитики"""
        tab = tk.Frame(self.parent, bg=self.office_colors['bg_white'])
        self.tabs['analytics'] = tab

        # Здесь будет логика создания графиков аналитики
        ttk.Label(tab, text="Аналитика - в разработке").pack(pady=20)

        return tab

    def _create_control_frame(self, parent):
        """Создание панели управления"""
        frame = tk.Frame(parent, bg=self.office_colors['bg_white'])
        frame.pack(fill=tk.X, padx=10, pady=10)
        return frame

    def _create_action_buttons(self, parent, table_type):
        """Создание кнопок действий для таблиц"""
        button_configs = {
            'instruments': [
                ("Добавить инструмент", None),
                ("Редактировать", None),
                ("Удалить", None),
                ("Обновить", None),
            ],
            'employees': [
                ("Добавить сотрудника", None),
                ("Редактировать", None),
                ("Удалить", None),
                ("Обновить", None),
            ]
        }

        for text, command in button_configs.get(table_type, []):
            self._create_button(parent, text, command)

    def _create_issue_buttons(self, parent):
        """Создание кнопок для вкладки выдачи"""
        self._create_button(parent, "Выдать инструмент", None)
        self._create_button(parent, "Оформить возврат", None)
        self._create_button(parent, "Обновить", None)

    def _create_return_buttons(self, parent):
        """Создание кнопок для вкладки возврата"""
        self._create_button(parent, "Массовая сдача", None)
        self._create_button(parent, "Обновить", None)

    def _create_history_buttons(self, parent):
        """Создание кнопок для вкладки истории"""
        self._create_button(parent, "Экспорт в PDF", None)
        self._create_button(parent, "Экспорт в Excel", None)

    def _create_address_buttons(self, parent):
        """Создание кнопок для вкладки адресов"""
        self._create_button(parent, "Добавить адрес", None)
        self._create_button(parent, "Редактировать", None)
        self._create_button(parent, "Удалить", None)
        self._create_button(parent, "Обновить", None)

    def _create_button(self, parent, text, command):
        """Создание кнопки с стандартными настройками"""
        btn = ttk.Button(parent, text=text, command=command)
        btn.pack(side=tk.LEFT, padx=5)
        return btn

    def _create_search_widget(self, parent):
        """Создание виджета поиска"""
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
        # search_entry.bind('<KeyRelease>', lambda e: self.load_data_callback())

        return search_entry

    def _create_barcode_search(self, parent):
        """Создание виджета поиска по штрих-коду"""
        barcode_frame = tk.Frame(parent, bg=self.office_colors['bg_white'])
        barcode_frame.pack(side=tk.RIGHT, padx=5)

        tk.Label(
            barcode_frame,
            text="Штрих-код:",
            bg=self.office_colors['bg_white'],
            fg=self.office_colors['fg_main'],
            font=self.default_font
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.barcode_search = ttk.Entry(barcode_frame, width=20)
        self.barcode_search.pack(side=tk.LEFT, padx=5)
        # self.barcode_search.bind('<Return>', lambda e: self.search_by_barcode())

        ttk.Button(
            barcode_frame,
            text="🔍 Найти",
            command=None  # self.search_by_barcode
        ).pack(side=tk.LEFT, padx=5)

    def _create_issue_filters(self, parent):
        """Создание фильтров для вкладки выдачи"""
        # Фильтр по статусу
        status_frame = tk.Frame(parent, bg=self.office_colors['bg_white'])
        status_frame.pack(side=tk.LEFT, padx=10)

        tk.Label(status_frame, text="Статус:", bg=self.office_colors['bg_white']).pack(side=tk.LEFT)
        # Здесь будут фильтры статуса

    def _create_history_filters(self, parent):
        """Создание фильтров для вкладки истории"""
        # Фильтр по типу операции
        type_frame = tk.Frame(parent, bg=self.office_colors['bg_white'])
        type_frame.pack(side=tk.LEFT, padx=10)

        tk.Label(type_frame, text="Тип операции:", bg=self.office_colors['bg_white']).pack(side=tk.LEFT)
        # self.history_filter = ttk.Combobox(type_frame, values=['Все', 'Выдача', 'Возврат'], state='readonly')
        # self.history_filter.pack(side=tk.LEFT, padx=5)

        # Фильтр по датам
        date_frame = tk.Frame(parent, bg=self.office_colors['bg_white'])
        date_frame.pack(side=tk.LEFT, padx=10)

        tk.Label(date_frame, text="Дата с:", bg=self.office_colors['bg_white']).pack(side=tk.LEFT, padx=(0, 5))
        # self.history_date_from = DateEntry(date_frame, width=12)

        tk.Label(date_frame, text="по:", bg=self.office_colors['bg_white']).pack(side=tk.LEFT, padx=(10, 5))
        # self.history_date_to = DateEntry(date_frame, width=12)

        # ttk.Button(date_frame, text="Сбросить даты", command=None).pack(side=tk.LEFT, padx=5)

    def _create_treeview(self, parent, table_name):
        """Создание таблицы Treeview"""
        from app import TABLES_CONFIG, TREEVIEW_HEIGHT

        config = TABLES_CONFIG[table_name]
        columns = config['columns']
        column_widths = config['column_widths']

        # Контейнер для таблицы
        tree_container = tk.Frame(parent, bg=self.office_colors['bg_white'])
        tree_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tree = ttk.Treeview(tree_container, columns=columns, show='headings', height=TREEVIEW_HEIGHT)

        # Настройка колонок
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=column_widths.get(col, 100), anchor=tk.W)

        # Полосы прокрутки
        v_scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Размещение
        tree.grid(row=0, column=0, sticky=tk.NSEW)
        v_scrollbar.grid(row=0, column=1, sticky=tk.NS)
        h_scrollbar.grid(row=1, column=0, sticky=tk.EW)

        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        return tree

    def _setup_instrument_event_handlers(self):
        """Настройка обработчиков событий для инструментов"""
        tree = self.tree_mappings['instruments']
        # tree.bind('<Motion>', self._on_instrument_hover)
        # tree.bind('<Leave>', self._on_instrument_leave)
        # tree.bind('<Double-1>', self._on_instrument_double_click)

    def _setup_employee_event_handlers(self):
        """Настройка обработчиков событий для сотрудников"""
        tree = self.tree_mappings['employees']
        # tree.bind('<Double-1>', self._on_employee_double_click)

    def _setup_issue_event_handlers(self):
        """Настройка обработчиков событий для выдач"""
        tree = self.tree_mappings['issues']
        # Обработчики для выдач

    def _setup_return_event_handlers(self):
        """Настройка обработчиков событий для возвратов"""
        tree = self.tree_mappings['returns']
        # tree.bind('<Motion>', self._on_return_hover)
        # tree.bind('<Leave>', self._on_return_leave)
        # tree.bind('<Double-1>', self._on_return_double_click)



