"""
Демо-скрипт: запуск всех 5 типов выгрузок из сохранённого состояния.

Запуск:  python demo_exports_all_types.py

Зависимость: сначала запустите demo_chats.py для создания platform_state.json.

Выполняет:
  1. Выгрузка всех чатов
  2. Выгрузка чатов случайного оператора
  3. Выгрузка чатов случайного пользователя
  4. База профилей операторов
  5. База профилей пользователей
"""
import json
import random
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

# Загружаем ранее сохранённое состояние платформы
with open("platform_state.json", "r", encoding="utf-8") as f:
    platform = SupportPlatform.from_dict(json.load(f))

print(f"Операторов: {len(platform.operators)}, пользователей: {len(platform.users)}, "
      f"чатов: {len(platform.chats)}")

# Запускаем все типы выгрузок по очереди
export_all_chats(platform)

rand_op = random.choice(list(platform.operators.values()))
export_chats_by_operator(platform, rand_op.person_id)

rand_user = random.choice(list(platform.users.values()))
export_chats_by_user(platform, rand_user.person_id)

export_operators_db(platform)
export_users_db(platform)
