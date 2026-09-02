import random
from datetime import datetime

from .entities import Operator, User, Chat


# Основной класс платформы поддержки.
# Хранит всех операторов, пользователей и чаты.
# Предоставляет API для управления жизненным циклом чатов,
# а также методы для построения профилей и выгрузки данных.
class SupportPlatform:
    def __init__(self):
        # Хранилища: id -> объект
        self.operators = {}
        self.users = {}
        self.chats = {}
        # Автоинкремент ID
        self._next_chat_id = 1
        self._next_operator_id = 1
        self._next_user_id = 1

    # --- Управление операторами и пользователями ---

    def add_operator(self, operator):
        """Зарегистрировать оператора, присвоить ему ID и вернуть его."""
        operator.person_id = f"OP-{self._next_operator_id:03d}"
        self._next_operator_id += 1
        self.operators[operator.person_id] = operator
        return operator

    def add_user(self, user):
        """Зарегистрировать пользователя, присвоить ему ID и вернуть его."""
        user.person_id = f"US-{self._next_user_id:03d}"
        self._next_user_id += 1
        self.users[user.person_id] = user
        return user

    # --- Вспомогательные методы поиска (принимают объект или ID) ---

    def get_operator(self, operator):
        """Получить оператора по объекту или строковому ID."""
        if isinstance(operator, Operator):
            return operator
        return self.operators[operator]

    def get_user(self, user):
        """Получить пользователя по объекту или строковому ID."""
        if isinstance(user, User):
            return user
        return self.users[user]

    def get_chat(self, chat):
        """Получить чат по объекту или числовому ID."""
        if isinstance(chat, Chat):
            return chat
        return self.chats[chat]

    def free_operators(self):
        """Вернуть список операторов, у которых нет текущих чатов."""
        return [op for op in self.operators.values() if op.is_free]

    # --- Жизненный цикл чата ---

    def create_chat(self, user, topic, first_message=None, now=None):
        """
        Создать новый чат. Если есть свободный оператор — сразу назначить,
        иначе чат остаётся в очереди (operator=None).
        """
        user = self.get_user(user)
        now = now or datetime.now()
        free = self.free_operators()
        operator = random.choice(free) if free else None
        chat_id = self._next_chat_id
        self._next_chat_id += 1
        if first_message is None:
            first_message = f"Здравствуйте! У меня вопрос: {topic}."
        chat = Chat(chat_id, user, operator, topic, now, first_message)
        if operator is not None:
            operator.take_chat(chat_id)
        self.chats[chat_id] = chat
        return chat

    def _ensure_open(self, chat):
        """Проверить, что чат ещё открыт (иначе выбросить ошибку)."""
        if chat.is_closed:
            raise ValueError(f"Чат #{chat.chat_id} закрыт — отправка сообщений невозможна")

    def operator_reply(self, chat, text, operator=None, now=None):
        """
        Ответ оператора в чате.
        Проверяет: чат открыт, оператор назначен и совпадает (если указан).
        """
        chat = self.get_chat(chat)
        self._ensure_open(chat)
        if chat.operator is None:
            raise ValueError(
                f"К чату #{chat.chat_id} ещё не назначен оператор (чат в очереди)")
        if operator is not None and self.get_operator(operator) is not chat.operator:
            raise ValueError(
                f"Оператор {self.get_operator(operator).person_id} не назначен "
                f"на чат #{chat.chat_id}")
        chat.add_message("operator", text, now)
        return chat

    def user_reply(self, chat, text, user=None, now=None):
        """
        Сообщение пользователя в чате.
        Проверяет: чат открыт, автор совпадает (если указан).
        """
        chat = self.get_chat(chat)
        self._ensure_open(chat)
        if user is not None and self.get_user(user) is not chat.user:
            raise ValueError(
                f"Пользователь {self.get_user(user).person_id} не является автором "
                f"чата #{chat.chat_id}")
        chat.add_message("user", text, now)
        return chat

    def close_chat(self, chat, operator=None, now=None):
        """
        Закрыть чат оператором.
        После закрытия оператор освобождается и запускается перераспределение
        чатов из очереди (если есть свободные операторы).
        """
        chat = self.get_chat(chat)
        if chat.is_closed:
            raise ValueError(f"Чат #{chat.chat_id} уже закрыт")
        if chat.operator is None:
            raise ValueError(
                f"Чат #{chat.chat_id} находится в очереди — закрывать некому")
        if operator is not None and self.get_operator(operator) is not chat.operator:
            raise ValueError(
                f"Чат #{chat.chat_id} назначен другому оператору")
        chat.close(now)
        chat.operator.release_chat(chat.chat_id)
        # После освобождения оператора — попробовать назначить чаты из очереди
        self.assign_queued_chats()
        return chat

    def reopen_chat(self, chat):
        """
        Переоткрыть ранее закрытый чат.
        Сбрасывает статус на 'open' и возвращает оператора в текущие чаты.
        CSAT сбрасывается неявно — при повторном rate() перезапишется последнее значение.
        """
        chat = self.get_chat(chat)
        if not chat.is_closed:
            raise ValueError(f"Чат #{chat.chat_id} не закрыт")
        chat.status = Chat.STATUS_OPEN
        chat.closed_at = None
        if chat.operator is not None:
            chat.operator.take_chat(chat.chat_id)
        return chat

    def rate_chat(self, chat, score, user=None):
        """
        Оценить чат по шкале 1-5.
        Проверяет, что оценивает автор чата.
        Последняя оценка перезаписывает предыдущую (если чат переоткрывался).
        """
        chat = self.get_chat(chat)
        if user is not None and self.get_user(user) is not chat.user:
            raise ValueError(
                f"Оценить чат #{chat.chat_id} может только его автор "
                f"({chat.user.person_id})")
        chat.rate(score)
        return chat

    # --- Очередь чатов ---

    def assign_queued_chats(self):
        """
        Распределить чаты из очереди между свободными операторами.
        Чаты берутся в порядке создания.
        Возвращает количество назначенных чатов.
        """
        assigned = 0
        queued = sorted((c for c in self.chats.values() if c.is_queued),
                        key=lambda c: c.created_at)
        for chat in queued:
            free = self.free_operators()
            if not free:
                break
            operator = random.choice(free)
            chat.operator = operator
            operator.take_chat(chat.chat_id)
            assigned += 1
        return assigned

    # --- Выборка чатов ---

    def chats_by_operator(self, operator):
        """Вернуть все чаты, включая текущие и историю оператора."""
        operator = self.get_operator(operator)
        return [c for c in self.chats.values()
                if c.operator is not None and c.operator.person_id == operator.person_id]

    def chats_by_user(self, user):
        """Вернуть все чаты пользователя."""
        user = self.get_user(user)
        return [c for c in self.chats.values() if c.user.person_id == user.person_id]

    # --- Профили и статистика ---

    def operator_profile(self, operator):
        """
        Собрать профиль оператора: личные данные + статистика
        (количество чатов, закрытых, открытых, средний CSAT).
        """
        operator = self.get_operator(operator)
        chats = self.chats_by_operator(operator)
        csats = [c.csat for c in chats if c.csat is not None]
        profile = operator.to_dict()
        profile.update({
            "open_chats": len(operator.open_chats),
            "total_chats": len(chats),
            "closed_chats": sum(1 for c in chats if c.is_closed),
            "rated_chats": len(csats),
            "average_csat": round(sum(csats) / len(csats), 2) if csats else None,
        })
        return profile

    def user_profile(self, user):
        """
        Собрать профиль пользователя: личные данные + статистика
        (количество чатов, оценённых, открытых, закрытых).
        """
        user = self.get_user(user)
        chats = self.chats_by_user(user)
        rated = [c.csat for c in chats if c.csat is not None]
        profile = user.to_dict()
        profile.update({
            "total_chats": len(chats),
            "open_chats": sum(1 for c in chats if not c.is_closed),
            "closed_chats": sum(1 for c in chats if c.is_closed),
            "chats_rated": len(rated),
        })
        return profile

    def stats(self):
        """
        Общая статистика платформы: количество операторов, пользователей,
        чатов по статусам, средний CSAT, количество свободных операторов.
        """
        chats = list(self.chats.values())
        closed = [c for c in chats if c.is_closed]
        csats = [c.csat for c in closed if c.csat is not None]
        return {
            "operators": len(self.operators),
            "users": len(self.users),
            "total_chats": len(chats),
            "open_chats": sum(1 for c in chats if not c.is_closed
                              and c.operator is not None),
            "queued_chats": sum(1 for c in chats if c.is_queued),
            "closed_chats": len(closed),
            "closed_with_csat": len(csats),
            "closed_without_csat": len(closed) - len(csats),
            "average_csat": round(sum(csats) / len(csats), 2) if csats else None,
            "free_operators": sum(1 for op in self.operators.values()
                                  if not op.open_chats),
        }

    # --- Сериализация (сохранение / загрузка из JSON) ---

    def to_dict(self):
        """
        Сериализовать всё состояние платформы в словарь (для JSON).
        Включает счётчики ID, все объекты операторов, пользователей и чатов.
        """
        return {
            "_next_chat_id": self._next_chat_id,
            "_next_operator_id": self._next_operator_id,
            "_next_user_id": self._next_user_id,
            "operators": {
                pid: {
                    "full_name": op.full_name,
                    "city": op.city,
                    "birth_date": op.birth_date.strftime("%Y-%m-%d"),
                    "position": op.position,
                    "experience_years": op.experience_years,
                    "open_chats": list(op.open_chats),
                    "served_chat_ids": op.served_chat_ids,
                }
                for pid, op in self.operators.items()
            },
            "users": {
                uid: {
                    "full_name": u.full_name,
                    "city": u.city,
                    "birth_date": u.birth_date.strftime("%Y-%m-%d"),
                }
                for uid, u in self.users.items()
            },
            "chats": {
                str(cid): {
                    "user_id": c.user.person_id,
                    "operator_id": c.operator.person_id if c.operator else None,
                    "topic": c.topic,
                    "status": c.status,
                    "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "closed_at": c.closed_at.strftime("%Y-%m-%d %H:%M:%S") if c.closed_at else None,
                    "csat": c.csat,
                    "messages": [
                        {"author": m["author"], "name": m["name"],
                         "text": m["text"],
                         "time": m["time"].strftime("%Y-%m-%d %H:%M:%S")}
                        for m in c.messages
                    ],
                }
                for cid, c in self.chats.items()
            },
        }

    @classmethod
    def from_dict(cls, data):
        """
        Восстановить объект SupportPlatform из словаря (обратная операция to_dict).
        Восстанавливает все связи: чаты ссылаются на операторов и пользователей,
        операторы — свои текущие и закрытые чаты.
        """
        from datetime import datetime as dt
        platform = cls()
        platform._next_chat_id = data["_next_chat_id"]
        platform._next_operator_id = data["_next_operator_id"]
        platform._next_user_id = data["_next_user_id"]
        # Восстанавливаем операторов
        for pid, od in data["operators"].items():
            op = Operator(
                od["full_name"], od["city"],
                dt.strptime(od["birth_date"], "%Y-%m-%d").date(),
                od["position"], od["experience_years"],
                person_id=pid,
            )
            op.open_chats = set(od["open_chats"])
            op.served_chat_ids = od["served_chat_ids"]
            platform.operators[pid] = op
        # Восстанавливаем пользователей
        for uid, ud in data["users"].items():
            u = User(
                ud["full_name"], ud["city"],
                dt.strptime(ud["birth_date"], "%Y-%m-%d").date(),
                person_id=uid,
            )
            platform.users[uid] = u
        # Восстанавливаем чаты
        for cid_str, cd in data["chats"].items():
            cid = int(cid_str)
            user = platform.users[cd["user_id"]]
            operator = platform.operators[cd["operator_id"]] if cd["operator_id"] else None
            c = Chat(
                cid, user, operator, cd["topic"],
                dt.strptime(cd["created_at"], "%Y-%m-%d %H:%M:%S"),
            )
            c.status = cd["status"]
            if cd["closed_at"]:
                c.closed_at = dt.strptime(cd["closed_at"], "%Y-%m-%d %H:%M:%S")
            c.csat = cd["csat"]
            c.messages = [
                {"author": m["author"], "name": m["name"],
                 "text": m["text"],
                 "time": dt.strptime(m["time"], "%Y-%m-%d %H:%M:%S")}
                for m in cd["messages"]
            ]
            platform.chats[cid] = c
        return platform
