import json
from datetime import datetime
from pathlib import Path


# Сохраняет экспортные данные в JSON-файл в папку exports/.
# Имя файла: {name}_{timestamp}.json для уникальности.
# Возвращает путь к созданному файлу.
def save_export(export_data, name, folder="exports"):
    directory = Path(folder)
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = directory / f"{name}_{stamp}.json"
    path.write_text(json.dumps(export_data, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    return path


# Выводит шапку отчёта в консоль: заголовок, количество записей, путь к файлу.
def _report(title, path, count):
    print(f"\n=== {title} ===")
    print(f"Записей: {count}")
    print(f"Файл: {path}")


# Формирует одну строку-описание чата для консольного вывода.
def _chat_line(chat):
    operator = chat["operator"]["full_name"] if chat["operator"] else "не назначен (очередь)"
    return (f"  чат #{chat['chat_id']}: {chat['status']}, "
            f"CSAT={chat['csat']}, сообщений={len(chat['messages'])}, "
            f"пользователь={chat['user']['full_name']}, оператор={operator}")


# Выгрузка всех чатов платформы (sorted по ID).
# Сохраняет в JSON и выводит краткую информацию о каждом чате.
def export_all_chats(platform, folder="exports"):
    chats = [c.to_dict() for c in sorted(platform.chats.values(),
                                         key=lambda c: c.chat_id)]
    path = save_export(chats, "all_chats", folder)
    _report("Выгрузка: все чаты платформы", path, len(chats))
    for chat in chats:
        print(_chat_line(chat))
    return path


# Выгрузка чатов конкретного оператора.
# Включает профиль оператора (должность, стаж, статистика) и список его чатов.
def export_chats_by_operator(platform, operator_id, folder="exports"):
    operator = platform.get_operator(operator_id)
    chats = [c.to_dict() for c in
             sorted(platform.chats_by_operator(operator), key=lambda c: c.chat_id)]
    payload = {"operator": platform.operator_profile(operator), "chats": chats}
    path = save_export(payload, f"chats_by_operator_{operator.person_id}", folder)
    profile = payload["operator"]
    _report(f"Выгрузка: чаты оператора {operator.full_name} "
            f"({operator.person_id})", path, len(chats))
    print(f"  Должность: {profile['position']}, стаж: {profile['experience_years']} г., "
          f"закрыто: {profile['closed_chats']}, средний CSAT: {profile['average_csat']}")
    for chat in chats:
        print(_chat_line(chat))
    return path


# Выгрузка чатов конкретного пользователя.
# Включает профиль пользователя и список его чатов.
def export_chats_by_user(platform, user_id, folder="exports"):
    user = platform.get_user(user_id)
    chats = [c.to_dict() for c in
             sorted(platform.chats_by_user(user), key=lambda c: c.chat_id)]
    payload = {"user": platform.user_profile(user), "chats": chats}
    path = save_export(payload, f"chats_by_user_{user.person_id}", folder)
    _report(f"Выгрузка: чаты пользователя {user.full_name} "
            f"({user.person_id})", path, len(chats))
    for chat in chats:
        print(_chat_line(chat))
    return path


# Выгрузка базы профилей всех операторов (как список).
# Каждый профиль содержит личные данные + агрегированную статистику.
def export_operators_db(platform, folder="exports"):
    profiles = [platform.operator_profile(op) for op in platform.operators.values()]
    path = save_export(profiles, "operators_db", folder)
    _report("Выгрузка: база профилей операторов", path, len(profiles))
    for profile in profiles:
        print(f"  {profile['id']} {profile['full_name']}: {profile['position']}, "
              f"город {profile['city']}, стаж {profile['experience_years']} г., "
              f"чатов: {profile['total_chats']}, открытых: {profile['open_chats']}, "
              f"ср. CSAT: {profile['average_csat']}")
    return path


# Выгрузка базы профилей всех пользователей (как список).
# Каждый профиль содержит личные данные + статистику по чатам.
def export_users_db(platform, folder="exports"):
    profiles = [platform.user_profile(u) for u in platform.users.values()]
    path = save_export(profiles, "users_db", folder)
    _report("Выгрузка: база профилей пользователей", path, len(profiles))
    for profile in profiles:
        print(f"  {profile['id']} {profile['full_name']}, "
              f"город {profile['city']}, дата рождения: {profile['birth_date']}, "
              f"чатов: {profile['total_chats']}, оценено: {profile['chats_rated']}")
    return path
