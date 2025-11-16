#!/usr/bin/env python3
"""
Создание иконки для exe файла
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    """Создание простой иконки для приложения"""

    # Размер иконки (стандартный для Windows)
    size = (256, 256)

    # Создаем новое изображение с прозрачным фоном
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Основной цвет (темно-синий)
    primary_color = (31, 97, 141)  # Темно-синий как в интерфейсе

    # Рисуем фон круга
    center = (size[0] // 2, size[1] // 2)
    radius = 100
    draw.ellipse(
        [(center[0] - radius, center[1] - radius),
         (center[0] + radius, center[1] + radius)],
        fill=primary_color
    )

    # Добавляем светлый круг внутри
    inner_radius = 70
    draw.ellipse(
        [(center[0] - inner_radius, center[1] - inner_radius),
         (center[0] + inner_radius, center[1] + inner_radius)],
        fill=(70, 150, 180)
    )

    # Рисуем гаечный ключ (простая форма)
    # Ручка
    draw.rectangle(
        [(center[0] - 15, center[1] + 10), (center[0] + 15, center[1] + 40)],
        fill=(255, 255, 255)
    )

    # Головка ключа
    draw.rectangle(
        [(center[0] - 25, center[1] - 15), (center[0] - 5, center[1] + 15)],
        fill=(255, 255, 255)
    )

    # Отверстие в головке
    draw.rectangle(
        [(center[0] - 20, center[1] - 5), (center[0] - 10, center[1] + 5)],
        fill=primary_color
    )

    # Добавляем текст "TM" по центру
    try:
        # Пробуем загрузить шрифт
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        # Если шрифт не найден, используем дефолтный
        font = ImageFont.load_default()

    # Добавляем текст
    text = "TM"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    draw.text(
        (center[0] - text_width // 2, center[1] - text_height // 2 - 10),
        text,
        fill=(255, 255, 255),
        font=font
    )

    # Сохраняем как ICO
    icon_path = "icon.ico"
    img.save(icon_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

    print(f"✅ Иконка создана: {icon_path}")
    return icon_path

if __name__ == "__main__":
    create_icon()
