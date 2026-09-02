# Пакет support_platform — симуляция платформы поддержки.
#
# Состав:
#   data.py       — статические списки (имена, темы, шаблоны сообщений)
#   entities.py   — модели данных: Person, Operator, User, Chat
#   core.py       — SupportPlatform: управление чатами, статистика, сериализация
#   generators.py — случайная генерация операторов, пользователей и истории
#   export.py     — выгрузка данных в JSON и консоль

from .entities import Person, Operator, User, Chat
from .core import SupportPlatform
from .generators import (
    generate_operators,
    generate_users,
    generate_history,
    generate_platform,
    random_person_fields,
    female_surname,
)
from .export import (
    save_export,
    export_all_chats,
    export_chats_by_operator,
    export_chats_by_user,
    export_operators_db,
    export_users_db,
)

__all__ = [
    "Person", "Operator", "User", "Chat", "SupportPlatform",
    "generate_operators", "generate_users", "generate_history",
    "generate_platform", "random_person_fields", "female_surname",
    "save_export", "export_all_chats", "export_chats_by_operator",
    "export_chats_by_user", "export_operators_db", "export_users_db",
]
