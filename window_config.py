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
                try:
                    if window.winfo_exists() and window.winfo_viewable() and event.widget == window:
                        geometry = window.geometry()
                        if geometry and geometry != "1x1+0+0":  # Игнорируем некорректную геометрию
                            self.save_window_geometry(window_name, geometry)
                except:
                    pass

            # Для модальных окон события Configure могут не работать, попробуем другие события
            window.bind('<Configure>', on_configure)
            window.bind('<ButtonRelease-1>', on_configure)  # При отпускании кнопки мыши
            window.bind('<FocusOut>', on_configure)          # При потере фокуса
        
        # Всегда сохраняем при закрытии окна (гарантированное сохранение)
        def on_closing():
            try:
                if window.winfo_exists() and window.winfo_viewable():
                    geometry = window.geometry()
                    if geometry and geometry != "1x1+0+0":  # Игнорируем некорректную геометрию
                        self.save_window_geometry(window_name, geometry)
            except:
                pass  # Окно уже закрывается
            try:
                if window.winfo_exists():
                    window.destroy()
            except:
                pass
        
        # Сохраняем ссылку на обработчик для возможного использования
        window._window_config_name = window_name
        window._window_config = self
        
        window.protocol("WM_DELETE_WINDOW", on_closing)
    
    def close_window_with_save(self, window, window_name=None):
        """Закрытие окна с сохранением настроек
        
        Args:
            window: окно tkinter
            window_name: имя окна (если не указано, берется из атрибута окна)
        """
        if window_name is None:
            window_name = getattr(window, '_window_config_name', None)
        
        try:
            if window_name and window.winfo_exists() and window.winfo_viewable():
                geometry = window.geometry()
                if geometry and geometry != "1x1+0+0":  # Игнорируем некорректную геометрию
                    self.save_window_geometry(window_name, geometry)
        except:
            pass
        
        try:
            if window.winfo_exists():
                window.destroy()
        except:
            pass






