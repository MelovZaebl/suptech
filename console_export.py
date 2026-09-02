"""
Интерактивный консольный интерфейс для выгрузки данных.

Запуск:  python console_export.py

Зависимость: сначала запустите demo_chats.py для создания platform_state.json.

Меню:
  1. Все чаты — полная выгрузка всех чатов платформы
  2. Чаты по оператору — ввести ID оператора (например OP-001)
  3. Чаты по пользователю — ввести ID пользователя (например US-001)
  4. База операторов — профили всех операторов
  5. База пользователей — профили всех пользователей
  0. Выход
"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from support_platform import (
    SupportPlatform,
    export_all_chats,
    export_chats_by_operator,
    export_chats_by_user,
    export_operators_db,
    export_users_db,
)

# Загружаем состояние платформы из JSON-файла
with open("platform_state.json", "r", encoding="utf-8") as f:
    platform = SupportPlatform.from_dict(json.load(f))

print(f"Платформа: {len(platform.operators)} операторов, "
      f"{len(platform.users)} пользователей, "
      f"{len(platform.chats)} чатов\n")

# Пункты меню
MENU = {
    "1": "Все чаты",
    "2": "Чаты по оператору",
    "3": "Чаты по пользователю",
    "4": "База операторов",
    "5": "База пользователей",
}

# Основной цикл интерфейса
while True:
    print("=== Меню выгрузок ===")
    for k, v in MENU.items():
        print(f"  {k}. {v}")
    print("  0. Выход")

    choice = input("\n> ").strip()

    if choice == "0":
        break
    elif choice == "1":
        export_all_chats(platform)
    elif choice == "2":
        op_id = input("Введите ID оператора (например OP-001): ").strip()
        if op_id not in platform.operators:
            print(f"Оператор {op_id} не найден")
            continue
        export_chats_by_operator(platform, op_id)
    elif choice == "3":
        user_id = input("Введите ID пользователя (например US-001): ").strip()
        if user_id not in platform.users:
            print(f"Пользователь {user_id} не найден")
            continue
        export_chats_by_user(platform, user_id)
    elif choice == "4":
        export_operators_db(platform)
    elif choice == "5":
        export_users_db(platform)
    else:
        print("Неверный выбор")

    print()
