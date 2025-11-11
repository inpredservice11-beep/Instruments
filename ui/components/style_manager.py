"""
Менеджер стилей UI
"""
import platform
import tkinter as tk
from tkinter import ttk
from config.ui_config import OFFICE_COLORS


class StyleManager:
    """Управление стилями интерфейса"""
    
    def __init__(self, root):
        self.root = root
        self.style = ttk.Style()
        self._setup_fonts()
        self._setup_colors()
        self._apply_styles()
    
    def _setup_fonts(self):
        """Настройка шрифтов"""
        if platform.system() == 'Windows':
            try:
                self.default_font = ("Segoe UI", 9)
                self.title_font = ("Segoe UI", 16, "bold")
                self.tab_font = ("Segoe UI", 11, "bold")
            except:
                self.default_font = ("Arial", 9)
                self.title_font = ("Arial", 16, "bold")
                self.tab_font = ("Arial", 11, "bold")
        else:
            self.default_font = ("Arial", 9)
            self.title_font = ("Arial", 16, "bold")
            self.tab_font = ("Arial", 11, "bold")
    
    def _setup_colors(self):
        """Настройка цветов"""
        self.colors = OFFICE_COLORS.copy()
        self.root.configure(bg=self.colors['bg_main'])
    
    def _apply_styles(self):
        """Применение стилей к виджетам"""
        # Treeview
        self.style.configure("Treeview", 
                           rowheight=32,
                           background=self.colors['bg_white'],
                           foreground=self.colors['fg_main'],
                           fieldbackground=self.colors['bg_white'],
                           font=self.default_font,
                           borderwidth=1,
                           relief='flat')
        
        self.style.map("Treeview",
                     background=[('selected', self.colors['selected'])],
                     foreground=[('selected', '#ffffff')])
        
        # Заголовки Treeview
        self.style.configure("Treeview.Heading",
                          background=self.colors['bg_header'],
                          foreground=self.colors['fg_header'],
                          font=(self.default_font[0], self.default_font[1], "bold"),
                          relief='flat',
                          borderwidth=0,
                          padding=8)
        
        self.style.map("Treeview.Heading",
                     background=[('active', self.colors['bg_header_light'])])
        
        # Вкладки
        self.style.configure("TNotebook",
                           background=self.colors['bg_main'],
                           borderwidth=0)
        
        self.style.configure("TNotebook.Tab",
                           font=self.tab_font,
                           padding=[20, 10],
                           background=self.colors['bg_white'],
                           foreground=self.colors['fg_main'],
                           borderwidth=1,
                           relief='flat')
        
        self.style.map("TNotebook.Tab",
                     background=[('selected', self.colors['bg_white']),
                                ('!selected', self.colors['bg_main'])],
                     expand=[('selected', [1, 1, 1, 0])])
        
        # Кнопки
        self.style.configure("TButton",
                           font=self.default_font,
                           padding=[12, 6],
                           relief='flat',
                           borderwidth=1)
        
        self.style.map("TButton",
                     background=[('active', self.colors['hover']),
                                ('!active', self.colors['bg_white'])],
                     foreground=[('active', self.colors['fg_main']),
                                ('!active', self.colors['fg_main'])],
                     bordercolor=[('active', self.colors['border']),
                                 ('!active', self.colors['border'])],
                     focuscolor=[('', 'none')])
        
        # Frame
        self.style.configure("TFrame",
                          background=self.colors['bg_white'])
        
        # Label
        self.style.configure("TLabel",
                           background=self.colors['bg_white'],
                           foreground=self.colors['fg_main'],
                           font=self.default_font)
        
        # Entry
        self.style.configure("TEntry",
                          fieldbackground=self.colors['bg_white'],
                          foreground=self.colors['fg_main'],
                          borderwidth=1,
                          relief='flat',
                          font=self.default_font,
                          padding=6)
        
        self.style.map("TEntry",
                     bordercolor=[('focus', self.colors['selected']),
                                 ('!focus', self.colors['border'])],
                     lightcolor=[('focus', self.colors['selected']),
                               ('!focus', self.colors['border'])],
                     darkcolor=[('focus', self.colors['selected']),
                              ('!focus', self.colors['border'])])
        
        # Combobox
        self.style.configure("TCombobox",
                          fieldbackground=self.colors['bg_white'],
                          foreground=self.colors['fg_main'],
                          borderwidth=1,
                          relief='flat',
                          font=self.default_font,
                          padding=6)
        
        self.style.map("TCombobox",
                     fieldbackground=[('readonly', self.colors['bg_white'])],
                     bordercolor=[('focus', self.colors['selected']),
                                 ('!focus', self.colors['border'])])
        
        # LabelFrame
        self.style.configure("TLabelframe",
                           background=self.colors['bg_white'],
                           borderwidth=1,
                           relief='flat')
        
        self.style.configure("TLabelframe.Label",
                           background=self.colors['bg_white'],
                           foreground=self.colors['fg_main'],
                           font=(self.default_font[0], self.default_font[1], "bold"))

