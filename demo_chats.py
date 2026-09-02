"""
Демо-скрипт: генерация платформы и сохранение состояния в JSON.

Запуск:  python demo_chats.py

Результат:
  - Генерирует случайную платформу (операторы, пользователи, история чатов)
  - Сохраняет полное состояние в platform_state.json
  - Выводит общую статистику в консоль
"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from support_platform import generate_platform

# Генерируем платформу со случайными размерами
platform = generate_platform()

# Сохраняем состояние в JSON (файл bridge-механизм для других скриптов)
with open("platform_state.json", "w", encoding="utf-8") as f:
    json.dump(platform.to_dict(), f, ensure_ascii=False, indent=2)

# Выводим статистику
for key, value in platform.stats().items():
    print(f"  {key}: {value}")
