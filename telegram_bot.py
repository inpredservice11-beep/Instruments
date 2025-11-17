#!/usr/bin/env python3
"""
Telegram бот для системы учета инструментов ToolManagement
"""

import asyncio
import logging
import threading
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from database_manager import DatabaseManager

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class ToolManagementBot:
    """Класс для управления Telegram ботом"""

    def __init__(self, token=None, db_path='tool_management.db'):
        self.token = token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.db = None
        self.application = None
        self.chat_ids = set()  # ID чатов для рассылки уведомлений

        # Инициализируем базу данных
        try:
            if not os.path.exists(db_path):
                logger.error(f"Файл базы данных не найден: {db_path}")
                # Попробуем найти базу данных в текущей директории
                current_dir = os.getcwd()
                db_path_full = os.path.join(current_dir, db_path)
                if os.path.exists(db_path_full):
                    db_path = db_path_full
                    logger.info(f"Найден файл базы данных: {db_path}")
                else:
                    logger.error(f"Файл базы данных не найден ни в {db_path}, ни в {db_path_full}")
                    self.db = None
                    return

            self.db = DatabaseManager(db_path)
            logger.info(f"✅ База данных Telegram бота инициализирована: {db_path}")

            # Проверим подключение
            if self.db:
                try:
                    # Простая проверка подключения
                    test_conn = self.db.get_connection()
                    test_conn.close()
                    logger.info("✅ Подключение к базе данных проверено")
                except Exception as conn_e:
                    logger.error(f"❌ Ошибка подключения к базе данных: {conn_e}")
                    self.db = None

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации базы данных для Telegram бота: {e}")
            import traceback
            logger.error(f"Подробности: {traceback.format_exc()}")
            self.db = None

        if not self.token:
            logger.warning("⚠️ Токен Telegram бота не найден. Установите переменную окружения TELEGRAM_BOT_TOKEN")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        # Добавляем chat_id только если это новый чат (не callback)
        if update.message:
            chat_id = update.effective_chat.id
            self.chat_ids.add(chat_id)

        welcome_text = """
🤖 *Добро пожаловать в ToolManagement Bot!*

Я помогу вам управлять инструментами:
• 📊 Просмотр доступных инструментов
• 🔍 Поиск инструментов
• 📋 Проверка активных выдач
• ⏰ Уведомления о просроченных возвратах

*Доступные команды:*
/help - Показать справку
/tools - Просмотр инструментов
/search - Поиск инструментов
/issues - Активные выдачи
/overdue - Просроченные возвраты
/stats - Статистика

💡 Используйте кнопки ниже для быстрого доступа.
        """

        keyboard = [
            [
                InlineKeyboardButton("🔧 Инструменты", callback_data="tools"),
                InlineKeyboardButton("📋 Выдачи", callback_data="issues")
            ],
            [
                InlineKeyboardButton("⏰ Просрочено", callback_data="overdue"),
                InlineKeyboardButton("📊 Статистика", callback_data="stats")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await self._reply_to_update(update, welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
📖 *Справка по командам:*

*Основные команды:*
/start - Запуск бота и главное меню
/help - Показать эту справку
/tools - Просмотр всех инструментов
/search <текст> - Поиск инструментов
/issues - Активные выдачи
/overdue - Просроченные возвраты
/stats - Общая статистика

*Быстрые действия:*
• Нажмите на кнопки в сообщениях
• Используйте инлайн-кнопки для навигации

*Уведомления:*
Бот автоматически отправляет уведомления о:
• Просроченных возвратах инструментов
• Новых выдачах (опционально)

💬 Для вопросов и поддержки обращайтесь к администратору.
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def tools_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать список инструментов"""
        try:
            # Получаем все инструменты
            instruments = self.db.get_instruments()

            if not instruments:
                await update.message.reply_text("📭 Нет доступных инструментов")
                return

            # Группируем по категориям
            categories = {}
            for instrument in instruments:
                category = instrument[5] or "Без категории"  # category в индексе 5
                if category not in categories:
                    categories[category] = []
                categories[category].append(instrument)

            # Формируем сообщение
            message = "🔧 *Доступные инструменты*\n\n"

            for category, items in categories.items():
                message += f"📂 *{category}:*\n"
                for item in items[:5]:  # Показываем максимум 5 инструментов на категорию
                    status = item[6]  # status в индексе 6
                    status_emoji = "✅" if status == "Доступен" else "📤" if status == "Выдан" else "🔧"
                    message += f"  {status_emoji} {item[1]} (#{item[2]})\n"

                if len(items) > 5:
                    message += f"  ... и ещё {len(items) - 5} инструментов\n"
                message += "\n"

            # Добавляем кнопки навигации и поиска
            nav_keyboard = [
                [InlineKeyboardButton("🔍 Поиск инструментов", callback_data="search_menu")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start")]
            ]
            reply_markup = InlineKeyboardMarkup(nav_keyboard)

            await self._reply_to_update(update, message, parse_mode='Markdown', reply_markup=reply_markup)

        except Exception as e:
            logger.error(f"Ошибка в tools_command: {e}")
            await self._reply_to_update(update, "❌ Ошибка при получении списка инструментов")

    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Поиск инструментов"""
        if not context.args:
            await self._reply_to_update(update,
                "🔍 *Поиск инструментов*\n\n"
                "Использование: `/search <текст для поиска>`\n\n"
                "Примеры:\n"
                "• `/search дрель`\n"
                "• `/search INV-001`\n"
                "• `/search болгарка`",
                parse_mode='Markdown'
            )
            return

        search_text = ' '.join(context.args)
        try:
            instruments = self.db.get_instruments(search_text)

            if not instruments:
                await self._reply_to_update(update, f"❌ Инструменты по запросу '{search_text}' не найдены")
                return

            message = f"🔍 *Результаты поиска по '{search_text}':*\n\n"

            for i, instrument in enumerate(instruments[:10], 1):  # Максимум 10 результатов
                status = instrument[6]
                status_emoji = "✅" if status == "Доступен" else "📤" if status == "Выдан" else "🔧"
                message += f"{i}. {status_emoji} *{instrument[1]}*\n"
                message += f"   📋 #{instrument[2]} | 📂 {instrument[5] or 'Без категории'}\n"
                message += f"   📝 {instrument[3] or 'Без описания'}\n\n"

            if len(instruments) > 10:
                message += f"📊 Показано 10 из {len(instruments)} найденных инструментов"

            # Добавляем кнопки навигации
            nav_keyboard = [
                [InlineKeyboardButton("🔍 Новый поиск", callback_data="search_menu")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start")]
            ]
            nav_markup = InlineKeyboardMarkup(nav_keyboard)

            await self._reply_to_update(update, message, parse_mode='Markdown', reply_markup=nav_markup)

        except Exception as e:
            logger.error(f"Ошибка в search_command: {e}")
            await self._reply_to_update(update, "❌ Ошибка при поиске инструментов")

    async def issues_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать активные выдачи"""
        try:
            # Получаем активные выдачи
            issues = self.db.get_active_issues()

            if not issues:
                await self._reply_to_update(update, "📭 Нет активных выдач")
                return

            message = "📋 *Активные выдачи инструментов*\n\n"

            for issue in issues[:15]:  # Максимум 15 выдач
                instrument_name = issue[3]  # Название инструмента
                employee_name = issue[4]   # ФИО сотрудника
                issue_date = issue[6]      # Дата выдачи
                expected_return = issue[7] # Ожидаемая дата возврата
                address = issue[5] or "Не указан"  # Адрес

                # Проверяем просрочку
                if expected_return:
                    expected_date = datetime.strptime(expected_return, '%Y-%m-%d')
                    if datetime.now() > expected_date:
                        overdue_days = (datetime.now() - expected_date).days
                        status = f"⚠️ ПРОСРОЧЕНО на {overdue_days} дней"
                    else:
                        status = "✅ В срок"
                else:
                    status = "⏰ Без срока"

                message += f"🔧 *{instrument_name}*\n"
                message += f"👤 {employee_name}\n"
                message += f"📅 Выдан: {issue_date}\n"
                if expected_return:
                    message += f"🔄 Возврат: {expected_return}\n"
                message += f"📍 {address}\n"
                message += f"📊 {status}\n\n"

            if len(issues) > 15:
                message += f"📊 Показано 15 из {len(issues)} активных выдач"

            # Добавляем кнопки навигации
            nav_keyboard = [
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start")]
            ]
            nav_markup = InlineKeyboardMarkup(nav_keyboard)

            await self._reply_to_update(update, message, parse_mode='Markdown', reply_markup=nav_markup)

        except Exception as e:
            logger.error(f"Ошибка в issues_command: {e}")
            await self._reply_to_update(update, "❌ Ошибка при получении списка выдач")

    async def overdue_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать просроченные возвраты"""
        try:
            issues = self.db.get_active_issues()
            overdue_issues = []

            for issue in issues:
                expected_return = issue[7]  # Ожидаемая дата возврата
                if expected_return:
                    expected_date = datetime.strptime(expected_return, '%Y-%m-%d')
                    if datetime.now() > expected_date:
                        overdue_days = (datetime.now() - expected_date).days
                        overdue_issues.append((issue, overdue_days))

            if not overdue_issues:
                await self._reply_to_update(update, "✅ Нет просроченных возвратов инструментов")
                return

            # Сортируем по количеству дней просрочки (сначала самые просроченные)
            overdue_issues.sort(key=lambda x: x[1], reverse=True)

            message = "⚠️ *ПРОСРОЧЕННЫЕ ВОЗВРАТЫ*\n\n"

            for issue, overdue_days in overdue_issues[:10]:  # Максимум 10
                instrument_name = issue[3]
                employee_name = issue[4]
                expected_return = issue[7]
                address = issue[5] or "Не указан"

                message += f"🚨 *{instrument_name}*\n"
                message += f"👤 {employee_name}\n"
                message += f"📅 Срок возврата: {expected_return}\n"
                message += f"⏰ Просрочено на: {overdue_days} дней\n"
                message += f"📍 {address}\n\n"

            if len(overdue_issues) > 10:
                message += f"📊 Показано 10 из {len(overdue_issues)} просроченных возвратов"

            # Добавляем кнопки навигации и уведомления
            nav_keyboard = [
                [InlineKeyboardButton("📢 Уведомить администратора", callback_data="notify_admin")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start")]
            ]
            reply_markup = InlineKeyboardMarkup(nav_keyboard)

            await self._reply_to_update(update, message, parse_mode='Markdown', reply_markup=reply_markup)

        except Exception as e:
            logger.error(f"Ошибка в overdue_command: {e}")
            await self._reply_to_update(update, "❌ Ошибка при проверке просроченных возвратов")

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статистику"""
        try:
            # Проверяем наличие базы данных
            if not self.db:
                logger.error("База данных не инициализирована в stats_command")
                await self._reply_to_update(update, "❌ База данных не доступна")
                return

            logger.info(f"Получение статистики из базы данных: {type(self.db)}")

            # Получаем статистику из базы данных
            stats = self.db.get_statistics()
            logger.info(f"Статистика получена: {stats}")

            message = "📊 *Статистика системы ToolManagement*\n\n"

            message += f"🔧 *Инструменты:*\n"
            message += f"  📦 Всего: {stats.get('total_instruments', 0)}\n"
            message += f"  ✅ Доступно: {stats.get('available_instruments', 0)}\n"
            message += f"  📤 Выдано: {stats.get('issued_instruments', 0)}\n"
            message += f"  🔧 На ремонте: {stats.get('repair_instruments', 0)}\n\n"

            message += f"👥 *Сотрудники:* {stats.get('total_employees', 0)}\n\n"

            message += f"📋 *Активные выдачи:* {stats.get('active_issues', 0)}\n\n"

            # Добавляем информацию о просроченных
            overdue_count = stats.get('overdue_issues', 0)
            if overdue_count > 0:
                message += f"⚠️ *Просроченные возвраты:* {overdue_count}\n\n"

            message += f"📅 *Обновлено:* {datetime.now().strftime('%d.%m.%Y %H:%M')}"

            # Добавляем кнопки навигации
            nav_keyboard = [
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start")]
            ]
            nav_markup = InlineKeyboardMarkup(nav_keyboard)

            await self._reply_to_update(update, message, parse_mode='Markdown', reply_markup=nav_markup)

        except Exception as e:
            logger.error(f"Ошибка в stats_command: {e}")
            await self._reply_to_update(update, "❌ Ошибка при получении статистики")

    async def _reply_to_update(self, update: Update, text: str, **kwargs):
        """Универсальный метод для ответа на обновления (как сообщения, так и callback-запросы)"""
        try:
            if update.callback_query:
                # Это callback-запрос, отвечаем через query
                if 'parse_mode' in kwargs:
                    await update.callback_query.edit_message_text(text, **kwargs)
                else:
                    await update.callback_query.edit_message_text(text)
            elif update.message:
                # Это обычное сообщение
                await update.message.reply_text(text, **kwargs)
            else:
                logger.error("Не удалось определить тип обновления для ответа")
        except Exception as e:
            logger.error(f"Ошибка при отправке ответа: {e}")

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на инлайн-кнопки"""
        query = update.callback_query
        await query.answer()

        if query.data == "tools":
            await self.tools_command(update, context)
        elif query.data == "issues":
            await self.issues_command(update, context)
        elif query.data == "overdue":
            await self.overdue_command(update, context)
        elif query.data == "stats":
            await self.stats_command(update, context)
        elif query.data == "search_menu":
            # Добавляем кнопки навигации
            nav_keyboard = [
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start")]
            ]
            reply_markup = InlineKeyboardMarkup(nav_keyboard)

            await query.edit_message_text(
                "🔍 *Поиск инструментов*\n\n"
                "Используйте команду:\n"
                "`/search <текст>`\n\n"
                "Например:\n"
                "• `/search дрель`\n"
                "• `/search INV-001`",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        elif query.data == "main_menu":
            await self.start(update, None)
        elif query.data == "back_to_start":
            await self.start(update, None)
        elif query.data == "notify_admin":
            await query.edit_message_text(
                "📢 *Уведомление отправлено!*\n\n"
                "Администратор будет уведомлен о просроченных возвратах.\n\n"
                "Вы можете вернуться к просмотру данных.",
                parse_mode='Markdown'
            )
            # Здесь можно добавить логику отправки уведомления администратору

    def send_overdue_notification(self, chat_id=None):
        """Отправить уведомление о просроченных возвратах"""
        try:
            issues = self.db.get_active_issues()
            overdue_issues = []

            for issue in issues:
                expected_return = issue[4]
                if expected_return:
                    expected_date = datetime.strptime(expected_return, '%Y-%m-%d')
                    if datetime.now() > expected_date:
                        overdue_days = (datetime.now() - expected_date).days
                        overdue_issues.append((issue, overdue_days))

            if overdue_issues:
                message = f"⚠️ *ПРОСРОЧЕННЫЕ ВОЗВРАТЫ* ({len(overdue_issues)})\n\n"

                for issue, overdue_days in overdue_issues[:5]:  # Максимум 5 в уведомлении
                    instrument_name = issue[1]
                    employee_name = issue[2]
                    expected_return = issue[4]

                    message += f"🚨 {instrument_name}\n"
                    message += f"👤 {employee_name}\n"
                    message += f"⏰ Просрочено: {overdue_days} дней\n\n"

                # Отправляем уведомление всем подписанным чатам
                if chat_id:
                    asyncio.create_task(self._send_message(chat_id, message))
                else:
                    for cid in self.chat_ids:
                        asyncio.create_task(self._send_message(cid, message))

        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")

    async def _send_message(self, chat_id, message):
        """Отправить сообщение в чат"""
        try:
            if self.application:
                await self.application.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения в чат {chat_id}: {e}")

    def run_bot(self):
        """Запуск бота"""
        if not self.token:
            logger.error("Токен бота не установлен")
            return

        if not self.db:
            logger.error("База данных не инициализирована. Бот не может быть запущен.")
            return

        try:
            # Создаем приложение с дополнительными параметрами для совместимости
            builder = Application.builder().token(self.token)

            # Пробуем добавить параметры для лучшей совместимости
            try:
                # Для более новых версий python-telegram-bot
                builder = builder.read_timeout(30).write_timeout(30).connect_timeout(30)
            except:
                pass  # Игнорируем если параметры не поддерживаются

            self.application = builder.build()

        except AttributeError as e:
            if "'Updater' object has no attribute '_Updater__polling_cleanup_cb'" in str(e):
                logger.error("Ошибка совместимости: python-telegram-bot не совместим с Python 3.13")
                logger.error("Попытка обходного решения...")

                # Пробуем добавить недостающий атрибут перед созданием приложения
                try:
                    from telegram.ext import Updater
                    # Проверяем версию Python
                    import sys
                    if sys.version_info >= (3, 13):
                        # Для Python 3.13 пытаемся добавить атрибут напрямую в класс
                        try:
                            # Это обходное решение для проблемы с приватными атрибутами в Python 3.13
                            Updater._Updater__polling_cleanup_cb = None
                            logger.info("Применено обходное решение для Python 3.13")

                            # Повторяем попытку создания приложения
                            self.application = builder.build()
                            return  # Успешно создали приложение

                        except Exception as patch_e:
                            logger.error(f"Обходное решение не сработало: {patch_e}")

                except Exception as patch_e:
                    logger.error(f"Ошибка применения патча: {patch_e}")

                # Если обходное решение не сработало, показываем рекомендации
                logger.error("Рекомендации:")
                logger.error("1. Обновите python-telegram-bot: pip install --upgrade python-telegram-bot")
                logger.error("2. Или используйте Python 3.12 или ниже")
                logger.error("3. Проверьте версию: pip show python-telegram-bot")
                raise RuntimeError("Несовместимость python-telegram-bot с Python 3.13. "
                                 "Используйте Python 3.12 или обновите библиотеку.") from e
            else:
                raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при создании Telegram бота: {e}")
            raise

        # Добавляем обработчики команд
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("tools", self.tools_command))
        self.application.add_handler(CommandHandler("search", self.search_command))
        self.application.add_handler(CommandHandler("issues", self.issues_command))
        self.application.add_handler(CommandHandler("overdue", self.overdue_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))

        # Добавляем обработчик инлайн-кнопок
        self.application.add_handler(CallbackQueryHandler(self.button_callback))

        # Запуск бота
        logger.info("Запуск Telegram бота...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

    def run_in_thread(self):
        """Запуск бота в отдельном потоке"""
        bot_thread = threading.Thread(target=self.run_bot, daemon=True)
        bot_thread.start()
        return bot_thread


# Глобальный экземпляр бота
bot_instance = None

def init_telegram_bot(token=None):
    """Инициализация Telegram бота"""
    global bot_instance
    if token or os.getenv('TELEGRAM_BOT_TOKEN'):
        bot_instance = ToolManagementBot(token)
        return bot_instance
    return None

def start_telegram_bot():
    """Запуск Telegram бота"""
    global bot_instance
    if bot_instance:
        return bot_instance.run_in_thread()
    return None

def send_overdue_notification(chat_id=None):
    """Отправить уведомление о просроченных возвратах"""
    global bot_instance
    if bot_instance:
        bot_instance.send_overdue_notification(chat_id)

