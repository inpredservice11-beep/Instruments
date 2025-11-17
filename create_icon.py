#!/usr/bin/env python3
"""
Создание иконки для exe файла
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    """Создание профессиональной иконки для приложения ToolManagement"""

    # Размер иконки (стандартный для Windows)
    size = (256, 256)

    # Создаем новое изображение с прозрачным фоном
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Основной цвет (темно-синий)
    primary_color = (31, 97, 141)  # Темно-синий как в интерфейсе

    # Рисуем фон круга
    center = (size[0] // 2, size[1] // 2)
    radius = 110
    draw.ellipse(
        [(center[0] - radius, center[1] - radius),
         (center[0] + radius, center[1] + radius)],
        fill=primary_color
    )

    # Добавляем градиентный эффект (светлый круг внутри)
    inner_radius = 85
    draw.ellipse(
        [(center[0] - inner_radius, center[1] - inner_radius),
         (center[0] + inner_radius, center[1] + inner_radius)],
        fill=(70, 150, 180)
    )

    # Рисуем гаечный ключ (улучшенная форма)
    # Ручка ключа
    draw.rectangle(
        [(center[0] - 8, center[1] + 15), (center[0] + 8, center[1] + 45)],
        fill=(255, 255, 255)
    )

    # Головка ключа (шестигранная)
    # Верхняя часть головки
    draw.polygon([
        (center[0] - 20, center[1] - 20),  # Левый верхний
        (center[0] - 5, center[1] - 35),   # Верхний
        (center[0] + 10, center[1] - 35),  # Правый верхний
        (center[0] + 25, center[1] - 20),  # Правый
        (center[0] + 25, center[1] - 5),   # Правый нижний
        (center[0] + 10, center[1] + 10),  # Нижний правый
        (center[0] - 5, center[1] + 10),   # Нижний левый
        (center[0] - 20, center[1] - 5),   # Левый нижний
    ], fill=(255, 255, 255))

    # Отверстие в головке (шестигранное)
    draw.polygon([
        (center[0] - 5, center[1] - 15),
        (center[0], center[1] - 20),
        (center[0] + 5, center[1] - 15),
        (center[0] + 5, center[1] - 10),
        (center[0], center[1] - 5),
        (center[0] - 5, center[1] - 10),
    ], fill=primary_color)

    # Добавляем тень/контур для глубины
    shadow_offset = 2
    draw.ellipse(
        [(center[0] - radius + shadow_offset, center[1] - radius + shadow_offset),
         (center[0] + radius + shadow_offset, center[1] + radius + shadow_offset)],
        fill=(20, 20, 20, 80)
    )

    # Добавляем текст "TM" по центру
    try:
        # Пробуем загрузить шрифт
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        # Если шрифт не найден, используем дефолтный
        font = ImageFont.load_default()

    # Добавляем текст
    text = "TM"
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        draw.text(
            (center[0] - text_width // 2, center[1] - text_height // 2 - 15),
            text,
            fill=(255, 255, 255),
            font=font
        )
    except:
        # Если textbbox не поддерживается, центрируем вручную
        draw.text(
            (center[0] - 20, center[1] - 30),
            text,
            fill=(255, 255, 255),
            font=font
        )

    # Сохраняем как ICO с разными размерами
    icon_path = "icon.ico"
    img.save(icon_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

    print(f"✅ Профессиональная иконка создана: {icon_path}")
    print("   📏 Размеры: 16x16, 32x32, 48x48, 64x64, 128x128, 256x256")
    print("   🎨 Дизайн: Гаечный ключ + градиент + тень")
    return icon_path

if __name__ == "__main__":
    create_icon()
