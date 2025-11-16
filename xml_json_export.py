"""
Модуль для экспорта данных в XML и JSON форматы
"""

import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import os


class XMLJSONExporter:
    """Класс для экспорта данных в XML и JSON форматы"""

    def __init__(self):
        pass

    def export_to_json(self, data, output_path, data_type='instruments'):
        """Экспорт данных в JSON формат"""
        try:
            # Структура данных
            export_data = {
                'export_info': {
                    'timestamp': datetime.now().isoformat(),
                    'data_type': data_type,
                    'total_records': len(data)
                },
                'data': []
            }

            # Преобразуем данные в зависимости от типа
            if data_type == 'instruments':
                for item in data:
                    instrument = {
                        'id': item[0],
                        'name': item[1],
                        'inventory_number': item[2],
                        'serial_number': item[3] if len(item) > 3 else '',
                        'category': item[4] if len(item) > 4 else '',
                        'current_address': item[5] if len(item) > 5 else '',
                        'status': item[6] if len(item) > 6 else '',
                        'photo_path': item[7] if len(item) > 7 else ''
                    }
                    export_data['data'].append(instrument)

            elif data_type == 'employees':
                for item in data:
                    employee = {
                        'id': item[0],
                        'full_name': item[1],
                        'position': item[2] if len(item) > 2 else '',
                        'department': item[3] if len(item) > 3 else '',
                        'phone': item[4] if len(item) > 4 else '',
                        'email': item[5] if len(item) > 5 else '',
                        'status': item[6] if len(item) > 6 else '',
                        'photo_path': item[7] if len(item) > 7 else ''
                    }
                    export_data['data'].append(employee)

            elif data_type == 'issues':
                for item in data:
                    issue = {
                        'id': item[0],
                        'batch_id': item[1] if len(item) > 1 else None,
                        'instrument_id': item[2] if len(item) > 2 else '',
                        'employee_id': item[3] if len(item) > 3 else '',
                        'address_id': item[4] if len(item) > 4 else None,
                        'issue_date': item[5] if len(item) > 5 else '',
                        'expected_return_date': item[6] if len(item) > 6 else '',
                        'actual_return_date': item[7] if len(item) > 7 else None,
                        'status': item[8] if len(item) > 8 else '',
                        'notes': item[9] if len(item) > 9 else '',
                        'issued_by': item[10] if len(item) > 10 else '',
                        'address_name': item[11] if len(item) > 11 else '',
                        'address_full': item[12] if len(item) > 12 else '',
                        'instrument_name': item[13] if len(item) > 13 else '',
                        'inventory_number': item[14] if len(item) > 14 else '',
                        'employee_name': item[15] if len(item) > 15 else ''
                    }
                    export_data['data'].append(issue)

            elif data_type == 'history':
                for item in data:
                    record = {
                        'operation_id': item[0] if len(item) > 0 else '',
                        'operation_type': item[1] if len(item) > 1 else '',
                        'inventory_number': item[2] if len(item) > 2 else '',
                        'instrument_name': item[3] if len(item) > 3 else '',
                        'employee_name': item[4] if len(item) > 4 else '',
                        'address': item[5] if len(item) > 5 else '',
                        'operation_date': item[6] if len(item) > 6 else '',
                        'performed_by': item[7] if len(item) > 7 else '',
                        'notes': item[8] if len(item) > 8 else ''
                    }
                    export_data['data'].append(record)

            # Записываем в файл
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            return True, f"Данные успешно экспортированы в JSON ({len(data)} записей)"

        except Exception as e:
            return False, f"Ошибка экспорта в JSON: {e}"

    def export_to_xml(self, data, output_path, data_type='instruments'):
        """Экспорт данных в XML формат"""
        try:
            # Создаем корневой элемент
            root_name = f"{data_type}_export"
            root = ET.Element(root_name)

            # Добавляем информацию об экспорте
            export_info = ET.SubElement(root, "export_info")
            ET.SubElement(export_info, "timestamp").text = datetime.now().isoformat()
            ET.SubElement(export_info, "data_type").text = data_type
            ET.SubElement(export_info, "total_records").text = str(len(data))

            # Создаем контейнер для данных
            data_container = ET.SubElement(root, "data")

            # Преобразуем данные в зависимости от типа
            if data_type == 'instruments':
                for item in data:
                    instrument = ET.SubElement(data_container, "instrument")
                    instrument.set("id", str(item[0]))

                    ET.SubElement(instrument, "name").text = item[1] or ""
                    ET.SubElement(instrument, "inventory_number").text = item[2] or ""
                    ET.SubElement(instrument, "serial_number").text = item[3] if len(item) > 3 and item[3] else ""
                    ET.SubElement(instrument, "category").text = item[4] if len(item) > 4 and item[4] else ""
                    ET.SubElement(instrument, "current_address").text = item[5] if len(item) > 5 and item[5] else ""
                    ET.SubElement(instrument, "status").text = item[6] if len(item) > 6 and item[6] else ""
                    ET.SubElement(instrument, "photo_path").text = item[7] if len(item) > 7 and item[7] else ""

            elif data_type == 'employees':
                for item in data:
                    employee = ET.SubElement(data_container, "employee")
                    employee.set("id", str(item[0]))

                    ET.SubElement(employee, "full_name").text = item[1] or ""
                    ET.SubElement(employee, "position").text = item[2] if len(item) > 2 and item[2] else ""
                    ET.SubElement(employee, "department").text = item[3] if len(item) > 3 and item[3] else ""
                    ET.SubElement(employee, "phone").text = item[4] if len(item) > 4 and item[4] else ""
                    ET.SubElement(employee, "email").text = item[5] if len(item) > 5 and item[5] else ""
                    ET.SubElement(employee, "status").text = item[6] if len(item) > 6 and item[6] else ""
                    ET.SubElement(employee, "photo_path").text = item[7] if len(item) > 7 and item[7] else ""

            elif data_type == 'issues':
                for item in data:
                    issue = ET.SubElement(data_container, "issue")
                    issue.set("id", str(item[0]))

                    if len(item) > 1 and item[1]:
                        ET.SubElement(issue, "batch_id").text = str(item[1])
                    ET.SubElement(issue, "instrument_id").text = str(item[2]) if len(item) > 2 else ""
                    ET.SubElement(issue, "employee_id").text = str(item[3]) if len(item) > 3 else ""
                    if len(item) > 4 and item[4]:
                        ET.SubElement(issue, "address_id").text = str(item[4])
                    ET.SubElement(issue, "issue_date").text = item[5] if len(item) > 5 and item[5] else ""
                    ET.SubElement(issue, "expected_return_date").text = item[6] if len(item) > 6 and item[6] else ""
                    if len(item) > 7 and item[7]:
                        ET.SubElement(issue, "actual_return_date").text = item[7]
                    ET.SubElement(issue, "status").text = item[8] if len(item) > 8 and item[8] else ""
                    ET.SubElement(issue, "notes").text = item[9] if len(item) > 9 and item[9] else ""
                    ET.SubElement(issue, "issued_by").text = item[10] if len(item) > 10 and item[10] else ""
                    ET.SubElement(issue, "address_name").text = item[11] if len(item) > 11 and item[11] else ""
                    ET.SubElement(issue, "address_full").text = item[12] if len(item) > 12 and item[12] else ""
                    ET.SubElement(issue, "instrument_name").text = item[13] if len(item) > 13 and item[13] else ""
                    ET.SubElement(issue, "inventory_number").text = item[14] if len(item) > 14 and item[14] else ""
                    ET.SubElement(issue, "employee_name").text = item[15] if len(item) > 15 and item[15] else ""

            elif data_type == 'history':
                for item in data:
                    record = ET.SubElement(data_container, "operation")
                    record.set("id", str(item[0]) if len(item) > 0 and item[0] else "")

                    ET.SubElement(record, "operation_type").text = item[1] if len(item) > 1 and item[1] else ""
                    ET.SubElement(record, "inventory_number").text = item[2] if len(item) > 2 and item[2] else ""
                    ET.SubElement(record, "instrument_name").text = item[3] if len(item) > 3 and item[3] else ""
                    ET.SubElement(record, "employee_name").text = item[4] if len(item) > 4 and item[4] else ""
                    ET.SubElement(record, "address").text = item[5] if len(item) > 5 and item[5] else ""
                    ET.SubElement(record, "operation_date").text = item[6] if len(item) > 6 and item[6] else ""
                    ET.SubElement(record, "performed_by").text = item[7] if len(item) > 7 and item[7] else ""
                    ET.SubElement(record, "notes").text = item[8] if len(item) > 8 and item[8] else ""

            # Преобразуем в строку с красивым форматированием
            rough_string = ET.tostring(root, encoding='unicode')
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ", encoding=None)

            # Записываем в файл
            with open(output_path, 'w', encoding='utf-8') as f:
                # Убираем лишние пустые строки
                lines = pretty_xml.split('\n')
                filtered_lines = [line for line in lines if line.strip()]
                f.write('\n'.join(filtered_lines))

            return True, f"Данные успешно экспортированы в XML ({len(data)} записей)"

        except Exception as e:
            return False, f"Ошибка экспорта в XML: {e}"




