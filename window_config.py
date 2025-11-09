"""
Утилита для сохранения и восстановления позиций окон
"""

import json
import os


class WindowConfig:
    """Класс для управления конфигурацией окон"""
    
    def __init__(self, config_file='window_config.json'):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        """Загрузка конфигурации из файла"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_config(self):
        """Сохранение конфигурации в файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
    
    def get_window_geometry(self, window_name):
        """Получение геометрии окна по имени"""
        if window_name in self.config:
            return self.config[window_name].get('geometry')
        return None
    
    def get_window_position(self, window_name):
        """Получение позиции окна по имени"""
        if window_name in self.config:
            pos = self.config[window_name]
            return (pos.get('x'), pos.get('y'))
        return None
    
    def save_window_geometry(self, window_name, geometry):
        """Сохранение геометрии окна"""
        if window_name not in self.config:
            self.config[window_name] = {}
        self.config[window_name]['geometry'] = geometry
        self.save_config()
    
    def save_window_position(self, window_name, x, y):
        """Сохранение позиции окна"""
        if window_name not in self.config:
            self.config[window_name] = {}
        self.config[window_name]['x'] = x
        self.config[window_name]['y'] = y
        self.save_config()
    
    def restore_window(self, window, window_name, default_geometry, auto_save=True):
        """Восстановление позиции и размера окна
        
        Args:
            window: окно tkinter
            window_name: имя окна для сохранения в конфиге
            default_geometry: геометрия по умолчанию
            auto_save: если True, автоматически сохранять при изменении (по умолчанию True)
        """
        if window_name in self.config:
            config = self.config[window_name]
            if 'geometry' in config:
                window.geometry(config['geometry'])
            elif 'x' in config and 'y' in config:
                # Восстанавливаем только позицию, размер берем из default_geometry
                size_part = default_geometry.split('+')[0] if '+' in default_geometry else default_geometry.split('-')[0]
                window.geometry(f"{size_part}+{config['x']}+{config['y']}")
        else:
            window.geometry(default_geometry)
        
        # Привязываем сохранение позиции при перемещении окна (только если auto_save=True)
        if auto_save:
            def on_configure(event):
                if window.winfo_viewable():
                    geometry = window.geometry()
                    self.save_window_geometry(window_name, geometry)
            
            window.bind('<Configure>', on_configure)






