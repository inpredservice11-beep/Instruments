"""
Главное окно приложения
"""
import tkinter as tk
from tkinter import ttk
from window_config import WindowConfig
from ui.components.style_manager import StyleManager
from ui.components.widgets import OfficeButton, SearchWidget
from config.ui_config import OFFICE_COLORS, TABLES_CONFIG, TREEVIEW_HEIGHT


class MainWindow:
    """Главное окно приложения"""
    
    def __init__(self, root, services, dialogs):
        self.root = root
        self.root.title("Система учета инструмента")
        self.services = services
        self.dialogs = dialogs
        
        # Инициализация конфигурации окон
        self.window_config = WindowConfig()
        
        # Восстановление размера и позиции основного окна
        default_geometry = "1200x700"
        self.window_config.restore_window(self.root, "main_window", default_geometry, auto_save=False)
        
        # Переменная для debouncing сохранения размера окна
        self._save_geometry_job = None
        
        # Настройка стиля
        self.style_manager = StyleManager(root)
        self.colors = self.style_manager.colors
        self.default_font = self.style_manager.default_font
        self.title_font = self.style_manager.title_font
        
        # Состояние сортировки для каждой таблицы
        from config.ui_config import DEFAULT_SORT_STATES
        self.sort_states = DEFAULT_SORT_STATES.copy()
        
        # Маппинг имен таблиц на виджеты Treeview
        self.tree_mapping = {}
        
        # Настройка обработчиков окна
        self._setup_window_handlers()
        
        # Создание интерфейса
        self.create_widgets()
    
    def _setup_window_handlers(self):
        """Настройка обработчиков окна"""
        def on_configure(event):
            if self.root.winfo_viewable() and event.widget == self.root:
                if self._save_geometry_job:
                    self.root.after_cancel(self._save_geometry_job)
                self._save_geometry_job = self.root.after(500, self._save_window_geometry)
        
        self.root.bind('<Configure>', on_configure)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _save_window_geometry(self):
        """Сохранение геометрии окна"""
        if self.root.winfo_viewable():
            geometry = self.root.geometry()
            self.window_config.save_window_geometry("main_window", geometry)
        self._save_geometry_job = None
    
    def _on_closing(self):
        """Обработка закрытия окна"""
        if self._save_geometry_job:
            self.root.after_cancel(self._save_geometry_job)
        
        if self.root.winfo_viewable():
            geometry = self.root.geometry()
            self.window_config.save_window_geometry("main_window", geometry)
        
        self.root.destroy()
    
    def create_widgets(self):
        """Создание элементов интерфейса"""
        # Верхняя панель (Header)
        header_frame = tk.Frame(self.root, bg=self.colors['bg_header'], height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Заголовок приложения
        title_label = tk.Label(
            header_frame,
            text="Система учета выдачи и возврата инструмента",
            font=self.title_font,
            bg=self.colors['bg_header'],
            fg=self.colors['fg_header'],
            pady=15
        )
        title_label.pack()
        
        # Панель инструментов
        toolbar_frame = tk.Frame(self.root, bg=self.colors['bg_white'], height=50)
        toolbar_frame.pack(fill=tk.X, padx=0, pady=0)
        toolbar_frame.pack_propagate(False)
        
        toolbar_inner = tk.Frame(toolbar_frame, bg=self.colors['bg_white'])
        toolbar_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        
        # Разделитель
        separator = tk.Frame(self.root, bg=self.colors['border'], height=1)
        separator.pack(fill=tk.X)
        
        # Notebook для вкладок
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
    
    def create_button(self, parent, text, command, side=tk.LEFT, style='default'):
        """Создание кнопки"""
        return OfficeButton.create(parent, text, command, side, style, self.colors)
    
    def create_search_widget(self, parent, on_change_callback):
        """Создание виджета поиска"""
        return SearchWidget.create(parent, on_change_callback, self.colors, self.default_font)
    
    def create_treeview(self, parent, table_name, sort_callback=None):
        """Создание таблицы Treeview"""
        from ui.components.widgets import TreeViewWidget
        tree = TreeViewWidget.create(parent, table_name, sort_callback, self.colors, self.default_font)
        self.tree_mapping[table_name] = tree
        return tree
    
    def create_control_frame(self, tab):
        """Создание панели управления для вкладки"""
        control_frame = tk.Frame(tab, bg=self.colors['bg_white'], padx=10, pady=8)
        control_frame.pack(fill=tk.X)
        return control_frame

