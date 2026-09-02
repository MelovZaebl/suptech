import random
from datetime import datetime, timedelta

from . import data
from .core import SupportPlatform
from .entities import Operator, User


# Преобразует мужскую фамилию в женскую.
# Учитывает окончания: -ский/-цкий → -ская, -ов/-ев/-ин → -ова/-ева/-ина.
def female_surname(surname):
    if surname.endswith("ский") or surname.endswith("цкий"):
        return surname[:-2] + "ая"
    if surname.endswith("ов") or surname.endswith("ев") or surname.endswith("ин"):
        return surname + "а"
    return surname


# Генерирует случайное ФИО, город и дату рождения.
# Пол выбирается случайно (50/50), от пола зависят имя, отчество и фамилия.
def random_person_fields(rng):
    if rng.random() < 0.5:
        name = rng.choice(data.MALE_NAMES)
        patronymic = rng.choice(data.PATRONYMICS_M)
        full_name = f"{rng.choice(data.SURNAMES)} {name} {patronymic}"
    else:
        name = rng.choice(data.FEMALE_NAMES)
        patronymic = rng.choice(data.PATRONYMICS_F)
        full_name = f"{female_surname(rng.choice(data.SURNAMES))} {name} {patronymic}"
    city = rng.choice(data.CITIES)
    birth_date = datetime(rng.randint(1958, 2006),
                          rng.randint(1, 12), rng.randint(1, 28))
    return full_name, city, birth_date


# Создаёт operators_count операторов и добавляет их на платформу.
# Стаж ограничивается: не более (возраст - 18) и не более 30 лет.
def generate_operators(platform, count, rng):
    for _ in range(count):
        full_name, city, birth_date = random_person_fields(rng)
        max_experience = max(0, min(datetime.now().year - birth_date.year - 18, 30))
        experience_years = rng.randint(0, max_experience)
        platform.add_operator(Operator(
            full_name, city, birth_date, rng.choice(data.OPERATOR_POSITIONS),
            experience_years))


# Создаёт users_count пользователей и добавляет их на платформу.
def generate_users(platform, count, rng):
    for _ in range(count):
        full_name, city, birth_date = random_person_fields(rng)
        platform.add_user(User(full_name, city, birth_date))


# Генерирует историю чатов за days_span дней (по умолчанию 90).
#
# Сценарий каждого чата:
# 1. Пользователь пишет первое сообщение
# 2. Если нет свободных операторов — чат остаётся в очереди (~continue)
# 3. С вероятностью 15% оператор не отвечает (чат остаётся открытым)
# 4. Иначе: оператор отвечает → чат закрывается
# 5. С вероятностью 90% пользователь ставит оценку CSAT
# 6. С вероятностью 10% пользователь реоткрывает чат с жалобой,
#    оператор даёт доп. решение и закрывает повторно
#
# Время между событиями — случайный интервал (10-300 мин между чатами,
# 1-5 мин между ответом и закрытием, 10-30 мин до реоткрытия).
def generate_history(platform, chats_count, rng=None, days_span=90):
    rng = rng or random.Random()
    users = list(platform.users.values())
    if not users:
        raise ValueError("Сначала нужно добавить пользователей на платформу")
    t = datetime.now() - timedelta(days=days_span)
    for _ in range(chats_count):
        t += timedelta(minutes=rng.randint(10, 300))
        user = rng.choice(users)
        topic = rng.choice(data.TOPICS)
        opener = rng.choice(data.USER_OPENERS).format(topic=topic)
        chat = platform.create_chat(user, topic, first_message=opener, now=t)
        roll = rng.random()
        # Чат остался в очереди (нет свободных операторов) — пропускаем
        if chat.operator is None:
            continue
        # 15% — оператор не отвечает, чат остаётся открытым
        if roll < 0.15:
            continue
        t += timedelta(minutes=rng.randint(1, 5))
        platform.operator_reply(
            chat, rng.choice(data.OPERATOR_SOLUTIONS), now=t)
        platform.close_chat(chat, now=t)
        # 90% — пользователь оценивает чат
        if rng.random() < 0.9:
            platform.rate_chat(chat, rng.randint(1, 5), user)
        # 10% — пользователь реоткрывает чат с жалобой
        if rng.random() < 0.1:
            t += timedelta(minutes=rng.randint(10, 30))
            platform.reopen_chat(chat)
            platform.user_reply(chat, data.USER_COMPLAINT, user, now=t)
            t += timedelta(minutes=rng.randint(1, 5))
            platform.operator_reply(
                chat, data.OPERATOR_SOLUTION_AFTER_COMPLAINT, now=t)
            platform.close_chat(chat, now=t)
    return platform


# Главная функция-генератор: создаёт полную платформу с нуля.
# Принимает необязательные параметры количества (по умолчанию — случайные
# в диапазонах: 10-100 операторов, 35-100 пользователей, 120-200 чатов).
# Параметр seed фиксирует случайность для воспроизводимости.
def generate_platform(n_operators=None, n_users=None, n_chats=None, seed=None):
    rng = random.Random(seed)
    n_operators = rng.randint(10, 100) if n_operators is None else n_operators
    n_users = rng.randint(35, 100) if n_users is None else n_users
    n_chats = rng.randint(120, 200) if n_chats is None else n_chats
    platform = SupportPlatform()
    generate_operators(platform, n_operators, rng)
    generate_users(platform, n_users, rng)
    generate_history(platform, n_chats, rng)
    return platform
