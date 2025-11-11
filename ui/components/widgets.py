"""
Переиспользуемые UI виджеты
"""
import tkinter as tk
from tkinter import ttk
from config.ui_config import TABLES_CONFIG, OFFICE_COLORS


class OfficeButton:
    """Кнопка в стиле MS Office"""
    
    @staticmethod
    def create(parent, text, command, side=tk.LEFT, style='default', colors=None):
        """Создание кнопки"""
        if colors is None:
            colors = OFFICE_COLORS
            
        if style == 'primary':
            btn_frame = tk.Frame(parent, bg=colors['bg_white'])
            btn_frame.pack(side=side, padx=2)
            
            button = tk.Button(
                btn_frame,
                text=text,
                command=command,
                bg=colors['selected'],
                fg='#ffffff',
                font=("Arial", 9),
                relief='flat',
                padx=16,
                pady=8,
                cursor='hand2',
                activebackground=colors['bg_header_light'],
                activeforeground='#ffffff',
                borderwidth=0
            )
            button.pack()
        else:
            button = ttk.Button(parent, text=text, command=command)
            button.pack(side=side, padx=2)
        
        return button


class SearchWidget:
    """Виджет поиска"""
    
    @staticmethod
    def create(parent, on_change_callback, colors=None, default_font=None):
        """Создание виджета поиска"""
        if colors is None:
            colors = OFFICE_COLORS
        if default_font is None:
            default_font = ("Arial", 9)
            
        search_frame = tk.Frame(parent, bg=colors['bg_white'])
        search_frame.pack(side=tk.RIGHT, padx=5)
        
        tk.Label(
            search_frame,
            text="Поиск:",
            bg=colors['bg_white'],
            fg=colors['fg_main'],
            font=default_font
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        search_entry = ttk.Entry(search_frame, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind('<KeyRelease>', lambda e: on_change_callback())
        return search_entry


class TreeViewWidget:
    """Виджет таблицы Treeview"""
    
    @staticmethod
    def create(parent, table_name, sort_callback=None, colors=None, default_font=None):
        """Создание таблицы Treeview"""
        if colors is None:
            colors = OFFICE_COLORS
        if default_font is None:
            default_font = ("Arial", 9)
            
        config = TABLES_CONFIG[table_name]
        columns = config['columns']
        column_widths = config['column_widths']
        tags = config.get('tags', {})
        
        # Контейнер для таблицы
        tree_container = tk.Frame(parent, bg=colors['bg_white'])
        tree_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        from config.ui_config import TREEVIEW_HEIGHT
        tree = ttk.Treeview(tree_container, columns=columns, show='headings', height=TREEVIEW_HEIGHT)
        
        # Настройка столбцов
        for col in columns:
            tree.column(col, width=column_widths.get(col, 100))
            if sort_callback:
                tree.heading(col, text=col, command=lambda c=col: sort_callback(table_name, c))
            else:
                tree.heading(col, text=col)
        
        # Настройка тегов
        for tag_name, tag_config in tags.items():
            updated_config = tag_config.copy()
            if 'background' in updated_config:
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

