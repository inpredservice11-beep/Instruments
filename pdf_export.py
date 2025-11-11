"""
Модуль для экспорта данных в PDF
"""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os
import platform


class PDFExporter:
    """Класс для экспорта данных в PDF"""
    
    def __init__(self):
        self.page_width, self.page_height = A4
        self.styles = getSampleStyleSheet()
        self._register_fonts()
        self._setup_styles()
    
    def _register_fonts(self):
        """Регистрация шрифтов с поддержкой кириллицы"""
        try:
            # Пытаемся использовать системные шрифты Windows
            if platform.system() == 'Windows':
                # Пути к стандартным шрифтам Windows
                font_paths = [
                    r'C:\Windows\Fonts\arial.ttf',
                    r'C:\Windows\Fonts\arialbd.ttf',
                    r'C:\Windows\Fonts\times.ttf',
                    r'C:\Windows\Fonts\timesbd.ttf',
                ]
                
                # Регистрируем Arial
                if os.path.exists(font_paths[0]):
                    pdfmetrics.registerFont(TTFont('Arial', font_paths[0]))
                    if os.path.exists(font_paths[1]):
                        pdfmetrics.registerFont(TTFont('Arial-Bold', font_paths[1]))
                    self.font_name = 'Arial'
                    self.font_bold = 'Arial-Bold'
                    return
                
                # Регистрируем Times New Roman
                if os.path.exists(font_paths[2]):
                    pdfmetrics.registerFont(TTFont('Times', font_paths[2]))
                    if os.path.exists(font_paths[3]):
                        pdfmetrics.registerFont(TTFont('Times-Bold', font_paths[3]))
                    self.font_name = 'Times'
                    self.font_bold = 'Times-Bold'
                    return
            
            # Если системные шрифты не найдены, используем DejaVu Sans
            # (требует установки reportlab-fonts или можно скачать шрифты)
            try:
                from reportlab.pdfbase.cidfonts import UnicodeCIDFont
                pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
                self.font_name = 'HeiseiMin-W3'
                self.font_bold = 'HeiseiMin-W3'
            except:
                # Используем стандартный шрифт (может не поддерживать кириллицу)
                self.font_name = 'Helvetica'
                self.font_bold = 'Helvetica-Bold'
        except Exception as e:
            # В случае ошибки используем стандартные шрифты
            self.font_name = 'Helvetica'
            self.font_bold = 'Helvetica-Bold'
    
    def _setup_styles(self):
        """Настройка стилей для PDF"""
        # Заголовок документа
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=1,  # Центрирование
            fontName=getattr(self, 'font_bold', 'Helvetica-Bold')
        )
        
        # Подзаголовок
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#666666'),
            spaceAfter=20,
            alignment=1,
            fontName=getattr(self, 'font_name', 'Helvetica')
        )
        
        # Обычный текст
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName=getattr(self, 'font_name', 'Helvetica')
        )
        
        # Заголовок таблицы
        self.table_header_style = ParagraphStyle(
            'TableHeader',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.white,
            fontName=getattr(self, 'font_bold', 'Helvetica-Bold')
        )
    
    def export_issues_journal(self, issues_data, output_path, title="Журнал выдачи инструмента"):
        """Экспорт журнала выдачи инструмента в PDF
        
        Args:
            issues_data: список кортежей с данными о выдачах
            output_path: путь для сохранения PDF файла
            title: заголовок документа
        """
        # Используем альбомную ориентацию для лучшего размещения таблицы
        doc = SimpleDocTemplate(
            output_path,
            pagesize=landscape(A4),
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=15*mm
        )
        
        story = []
        
        # Заголовок
        story.append(Paragraph(title, self.title_style))
        story.append(Paragraph(
            f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            self.subtitle_style
        ))
        story.append(Spacer(1, 12*mm))
        
        # Подготовка данных для таблицы
        if not issues_data:
            story.append(Paragraph("Нет данных для отображения", self.normal_style))
        else:
            # Заголовки таблицы
            headers = ['№', 'Инв. номер', 'Инструмент', 'Сотрудник', 
                      'Адрес', 'Дата выдачи', 'Ожид. возврат', 'Выдал', 'Примечание']
            
            # Подготовка данных с использованием Paragraph для поддержки кириллицы
            table_data = []
            
            # Заголовки
            header_row = []
            for header in headers:
                header_row.append(Paragraph(header, self.table_header_style))
            table_data.append(header_row)
            
            for idx, issue in enumerate(issues_data, 1):
                # Форматирование даты
                issue_date = self._format_date(issue[5]) if len(issue) > 5 else ''
                expected_return = self._format_date(issue[6]) if len(issue) > 6 else ''
                
                # Используем Paragraph для всех ячеек для поддержки кириллицы
                row = [
                    Paragraph(str(idx), self.normal_style),
                    Paragraph(str(issue[1]) if len(issue) > 1 else '', self.normal_style),  # Инв. номер
                    Paragraph(str(issue[2]) if len(issue) > 2 else '', self.normal_style),  # Инструмент
                    Paragraph(str(issue[3]) if len(issue) > 3 else '', self.normal_style),  # Сотрудник
                    Paragraph(str(issue[4]) if len(issue) > 4 else '', self.normal_style),  # Адрес
                    Paragraph(issue_date, self.normal_style),
                    Paragraph(expected_return, self.normal_style),
                    Paragraph(str(issue[7]) if len(issue) > 7 else '', self.normal_style),  # Выдал
                    Paragraph(str(issue[8]) if len(issue) > 8 else '', self.normal_style)  # Примечание
                ]
                table_data.append(row)
            
            # Создание таблицы
            table = Table(table_data, repeatRows=1)
            
            # Вычисляем доступную ширину (альбомная ориентация A4 минус отступы)
            available_width = landscape(A4)[0] - 30*mm  # минус левый и правый отступы
            total_cols = 9
            
            # Стилизация таблицы
            table.setStyle(TableStyle([
                # Заголовок
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), getattr(self, 'font_bold', 'Helvetica-Bold')),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                
                # Чередование цветов строк
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
                
                # Границы
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                
                # Размеры столбцов (оптимизированы для альбомной ориентации)
                ('COLWIDTH', (0, 0), (0, -1), 15*mm),  # №
                ('COLWIDTH', (1, 0), (1, -1), 22*mm),  # Инв. номер
                ('COLWIDTH', (2, 0), (2, -1), 35*mm),  # Инструмент
                ('COLWIDTH', (3, 0), (3, -1), 30*mm),  # Сотрудник
                ('COLWIDTH', (4, 0), (4, -1), 40*mm),  # Адрес
                ('COLWIDTH', (5, 0), (5, -1), 25*mm),  # Дата выдачи
                ('COLWIDTH', (6, 0), (6, -1), 25*mm),  # Ожид. возврат
                ('COLWIDTH', (7, 0), (7, -1), 22*mm),  # Выдал
                ('COLWIDTH', (8, 0), (8, -1), 35*mm),  # Примечание
                
                # Перенос текста
                ('WORDWRAP', (0, 0), (-1, -1), True),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ]))
            
            story.append(table)
        
        # Итоговая информация
        story.append(Spacer(1, 10*mm))
        story.append(Paragraph(
            f"<b>Всего записей:</b> {len(issues_data)}",
            self.normal_style
        ))
        
        # Генерация PDF
        doc.build(story)
    
    def _format_date(self, date_str):
        """Форматирование даты для отображения"""
        if not date_str:
            return ''
        
        try:
            # Пробуем разные форматы
            if ' ' in str(date_str):
                dt = datetime.strptime(str(date_str), '%Y-%m-%d %H:%M:%S')
                return dt.strftime('%d.%m.%Y %H:%M')
            else:
                dt = datetime.strptime(str(date_str), '%Y-%m-%d')
                return dt.strftime('%d.%m.%Y')
        except:
            return str(date_str)
    
    def export_all_issues(self, db_manager, output_path, include_returned=False):
        """Экспорт всех выдач (активных и/или возвращенных)
        
        Args:
            db_manager: экземпляр DatabaseManager
            output_path: путь для сохранения PDF
            include_returned: включать ли возвращенные инструменты
        """
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        if include_returned:
            # Все выдачи (активные и возвращенные)
            query = """
                SELECT 
                    i.id,
                    ins.inventory_number,
                    ins.name,
                    e.full_name,
                    COALESCE(NULLIF(a.full_address, ''), a.name, ''),
                    datetime(i.issue_date, 'localtime'),
                    i.expected_return_date,
                    i.issued_by,
                    i.notes,
                    i.status
                FROM issues i
                JOIN instruments ins ON i.instrument_id = ins.id
                JOIN employees e ON i.employee_id = e.id
                LEFT JOIN addresses a ON i.address_id = a.id
                ORDER BY i.issue_date DESC
            """
        else:
            # Только активные выдачи
            query = """
                SELECT 
                    i.id,
                    ins.inventory_number,
                    ins.name,
                    e.full_name,
                    COALESCE(NULLIF(a.full_address, ''), a.name, ''),
                    datetime(i.issue_date, 'localtime'),
                    i.expected_return_date,
                    i.issued_by,
                    i.notes
                FROM issues i
                JOIN instruments ins ON i.instrument_id = ins.id
                JOIN employees e ON i.employee_id = e.id
                LEFT JOIN addresses a ON i.address_id = a.id
                WHERE i.status = 'Выдан'
                ORDER BY i.issue_date DESC
            """
        
        cursor.execute(query)
        issues = cursor.fetchall()
        conn.close()
        
        title = "Журнал выдачи инструмента" + (" (все записи)" if include_returned else " (активные)")
        self.export_issues_journal(issues, output_path, title)

