#!/usr/bin/env python3
"""
Менеджер уведомлений для ToolManagement
Система уведомлений о просроченных возвратах и других событиях
"""

import threading
import time
import queue
from datetime import datetime, timedelta


class NotificationManager:
    """Класс для управления уведомлениями"""

    def __init__(self, db_manager, telegram_bot=None):
        self.db = db_manager
        self.telegram_bot = telegram_bot
        self.is_running = False
        self.check_interval = 300  # Проверка каждые 5 минут
        self.notification_thread = None

        # Очередь для desktop уведомлений (для обработки в главном потоке)
        self.notification_queue = queue.Queue()

        # Настройки уведомлений
        self.settings = {
            'enable_desktop_notifications': True,
            'enable_telegram_notifications': True,
            'overdue_warning_days': 1,  # Предупреждать за 1 день до просрочки
            'overdue_critical_days': 3,  # Критическое уведомление через 3 дня просрочки
        }

        self.load_settings()

    def load_settings(self):
        """Загрузка настроек уведомлений"""
        try:
            import json
            import os
            settings_file = 'notification_settings.json'

            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    self.settings.update(loaded_settings)
        except Exception as e:
            print(f"Ошибка загрузки настроек уведомлений: {e}")

    def save_settings(self):
        """Сохранение настроек уведомлений"""
        try:
            import json
            settings_file = 'notification_settings.json'

            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения настроек уведомлений: {e}")

    def start_monitoring(self):
        """Запуск мониторинга уведомлений"""
        if self.is_running:
            return

        self.is_running = True
        self.notification_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.notification_thread.start()
        print("✅ Система уведомлений запущена")

    def stop_monitoring(self):
        """Остановка мониторинга уведомлений"""
        self.is_running = False
        if self.notification_thread:
            self.notification_thread.join(timeout=5)
        print("❌ Система уведомлений остановлена")

    def _monitoring_loop(self):
        """Основной цикл мониторинга"""
        while self.is_running:
            try:
                self._check_overdue_items()
                self._check_upcoming_deadlines()
            except Exception as e:
                print(f"Ошибка в цикле уведомлений: {e}")

            # Ждем следующей проверки
            time.sleep(self.check_interval)

    def _check_overdue_items(self):
        """Проверка просроченных возвратов"""
        try:
            # Получаем активные выдачи
            active_issues = self.db.get_active_issues()

            overdue_items = []
            for issue in active_issues:
                expected_return = issue[7]  # expected_return_date
                if expected_return:
                    expected_date = datetime.strptime(expected_return, '%Y-%m-%d')
                    now = datetime.now()

                    if now > expected_date:
                        overdue_days = (now - expected_date).days
                        overdue_items.append((issue, overdue_days))

            # Отправляем уведомления
            if overdue_items:
                self._send_overdue_notification(overdue_items)

        except Exception as e:
            print(f"Ошибка проверки просроченных возвратов: {e}")

    def _check_upcoming_deadlines(self):
        """Проверка приближающихся сроков возврата"""
        try:
            active_issues = self.db.get_active_issues()

            upcoming_items = []
            warning_days = self.settings['overdue_warning_days']

            for issue in active_issues:
                expected_return = issue[7]  # expected_return_date
                if expected_return:
                    expected_date = datetime.strptime(expected_return, '%Y-%m-%d')
                    now = datetime.now()

                    # Проверяем, что срок наступает в ближайшие дни
                    if expected_date > now and (expected_date - now).days <= warning_days:
                        days_left = (expected_date - now).days
                        upcoming_items.append((issue, days_left))

            # Отправляем предупреждения
            if upcoming_items:
                self._send_upcoming_notification(upcoming_items)

        except Exception as e:
            print(f"Ошибка проверки предстоящих сроков: {e}")

    def _send_overdue_notification(self, overdue_items):
        """Отправка уведомления о просроченных возвратах"""
        try:
            # Группируем по уровню просрочки
            critical_overdue = []
            regular_overdue = []

            for issue, days in overdue_items:
                if days >= self.settings['overdue_critical_days']:
                    critical_overdue.append((issue, days))
                else:
                    regular_overdue.append((issue, days))

            # Отправляем критические уведомления
            if critical_overdue:
                self._send_critical_overdue_notification(critical_overdue)

            # Отправляем обычные уведомления
            if regular_overdue:
                self._send_regular_overdue_notification(regular_overdue)

        except Exception as e:
            print(f"Ошибка отправки уведомления о просрочке: {e}")

    def _send_critical_overdue_notification(self, overdue_items):
        """Отправка критического уведомления о просрочке"""
        message = f"🚨 КРИТИЧЕСКАЯ ПРОСРОЧКА!\n\n"
        message += f"Обнаружено {len(overdue_items)} просроченных возвратов:\n\n"

        for issue, days in overdue_items[:5]:  # Максимум 5 в уведомлении
            instrument_name = issue[1]
            employee_name = issue[2]
            expected_return = issue[7]

            message += f"🔴 {instrument_name}\n"
            message += f"👤 {employee_name}\n"
            message += f"📅 Просрочено на {days} дней\n\n"

        if len(overdue_items) > 5:
            message += f"И ещё {len(overdue_items) - 5} просроченных возвратов...\n\n"

        message += "⚡ Требуется немедленное вмешательство!"

        # Отправляем уведомления
        self._send_notification("Критическая просрочка инструментов", message)

    def _send_regular_overdue_notification(self, overdue_items):
        """Отправка обычного уведомления о просрочке"""
        message = f"⚠️ ПРОСРОЧЕННЫЕ ВОЗВРАТЫ\n\n"
        message += f"Обнаружено {len(overdue_items)} просроченных возвратов:\n\n"

        for issue, days in overdue_items[:10]:  # Максимум 10 в уведомлении
            instrument_name = issue[1]
            employee_name = issue[2]
            expected_return = issue[7]

            message += f"🟡 {instrument_name}\n"
            message += f"👤 {employee_name}\n"
            message += f"📅 Просрочено на {days} дней\n\n"

        if len(overdue_items) > 10:
            message += f"И ещё {len(overdue_items) - 10} просроченных возвратов...\n\n"

        message += "📞 Необходимо связаться с сотрудниками для возврата."

        # Отправляем уведомления
        self._send_notification("Просроченные возвраты инструментов", message)

    def _send_upcoming_notification(self, upcoming_items):
        """Отправка уведомления о приближающихся сроках"""
        message = f"⏰ НАПОМИНАНИЕ О СРОКАХ ВОЗВРАТА\n\n"
        message += f"В ближайшие дни истекают сроки возврата {len(upcoming_items)} инструментов:\n\n"

        for issue, days_left in upcoming_items[:10]:  # Максимум 10 в уведомлении
            instrument_name = issue[1]
            employee_name = issue[2]
            expected_return = issue[7]

            urgency_icon = "🔴" if days_left == 0 else "🟡" if days_left == 1 else "🟢"

            message += f"{urgency_icon} {instrument_name}\n"
            message += f"👤 {employee_name}\n"
            message += f"📅 Возврат через {days_left} дней ({expected_return})\n\n"

        if len(upcoming_items) > 10:
            message += f"И ещё {len(upcoming_items) - 10} напоминаний...\n\n"

        message += "💡 Рекомендуется напомнить сотрудникам о необходимости возврата."

        # Отправляем уведомления (только desktop, без telegram для напоминаний)
        if self.settings['enable_desktop_notifications']:
            self._show_desktop_notification("Напоминание о возвратах", message)

    def _send_notification(self, title, message):
        """Отправка уведомления всеми доступными способами"""
        # Desktop уведомление
        if self.settings['enable_desktop_notifications']:
            self._show_desktop_notification(title, message)

        # Telegram уведомление
        if self.settings['enable_telegram_notifications'] and self.telegram_bot:
            try:
                self.telegram_bot.send_overdue_notification()
            except Exception as e:
                print(f"Ошибка отправки Telegram уведомления: {e}")

    def _show_desktop_notification(self, title, message):
        """Поставить desktop уведомление в очередь для обработки в главном потоке"""
        try:
            # Помещаем уведомление в очередь для обработки в главном потоке
            self.notification_queue.put((title, message))
        except Exception as e:
            print(f"Ошибка постановки уведомления в очередь: {e}")

    def get_pending_notifications(self):
        """Получить все ожидающие уведомления из очереди"""
        notifications = []
        try:
            while not self.notification_queue.empty():
                notifications.append(self.notification_queue.get_nowait())
        except queue.Empty:
            pass
        return notifications

    def update_settings(self, new_settings):
        """Обновление настроек уведомлений"""
        self.settings.update(new_settings)
        self.save_settings()

    def get_overdue_summary(self):
        """Получение сводки по просроченным возвратах"""
        try:
            active_issues = self.db.get_active_issues()

            overdue_summary = {
                'total_overdue': 0,
                'critical_overdue': 0,
                'upcoming_deadlines': 0,
                'overdue_items': []
            }

            for issue in active_issues:
                expected_return = issue[7]
                if expected_return:
                    expected_date = datetime.strptime(expected_return, '%Y-%m-%d')
                    now = datetime.now()

                    if now > expected_date:
                        overdue_days = (now - expected_date).days
                        overdue_summary['total_overdue'] += 1

                        if overdue_days >= self.settings['overdue_critical_days']:
                            overdue_summary['critical_overdue'] += 1

                        overdue_summary['overdue_items'].append({
                            'instrument': issue[1],
                            'employee': issue[2],
                            'expected_return': expected_return,
                            'overdue_days': overdue_days
                        })
                    elif (expected_date - now).days <= self.settings['overdue_warning_days']:
                        overdue_summary['upcoming_deadlines'] += 1

            return overdue_summary

        except Exception as e:
            print(f"Ошибка получения сводки просрочек: {e}")
            return {
                'total_overdue': 0,
                'critical_overdue': 0,
                'upcoming_deadlines': 0,
                'overdue_items': []
            }


# Глобальный экземпляр менеджера уведомлений
notification_manager = None

def init_notification_manager(db_manager, telegram_bot=None):
    """Инициализация глобального менеджера уведомлений"""
    global notification_manager
    notification_manager = NotificationManager(db_manager, telegram_bot)
    return notification_manager

def start_notifications():
    """Запуск системы уведомлений"""
    global notification_manager
    if notification_manager:
        notification_manager.start_monitoring()

def stop_notifications():
    """Остановка системы уведомлений"""
    global notification_manager
    if notification_manager:
        notification_manager.stop_monitoring()

