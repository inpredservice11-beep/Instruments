"""
Система учета выдачи и возврата инструмента
Графический интерфейс на tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
import sys
import platform

from database_manager import DatabaseManager
from window_config import WindowConfig
from dialogs import (
    AddInstrumentDialog, EditInstrumentDialog,
    AddEmployeeDialog, EditEmployeeDialog,
    IssueInstrumentDialog, ReturnInstrumentDialog
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
                   'Местоположение', 'Статус'),
        'column_widths': {
            'ID': 50, 'Название': 220, 'Инв. номер': 110, 'Серийный номер': 120,
            'Категория': 160, 'Местоположение': 160, 'Статус': 110
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
                   'Дата выдачи', 'Ожид. возврат', 'Выдал', 'Примечание'),
        'column_widths': {
            'ID': 50, 'Инв. номер': 110, 'Инструмент': 200, 'Сотрудник': 180,
            'Дата выдачи': 130, 'Ожид. возврат': 110, 'Выдал': 140, 'Примечание': 200
        }
    },
    'returns': {
        'columns': ('ID', 'Инв. номер', 'Инструмент', 'Сотрудник', 
                   'Дата выдачи', 'Ожид. возврат', 'Дней в использовании'),
        'column_widths': {
            'ID': 50, 'Инв. номер': 110, 'Инструмент': 230, 'Сотрудник': 200,
            'Дата выдачи': 130, 'Ожид. возврат': 120, 'Дней в использовании': 160
        },
        'tags': {'overdue': {'background': '#ffcccc'}}
    },
    'history': {
        'columns': ('ID', 'Тип', 'Инв. номер', 'Инструмент', 'Сотрудник', 
                   'Дата операции', 'Выполнил', 'Примечание'),
        'column_widths': {
            'ID': 50, 'Тип': 80, 'Инв. номер': 110, 'Инструмент': 200,
            'Сотрудник': 180, 'Дата операции': 140, 'Выполнил': 140, 'Примечание': 200
        },
        'tags': {
            'issue': {'background': '#ffffcc'},
            'return': {'background': '#ccffcc'}
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
        
        # Настройка стиля для увеличения расстояния между строками
        style = ttk.Style()
        style.configure("Treeview", rowheight=30)
        
        # Настройка шрифта заголовков вкладок
        style.configure("TNotebook.Tab", font=("Arial", 12, "bold"), padding=[15, 8])
        
        # Состояние сортировки для каждой таблицы: {column: 'asc'/'desc'}
        self.sort_states = {
            'instruments': {'column': None, 'direction': 'asc'},
            'employees': {'column': None, 'direction': 'asc'},
            'issues': {'column': None, 'direction': 'asc'},
            'returns': {'column': None, 'direction': 'asc'},
            'history': {'column': None, 'direction': 'asc'}
        }
        
        # Маппинг имен таблиц на виджеты Treeview (инициализируется после создания вкладок)
        self.tree_mapping = {}
        
        # Создание интерфейса
        self.create_widgets()
        self.load_data()
        
    def create_widgets(self):
        """Создание элементов интерфейса"""
        # Заголовок
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(
            title_frame, 
            text="Система учета выдачи и возврата инструмента",
            font=("Arial", 16, "bold")
        )
        title_label.pack()
        
        # Notebook для вкладок
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Вкладки
        self.create_instruments_tab()
        self.create_employees_tab()
        self.create_issues_tab()
        self.create_returns_tab()
        self.create_history_tab()
    
    def _create_button(self, parent, text, command, side=tk.LEFT):
        """Создание кнопки с единообразным стилем"""
        button = ttk.Button(parent, text=text, command=command)
        button.pack(side=side, padx=BUTTON_PADDING)
        return button
    
    def _create_search_widget(self, parent, on_change_callback):
        """Создание виджета поиска"""
        search_frame = ttk.Frame(parent)
        search_frame.pack(side=tk.RIGHT, padx=5)
        
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(search_frame, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind('<KeyRelease>', lambda e: on_change_callback())
        return search_entry
    
    def _create_treeview(self, parent, table_name):
        """Создание таблицы Treeview с настройками"""
        config = TABLES_CONFIG[table_name]
        columns = config['columns']
        column_widths = config['column_widths']
        tags = config.get('tags', {})
        
        tree = ttk.Treeview(parent, columns=columns, show='headings', height=TREEVIEW_HEIGHT)
        
        # Настройка столбцов
        for col in columns:
            tree.column(col, width=column_widths.get(col, 100))
            tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(table_name, c))
        
        # Настройка тегов
        for tag_name, tag_config in tags.items():
            tree.tag_configure(tag_name, **tag_config)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5))
        
        return tree
    
    def _create_control_frame(self, tab):
        """Создание панели управления для вкладки"""
        control_frame = ttk.Frame(tab, padding="5")
        control_frame.pack(fill=tk.X)
        return control_frame
        
    def create_instruments_tab(self):
        """Вкладка управления инструментами"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Инструменты")
        
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
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Сотрудники")
        
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
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Выдача инструмента")
        
        control_frame = self._create_control_frame(tab)
        
        self._create_button(control_frame, "Выдать инструмент", self.issue_instrument)
        self._create_button(control_frame, "Обновить", self.load_active_issues)
        
        # Статистика
        stats_frame = ttk.Frame(control_frame)
        stats_frame.pack(side=tk.RIGHT, padx=5)
        self.stats_label = ttk.Label(stats_frame, text="", font=("Arial", 10))
        self.stats_label.pack()
        
        self.issues_tree = self._create_treeview(tab, 'issues')
        self.tree_mapping['issues'] = self.issues_tree
        
    def create_returns_tab(self):
        """Вкладка возврата инструмента"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Возврат инструмента")
        
        control_frame = self._create_control_frame(tab)
        
        self._create_button(control_frame, "Оформить возврат", self.return_instrument)
        self._create_button(control_frame, "Обновить", self.load_active_issues_for_return)
        
        self.returns_tree = self._create_treeview(tab, 'returns')
        self.tree_mapping['returns'] = self.returns_tree
        
    def create_history_tab(self):
        """Вкладка истории операций"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="История операций")
        
        control_frame = self._create_control_frame(tab)
        
        self._create_button(control_frame, "Обновить", self.load_history)
        
        # Фильтр
        filter_frame = ttk.Frame(control_frame)
        filter_frame.pack(side=tk.LEFT, padx=20)
        ttk.Label(filter_frame, text="Тип операции:").pack(side=tk.LEFT)
        self.history_filter = ttk.Combobox(
            filter_frame, values=['Все', 'Выдача', 'Возврат'],
            state='readonly', width=15
        )
        self.history_filter.set('Все')
        self.history_filter.pack(side=tk.LEFT, padx=5)
        self.history_filter.bind('<<ComboboxSelected>>', lambda e: self.load_history())
        
        self.history_tree = self._create_treeview(tab, 'history')
        self.tree_mapping['history'] = self.history_tree
        
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
            expected_return = datetime.strptime(issue[5], '%Y-%m-%d').date() if issue[5] else None
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

