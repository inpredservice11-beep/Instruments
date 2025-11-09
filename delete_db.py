import os

db_path = 'tool_management.db'

if os.path.exists(db_path):
    os.remove(db_path)
    print(f"✓ База данных {db_path} удалена")
else:
    print(f"База данных {db_path} не найдена")

print("\nТеперь запустите: python app.py")











